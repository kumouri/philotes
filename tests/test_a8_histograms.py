import math
import sqlite3

import pytest

from philotes_bot.measurement import _week, a8_metrics, report, save_a8
from philotes_bot.store import DAY, Store
from philotes_sim.metric_helpers import (
    A8_BINS,
    histogram_auc,
    histogram_error_bound,
    rejection_score,
    score_bin,
)
from philotes_sim.metrics import auc
from tests.test_bot_core import world


@pytest.mark.parametrize(
    ("pos", "neg", "expected"),
    [
        ([0, 0], [-1, -1], 1),
        ([-1], [0], 0),
        ([0], [0], 0.5),
        ([-1, 0], [-1, 0], 0.5),
        ([-0.51, -0.49], [-0.5], 0.5),
    ],
)
def test_known_auc(pos, neg, expected):
    hp, hn = [0] * A8_BINS, [0] * A8_BINS
    for values, hist in ((pos, hp), (neg, hn)):
        for value in values:
            hist[score_bin(value)] += 1
    assert auc(pos, neg) == expected
    assert histogram_auc(hp, hn) == expected
    assert abs(histogram_auc(hp, hn) - auc(pos, neg)) <= histogram_error_bound(hp, hn)
    assert math.isnan(rejection_score(0, 2))
    assert rejection_score(1, 3) == -1 / 3


def test_privacy_migration_suppression_bar_and_expiry(tmp_path):
    path = tmp_path / "legacy.db"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE legacy (value INTEGER)")
    db.execute("INSERT INTO legacy VALUES (7)")
    db.commit()
    db.close()
    store = Store(path)
    assert store._one("SELECT value FROM legacy")[0] == 7
    assert [r[1] for r in store._all("PRAGMA table_info(alpha_a8)")] == [
        "week",
        "avoided",
        "bin",
        "count",
    ]
    w = world()
    now = w.clock.t
    week = _week(now)
    w.store._exec("INSERT INTO alpha_a8 VALUES (?, 1, 255, 9)", week)
    w.store._exec("INSERT INTO alpha_a8 VALUES (?, 0, 0, 10)", week)
    metrics, sample = a8_metrics(w.store, 0, 0, now + 1)
    assert sample is None and math.isnan(metrics["detect_auc"])
    w.store._exec("UPDATE alpha_a8 SET count=10 WHERE avoided=1")
    assert report(w.store, w.bot.cfg, now)[-1]["A8"] == "n/a"
    for u in range(100):
        w.store.add_player(u + 1000, now)
    row = report(w.store, w.bot.cfg, now)[-1]
    assert row["A8"] == "FAIL" and row["detect_auc"] == 1
    w.store._exec("UPDATE alpha_a8 SET bin=0 WHERE avoided=1")
    assert report(w.store, w.bot.cfg, now)[-1]["A8"] == "pass"
    w.store.purge(now + 366 * DAY, 7, 0.05, 365)
    assert not w.store._all("SELECT * FROM alpha_a8")


def test_card_consumes_label_without_relationship_storage():
    w = world()
    now = w.clock.t
    for u in (101, 202, 303):
        w.store.add_player(u, now)
    w.store.create_seed(0, [101, 202], now - 100, now - 90)
    for offset in (70, 50, 30):
        w.store.create_seed(0, [202, 303], now - offset, now - offset + 10)
    save_a8(w.store, 101, 202, "neutral", now)
    rows = w.store._all("SELECT * FROM alpha_a8")
    assert rows == [(_week(now), 0, 255, 1)]
    save_a8(w.store, 101, 202, "more", now)
    assert w.store._all("SELECT * FROM alpha_a8") == rows
    w.store.clear_edge(101, 202)
    assert w.store._all("SELECT * FROM alpha_a8") == rows
