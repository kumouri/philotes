"""Run the bot locally with a fake clock and the in-memory transport. No network, no token.

Each typed line is one of:

* ``as <user> [mod] /<command> [subcommand] key=value …`` — run a slash command as that user
  (``mod`` gives them the moderator role). Quote values with spaces: ``reason="spoke over us"``.
* ``as <user> click <button id> [reason…]`` — press a card button (IDs are printed with cards).
* ``advance <n>d|h|m`` — move the clock forward, then run the bot's timer once.
* ``tick`` — run the bot's timer without moving the clock.
* ``help`` / ``quit``.

After every line the console prints the reply (only the invoking user would see it), then whatever
the bot sent through the transport: DMs, seed channels, and posts to the moderators' channel.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np

from .commands import UsageError, dispatch
from .config import BotConfig
from .core import Bot, Invocation, Reply
from .store import Store
from .transport import InMemoryTransport, Message

USAGE = __doc__.split("\n\n", 1)[1].rsplit("\n\nAfter", 1)[0]


@dataclass
class FakeClock:
    t: float

    def __call__(self) -> float:
        return self.t


def _render_ts(s: str) -> str:
    def iso(m: re.Match[str]) -> str:
        return datetime.fromtimestamp(int(m.group(1)), UTC).strftime("%a %Y-%m-%d %H:%M UTC")

    return re.sub(r"<t:(\d+):\w>", iso, s)


def _fmt(msg: Message) -> str:
    out = _render_ts(msg.text)
    if msg.buttons:
        out += "\n    [" + "] [".join(f"{b.label}: {b.custom_id}" for b in msg.buttons) + "]"
    return out


class Console:
    def __init__(self, cfg: BotConfig, start: float, db: str = ":memory:", seed: int = 0) -> None:
        self.clock = FakeClock(start)
        self.transport = InMemoryTransport()
        self.store = Store(db)
        self.bot = Bot(cfg, self.store, self.transport, self.clock, np.random.default_rng(seed))
        self.guild = cfg.community.guild_id
        self._seen = (0, 0, 0)
        self.bot.tick()

    def run_line(self, line: str) -> list[str]:
        line = line.strip()
        if not line or line.startswith("#"):
            return []
        try:
            out = self._run(shlex.split(line))
        except UsageError as e:
            out = [f"! {e}"]
        return out + self._drain()

    def _run(self, words: list[str]) -> list[str]:
        head = words[0].lower()
        if head == "help":
            return [USAGE]
        if head == "tick":
            self.bot.tick()
            return []
        if head == "advance":
            m = re.fullmatch(r"(\d+(?:\.\d+)?)([dhm])", words[1] if len(words) > 1 else "")
            if m is None:
                raise UsageError("advance takes e.g. 7d, 12h or 30m")
            self.clock.t += float(m.group(1)) * {"d": 86400, "h": 3600, "m": 60}[m.group(2)]
            self.bot.tick()
            return [f"-- now {_render_ts(f'<t:{int(self.clock.t)}:f>')}"]
        if head != "as" or len(words) < 3:
            raise UsageError("expected: as <user> [mod] /command … | click …; see help")
        user = int(words[1])
        rest = words[2:]
        is_mod = rest[0] == "mod" and len(rest) > 1 and rest[1].startswith("/")
        if is_mod:
            rest = rest[1:]
        if rest[0] == "click":
            if len(rest) < 2:
                raise UsageError("click needs a button id")
            inv = Invocation(user, None, is_mod)
            return self._reply(self.bot.card(inv, rest[1], " ".join(rest[2:]) or None))
        if not rest[0].startswith("/"):
            raise UsageError("commands start with /")
        name = rest[0][1:]
        args_at = 1
        if name == "mod" and len(rest) > 1 and "=" not in rest[1]:
            name, args_at = f"mod {rest[1]}", 2
        args = {}
        for w in rest[args_at:]:
            k, sep, v = w.partition("=")
            if not sep:
                raise UsageError(f"options look like key=value, not {w!r}")
            args[k] = v
        return self._reply(dispatch(self.bot, Invocation(user, self.guild, is_mod), name, args))

    def _reply(self, r: Reply) -> list[str]:
        lines = [("> " if r.ok else "! ") + _render_ts(r.text).replace("\n", "\n  ")]
        lines += ["  " + _fmt(m).replace("\n", "\n  ") for m in r.follow_ups]
        return lines

    def _drain(self) -> list[str]:
        t = self.transport
        d0, c0, m0 = self._seen
        out = [f"  DM -> {d.user_id}: " + _fmt(d.message) for d in t.dms[d0:]]
        chans = list(t.channels.values())
        for c in chans[c0:]:
            head = f"  CHANNEL #{c.name} ({c.channel_id}) for {c.members}: "
            out.append(head + _fmt(c.messages[0]))
        out += ["  MOD CHANNEL: " + _fmt(m) for m in t.mod_posts[m0:]]
        self._seen = (len(t.dms), len(chans), len(t.mod_posts))
        return out


DEMO = """
# Ten people join and sign up for a short seed; 900 is a moderator.
as 101 /join adult=true
as 102 /join adult=true
as 103 /join adult=true
as 104 /join adult=true
as 105 /join adult=true
as 106 /join adult=true
as 107 /join adult=true
as 108 /join adult=true
as 109 /join adult=true
as 110 /join adult=true
as 101 /style comms=voice talk=chatty intensity=chill
as 101 /signup goals=short size=4-6
as 102 /signup goals=short,medium size=4-6
as 103 /signup goals=short size=4-6
as 104 /signup goals=short size=4-6
as 105 /signup goals=short size=4-6
as 106 /signup goals=short size=4-6
as 107 /signup goals=short size=4-6
as 108 /signup goals=short size=4-6
as 109 /signup goals=short size=4-6
as 110 /signup goals=short,long size=4-6
as 101 /status
# The window closes on Sunday: seeds form in one batch.
advance 7d
# A short seed runs a week; then everyone gets a card.
advance 8d
as 101 /recent
""".strip()


def demo_lines(console: Console) -> list[str]:
    """The scripted demo: two weeks of sign-ups, a card, marks, a report and a rematch."""
    out: list[str] = []
    for line in DEMO.splitlines():
        out.append(f"$ {line}" if not line.startswith("#") else line)
        out += console.run_line(line)
    # React to whoever the first seed actually put together, so the demo reads the same at any
    # matcher setting.
    seed_of = {u: s.id for s in console.store.seeds() for u in console.store.seed_members(s.id)}
    mates = [u for u in console.store.seed_members(seed_of[101]) if u != 101]
    a, b = mates[0], mates[1]
    sid = seed_of[101]
    follow = [
        f"as 101 click ph:more:{sid}:{a}",
        f"as {a} click ph:more:{sid}:101",
        f"as 101 click ph:block:{sid}:{b}",
        f'as {b} /report user=101 reason="kept spoiling the seed after being asked to stop"',
        "as 900 mod /mod reports",
        "# Next week everyone signs up again. The matcher prefers 101 with "
        f"{a} and never puts 101 with {b}.",
        *(f"as {u} /signup goals=short size=4-6" for u in range(101, 111)),
        "advance 7d",
        "as 101 /status",
        "as 101 /mydata",
    ]
    for line in follow:
        out.append(f"$ {line}" if not line.startswith("#") else line)
        out += console.run_line(line)
    return out


def repl(console: Console) -> None:  # pragma: no cover - interactive
    print(USAGE)
    while True:
        try:
            line = input("philotes> ")
        except EOFError:
            return
        if line.strip() in {"quit", "exit"}:
            return
        for out in console.run_line(line):
            print(out)
