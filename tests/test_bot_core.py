"""The bot core end to end on the in-memory transport: §9.3 flow, §10 safety, §11 privacy."""

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from itertools import combinations

import numpy as np
import pytest

from philotes_bot import text
from philotes_bot.config import BotConfig, Community, Safety
from philotes_bot.console import FakeClock
from philotes_bot.core import (
    CARD_ACTIONS,
    DISCORD_EPOCH_MS,
    Bot,
    Invocation,
    card_id,
    parse_card_id,
)
from philotes_bot.store import DAY, Store
from philotes_bot.transport import InMemoryTransport

START = datetime(2026, 10, 12, 12, 0, tzinfo=UTC).timestamp()  # Monday; window closes Sunday 23:00
GUILD = 77
MOD = 900


@dataclass
class World:
    bot: Bot
    t: InMemoryTransport
    clock: FakeClock
    store: Store

    def advance(self, days: float) -> None:
        self.clock.t += days * DAY
        self.bot.tick()

    def run(self, who: int, method: str, /, mod: bool = False, **kw):
        return getattr(self.bot, method)(Invocation(who, GUILD, mod), **kw)

    def click(self, user: int, action: str, seed: int, target: int, reason: str | None = None):
        return self.bot.card(Invocation(user, None), card_id(action, seed, target), reason)

    def seeds(self) -> list[list[int]]:
        return [self.store.seed_members(s.id) for s in self.store.seeds()]


def world(seed: int = 0, **safety) -> World:
    cfg = BotConfig(community=Community(name="Test", guild_id=GUILD), safety=Safety(**safety))
    clock, t, store = FakeClock(START), InMemoryTransport(), Store()
    bot = Bot(cfg, store, t, clock, np.random.default_rng(seed))
    bot.tick()
    return World(bot, t, clock, store)


def join_and_sign(w: World, users, goals="short", size="4-6", accept=None) -> None:
    for u in users:
        if w.store.player(u) is None:
            assert w.run(u, "join", adult=True).ok
        kw = {"goals": goals, "size": size} | ({"accept": accept} if accept else {})
        assert w.run(u, "signup", **kw).ok


def to_close(w: World) -> None:
    w.advance(7)  # Monday noon + 7 days is past Sunday 23:00


# --- joining and signing up ------------------------------------------------------------------


def test_join_is_adults_only_in_the_host_guild_with_an_established_account():
    w = world()
    assert not w.run(1, "join", adult=False).ok
    assert not w.bot.join(Invocation(1, GUILD + 1), adult=True).ok
    young = int(w.clock.t * 1000 - DISCORD_EPOCH_MS - 86_400_000) << 22  # one day old
    assert "30 days" in w.run(young, "join", adult=True).text
    assert w.run(1, "join", adult=True).ok
    assert w.store.player(1) is not None


def test_signup_validation_and_defaults():
    w = world()
    assert not w.run(1, "signup", goals="short").ok  # not joined
    w.run(1, "join", adult=True)
    assert not w.run(1, "signup", goals="epic").ok
    assert not w.run(1, "signup", goals="short", size="9-12").ok
    assert not w.run(1, "signup", goals="short", size="4-6", accept="5-8").ok
    assert w.run(1, "signup", goals="medium,short", size="3").ok
    wid = w.store.open_window()[0]
    s = w.store.signup(wid, 1)
    assert s.goals == (1, 0) and s.pref == (3, 3) and s.acc == (3, 8)


def test_status_never_reveals_who_else_is_signed_up():
    alone, crowd = world(), world()
    join_and_sign(alone, [1])
    join_and_sign(crowd, range(1, 9))
    # Your view is identical whether nobody else or seven others signed up (§7.6: no roster).
    assert alone.run(1, "status").text == crowd.run(1, "status").text
    assert crowd.t.dms == []  # signing up notifies nobody (§13)


# --- seeds forming and the hand-off ----------------------------------------------------------


def test_window_close_forms_seeds_once_and_hands_off():
    w = world()
    join_and_sign(w, range(1, 11))
    w.advance(6)  # Sunday noon: still open
    assert w.store.seeds() == []
    w.advance(1)
    seeds = w.seeds()
    assert sorted(len(m) for m in seeds) == [4, 6] or sorted(len(m) for m in seeds) == [5, 5]
    assert sorted(u for m in seeds for u in m) == list(range(1, 11))
    for s in w.store.seeds():
        members = w.store.seed_members(s.id)
        chan = w.t.channels[s.channel_id]
        assert chan.members == members
        assert all(f"<@{u}>" in chan.messages[0].text for u in members)
    assert sorted(d.user_id for d in w.t.dms) == list(range(1, 11))  # one "formed" DM each
    wid = w.store.open_window()[0]
    assert w.store.signups(wid) == []  # nothing carried over: everyone placed
    w.bot.tick()
    assert len(w.store.seeds()) == 2  # idempotent


