"""The Phase 0 sweep plan, the exit-criteria checks, and the parallel runner.

Each sweep group varies a few knobs around a baseline and runs every arm under the same replicate
seeds (common random numbers: the population and schedules are identical across arms, so a
difference between arms is the knob, not the draw).

``LIVE_CRITERIA`` are the §12 suggestions for live 4-player co-op. ``ASYNC_CRITERIA`` are
**proposed** here for async Archipelago (§12 says they are still to be written); they are Ceryce's
to rule on. Both were fixed before the first full sweep was run.
"""

from __future__ import annotations

import itertools
import math
import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any

from .config import Scenario, async_baseline, flatten, live_baseline, with_overrides
from .metrics import compute, lockout_by_n
from .sim import Simulation

LIVE_WEEKS = 12  # 2 burn-in + 10 measured
ASYNC_WEEKS = 26  # 4 burn-in + 22 measured sign-up windows
CLOSE_ONLY = {"shape.cadence_hours": 168.0, "shape.ladder_minutes": "1e9,1e9,1e9"}


@dataclass(frozen=True)
class Group:
    name: str
    shape: str  # "live" | "async"
    question: str
    arms: list[dict[str, Any]]
    base: dict[str, Any] | None = None
    replicate_factor: int = 1  # noisy metrics (the newcomer cohort) get more replicates


def _grid(**axes: list[Any]) -> list[dict[str, Any]]:
    keys = list(axes)
    return [dict(zip(keys, vals, strict=True)) for vals in itertools.product(*axes.values())]


def _cadence(c: str) -> dict[str, Any]:
    return dict(CLOSE_ONLY) if c == "close" else {"shape.cadence_hours": float(c)}


