"""The bot's behaviour, independent of any chat platform (docs/spec.md §9.3 MVP flow, §10, §11).

``Bot`` holds the rules. A transport adapter turns platform events into calls on it: one method
per slash command, ``card`` for a post-seed card button, and ``tick`` on a timer. Every command
returns a ``Reply`` shown only to the person who ran it. Side effects that reach other people go
through the ``Transport``: a DM when your seed forms and when it ends (§13 allows no other
notifications), the private seed channel, and reports to the moderators' channel.

What never leaves the core (§7.6, §11, §13): who else is signed up or how many, anyone's edges
except your own, whether a `more` was mutual, and any count about a player except the avoid count
moderators see beside a report.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import numpy as np

from philotes_sim.edges import HARD, MORE, SOFT, soft_avoid_weight

from . import text
from .archipelago import Automation
from .config import BotConfig
from .matching import form_seeds
from .store import DAY, PlayerRow, SignupRow, Store
from .transport import Button, Message, Transport

DISCORD_EPOCH_MS = 1420070400000
CARD_ACTIONS = ("more", "neutral", "avoid", "block", "report")
MARK_NAMES = {MORE: "more", SOFT: "avoid", HARD: "block"}  # how a stored edge reads
STYLE_AXES = {
    "comms": {"voice": -1, "either": 0, "text": 1},
    "talk": {"chatty": -1, "either": 0, "heads-down": 1},
    "intensity": {"sweaty": -1, "either": 0, "chill": 1},
}
MAX_INTERESTS = 5
_TAG = re.compile(r"^[a-z0-9][a-z0-9 _-]{0,23}$")


@dataclass(frozen=True)
class Invocation:
    """Who ran a command, and where. ``guild_id`` is None in DMs (card buttons)."""

    user_id: int
    guild_id: int | None
    is_mod: bool = False


@dataclass(frozen=True)
class Reply:
    text: str
    follow_ups: tuple[Message, ...] = field(default_factory=tuple)
    ok: bool = True


def _err(msg: str) -> Reply:
    return Reply(msg, ok=False)


def account_created(user_id: int) -> float:
    """A Discord account's creation time, read from its snowflake ID (epoch seconds)."""
    return ((user_id >> 22) + DISCORD_EPOCH_MS) / 1000.0


def ts(t: float) -> str:
    """A Discord timestamp: each reader sees it in their own time zone."""
    return f"<t:{int(t)}:f>"


def mention(user_id: int) -> str:
    return f"<@{user_id}>"


def card_id(action: str, seed_id: int, target: int) -> str:
    return f"ph:{action}:{seed_id}:{target}"


def parse_card_id(custom_id: str) -> tuple[str, int, int] | None:
    parts = custom_id.split(":")
    if len(parts) != 4 or parts[0] != "ph" or parts[1] not in CARD_ACTIONS:
        return None
    try:
        return parts[1], int(parts[2]), int(parts[3])
    except ValueError:
        return None


def card_buttons(seed_id: int, target: int) -> tuple[Button, ...]:
    return tuple(Button(card_id(a, seed_id, target), a) for a in CARD_ACTIONS)


def parse_range(s: str, lo_bound: int, hi_bound: int) -> tuple[int, int] | None:
    """``"4-6"`` or ``"5"`` → (lo, hi), inside the community's bounds."""
    m = re.fullmatch(r"\s*(\d+)\s*(?:[-–]\s*(\d+))?\s*", s)
    if m is None:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    if not lo_bound <= lo <= hi <= hi_bound:
        return None
    return lo, hi


