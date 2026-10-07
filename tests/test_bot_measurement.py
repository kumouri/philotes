"""Known synthetic histories, offline commands and anonymous exports."""

import csv
import json
import sqlite3
from dataclasses import replace

import pytest

from philotes_bot.cli import main
from philotes_bot.core import Invocation
from philotes_bot.measurement import close_counts, export, render, report, save_close
from philotes_bot.store import DAY, SignupRow, Store
from philotes_sim import experiments
from philotes_sim.edges import HARD, MORE
from tests.test_bot_core import GUILD, join_and_sign, to_close, world


def test_real_close_counts_and_repeated_history():
    w = world()
    join_and_sign(w, range(1, 5))
    to_close(w)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert (row["entries"], row["placed"], row["preferred"], row["locked"]) == (4, 4, 4, 0)
    assert [row[k] for k in ("A1", "A3", "A4")] == ["pass"] * 3
    assert row["success"]["repeat_use"] == "FAIL"
    assert row["success"]["overall"] == "FAIL"
    join_and_sign(w, range(1, 5))
    to_close(w)
    rows = report(w.store, w.bot.cfg, w.clock.t)
    assert len(rows) == 3  # two UTC weeks and cumulative
    assert rows[-1]["entries"] == 8
    assert rows[-1]["repeat_placements"] == 4
    assert rows[-1]["reunion_pair_events"] == 6
    assert rows[-1]["success"]["repeat_use"] == "pass"
    assert rows[-1]["success"]["reunions"] == "pass"
    assert rows[-1]["success"]["overall"] == "n/a"
    assert rows[-1]["confidence_intervals"] is None
    # Reading does not save another close or notify anyone.
    before = len(w.t.mod_posts)
    assert w.run(900, "mod_metrics", mod=True).ok
    assert len(w.t.mod_posts) == before
    assert not w.run(1, "mod_metrics").ok
    assert not w.bot.mod_metrics(Invocation(900, GUILD + 1, True)).ok


def test_known_failures_and_distinct_denominators():
    w = world()
    join_and_sign(w, range(1, 6), size="5", accept="3-5")
    signups = w.store.signups(w.store.open_window()[0])
    # A deliberate fixture output isolates preferred sizes from the matcher heuristic.
    counts = close_counts(w.store, w.bot.cfg, signups, [(0, [1, 2, 3])], w.clock.t)
    assert counts["entries"] == 5 and counts["placed"] == counts["slots"] == 3
    assert counts["preferred"] == 0
    save_close(w.store, 1, w.clock.t, counts)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert row["placed_share"] == 0.6 and row["pref_size_share"] == 0
    assert row["A1"] == row["A3"] == "FAIL"


def test_lockout_uses_all_goals_and_original_pool():
    w = world()
    for u in range(1, 4):
        w.store.add_player(u, w.clock.t)
    signups = [SignupRow(1, u, (0,), (3, 3), (3, 3), w.clock.t) for u in range(1, 4)]
    w.store.set_edge(1, 2, HARD, w.clock.t)
    counts = close_counts(w.store, w.bot.cfg, signups, [], w.clock.t)
    assert counts["locked"] == 3 and counts["unknown"] == 0
    save_close(w.store, 1, w.clock.t, counts)
    assert report(w.store, w.bot.cfg, w.clock.t)[-1]["A4"] == "FAIL"
    # A hard block in goal 0 is not a lockout if goal 1 provides a legal lobby.
    w.store.add_player(4, w.clock.t)
    w.store.add_player(5, w.clock.t)
    extra = [SignupRow(1, u, (1,), (3, 3), (3, 3), w.clock.t) for u in (4, 5)]
    signups[0] = replace(signups[0], goals=(0, 1))
    counts = close_counts(w.store, w.bot.cfg, signups + extra, [], w.clock.t)
    assert counts["locked"] == 2