PHASE0: list[Group] = [
    Group(
        "live-density",
        "live",
        "R3: wait and placement by community size M and window habit (§9.1).",
        _grid(
            **{
                "population.M": [50, 100, 200, 350, 500],
                "shape.habit": ["live", "windows", "generous"],
            }
        ),
    ),
    Group(
        "live-lobby",
        "live",
        "Lobby size L and size flexibility (§8 point 3) against lockout and wait.",
        _grid(**{"population.lobby_size": [3, 4, 5], "population.M": [100, 200]})
        + _grid(**{"population.flex_share": [0.0, 1.0], "population.M": [200]}),
    ),
    Group(
        "live-half-life",
        "live",
        "§14 #9: soft-avoid half-life against lockout, avoid-holds, broken avoids and reunions.",
        _grid(
            **{
                "policy.soft_half_life_days": [7.0, 14.0, 30.0, 60.0, 90.0],
                "population.M": [100, 200, 500],
            }
        ),
    ),
    Group(
        "live-cap",
        "live",
        "§14 #8: hard-block cap against lockout, at three hard-block propensities.",
        _grid(**{"policy.hard_cap": [1, 3, 5, 10, 25], "behavior.p_hard": [0.08, 0.2, 0.4]}),
    ),
    Group(
        "live-newcomer",
        "live",
        "§7.4: newcomer-boost decay (0 = off) and anchors vs sessions to first mutual `more`.",
        _grid(
            **{
                "policy.newcomer_decay_sessions": [0, 5, 10, 20, 40],
                "policy.anchors_enabled": [True, False],
            }
        ),
        base={"population.newcomer_rate": 0.06},
        replicate_factor=2,
    ),
    Group(
        "live-noise",
        "live",
        "§7.6: matching noise against the detection test and reunions, by M.",
        _grid(**{"weights.noise": [0.0, 0.25, 0.5, 1.0, 2.0], "population.M": [50, 200, 500]}),
    ),
    Group(
        "live-tick",
        "live",
        "Matcher cadence: does batching the queue (bigger pools per run) buy reunions for wait?",
        _grid(**{"shape.tick_seconds": [30.0, 300.0, 900.0], "population.M": [200, 500]}),
    ),
    Group(
        "live-search",
        "live",
        "Kill/rethink check: can any combination of levers meet C1–C5 at M ≤ 500 (L = 4)?",
        _grid(
            **{
                "shape.habit": ["windows", "generous"],
                "population.M": [200, 350, 500],
                "population.flex_share": [0.5, 1.0],
                "population.n_games": [1, 3],
            }
        ),
    ),
    Group(
        "async-density",
        "async",
        "Async R3: time-to-seed and fill by M and matcher cadence (6 h, 24 h, batch at close).",
        [
            {"population.M": m, **_cadence(c)}
            for m in [50, 100, 200, 350, 500]
            for c in ["6", "24", "close"]
        ],
    ),
    Group(
        "async-half-life",
        "async",
        "§14 #9 for async: soft-avoid half-life, rolling 6 h cadence and batch at close.",
        [
            {"policy.soft_half_life_days": h, "population.M": m, **_cadence(c)}
            for h in [7.0, 14.0, 30.0, 60.0, 90.0]
            for m in [50, 100]
            for c in ["6", "close"]
        ],
    ),
    Group(
        "async-cap",
        "async",
        "§14 #8 for async: hard-block cap against locked sign-ups.",
        _grid(
            **{
                "policy.hard_cap": [1, 3, 5, 10, 25],
                "behavior.p_hard": [0.08, 0.4],
                "population.M": [50, 100],
            }
        ),
    ),
    Group(
        "async-newcomer",
        "async",
        "§7.4 for async: newcomer-boost decay and anchors against seeds to first mutual `more`.",
        _grid(
            **{
                "policy.newcomer_decay_sessions": [0, 5, 10, 20, 40],
                "policy.anchors_enabled": [True, False],
            }
        ),
        base={"population.newcomer_rate": 0.06},
        replicate_factor=2,
    ),
    Group(
        "async-noise",
        "async",
        "§7.6 for async: noise against the detection test, by M.",
        _grid(**{"weights.noise": [0.0, 0.5, 2.0], "population.M": [50, 100, 200, 500]}),
    ),
    Group(
        "live-newcomer-batch",
        "live",
        "§7.4 again where the matcher has choice: 15-minute batches, M = 200 and 500.",
        _grid(
            **{
                "policy.newcomer_decay_sessions": [0, 5, 10, 20, 40],
                "policy.anchors_enabled": [True, False],
                "population.M": [200, 500],
            }
        ),
        base={"population.newcomer_rate": 0.06, "shape.tick_seconds": 900.0},
        replicate_factor=2,
    ),
    Group(
        "async-newcomer-batch",
        "async",
        "§7.4 again where the matcher has choice: async batch at close, M = 100.",
        _grid(
            **{
                "policy.newcomer_decay_sessions": [0, 5, 10, 20, 40],
                "policy.anchors_enabled": [True, False],
            }
        ),
        base={"population.newcomer_rate": 0.06, **CLOSE_ONLY},
        replicate_factor=2,
    ),
    Group(
        "live-more-weight",
        "live",
        "R2 vs silent rejection: does a stronger `more` buy reunions, and at what detection cost?",
        _grid(
            **{
                "weights.more": [30.0, 60.0, 120.0, 240.0, 480.0],
                "shape.tick_seconds": [30.0, 900.0],
            }
        ),
    ),
    Group(
        "async-more-weight",
        "async",
        "R2 vs silent rejection, async M = 100: `more` weight, rolling 24 h vs batch at close.",
        [
            {"weights.more": w, **_cadence(c)}
            for w in [30.0, 60.0, 120.0, 240.0, 480.0]
            for c in ["24", "close"]
        ],
    ),
    Group(
        "detection-placebo",
        "live",
        "Validation: detection AUC with avoids ignored by the matcher (the other-channel floor).",
        _grid(**{"policy.honor_avoids": [True, False], "population.M": [200, 500]}),
    ),
    Group(
        "async-detection-placebo",
        "async",
        "Validation: async detection AUC with avoids ignored, rolling 6 h and batch at close.",
        [{"policy.honor_avoids": h, **_cadence(c)} for h in [True, False] for c in ["6", "close"]],
    ),
    Group(
        "matcher-validation",
        "live",
        "Heuristic vs hybrid (exact CP-SAT on pools ≤ 40): do the headline metrics move?",
        _grid(**{"policy.matcher": ["heuristic", "hybrid"], "population.M": [100, 200]}),
    ),
    Group(
        "async-matcher-validation",
        "async",
        "Heuristic vs hybrid for async, rolling and batch-at-close.",
        [
            {"policy.matcher": mt, "population.M": 50, **_cadence(c)}
            for mt in ["heuristic", "hybrid"]
            for c in ["6", "close"]
        ],
    ),
]

GROUPS = {g.name: g for g in PHASE0}


def scenario_for(group: Group, arm: dict[str, Any], seed: int) -> Scenario:
    base = (
        live_baseline(weeks=LIVE_WEEKS)
        if group.shape == "live"
        else async_baseline(weeks=ASYNC_WEEKS)
    )
    scn = with_overrides(base, {**(group.base or {}), **arm})
    return with_overrides(scn, {"seed": seed, "name": group.name})


# --- exit criteria ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    metric: str
    test: Callable[[float], bool]
    applies: Callable[[dict[str, float]], bool] = lambda m: True


def _near_chance(x: float) -> bool:
    return not math.isnan(x) and abs(x - 0.5) <= 0.05


