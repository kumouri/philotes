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
    for key in ("A5", "A6", "A7", "A8"):
        assert "not measurable on live data" in row["reasons"][key]
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
    assert "not measurable on live data" in capsys.readouterr().out
    missing = tmp_path / "missing.db"
    with pytest.raises(SystemExit):
        main(["metrics", "--db", str(missing)])
    assert not missing.exists()
    with pytest.raises(SystemExit):
        main(["metrics", "--db", str(db), "--out", str(db)])