class Bot:
    def __init__(
        self,
        cfg: BotConfig,
        store: Store,
        transport: Transport,
        clock: Callable[[], float],
        rng: np.random.Generator | None = None,
    ) -> None:
        self.cfg = cfg
        self.store = store
        self.transport = transport
        self.clock = clock
        self.rng = rng if rng is not None else np.random.default_rng()
        self.archipelago = Automation(cfg, store, transport)

    def yaml_permission(self, inv: Invocation, seed: int) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        try:
            self.archipelago.permission(seed, inv.user_id, self.clock())
        except ValueError as exc:
            return _err(str(exc))
        return Reply("Ready for YAML.")

    def submit_yaml(self, inv: Invocation, seed: int, file: bytes) -> Reply:
        allowed = self.yaml_permission(inv, seed)
        if not allowed.ok:
            return allowed
        try:
            self.archipelago.submit(seed, inv.user_id, file, self.clock())
        except (ValueError, OSError) as exc:
            return _err(str(exc) if isinstance(exc, ValueError) else "Unable to save YAML on host.")
        return Reply("YAML accepted. You can replace it until generation starts or the deadline.")

    def close(self) -> None:
        self.archipelago.close()
        self.store.close()

    # --- helpers ---------------------------------------------------------------------------

    def next_close(self, now: float) -> float:
        """The first configured weekly close strictly after ``now``."""
        w = self.cfg.window
        t = datetime.fromtimestamp(now, UTC).replace(minute=0, second=0, microsecond=0)
        t = t.replace(hour=w.close_hour_utc)
        t += timedelta(days=(w.close_weekday - t.weekday()) % 7)
        while t.timestamp() <= now:
            t += timedelta(days=7)
        return t.timestamp()

    def _window(self, now: float) -> tuple[int, float, float]:
        w = self.store.open_window()
        if w is None:
            wid = self.store.create_window(now, self.next_close(now))
            w = self.store.open_window()
            assert w is not None and w[0] == wid
        return w

    def _gate(self, inv: Invocation, need_player: bool = True) -> PlayerRow | Reply | None:
        """Refuse commands from outside the host guild, and (optionally) from non-members."""
        gid = self.cfg.community.guild_id
        if gid is not None and inv.guild_id != gid:
            return _err(f"Philotes runs only in {self.cfg.community.name}.")
        if not need_player:
            return None
        p = self.store.player(inv.user_id)
        if p is None:
            return _err("You haven't joined yet. " + text.JOIN)
        return p

    def _active(self, inv: Invocation) -> PlayerRow | Reply:
        g = self._gate(inv)
        if isinstance(g, Reply):
            return g
        assert g is not None
        if g.removed_at is not None:
            return _err(
                "This community's moderators have removed you from Philotes, so you can't sign "
                "up. You can still use /recent, /forget, /report, /mydata and /leave."
            )
        return g

    def _goal_name(self, goal: int) -> str:
        return self.cfg.window.goals[goal]

    def _shared_seeds(self, a: int, b: int) -> list[int]:
        mine = {s.id for s in self.store.seeds_of(a)}
        return sorted(s.id for s in self.store.seeds_of(b) if s.id in mine)

    def _may_mark(self, author: int, target: int, now: float) -> bool:
        """Edges only about people you shared a seed with that is running or recently ended."""
        horizon = self.cfg.safety.recently_played_days * DAY
        for sid in self._shared_seeds(author, target):
            s = self.store.seed(sid)
            if s is not None and now <= s.ends_at + horizon:
                return True
        return False

    def _recent(self, user_id: int, now: float) -> list[tuple[int, int]]:
        """(seed, person) for everyone you may still mark, most recent seed first."""
        horizon = self.cfg.safety.recently_played_days * DAY
        out: list[tuple[int, int]] = []
        seen: set[int] = set()
        for s in sorted(self.store.seeds_of(user_id), key=lambda s: -s.id):
            if now > s.ends_at + horizon:
                continue
            for m in self.store.seed_members(s.id):
                if m != user_id and m not in seen:
                    seen.add(m)
                    out.append((s.id, m))
        return out

    # --- membership and profile ------------------------------------------------------------

    def join(self, inv: Invocation, adult: bool = False) -> Reply:
        g = self._gate(inv, need_player=False)
        if isinstance(g, Reply):
            return g
        if not adult:
            return _err("Philotes is for adults only (18+) during the alpha. " + text.JOIN)
        now = self.clock()
        min_age = self.cfg.safety.min_account_age_days
        if min_age and now - account_created(inv.user_id) < min_age * DAY:
            return _err(f"Your Discord account needs to be at least {min_age} days old to join.")
        if self.store.player(inv.user_id) is not None:
            return Reply("You're already in. `/signup` to join this week's seeds.")
        self.store.add_player(inv.user_id, now)
        return Reply(
            "You're in. `/signup` for this week's seeds; `/help` lists everything.\n\n"
            + text.AVOIDS_HONOURED
        )

    def help(self, inv: Invocation) -> Reply:
        if self.store.player(inv.user_id) is None:
            return Reply(text.JOIN + "\n\n" + text.HELP)
        return Reply(text.HELP)

    def style(
        self,
        inv: Invocation,
        comms: str = "either",
        talk: str = "either",
        intensity: str = "either",
    ) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        vals = []
        for axis, given in (("comms", comms), ("talk", talk), ("intensity", intensity)):
            choices = STYLE_AXES[axis]
            if given not in choices:
                return _err(f"{axis} must be one of: {', '.join(choices)}.")
            vals.append(choices[given])
        self.store.set_style(inv.user_id, (vals[0], vals[1], vals[2]))
        return Reply(f"Style saved: {comms}, {talk}, {intensity}.")

    def interests(self, inv: Invocation, tags: str = "") -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        items = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if len(items) > MAX_INTERESTS or not all(_TAG.match(t) for t in items):
            return _err(
                f"Up to {MAX_INTERESTS} comma-separated tags, each up to 24 letters, digits, "
                "spaces, - or _."
            )
        self.store.set_interests(inv.user_id, tuple(dict.fromkeys(items)))
        return Reply("Interests saved." if items else "Interests cleared.")

    # --- sign-ups --------------------------------------------------------------------------

    def signup(
        self, inv: Invocation, goals: str, size: str | None = None, accept: str | None = None
    ) -> Reply:
        p = self._active(inv)
        if isinstance(p, Reply):
            return p
        w = self.cfg.window
        names = [g.strip().lower() for g in goals.split(",") if g.strip()]
        if not names or any(n not in w.goals for n in names) or len(set(names)) != len(names):
            return _err(f"goals: one or more of {', '.join(w.goals)}, first choice first.")
        bad_size = _err(f"Sizes look like 4-6 or 5, between {w.size_min} and {w.size_max}.")
        pref = w.default_preferred if size is None else parse_range(size, w.size_min, w.size_max)
        if pref is None:
            return bad_size
        if accept is None:
            d = w.default_accepted
            acc = (min(d[0], pref[0]), max(d[1], pref[1]))
        else:
            parsed = parse_range(accept, w.size_min, w.size_max)
            if parsed is None:
                return bad_size
            acc = parsed
        if not acc[0] <= pref[0] <= pref[1] <= acc[1]:
            return _err("Your preferred size has to sit inside the sizes you'd accept.")
        now = self.clock()
        wid, _, closes = self._window(now)
        prev = self.store.signup(wid, inv.user_id)
        self.store.upsert_signup(
            SignupRow(
                wid,
                inv.user_id,
                tuple(w.goals.index(n) for n in names),
                pref,
                acc,
                prev.signed_at if prev else now,  # changing a sign-up keeps your place
            )
        )
        return Reply(
            text.SIGNED_UP.format(
                goals=", ".join(names),
                pref=f"{pref[0]}–{pref[1]}",
                acc=f"{acc[0]}–{acc[1]}",
                closes=ts(closes),
            )
        )

    def withdraw(self, inv: Invocation) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        w = self.store.open_window()
        if w is None or not self.store.delete_signup(w[0], inv.user_id):
            return Reply("You weren't signed up.")
        return Reply("Sign-up withdrawn.")

    def status(self, inv: Invocation) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        now = self.clock()
        wid, opened, closes = self._window(now)
        lines = []
        s = self.store.signup(wid, inv.user_id)
        if s is None:
            lines.append(f"Not signed up this week. The window closes {ts(closes)}.")
        else:
            goals = ", ".join(self._goal_name(g) for g in s.goals)
            carried = " (carried over from an earlier week)" if s.signed_at < opened else ""
            lines.append(
                f"Signed up{carried}: {goals}, size {s.pref[0]}–{s.pref[1]} "
                f"(accepting {s.acc[0]}–{s.acc[1]}). Seeds form {ts(closes)}."
            )
        running = [x for x in self.store.seeds_of(inv.user_id) if x.ends_at > now]
        for x in running:
            where = f"<#{x.channel_id}>" if x.channel_id else "no channel"
            lines.append(
                f"Seed #{x.id} ({self._goal_name(x.goal)}), {where}, runs until {ts(x.ends_at)}."
            )
            job = self.archipelago.job(x.id)
            if job:
                submitted = (
                    self.store._one(
                        "SELECT 1 FROM ap_yamls WHERE seed_id = ? AND user_id = ?",
                        x.id,
                        inv.user_id,
                    )
                    is not None
                )
                lines.append(
                    f"Archipelago: {job['status']}; your YAML: "
                    f"{'submitted' if submitted else 'missing'}; "
                    f"submission deadline {ts(job['deadline'])}."
                )
        if p.removed_at is not None:
            lines.append("Moderators have removed you from matching.")
        return Reply("\n".join(lines))

    # --- edges: the post-seed card, /recent, /forget, /report ------------------------------

    def recent(self, inv: Invocation) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        now = self.clock()
        people = self._recent(inv.user_id, now)
        if not people:
            return Reply("Nobody yet: people show up here once you share a seed with them.")
        follow = []
        for sid, other in people:
            e = self.store.edge(inv.user_id, other)
            current = "neutral" if e is None else MARK_NAMES[e.kind]
            line = f"{mention(other)} (seed #{sid}) — yours: {current}"
            follow.append(Message(line, card_buttons(sid, other)))
        return Reply(
            "People you've played with lately. Only you can see what you chose.\n\n"
            + text.AVOIDS_HONOURED,
            tuple(follow),
        )

    def card(self, inv: Invocation, custom_id: str, reason: str | None = None) -> Reply:
        """A post-seed card or /recent button. Works from DMs; reports need a ``reason``."""
        parsed = parse_card_id(custom_id)
        if parsed is None:
            return _err("That button isn't recognised.")
        action, seed_id, target = parsed
        if self.store.player(inv.user_id) is None:
            return _err("You're no longer in Philotes.")
        if action == "report":
            return self._report(inv.user_id, target, reason or "", seed_id)
        reply = self._mark(inv.user_id, target, action)
        if reply.ok:
            from .measurement import save_a8

            save_a8(
                self.store,
                inv.user_id,
                target,
                action,
                self.clock(),
                self.cfg.safety.coplay_retention_days,
            )
        return reply

    def forget(self, inv: Invocation, user: int) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        if self.store.clear_edge(inv.user_id, user):
            return Reply(f"Cleared your mark on {mention(user)}. They're neutral to you now.")
        return Reply(f"You have no mark on {mention(user)}.")

    def report(self, inv: Invocation, user: int, reason: str) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        shared = self._shared_seeds(inv.user_id, user)
        return self._report(inv.user_id, user, reason, shared[-1] if shared else None)

    def _mark(self, author: int, target: int, action: str) -> Reply:
        now = self.clock()
        if target == author:
            return _err("That's you.")
        if not self._may_mark(author, target, now):
            days = self.cfg.safety.recently_played_days
            return _err(
                f"You can mark someone while you share a seed and for {days} days after it ends. "
                "You can still /forget an older mark, or /report."
            )
        if action == "neutral":
            self.store.clear_edge(author, target)
            return Reply(f"{mention(target)} is neutral to you.")
        if action == "more":
            self.store.set_edge(author, target, MORE, now)
            return Reply(f"Saved: you'd like more seeds with {mention(target)}.")
        if action == "avoid":
            self.store.set_edge(author, target, SOFT, now)
            return Reply(
                f"Saved: you'd rather not be matched with {mention(target)}. This fades over a few "
                "weeks; use block for never.\n\n" + text.AVOIDS_HONOURED
            )
        assert action == "block"
        cur = self.store.edge(author, target)
        if cur is not None and cur.kind == HARD:
            return Reply(f"{mention(target)} is already blocked.")
        cap = self.cfg.safety.hard_cap
        if self.store.capped_blocks(author) >= cap:
            # Over the cap a block becomes a soft avoid, as in the Phase 0 sim (EdgeStore.set_hard).
            self.store.set_edge(author, target, SOFT, now)
            return Reply(
                f"You've used all {cap} blocks, so this was saved as an avoid. /forget a block to "
                "free a slot. A report always blocks, outside the limit.\n\n" + text.AVOIDS_HONOURED
            )
        self.store.set_edge(author, target, HARD, now)
        return Reply(
            f"Blocked: you won't be matched with {mention(target)}.\n\n" + text.AVOIDS_HONOURED
        )

    def _report(self, reporter: int, target: int, reason: str, seed_id: int | None) -> Reply:
        now = self.clock()
        reason = reason.strip()
        if target == reporter:
            return _err("That's you.")
        if not reason:
            return _err("A report needs a short description of what happened.")
        if not self._shared_seeds(reporter, target):
            return _err("You can report people you've been in a seed with.")
        rid = self.store.add_report(reporter, target, seed_id, reason[:1500], now)
        self.store.set_edge(reporter, target, HARD, now, via_report=True)  # §10: outside the cap
        pol = self.cfg.policy()
        avoids = self.store.active_avoids_on(
            target, now, pol.soft_half_life_days, pol.soft_negligible
        )
        self.transport.post_mod(
            Message(
                f"**Report #{rid}** from {mention(reporter)} about {mention(target)}"
                + (f" (seed #{seed_id})" if seed_id else "")
                + f":\n> {reason[:1500]}\n"
                f"People currently avoiding or blocking them, this reporter included: {avoids}. "
                "That is context only; it is not a verdict.\n"
                f"`/mod resolve report:{rid}` when handled; `/mod remove` takes someone out of "
                "matching."
            )
        )
        return Reply(
            "Your report has gone to this community's moderators, and you won't be matched with "
            "them again. Thank you for telling us."
        )

    # --- your data (§11) -------------------------------------------------------------------

    def graduated(self, inv: Invocation, confirm: bool = False) -> Reply:
        p = self._gate(inv)
        if isinstance(p, Reply):
            return p
        if not confirm:
            return _err(
                "Optionally report that a group you found through Philotes now plays in "
                "its own server/chat: /graduated confirm:true. No names, links or members "
                "are collected. One report per account; /leave erases it."
            )
        self.store._exec(
            "INSERT OR IGNORE INTO alpha_graduations VALUES (?, ?)", inv.user_id, self.clock()
        )
        return Reply("Thank you. Your voluntary graduation report is counted anonymously.")

    def mydata(self, inv: Invocation) -> Reply:
        p = self.store.player(inv.user_id)
        if p is None:
            return Reply("We hold nothing about you.")
        now = self.clock()
        hl = self.cfg.safety.soft_half_life_days
        w = self.store.open_window()
        signup = self.store.signup(w[0], inv.user_id) if w else None
        data = {
            "your_alpha_placement_totals": self.store._all(
                "SELECT week, entries, placed FROM alpha_rates WHERE user_id = ?", inv.user_id
            ),
            "your_graduation_report": self.store._one(
                "SELECT t FROM alpha_graduations WHERE user_id = ?", inv.user_id
            ),
            "your_archipelago_yamls": [
                {"seed": sid, "yaml": content.decode("utf-8")}
                for sid, content in self.store._all(
                    "SELECT seed_id, content FROM ap_yamls WHERE user_id = ?", inv.user_id
                )
            ],
            "user_id": str(p.user_id),
            "joined_at": _iso(p.joined_at),
            "style": style_names(p.style),
            "interests": list(p.interests),
            "seeds_played": p.seeds_played,
            "removed_by_moderators": p.removed_at is not None,
            "signup": None
            if signup is None
            else {
                "goals": [self._goal_name(g) for g in signup.goals],
                "preferred": list(signup.pref),
                "accepted": list(signup.acc),
                "signed_at": _iso(signup.signed_at),
            },
            "seeds": [
                {
                    "seed": s.id,
                    "goal": self._goal_name(s.goal),
                    "formed_at": _iso(s.formed_at),
                    "ends_at": _iso(s.ends_at),
                    "with": [str(m) for m in self.store.seed_members(s.id) if m != p.user_id],
                }
                for s in self.store.seeds_of(p.user_id)
            ],
            "your_marks": [
                {
                    "about": str(e.target),
                    "kind": MARK_NAMES[e.kind],
                    "set_at": _iso(e.t),
                    **({"from_report": True} if e.via_report else {}),
                    **(
                        {"strength_now": round(soft_avoid_weight((now - e.t) / 60.0, hl), 3)}
                        if e.kind == SOFT
                        else {}
                    ),
                }
                for e in self.store.edges_of(p.user_id)
            ],
            "played_with": [
                {"user_id": str(o), "seeds_together": c, "last": _iso(t)}
                for o, c, t in self.store.coplay_of(p.user_id)
            ],
            "reports_you_filed": [
                {"report": r.id, "about": str(r.target), "filed_at": _iso(r.filed_at)}
                for r in self.store.reports()
                if r.reporter == p.user_id
            ],
        }
        return Reply(
            "Everything Philotes holds about you. Marks other people set about you are never "
            "shown, to anyone.\n```json\n" + json.dumps(data, indent=1) + "\n```"
        )

    def leave(self, inv: Invocation, confirm: bool = False) -> Reply:
        if self.store.player(inv.user_id) is None:
            return Reply("We hold nothing about you.")
        if not confirm:
            return _err(
                "This deletes your profile, sign-up, seed history and every mark set by you or "
                "about you, plus your submitted YAMLs. If your YAML has been generated, the "
                "whole local room and its generated files/channel are deleted because they "
                "combine player data. Downloaded or third-party copies cannot be recalled. "
                "Reports you filed stay with the moderators. Run `/leave confirm:true` "
                "to go ahead."
            )
        self.archipelago.forget(inv.user_id)
        self.store.delete_player(inv.user_id)
        return Reply("Done. Everything about you is deleted. You can /join again any time.")

    # --- moderators (§10) ------------------------------------------------------------------

    def _mod(self, inv: Invocation) -> Reply | None:
        g = self._gate(inv, need_player=False)
        if isinstance(g, Reply):
            return g
        return None if inv.is_mod else _err("Moderators only.")

    def mod_remove(self, inv: Invocation, user: int, reason: str = "") -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        if self.store.player(user) is None:
            return _err(f"{mention(user)} isn't in Philotes.")
        self.store.set_removed(user, self.clock(), reason.strip() or "no reason given")
        self.store.delete_user_signups(user)
        self.store.audit(inv.user_id, "remove", str(user), reason[:1500], self.clock())
        return Reply(
            f"{mention(user)} is out of matching and their sign-up is withdrawn. Seeds they are "
            "already in are unchanged."
        )

    def mod_restore(self, inv: Invocation, user: int) -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        if self.store.player(user) is None:
            return _err(f"{mention(user)} isn't in Philotes.")
        self.store.set_removed(user, None, None)
        self.store.audit(inv.user_id, "restore", str(user), "", self.clock())
        return Reply(f"{mention(user)} can sign up again.")

    def mod_reports(self, inv: Invocation) -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        self.store.audit(inv.user_id, "reports", "open", "", self.clock())
        rows = self.store.reports("open")
        if not rows:
            return Reply("No open reports.")
        return Reply(
            "\n".join(
                f"#{x.id} {ts(x.filed_at)}: {mention(x.reporter)} about {mention(x.target)}"
                f" — {x.reason[:200]}"
                for x in rows
            )
        )

    def mod_resolve(
        self, inv: Invocation, report: int, note: str = "", outcome: str = "resolved"
    ) -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        if outcome not in ("open", "resolved", "abusive", "false"):
            return _err("Outcome must be open, resolved, abusive or false.")
        old = next((r for r in self.store.reports() if r.id == report), None)
        if old is None:
            return _err(f"No report #{report}.")
        self.store.review_report(
            report,
            outcome,
            note.strip()[:1500] or outcome,
            inv.user_id,
            f"{old.status} ({old.resolution or 'no note'}) -> {outcome}: {note.strip()[:1500]}",
            self.clock(),
        )
        self._review_signals()
        return Reply(f"Report #{report} {outcome}. Safety block unchanged.")

    def mod_history(self, inv: Invocation, user: int, page: int = 1) -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        if page < 1:
            return _err("Page must be at least 1.")
        rows = [r for r in reversed(self.store.reports()) if user in (r.reporter, r.target)]
        self.store.audit(inv.user_id, "history", str(user), f"page {page}", self.clock())
        total = sum(r.reporter == user for r in rows)
        bad = sum(r.reporter == user and r.status in ("abusive", "false") for r in rows)
        lines = [
            f"Report history for {mention(user)}; page {page}/{max(1, (len(rows) + 9) // 10)}; "
            f"abusive/false filed: {bad}/{total} ({bad / total:.0%})."
            if total
            else f"Report history for {mention(user)}; page {page}; no reports filed."
        ]
        for r in rows[(page - 1) * 10 : page * 10]:
            changed = self.store._one(
                "SELECT t FROM moderation_audit WHERE action = 'resolve'"
                " AND subject = ? ORDER BY id DESC LIMIT 1",
                str(r.id),
            )
            outcome_date = ts(changed[0]) if changed else "not reviewed"
            lines.append(
                f"#{r.id} {ts(r.filed_at)} {'filed' if r.reporter == user else 'received'}: "
                f"{mention(r.reporter)} about {mention(r.target)} — {r.status}; "
                f"{r.resolution or 'no outcome'}; outcome date: {outcome_date}"
            )
        return Reply("\n".join(lines))

    def mod_audit(self, inv: Invocation, page: int = 1) -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        if page < 1:
            return _err("Page must be at least 1.")
        self.store.audit(inv.user_id, "audit", "log", f"page {page}", self.clock())
        rows = self.store._all(
            "SELECT * FROM moderation_audit ORDER BY id DESC LIMIT 10 OFFSET ?", (page - 1) * 10
        )
        return Reply(
            f"Audit page {page}\n"
            + "\n".join(
                f"#{id} {ts(t)} {mention(actor)} {action} {subject}: {detail}"
                for id, actor, action, subject, detail, t in rows
            )
        )

    def _review_signals(self) -> None:
        from .moderation import abusive, coordinated

        now = self.clock()
        flags = coordinated(self.store, now) | abusive(self.store)
        self.store._exec("DELETE FROM review_notices WHERE t < ?", now - 30 * DAY)
        for key, evidence in flags.items():
            if self.store._one("SELECT key FROM review_notices WHERE key = ?", key):
                continue
            if self.transport.post_mod(Message(evidence)):
                self.store._exec("INSERT INTO review_notices VALUES (?, ?)", key, now)

    def mod_metrics(self, inv: Invocation) -> Reply:
        if (r := self._mod(inv)) is not None:
            return r
        from .measurement import render, report

        return Reply(render(report(self.store, self.cfg, self.clock())))

    def mod_close_window(self, inv: Invocation) -> Reply:
        """Close this week's window now and form seeds (operations and testing)."""
        if (r := self._mod(inv)) is not None:
            return r
        now = self.clock()
        wid, _, _ = self._window(now)
        n = self._close_and_form(wid, now)
        self.store.audit(inv.user_id, "close-window", str(wid), f"{n} seeds", now)
        return Reply(f"Window closed: {n} seed(s) formed. The next window is open.")

    # --- the clock -------------------------------------------------------------------------

    def tick(self) -> None:
        """Run on a timer (every minute is plenty). Idempotent: safe to call at any rate."""
        now = self.clock()
        wid, _, closes = self._window(now)
        if closes <= now:
            self._close_and_form(wid, now)
        self.archipelago.tick(now)
        horizon = self.cfg.safety.recently_played_days * DAY
        for s in self.store.seeds():
            if not s.cards_sent and s.ends_at <= now:
                self._send_cards(s.id, s.goal)
            if s.cards_sent and not s.channel_closed and s.ends_at + horizon <= now:
                if s.channel_id is not None:
                    self.transport.delete_channel(s.channel_id)
                self.store.mark_channel_closed(s.id)
        self._review_signals()
        sf = self.cfg.safety
        self.store.purge(
            now, sf.soft_half_life_days, self.cfg.policy().soft_negligible, sf.coplay_retention_days
        )

    def _close_and_form(self, wid: int, now: float) -> int:
        signups = self.store.signups(wid)
        formed = form_seeds(self.store, self.cfg, signups, now, self.rng)
        from .measurement import close_counts, save_close, save_history

        counts = close_counts(self.store, self.cfg, signups, formed, now)
        save_history(self.store, wid, now, signups, formed)
        w = self.cfg.window
        for goal, members in formed:
            days = w.goal_days[goal]
            sid = self.store.create_seed(goal, members, now, now + days * DAY)
            name = self._goal_name(goal)
            welcome = text.SEED_CHANNEL_WELCOME.format(
                seed=sid, goal=name, days=days, mentions=", ".join(mention(m) for m in members)
            )
            if self.cfg.archipelago.enabled:
                welcome = welcome.replace(
                    "Share your Archipelago YAMLs here and pick one person to generate "
                    "and host the seed.",
                    "The bot will collect player YAMLs and generate and host the seed.",
                )
            chan = f"seed-{sid}-{name}"
            cid = self.transport.create_seed_channel(chan, members, Message(welcome))
            self.store.set_seed_channel(sid, cid)
            if self.cfg.archipelago.enabled:
                self.archipelago.formed(self.store.seed(sid))
            where = f"<#{cid}>" if cid is not None else "being set up by the moderators"
            for m in members:
                self.transport.send_dm(
                    m,
                    Message(
                        text.SEED_FORMED_DM.format(seed=sid, goal=name, n=len(members), where=where)
                    ),
                )
        save_close(self.store, wid, now, counts)
        self.store.close_window(wid)
        new_wid = self.store.create_window(now, self.next_close(now))
        placed = {m for _, members in formed for m in members}
        carry = []
        for s in signups:
            p = self.store.player(s.user_id)
            if s.user_id not in placed and p is not None and p.removed_at is None:
                carry.append(s.user_id)
        self.store.move_signups(wid, new_wid, carry)  # §7.5 step 7: keep waiting, keep priority
        return len(formed)

    def _send_cards(self, seed_id: int, goal: int) -> None:
        members = self.store.seed_members(seed_id)
        s = self.cfg.safety
        header = text.CARD_HEADER.format(
            seed=seed_id, goal=self._goal_name(goal), cap=s.hard_cap, days=s.recently_played_days
        )
        for u in members:
            others = [m for m in members if m != u]
            if not others:
                continue
            self.transport.send_dm(u, Message(header))
            for o in others:
                self.transport.send_dm(u, Message(mention(o), card_buttons(seed_id, o)))
        self.store.add_seeds_played(members)
        self.store.mark_cards_sent(seed_id)
        self.store.sample_first_mutual(self.clock())


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, UTC).isoformat(timespec="seconds")


def style_names(style: tuple[int, ...]) -> dict[str, str]:
    """(-1, 0, 1) → {"comms": "voice", "talk": "either", "intensity": "chill"}."""
    out = {}
    for (axis, choices), v in zip(STYLE_AXES.items(), style, strict=True):
        out[axis] = next(name for name, val in choices.items() if val == v)
    return out