LIVE_CRITERIA = [
    Criterion("C1", "median peak wait < 10 min", "wait_median_peak", lambda x: x < 10),
    Criterion(
        "C2", "hard-block lockout < 1% of peak ticks", "lockout_tick_share", lambda x: x < 0.01
    ),
    Criterion(
        "C3",
        "bottom-decile match rate ≥ 50% of median",
        "match_rate_p10_over_median",
        lambda x: x >= 0.5,
    ),
    Criterion(
        "C4",
        "most newcomers reach a mutual `more` within 5 sessions",
        "newcomer_within_horizon_share",
        lambda x: x > 0.5,
    ),
    Criterion(
        "C5",
        "detection advantage near chance (|AUC − 0.5| ≤ 0.05) at N ≥ 20",
        "detect_auc",
        _near_chance,
        applies=lambda m: m.get("peak_online_median", 0) >= 20,
    ),
]

ASYNC_CRITERIA = [  # PROPOSED for Ceryce to rule on (§12, §14 #15).
    Criterion(
        "A1",
        "≥ 90% of sign-ups placed in a seed by window close",
        "placed_share",
        lambda x: x >= 0.9,
    ),
    Criterion(
        "A2",
        "median sign-up → seed ≤ 48 h (rolling cadence only)",
        "wait_median_peak",
        lambda x: x <= 48,
    ),
    Criterion(
        "A3",
        "≥ 75% of placements at a preferred seed size",
        "pref_size_share",
        lambda x: x >= 0.75,
    ),
    Criterion("A4", "hard-block-locked sign-ups < 1%", "locked_signup_share", lambda x: x < 0.01),
    Criterion(
        "A5",
        "bottom-decile placement rate ≥ 50% of median",
        "match_rate_p10_over_median",
        lambda x: x >= 0.5,
    ),
    Criterion(
        "A6",
        "most newcomers reach a mutual `more` within 3 seeds",
        "newcomer_within_horizon_share",
        lambda x: x > 0.5,
    ),
    Criterion(
        "A7",
        "≥ 50% of co-signed-up mutual pairs share a seed",
        "cosignup_reunion_share",
        lambda x: x >= 0.5,
    ),
    Criterion(
        "A8",
        "detection advantage near chance at ≥ 20 sign-ups per window",
        "detect_auc",
        _near_chance,
        applies=lambda m: m.get("peak_online_median", 0) >= 20,
    ),
]


def check(m: dict[str, float], shape: str) -> dict[str, str]:
    """``{"C1": "pass" | "FAIL" | "n/a"}`` for one (mean) metrics row."""
    out = {}
    for c in LIVE_CRITERIA if shape == "live" else ASYNC_CRITERIA:
        v = m.get(c.metric, math.nan)
        if not c.applies(m) or (isinstance(v, float) and math.isnan(v)):
            out[c.key] = "n/a"
        else:
            out[c.key] = "pass" if c.test(v) else "FAIL"
    return out


# --- running ------------------------------------------------------------------------------------


def run_one(job: tuple[str, int, dict[str, Any], int]) -> dict[str, Any]:
    group_name, arm_idx, arm, seed = job
    group = GROUPS[group_name]
    scn = scenario_for(group, arm, seed)
    t0 = time.perf_counter()
    rec = Simulation(scn).run()
    m = compute(rec)
    row: dict[str, Any] = {"group": group_name, "arm": arm_idx, "replicate": seed}
    row.update({f"arm.{k}": v for k, v in arm.items()})
    row.update(flatten(scn))
    row.update(m)
    row["wall_seconds"] = time.perf_counter() - t0
    row["_lockout_by_n"] = lockout_by_n(rec)
    return row


def _cost(group: Group, arm: dict[str, Any]) -> float:
    """Rough relative run time, only used to schedule the slowest runs first."""
    m = float(arm.get("population.M", 200 if group.shape == "live" else 100))
    if group.shape == "async":
        batch = arm.get("shape.cadence_hours", 6.0) >= 168
        return m * (8.0 if batch else 0.2)
    return m * (5.0 if arm.get("policy.matcher") == "hybrid" else 1.0)


def run_groups(
    names: list[str], replicates: int, workers: int | None, progress: Callable[[str], None]
) -> list[dict[str, Any]]:
    jobs = [
        (name, i, arm, seed)
        for name in names
        for i, arm in enumerate(GROUPS[name].arms)
        for seed in range(1, replicates * GROUPS[name].replicate_factor + 1)
    ]
    jobs.sort(key=lambda j: -_cost(GROUPS[j[0]], j[2]))  # longest first keeps the pool busy
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as ex:
        for k, row in enumerate(ex.map(run_one, jobs, chunksize=1), 1):
            rows.append(row)
            if k % max(1, len(jobs) // 20) == 0 or k == len(jobs):
                progress(f"{k}/{len(jobs)} runs, {time.perf_counter() - t0:.0f}s")
    return rows