def test_all_na_reasons_and_ruled_bar(monkeypatch):
    w = world()
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert all(row[f"A{i}"] == "n/a" for i in range(1, 9))
    for key in ("A5", "A6", "A7"):
        assert "Insufficient" in row["reasons"][key]
    assert "not measurable by design" in row["reasons"]["A8"]
    assert "Rolling cadence" in row["reasons"]["A2"]
    monkeypatch.setattr(experiments, "A8_BAR", experiments.AucBar(0.57, 2))
    assert "M = 2" in report(w.store, w.bot.cfg, w.clock.t)[-1]["reasons"]["A8"]
    for u in (1, 2):
        w.store.add_player(u, w.clock.t)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert "0.57" in row["A8_bar"]
    assert "below M" not in row["reasons"]["A8"]
    assert row["A8"] == "n/a"  # enough population does not invent labels


def test_unknown_lockout_does_not_pass():
    w = world()
    counts = dict(entries=100, placed=100, slots=100, preferred=100, locked=0, unknown=1, seeds=25)
    save_close(w.store, 1, w.clock.t, counts)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert row["A4"] == "n/a" and "node limit" in row["reasons"]["A4"]


@pytest.mark.parametrize(
    ("placed", "preferred", "locked", "expected"),
    [(900, 675, 0, ("pass", "pass", "pass")), (899, 674, 10, ("FAIL", "FAIL", "FAIL"))],
)
def test_exact_ruled_boundaries(placed, preferred, locked, expected):
    w = world()
    save_close(
        w.store,
        1,
        w.clock.t,
        dict(
            entries=1000,
            placed=placed,
            slots=placed,
            preferred=preferred,
            locked=locked,
            unknown=0,
            seeds=25,
        ),
    )
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert tuple(row[k] for k in ("A1", "A3", "A4")) == expected


def test_a8_default_population_boundary_is_not_weekly_signups():
    w = world()
    for u in range(99):
        w.store.add_player(u, w.clock.t)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert row["population.M"] == 99 and "below M = 100" in row["reasons"]["A8"]
    w.store.add_player(99, w.clock.t)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert row["population.M"] == 100 and "below M" not in row["reasons"]["A8"]
    assert row["detect_auc"] is None and row["A8"] == "n/a"


def test_privacy_exports_deletion_retention_and_persistence(tmp_path):
    w = world()
    ids = [987654321012345600 + n for n in range(4)]
    join_and_sign(w, ids)
    to_close(w)
    w.store.set_edge(ids[0], ids[1], MORE, w.clock.t)
    w.store.set_edge(ids[1], ids[0], HARD, w.clock.t)
    w.store.add_report(ids[0], ids[1], 1, "PRIVATE_REPORT_TEXT", w.clock.t)
    rows = report(w.store, w.bot.cfg, w.clock.t)
    for suffix in (".csv", ".json"):
        path = tmp_path / ("summary" + suffix)
        export(rows, path)
        content = path.read_text()
        assert all(str(u) not in content for u in ids)
        assert "PRIVATE_REPORT_TEXT" not in content
        if suffix == ".csv":
            with path.open(newline="") as f:
                assert list(csv.DictReader(f))[-1]["placed_share"] == "1.0"
        else:
            assert json.loads(content) == rows
    w.store.delete_player(ids[0])
    assert report(w.store, w.bot.cfg, w.clock.t)[-1]["retained_seats"] == 3
    assert report(w.store, w.bot.cfg, w.clock.t)[-1]["entries"] == 4  # anonymous total
    db = tmp_path / "bot.db"
    dest = sqlite3.connect(db)
    w.store.db.backup(dest)
    dest.close()
    reopened = Store(str(db))
    assert render(report(reopened, w.bot.cfg, w.clock.t)) == render(
        report(w.store, w.bot.cfg, w.clock.t)
    )
    w.clock.t += 366 * DAY
    assert report(w.store, w.bot.cfg, w.clock.t)[-1]["entries"] == 0
    w.store.purge(w.clock.t, 7, 0.01, 365)
    assert not w.store._all("SELECT * FROM alpha_windows")
    reopened.close()


def test_cli_readonly_legacy_and_no_database_creation(tmp_path, capsys):
    db = tmp_path / "bot.db"
    store = Store(str(db))
    store.db.execute("DROP TABLE alpha_windows")  # read a slice 4 database without migration
    store.db.commit()
    store.close()
    before = db.read_bytes()
    output = tmp_path / "summary.json"
    assert main(["metrics", "--db", str(db), "--out", str(output)]) == 0
    assert db.read_bytes() == before
    assert json.loads(output.read_text())[-1]["A1"] == "n/a"
    assert "not measurable by design" in capsys.readouterr().out
    missing = tmp_path / "missing.db"
    with pytest.raises(SystemExit):
        main(["metrics", "--db", str(missing)])
    assert not missing.exists()
    with pytest.raises(SystemExit):
        main(["metrics", "--db", str(db), "--out", str(db)])


