"""Local alpha reporting. Only anonymous window totals survive sign-up deletion."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import UTC, datetime, timedelta
from itertools import combinations
from pathlib import Path

from philotes_sim import experiments
from philotes_sim.lockout import check_pool
from philotes_sim.metric_helpers import placement_metrics

from .config import BotConfig
from .matching import Entry, edge_snapshot
from .store import DAY, SignupRow, Store

UNMEASURABLE = {
    "A5": "Closed sign-ups are deleted; per-player placement denominators are unavailable.",
    "A6": "Marks are overwritten/forgotten; first mutual-more timing and newcomer cohorts "
    "are unavailable.",
    "A7": "Historical mutual-more state at co-signup is unavailable; current edges cannot "
    "reconstruct the simulator's denominator.",
    "A8": "First-session card labels (including neutral defaults) are not retained; "
    "current avoids cannot substitute for those labels.",
}


def close_counts(store: Store, cfg: BotConfig, signups: list[SignupRow], formed, now: float):
    """Sample the original pool, across all listed goals, as Simulation._sample_lockout does."""
    eligible = [s for s in signups if (p := store.player(s.user_id)) and p.removed_at is None]
    players = {
        s.user_id: Entry(s.user_id, s.signed_at / 60, s.goals, 0, *s.pref, *s.acc, (), ())
        for s in eligible
    }
    es = edge_snapshot(store, cfg)
    free, hard, unknown = set(), set(), 0
    for goal in sorted({g for s in eligible for g in s.goals}):
        pool = [s.user_id for s in eligible if goal in s.goals]
        if len(pool) < 2:
            continue
        result = check_pool(pool, players, es, now / 60)
        free |= result.free_ok
        hard |= result.hard_ok
        unknown += result.unknown
    sizes = {u: len(members) for _, members in formed for u in members}
    return {
        "entries": len(eligible),
        "placed": sum(s.user_id in sizes for s in eligible),
        "slots": len(sizes),
        "preferred": sum(
            s.pref[0] <= sizes[s.user_id] <= s.pref[1] for s in eligible if s.user_id in sizes
        ),
        "locked": len(free - hard),
        "unknown": unknown,
        "seeds": len(formed),
    }


def save_close(store: Store, wid: int, now: float, counts: dict) -> None:
    store._exec(
        "INSERT OR IGNORE INTO alpha_windows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        wid,
        now,
        *(
            counts[k]
            for k in ("entries", "placed", "slots", "preferred", "locked", "unknown", "seeds")
        ),
    )


def _week(t: float) -> float:
    dt = datetime.fromtimestamp(t, UTC)
    return (
        (dt - timedelta(days=dt.weekday()))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )


def report(store: Store, cfg: BotConfig, now: float) -> list[dict]:
    """Weekly and cumulative retained-data aggregates; no player/seed/edge IDs escape."""
    cutoff = now - cfg.safety.coplay_retention_days * DAY
    measured = store._one("SELECT name FROM sqlite_master WHERE name = 'alpha_windows'")
    rows = (
        store._all(
            "SELECT * FROM alpha_windows WHERE closed_at >= ? AND closed_at <= ?", cutoff, now
        )
        if measured
        else []
    )
    seeds = [s for s in store.seeds() if s.ends_at >= cutoff and s.formed_at <= now]
    weeks = sorted(
        {_week(r[1]) for r in rows} | {_week(s.formed_at) for s in seeds if s.formed_at >= cutoff}
    )
    periods = [
        (datetime.fromtimestamp(t, UTC).date().isoformat(), t, t + 7 * DAY) for t in weeks
    ] + [("cumulative", cutoff, now + 1)]
    out = []
    for label, start, end in periods:
        selected = [r for r in rows if start <= r[1] < end]
        counts = dict(
            zip(
                ("entries", "placed", "slots", "preferred", "locked", "unknown", "seeds"),
                (sum(r[i] for r in selected) for i in range(2, 9)),
                strict=True,
            )
        )
        metrics = placement_metrics(
            counts["entries"],
            counts["placed"],
            counts["slots"],
            counts["preferred"],
            counts["locked"],
        )
        # Size is the current opted-in population, not sign-up count or guild membership.
        population = store._one("SELECT COUNT(*) FROM players WHERE removed_at IS NULL")[0]
        metrics["population.M"] = population
        for criterion in experiments.ASYNC_CRITERIA:
            metrics.setdefault(criterion.metric, math.nan)
        criteria = experiments.check(metrics, "async")
        criteria["A2"] = "n/a"  # Ruled batch-at-close, even if an early manual close was used.
        reasons = {
            key: "not measurable on live data: " + reason for key, reason in UNMEASURABLE.items()
        }
        reasons["A2"] = "Rolling cadence only; Phase 1 batches at close."
        if population < experiments.A8_BAR.min_M:
            reasons["A8"] = f"n/a below M = {experiments.A8_BAR.min_M}. " + reasons["A8"]
        for key in ("A1", "A3", "A4"):
            if criteria[key] == "n/a":
                reasons[key] = "No measured samples; old closes cannot be reconstructed."
        if counts["unknown"]:
            criteria["A4"] = "n/a"
            reasons["A4"] = "Lockout search reached its node limit; incomplete classification."
        by_player, by_pair = Counter(), Counter()
        repeat, reunions, seats = 0, 0, 0
        for seed in sorted(seeds, key=lambda s: (s.formed_at, s.id)):
            if seed.formed_at >= end:
                continue
            members = store.seed_members(seed.id)
            measured = start <= seed.formed_at < end
            for member in members:
                if measured:
                    seats += 1
                    repeat += by_player[member] > 0
                by_player[member] += 1
            for pair in combinations(members, 2):
                if measured:
                    reunions += by_pair[pair] > 0
                by_pair[pair] += 1
        # This measures formation/return, not actual hours played or inferred friendship.
        success = {
            "repeat_use": "pass" if repeat else ("FAIL" if seats else "n/a"),
            "reunions": "pass" if reunions else ("FAIL" if seats else "n/a"),
            "graduation": "n/a",
            "overall": "FAIL" if seats and (not repeat or not reunions) else "n/a",
            "graduation_reason": "not measurable on live data: the bot cannot observe a group "
            "moving to its own server; leaving or inactivity is not graduation.",
        }
        out.append(
            {
                "period": label,
                "coverage": "retained data; closes measured since slice 5 only",
                **counts,
                **{k: None if math.isnan(v) else v for k, v in metrics.items()},
                **criteria,
                "reasons": reasons,
                "A8_bar": str(experiments.A8_BAR),
                "policy.soft_half_life_days": cfg.safety.soft_half_life_days,
                "policy.hard_cap": cfg.safety.hard_cap,
                "cadence": "batch at close",
                "sample_sizes": {
                    "A1": counts["entries"],
                    "A2": None,
                    "A3": counts["slots"],
                    "A4": counts["entries"],
                    "A5": None,
                    "A6": None,
                    "A7": None,
                    "A8": None,
                },
                "confidence_intervals": None,
                "uncertainty_reason": "The simulator supplies replicate standard deviations, "
                "not confidence intervals; one live history has no independent replicates.",
                "repeat_placements": repeat,
                "reunion_pair_events": reunions,
                "retained_seats": seats,
                "success": success,
            }
        )
    return out


def render(rows: list[dict]) -> str:
    return json.dumps(rows, indent=2, allow_nan=False)


def export(rows: list[dict], path: Path) -> None:
    """Only the report's allowlisted aggregate fields enter either export format."""
    if path.suffix.lower() == ".json":
        path.write_text(render(rows) + "\n", encoding="utf-8")
    elif path.suffix.lower() == ".csv":
        flat = [
            {k: json.dumps(v) if isinstance(v, dict) else v for k, v in r.items()} for r in rows
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(flat[0]))
            writer.writeheader()
            writer.writerows(flat)
    else:
        raise ValueError("Export path must end in .csv or .json")
