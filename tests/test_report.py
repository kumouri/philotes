"""Sweep plumbing on a tiny sweep: rows round-trip through JSON and the report renders."""

import pytest

from philotes_sim import experiments
from philotes_sim.experiments import Group, check
from philotes_sim.report import load_rows, save_rows, write_outputs


def test_tiny_sweep_round_trips(tmp_path, monkeypatch):
    g = Group(
        "tiny",
        "live",
        "Two arms varying different knobs.",
        [{"population.M": 40}, {"population.flex_share": 1.0, "population.M": 40}],
    )
    monkeypatch.setitem(experiments.GROUPS, "tiny", g)
    monkeypatch.setattr(experiments, "LIVE_WEEKS", 3)
    rows = [experiments.run_one(("tiny", i, arm, 1)) for i, arm in enumerate(g.arms)]
    save_rows(rows, tmp_path)
    again = load_rows(tmp_path)
    assert [r["arm"] for r in again] == [0, 1]
    summary = write_outputs(again, tmp_path, "tiny")
    md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "## tiny" in md and "| base |" in md  # arm 0 does not vary flex_share
    assert {"C1", "C2", "C3", "C4", "C5"} <= set(summary[0])
    assert summary[0]["population.M"] == 40  # carried through so A8 can be scoped by M
    assert "A8 applies the ruled bar (§14 #15): detection AUC ≤ 0.60 at M ≥ 100" in md


def test_criteria_checks():
    live = check(
        {
            "wait_median_peak": 8.0,
            "lockout_tick_share": 0.02,
            "match_rate_p10_over_median": 0.6,
            "newcomer_within_horizon_share": 0.7,
            "detect_auc": 0.53,
            "peak_online_median": 10,
        },
        "live",
    )
    assert live == {"C1": "pass", "C2": "FAIL", "C3": "pass", "C4": "pass", "C5": "n/a"}


@pytest.mark.parametrize(
    ("auc", "M", "expected"),
    [
        (0.60, 100, "pass"),  # on the ruled bar (§14 #15)
        (0.61, 100, "FAIL"),
        (0.586, 500, "pass"),
        (0.61, 500, "FAIL"),
        (0.60, 50, "n/a"),  # below M = 100 the ruling does not judge A8
        (0.70, 50, "n/a"),
        (0.60, None, "n/a"),  # no community size, no scope to judge in
    ],
)
def test_a8_ruled_bar(auc, M, expected):
    row = {"detect_auc": auc, "population.M": M}
    assert check(row, "async")["A8"] == expected