def test_multiweek_measured_followup_history(tmp_path):
    from philotes_bot.measurement import save_history
    from philotes_sim.metric_helpers import match_rate_metrics, newcomer_metrics

    w = world()
    base = w.clock.t
    ids = [987654321012345600 + n for n in range(4)]
    for u in ids:
        w.store.add_player(u, base)
    # Three completed seeds; two of four newcomers succeed within the horizon.
    for week in range(3):
        t = base + week * 7 * DAY
        wid = w.store.create_window(t, t + DAY)
        members = ids if week == 0 else ids[:3]
        if week == 1:
            w.store.set_edge(ids[0], ids[1], MORE, t)
            w.store.set_edge(ids[1], ids[0], MORE, t)
        signups = [SignupRow(wid, u, (0,), (3, 4), (3, 4), t) for u in ids]
        for signup in signups:
            w.store.upsert_signup(signup)
        # Change edges after co-signup: denominator must retain the snapshot.
        if week == 1:
            w.store.clear_edge(ids[1], ids[0])
        formed = [(0, members)]
        save_history(w.store, wid, t + DAY, signups, formed)
        save_history(w.store, wid, t + DAY, signups, formed)  # idempotent
        save_close(w.store, wid, t + DAY, close_counts(w.store, w.bot.cfg, signups, formed, t))
        w.store.create_seed(0, members, t + DAY, t + 2 * DAY)
        w.store.move_signups(wid, wid + 1000, [])
    # Give the fourth newcomer enough completed seeds to be censored as a failure.
    w.store.create_seed(0, [ids[3]], base + 3 * DAY, base + 4 * DAY)
    w.store.create_seed(0, [ids[3]], base + 5 * DAY, base + 6 * DAY)
    w.clock.t = base + 22 * DAY
    for u in range(1000, 1096):
        w.store.add_player(u, base)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    expected = match_rate_metrics([(3, 3)] * 3 + [(3, 1)])
    assert row["match_rate_p10_over_median"] == expected["match_rate_p10_over_median"]
    assert row["sample_sizes"]["A5"] == 4
    assert (
        row["newcomer_within_horizon_share"]
        == newcomer_metrics([(3, 1)] * 2 + [(3, None)] * 2, 3)["newcomer_within_horizon_share"]
    )
    assert row["sample_sizes"]["A6"] == 4
    assert row["cosignup_reunion_share"] == 1
    assert row["sample_sizes"]["A7"] == 1
    assert row["population.M"] == 100
    assert row["A8"] == "n/a" and row["detect_auc"] is None
    assert "not measurable by design" in row["reasons"]["A8"]
    assert not w.store._all("SELECT * FROM alpha_pending_pairs")
    assert not w.store._all("SELECT * FROM signups")
    assert not w.store._one("SELECT name FROM sqlite_master WHERE name = 'alpha_first_cards'")
    assert all(str(u) not in render([row]) for u in ids)
    own = w.run(ids[1], "mydata").text
    assert "first_mutual" not in own and "alpha_pending" not in own
    assert not w.run(ids[0], "graduated").ok
    assert w.run(ids[0], "graduated", confirm=True).ok
    assert w.run(ids[0], "graduated", confirm=True).ok
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert row["success"]["graduation_reports"] == 1
    assert row["success"]["overall"] == "pass"
    w.store.delete_player(ids[0])
    for table in ("alpha_rates", "alpha_newcomers", "alpha_graduations"):
        assert not w.store._one(f"SELECT 1 FROM {table} WHERE user_id = ?", ids[0])
    w.clock.t += 366 * DAY
    assert report(w.store, w.bot.cfg, w.clock.t)[-1]["sample_sizes"]["A6"] == 0
    w.store.purge(w.clock.t, 7, 0.01, 365)
    for table in ("alpha_rates", "alpha_newcomers", "alpha_reunions", "alpha_graduations"):
        assert not w.store._all(f"SELECT * FROM {table}")


