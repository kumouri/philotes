"""Sweep plumbing on a tiny sweep: rows round-trip through JSON and the report renders."""

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