def test_unplaced_signups_carry_over_quietly_keeping_their_place():
    w = world()
    join_and_sign(w, [1, 2, 3], size="4", accept="4")
    signed = {u: w.store.signup(w.store.open_window()[0], u).signed_at for u in (1, 2, 3)}
    to_close(w)
    assert w.store.seeds() == []
    assert w.t.dms == []  # no "nobody wanted you" message, or any message (§7.5, §13)
    wid = w.store.open_window()[0]
    assert {s.user_id: s.signed_at for s in w.store.signups(wid)} == signed
    assert "carried over" in w.run(1, "status").text
    join_and_sign(w, [4], size="4", accept="4")
    w.advance(7)
    assert w.seeds() == [[1, 2, 3, 4]]


# --- the post-seed card and marks ------------------------------------------------------------


def test_cards_at_seed_end_say_avoids_are_honoured():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    w.t.dms.clear()
    w.advance(6)  # short seeds run 7 days
    assert w.t.dms == []
    w.advance(1)
    for u in range(1, 5):
        msgs = w.t.dms_to(u)
        assert text.AVOIDS_HONOURED in msgs[0].text  # §12 Phase 1, §14 #15
        assert "undetectable" in msgs[0].text and "not undetectable" in msgs[0].text
        people = [m for m in msgs[1:] if m.buttons]
        assert len(people) == 3
        assert tuple(b.label for b in people[0].buttons) == CARD_ACTIONS
    n = len(w.t.dms)
    w.advance(1)
    assert len(w.t.dms) == n  # sent once
    assert w.store.player(1).seeds_played == 1
    assert text.AVOIDS_HONOURED in w.run(1, "help").text
    assert text.AVOIDS_HONOURED in w.run(1, "recent").text


def test_marks_are_private_and_never_reveal_mutuality():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    sid = w.store.seeds()[0].id
    r1 = w.click(1, "more", sid, 2)
    r2 = w.click(2, "more", sid, 1)
    assert r1.ok and r2.ok
    assert r1.text.replace("<@2>", "X") == r2.text.replace("<@1>", "X")  # same words either way
    assert w.t.dms_to(1)[1:] == [] and w.t.dms_to(2)[1:] == []  # nobody is told
    av = w.click(3, "avoid", sid, 4)
    assert av.ok and text.AVOIDS_HONOURED in av.text
    assert "neutral" in w.click(3, "neutral", sid, 4).text
    assert w.store.edge(3, 4) is None


def test_block_cap_falls_back_to_avoid_and_reports_sit_outside_it():
    w = world(hard_cap=1)
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    sid = w.store.seeds()[0].id
    assert "Blocked" in w.click(1, "block", sid, 2).text
    over = w.click(1, "block", sid, 3)
    assert "used all 1 blocks" in over.text and w.store.edge(1, 3).kind == "soft"
    rep = w.click(1, "report", sid, 4, reason="slurs in the seed channel")
    assert rep.ok
    e = w.store.edge(1, 4)
    assert e.kind == "hard" and e.via_report
    assert w.store.capped_blocks(1) == 1
    assert "Cleared" in w.run(1, "forget", user=2).text
    assert "Blocked" in w.click(1, "block", sid, 3).text  # the slot is free again


def test_marks_only_on_recent_co_players():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    join_and_sign(w, range(11, 15), goals="long", size="4")
    to_close(w)
    sid = next(s.id for s in w.store.seeds() if 1 in w.store.seed_members(s.id))
    assert not w.click(1, "more", sid, 11).ok  # never played together
    assert not w.click(1, "more", sid, 1).ok  # yourself
    assert w.click(1, "more", sid, 2).ok  # while the seed runs
    w.advance(7 + 14 + 1)  # seed ended more than 14 days ago
    assert not w.click(1, "avoid", sid, 3).ok
    assert w.run(1, "recent").text.startswith("Nobody")
    assert "Cleared" in w.run(1, "forget", user=2).text  # clearing always works


def test_report_reaches_moderators_with_a_count_and_nothing_else():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    sid = w.store.seeds()[0].id
    w.click(2, "avoid", sid, 1)
    w.click(3, "more", sid, 1)
    assert not w.click(4, "report", sid, 1).ok  # a report needs a reason
    assert w.run(4, "report", user=1, reason="threats").ok
    [post] = w.t.mod_posts
    assert "<@4>" in post.text and "<@1>" in post.text and "threats" in post.text
    assert "this reporter included: 2" in post.text  # 2's avoid + 4's report block
    assert "<@2>" not in post.text and "<@3>" not in post.text  # never who avoided whom
    assert "#1" in w.run(MOD, "mod_reports", mod=True).text
    assert not w.run(1, "mod_reports").ok
    assert w.run(MOD, "mod_resolve", mod=True, report=1, note="warned").ok
    assert w.run(MOD, "mod_reports", mod=True).text == "No open reports."
    assert not w.run(4, "report", user=11, reason="x").ok  # never shared a seed