def test_additive_old_schema_migration_and_legacy_snapshots(tmp_path):
    from philotes_bot.measurement import save_history

    path = tmp_path / "old.db"
    store = Store(str(path))
    store.add_player(123, 0)
    store.upsert_signup(SignupRow(1, 123, (0,), (2, 2), (2, 2), 0))
    store.add_player(456, 0)
    store.upsert_signup(SignupRow(1, 456, (0,), (2, 2), (2, 2), 0))
    store.set_edge(123, 456, HARD, 0)
    for (name,) in store._all("SELECT name FROM sqlite_master WHERE name LIKE 'alpha_%'"):
        if name != "alpha_windows":
            store.db.execute(f"DROP TABLE {name}")
    store.db.commit()
    store.close()
    store = Store(str(path))
    assert store.player(123) and store.edge(123, 456).kind == HARD
    assert len(store.signups(1)) == 2
    assert not store._all("SELECT * FROM alpha_newcomers")  # no invented newcomer history
    save_history(store, 1, 1, store.signups(1), [])
    row = report(store, world().bot.cfg, 1)[-1]
    assert row["A7"] == "n/a" and "incomplete denominator" in row["reasons"]["A7"]
    store.close()
    Store(str(path)).close()  # migration is repeatable


def test_a6_completed_seed_horizon_and_cohort_as_of_week():
    w = world()
    u, v = 101, 102
    w.store.add_player(u, w.clock.t)
    w.store.add_player(v, w.clock.t)
    end = w.clock.t + 3 * DAY
    sid = w.store.create_seed(0, [u, v], w.clock.t, end)
    w.store.set_edge(u, v, MORE, w.clock.t)
    w.store.set_edge(v, u, MORE, w.clock.t)
    assert w.store._one(
        "SELECT first_mutual_session FROM alpha_newcomers WHERE user_id = ?", u
    ) == (0,)
    w.clock.t = end
    w.store.sample_first_mutual(end)
    assert w.store._one(
        "SELECT first_mutual_session FROM alpha_newcomers WHERE user_id = ?", u
    ) == (0,)
    row = report(w.store, w.bot.cfg, w.clock.t)[-1]
    assert row["newcomer_within_horizon_share"] == 1
    assert row["sample_sizes"]["A6"] == 2
    assert w.store.seed(sid)


def test_cosignup_snapshots_survive_carry_edits_and_end_on_withdrawal():
    w = world()
    for u in (1, 2, 3):
        w.store.add_player(u, w.clock.t)
    w.store.set_edge(1, 2, MORE, w.clock.t)
    w.store.set_edge(2, 1, MORE, w.clock.t)
    for u in (1, 2):
        w.store.upsert_signup(SignupRow(11, u, (0,), (2, 2), (2, 2), w.clock.t))
    w.store.clear_edge(2, 1)
    w.store.upsert_signup(SignupRow(11, 2, (0, 1), (2, 3), (2, 3), w.clock.t))
    assert w.store._one("SELECT mutual FROM alpha_pending_pairs WHERE window_id = 11") == (1,)
    w.store.move_signups(11, 12, [1, 2])
    assert w.store._one("SELECT mutual FROM alpha_pending_pairs WHERE window_id = 12") == (1,)
    assert not w.store._all("SELECT * FROM alpha_pending_pairs WHERE window_id = 11")
    w.store.delete_signup(12, 2)
    assert not w.store._all("SELECT * FROM alpha_pending_pairs")
    w.store.upsert_signup(SignupRow(12, 2, (0,), (2, 2), (2, 2), w.clock.t + DAY))
    assert w.store._one("SELECT mutual FROM alpha_pending_pairs") == (0,)
    w.store.delete_user_signups(1)
    assert not w.store._all("SELECT * FROM alpha_pending_pairs")


def test_weekly_newcomers_do_not_count_future_seed_completions():
    w = world()
    w.store.add_player(101, w.clock.t)
    for _ in range(3):
        w.store.create_seed(0, [101], w.clock.t, w.clock.t + DAY)
    rows = report(w.store, w.bot.cfg, w.clock.t)
    assert len(rows) == 2
    assert all(row["sample_sizes"]["A6"] == 0 for row in rows)
    assert all(row["A6"] == "n/a" for row in rows)
