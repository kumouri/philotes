"""Offline moderation scenarios and privacy regression checks."""

import pytest

from philotes_bot.commands import dispatch
from philotes_bot.core import Invocation
from philotes_bot.moderation import abusive, coordinated
from philotes_bot.store import DAY, Store
from tests.test_bot_core import GUILD, MOD, world


@pytest.mark.parametrize("kind", ["soft", "hard"])
def test_burst_threshold_and_window(kind):
    s = Store()
    now = 40 * DAY
    for u in (1, 2):
        s.set_edge(u, 99, kind, now)
    assert not coordinated(s, now)
    s.set_edge(3, 99, kind, now - DAY)
    assert "burst:99" in coordinated(s, now)
    s.set_edge(3, 99, kind, now - DAY - 1)
    assert not coordinated(s, now)
    s.set_edge(3, 99, "more", now)
    assert not coordinated(s, now)


def test_consistent_group_positive_and_negatives():
    s = Store()
    now = 40 * DAY
    for u in (1, 2, 3):
        for target in (90, 91, 92):
            s.set_edge(u, target, "hard", now - u * 2 * DAY)
    assert set(coordinated(s, now)) == {"together"}
    s.clear_edge(3, 92)
    assert not coordinated(s, now)
    s.set_edge(3, 92, "hard", now - 31 * DAY)
    assert not coordinated(s, now)


def test_signals_private_idempotent_and_state_unchanged():
    w = world()
    for u in (101, 102, 103):
        w.store.set_edge(u, 999, "soft", w.clock.t)
    before = w.store.edges()
    w.bot._review_signals()
    w.bot._review_signals()
    assert len(w.t.mod_posts) == 1
    evidence = w.t.mod_posts[0].text
    assert "3 accounts" in evidence and "999" in evidence
    assert all(str(u) not in evidence for u in (101, 102, 103))
    assert w.store.edges() == before
    assert not w.t.dms and not w.t.channels
    w.store.delete_player(999)
    w.clock.t += 31 * DAY
    w.bot._review_signals()
    assert not w.store._all("SELECT * FROM review_notices")


def test_abusive_rate_boundaries_and_reversal():
    s = Store()
    ids = [s.add_report(1, 2, None, "allegation", 0) for _ in range(7)]
    for rid in ids[:3]:
        s.set_report_outcome(rid, "false", "reviewed")
    assert not abusive(s)  # 3/7
    s.set_report_outcome(ids[3], "abusive", "reviewed")
    assert "reporter:1" in abusive(s)
    s.set_report_outcome(ids[3], "open", "reopened")
    assert not abusive(s)


def test_history_outcomes_audit_permissions_and_retention(tmp_path):
    w = world()
    w.store.add_player(1, w.clock.t)
    w.store.add_player(2, w.clock.t)
    w.store.create_seed(0, [1, 2], w.clock.t, w.clock.t + DAY)
    for _ in range(12):
        assert w.run(1, "report", user=2, reason="allegation").ok
    for rid in (1, 2, 3, 4, 5, 6):
        assert w.run(MOD, "mod_resolve", mod=True, report=rid, outcome="abusive").ok
    assert len(w.t.mod_posts) == 13  # reports plus repeat-reporter flag
    edge = w.store.edge(1, 2)
    assert w.run(MOD, "mod_resolve", mod=True, report=1, outcome="open").ok
    assert w.store.edge(1, 2) == edge
    assert not w.run(1, "mod_history", user=2).ok
    assert not w.run(1, "mod_audit").ok
    assert not w.bot.mod_audit(Invocation(MOD, GUILD + 1, True)).ok
    assert not w.run(MOD, "mod_history", mod=True, user=2, page=0).ok
    assert not w.run(MOD, "mod_resolve", mod=True, report=999).ok
    assert not w.run(MOD, "mod_resolve", mod=True, report=1, outcome="invalid").ok
    reply = dispatch(w.bot, Invocation(MOD, GUILD, True), "mod history", {"user": "2"})
    assert reply.text.count("received:") == 10
    assert "#12" in reply.text and "#1 " not in reply.text
    second = w.run(MOD, "mod_history", mod=True, user=2, page=2).text
    assert "#1 " in second and "outcome date:" in second
    assert "5/12" in w.run(MOD, "mod_history", mod=True, user=1).text
    assert w.run(MOD, "mod_remove", mod=True, user=2, reason="review").ok
    assert w.run(MOD, "mod_restore", mod=True, user=2).ok
    assert w.run(MOD, "mod_close_window", mod=True).ok
    assert w.run(MOD, "mod_reports", mod=True).ok
    actions = w.store._all("SELECT actor, action, t FROM moderation_audit")
    assert all(actor == MOD and t == w.clock.t for actor, _, t in actions)
    assert {a for _, a, _ in actions} >= {
        "resolve",
        "history",
        "remove",
        "restore",
        "close-window",
        "reports",
    }
    assert "resolve" in w.run(MOD, "mod_audit", mod=True, page=2).text
    w.store.purge(w.clock.t + 400 * DAY, 7, 0.01, 365)
    assert len(w.store.reports()) == 12  # moderation policy is retained, unlike co-play
    assert not w.store.coplay()
    # New tables migrate a pre-slice database and persist across restarts.
    path = str(tmp_path / "moderation.db")
    s = Store(path)
    s.audit(MOD, "test", "1", "detail", 123)
    s.close()
    s = Store(path)
    assert s._all("SELECT actor, action, t FROM moderation_audit") == [(MOD, "test", 123)]
    s.close()


def test_failed_notice_retries_and_dedup_persists(tmp_path):
    w = world()
    w.store = Store(str(tmp_path / "notices.db"))
    w.bot.store = w.store
    for u in (1, 2, 3):
        w.store.set_edge(u, 99, "hard", w.clock.t)
    post = w.t.post_mod
    w.t.post_mod = lambda message: False
    w.bot._review_signals()
    assert not w.store._all("SELECT * FROM review_notices")
    w.t.post_mod = post
    w.bot._review_signals()
    w.store.close()
    w.store = Store(str(tmp_path / "notices.db"))
    w.bot.store = w.store
    w.bot._review_signals()
    assert len(w.t.mod_posts) == 1
    w.store.close()