# --- the matcher across weeks ----------------------------------------------------------------


@pytest.mark.parametrize("seed", range(5))
def test_blocks_hold_and_mutual_pairs_reunite_next_week(seed):
    w = world(seed=seed)
    users = list(range(1, 13))
    join_and_sign(w, users)
    to_close(w)
    first = w.seeds()
    a, b = first[0][0], first[0][1]
    c = first[0][2]
    sa = w.store.seeds()[0].id
    w.click(a, "more", sa, b)
    w.click(b, "more", sa, a)
    w.click(a, "block", sa, c)
    join_and_sign(w, users)
    w.advance(7)
    second = w.seeds()[len(first) :]
    assert second, "week two formed seeds"
    together = [m for m in second if a in m]
    assert together and b in together[0]
    assert all(not (a in m and c in m) for m in second)


def test_removed_players_are_not_matched_and_only_mods_can_remove():
    w = world()
    join_and_sign(w, range(1, 6), size="4-5")
    assert not w.run(2, "mod_remove", user=5).ok
    assert w.run(MOD, "mod_remove", mod=True, user=5, reason="harassment").ok
    assert not w.run(5, "signup", goals="short").ok
    to_close(w)
    assert all(5 not in m for m in w.seeds())
    assert w.run(MOD, "mod_restore", mod=True, user=5).ok
    assert w.run(5, "signup", goals="short").ok


def test_mod_close_window_forms_seeds_now():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    r = w.run(MOD, "mod_close_window", mod=True)
    assert r.ok and "1 seed" in r.text
    assert w.seeds() == [[1, 2, 3, 4]]


# --- privacy and retention (§11) -------------------------------------------------------------


def test_mydata_shows_your_marks_never_marks_about_you():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    sid = w.store.seeds()[0].id
    w.click(2, "block", sid, 1)
    w.click(1, "more", sid, 3)
    out = w.run(1, "mydata").text
    assert '"about": "3"' in out and '"kind": "more"' in out
    assert '"block"' not in out


def test_leave_deletes_edges_both_ways_but_keeps_reports():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    sid = w.store.seeds()[0].id
    w.click(1, "more", sid, 2)
    w.click(2, "avoid", sid, 1)
    w.run(3, "report", user=1, reason="cheating")
    assert not w.run(1, "leave").ok  # needs confirm
    assert w.run(1, "leave", confirm=True).ok
    assert w.store.player(1) is None
    assert all(1 not in (e.author, e.target) for e in w.store.edges())
    assert all(1 not in pair[:2] for pair in w.store.coplay())
    assert len(w.store.reports()) == 1


def test_seed_channel_closes_and_soft_avoids_expire():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    s = w.store.seeds()[0]
    w.click(1, "avoid", s.id, 2)
    w.advance(7 + 13)
    assert not w.t.channels[s.channel_id].deleted
    w.advance(2)
    assert w.t.channels[s.channel_id].deleted
    assert w.store.edge(1, 2) is not None  # ~22 days: still above 5% at a 7-day half-life
    w.advance(10)
    assert w.store.edge(1, 2) is None  # ~32 days: below 5%, deleted


def test_next_close_and_card_ids():
    w = world()
    sunday = datetime(2026, 10, 18, 23, 0, tzinfo=UTC).timestamp()
    assert w.bot.next_close(START) == sunday
    assert w.bot.next_close(sunday) == sunday + 7 * DAY
    assert parse_card_id(card_id("block", 3, 99)) == ("block", 3, 99)
    assert parse_card_id("ph:hug:1:2") is None and parse_card_id("nope") is None


def test_dms_closed_does_not_break_seed_forming():
    w = world()
    w.t.dm_closed.add(2)
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    assert w.seeds() == [[1, 2, 3, 4]]
    assert 2 in w.t.channels[w.store.seeds()[0].channel_id].members


def test_every_pair_in_a_seed_gets_a_coplay_record():
    w = world()
    join_and_sign(w, range(1, 5), size="4")
    to_close(w)
    pairs = {(a, b) for a, b, _, _ in w.store.coplay()}
    assert pairs == set(combinations(range(1, 5), 2))


def test_config_is_frozen_and_replaceable():
    cfg = BotConfig()
    assert replace(cfg, db_path="x").db_path == "x"
