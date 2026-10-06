"""Matcher v0 quality against the exact CP-SAT baseline (docs/spec.md §7.1 step 4, §12).

Pools are captured from real simulation runs: the exact candidates, edges and weights the matcher
saw. Each is solved by the heuristic and by CP-SAT with a generous deterministic budget. The gap is
reported in placements (the dominant term) and in objective points.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from typing import Any

from .config import Policy, async_baseline, live_baseline, with_overrides
from .experiments import CLOSE_ONLY
from .matcher import solve_cpsat, solve_heuristic
from .sim import Simulation

SOURCES: list[tuple[str, Any]] = [
    (
        "live M=500 generous, 5-min batches",
        lambda: with_overrides(
            live_baseline(weeks=4),
            {"population.M": 500, "shape.habit": "generous", "shape.tick_seconds": 300.0},
        ),
    ),
    (
        "live M=200 windows, 15-min batches",
        lambda: with_overrides(live_baseline(weeks=4), {"shape.tick_seconds": 900.0}),
    ),
    (
        "async M=50 batch at close",
        lambda: with_overrides(async_baseline(weeks=10), {"population.M": 50, **CLOSE_ONLY}),
    ),
    (
        "async M=100 rolling 24 h",
        lambda: with_overrides(async_baseline(weeks=10), {"shape.cadence_hours": 24.0}),
    ),
]


def _compare(job: tuple[str, int, int, float]) -> list[dict[str, Any]]:
    label, src_idx, per_source, det_time = job
    scn = SOURCES[src_idx][1]()
    rec = Simulation(scn, capture_contexts=10**6).run()
    pools = [c for c in rec.contexts if 6 <= c.n <= 40]
    step = max(1, len(pools) // per_source)
    pools = pools[::step][:per_source]
    policy = Policy(cpsat_det_time=det_time)
    rows = []
    for k, ctx in enumerate(pools):
        h = solve_heuristic(ctx, policy)
        e = solve_cpsat(ctx, policy)
        best = max(e.score, h.score)
        rows.append(
            {
                "source": label,
                "pool": k,
                "n": ctx.n,
                "heuristic_placed": sum(len(lob) for lob in h.lobbies),
                "cpsat_placed": sum(len(lob) for lob in e.lobbies),
                "heuristic_score": h.score,
                "cpsat_score": e.score,
                "cpsat_optimal": e.optimal,
                "cpsat_bound": e.bound,
                "score_gap_pct": 100.0 * (best - h.score) / best if best else 0.0,
                "heuristic_ms": 1000 * h.seconds,
                "cpsat_ms": 1000 * e.seconds,
            }
        )
    return rows


def compare(per_source: int = 30, det_time: float = 30.0, workers: int | None = None) -> list[dict]:
    jobs = [(label, i, per_source, det_time) for i, (label, _) in enumerate(SOURCES)]
    out: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers or len(jobs)) as ex:
        for rows in ex.map(_compare, jobs):
            out.extend(rows)
    return out


def summary_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| pools from | pools | mean N | CP-SAT proved optimal | heuristic placed fewer | "
        "mean score gap | worst score gap | heuristic ms | CP-SAT ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label in dict.fromkeys(r["source"] for r in rows):
        rs = [r for r in rows if r["source"] == label]
        n = len(rs)
        lines.append(
            f"| {label} | {n} | {sum(r['n'] for r in rs) / n:.1f} | "
            f"{sum(r['cpsat_optimal'] for r in rs)}/{n} | "
            f"{sum(r['heuristic_placed'] < r['cpsat_placed'] for r in rs)}/{n} | "
            f"{sum(r['score_gap_pct'] for r in rs) / n:.2f}% | "
            f"{max(r['score_gap_pct'] for r in rs):.2f}% | "
            f"{sum(r['heuristic_ms'] for r in rs) / n:.1f} | "
            f"{sum(r['cpsat_ms'] for r in rs) / n:.0f} |"
        )
    return "\n".join(lines)
