"""Anonymous alpha reports from retention-limited summaries and private milestones."""

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
from philotes_sim.metric_helpers import (
    cosignup_metrics,
    match_rate_metrics,
    newcomer_metrics,
    placement_metrics,
)

from .config import BotConfig
from .matching import Entry, edge_snapshot
from .store import DAY, SignupRow, Store


def save_a8(store, author, observer, action, now, retention_days=365):
    """Consume a card label immediately; never persist a labelled relationship."""
    from philotes_sim.edges import HARD, SOFT
    from philotes_sim.metric_helpers import rejection_score, score_bin

    if action == "more":
        return
    history = [
        (s, store.seed_members(s.id))
        for s in store.seeds()
        if now - retention_days * DAY <= s.ends_at < now
    ]
    shared = [s.ends_at for s, members in history if author in members and observer in members]
    if not shared:
        return
    first = min(shared)
    later = sum(observer in members and s.ends_at > first for s, members in history)
    again = sum(t > first for t in shared)
    score = rejection_score(again, later)
    if math.isnan(score):
        return
    edge = store.edge(author, observer)
    avoided = int(edge is not None and edge.kind in (HARD, SOFT))
    store._exec(
        "INSERT INTO alpha_a8 VALUES (?, ?, ?, 1) "
        "ON CONFLICT(week, avoided, bin) DO UPDATE SET count = count + 1",
        _week(now),
        avoided,
        score_bin(score),
    )


def a8_metrics(store, cutoff, start, end):
    from philotes_sim.metric_helpers import (
        A8_BINS,
        A8_MIN_CLASS,
        histogram_auc,
        histogram_error_bound,
    )

    pos, neg = [0] * A8_BINS, [0] * A8_BINS
    if store._one("SELECT name FROM sqlite_master WHERE name = 'alpha_a8'"):
        for week, avoided, bin_, count in store._all("SELECT * FROM alpha_a8"):
            if max(cutoff, start) <= week < end:
                (pos if avoided else neg)[bin_] += count
    suppressed = min(sum(pos), sum(neg)) < A8_MIN_CLASS
    return {
        "detect_auc": math.nan if suppressed else histogram_auc(pos, neg),
        "A8_binning_error_bound": math.nan if suppressed else histogram_error_bound(pos, neg),
        "A8_bins": A8_BINS,
        "A8_calibration_max_error": 0.000058185,
    }, None if suppressed else sum(pos) + sum(neg)


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


def save_history(store, wid, now, signups, formed):
    """Delete-window-compatible summaries; never retain closed individual sign-ups."""
    if store._one("SELECT 1 FROM alpha_reunions WHERE window_id = ?", wid):
        return
    eligible = {
        s.user_id: s for s in signups if (p := store.player(s.user_id)) and p.removed_at is None
    }
    seats = {u: i for i, (_, members) in enumerate(formed) for u in members}
    snapshots = {
        (a, b): mutual
        for _, a, b, mutual in store._all(
            "SELECT * FROM alpha_pending_pairs WHERE window_id = ?", wid
        )
    }
    tries = hits = unknown = 0
    for a, b in combinations(sorted(eligible), 2):
        if eligible[a].goals[0] != eligible[b].goals[0]:
            continue
        if (a, b) not in snapshots:
            unknown += 1
        elif snapshots[a, b]:
            tries += 1
            hits += a in seats and b in seats and seats[a] == seats[b]
    with store.db:
        store.db.execute(
            "INSERT INTO alpha_reunions VALUES (?, ?, ?, ?, ?)", (wid, now, tries, hits, unknown)
        )
        for u in eligible:
            store.db.execute(
                "INSERT INTO alpha_rates VALUES (?, ?, 1, ?) "
                "ON CONFLICT(user_id, week) DO UPDATE SET entries = entries + 1, "
                "placed = placed + excluded.placed",
                (u, _week(now), int(u in seats)),
            )


def history_metrics(store, cutoff, start, end):
    tables = {r[0] for r in store._all("SELECT name FROM sqlite_master WHERE type = 'table'")}
    metrics, samples = {}, {k: None for k in ("A5", "A6", "A7", "A8")}
    unknown = 0
    if "alpha_rates" in tables:
        counts = store._all(
            "SELECT SUM(entries), SUM(placed) FROM alpha_rates "
            "WHERE week >= ? AND week >= ? AND week < ? GROUP BY user_id",
            cutoff,
            start,
            end,
        )
        metrics.update(match_rate_metrics(counts))
        samples["A5"] = sum(n >= 3 for n, _ in counts)
    if "alpha_newcomers" in tables:
        players = []
        for u, joined, first_at, first_session in store._all("SELECT * FROM alpha_newcomers"):
            if not max(cutoff, start) <= joined < end:
                continue
            n = store._one(
                "SELECT COUNT(*) FROM seed_members m JOIN seeds s ON s.id = m.seed_id "
                "WHERE m.user_id = ? AND s.ends_at < ?",
                u,
                end,
            )[0]
            players.append((n, first_session if first_at is not None and first_at < end else None))
        metrics.update(newcomer_metrics(players, 3))
        samples["A6"] = metrics["newcomers_eligible"]
    if "alpha_reunions" in tables:
        rows = store._all(
            "SELECT tries, hits, unknown FROM alpha_reunions "
            "WHERE closed_at >= ? AND closed_at >= ? AND closed_at < ?",
            cutoff,
            start,
            end,
        )
        tries, hits, unknown = (sum(r[i] for r in rows) for i in range(3))
        metrics.update(cosignup_metrics(tries, hits))
        samples["A7"] = tries
    return metrics, samples, unknown


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
    graduation_table = store._one("SELECT name FROM sqlite_master WHERE name = 'alpha_graduations'")
    graduation_weeks = (
        {
            _week(t)
            for (t,) in store._all(
                "SELECT t FROM alpha_graduations WHERE t >= ? AND t <= ?", cutoff, now
            )
        }
        if graduation_table
        else set()
    )
    weeks = sorted(
        {_week(r[1]) for r in rows}
        | {_week(s.formed_at) for s in seeds if s.formed_at >= cutoff}
        | graduation_weeks
        | (
            {
                r[0]
                for r in store._all(
                    "SELECT week FROM alpha_a8 WHERE week >= ? AND week <= ?", cutoff, now
                )
            }
            if store._one("SELECT name FROM sqlite_master WHERE name = 'alpha_a8'")
            else set()
        )
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
        history, history_samples, history_unknown = history_metrics(
            store, cutoff, start, min(end, now + 1)
        )
        metrics.update(history)
        a8, history_samples["A8"] = a8_metrics(store, cutoff, start, min(end, now + 1))
        metrics.update(a8)
        # Size is the current opted-in population, not sign-up count or guild membership.
        population = store._one("SELECT COUNT(*) FROM players WHERE removed_at IS NULL")[0]
        metrics["population.M"] = population
        for criterion in experiments.ASYNC_CRITERIA:
            metrics.setdefault(criterion.metric, math.nan)
        criteria = experiments.check(metrics, "async")
        criteria["A2"] = "n/a"  # Ruled batch-at-close, even if an early manual close was used.
        reasons = {}
        if criteria["A8"] == "n/a":
            reasons["A8"] = (
                "Suppressed: fewer than 10 events in either label class; no legacy backfill."
            )
        reasons["A2"] = "Rolling cadence only; Phase 1 batches at close."
        if population < experiments.A8_BAR.min_M:
            reasons["A8"] = f"n/a below M = {experiments.A8_BAR.min_M}. " + reasons.get("A8", "")
        for key in ("A5", "A6", "A7"):
            if criteria[key] == "n/a":
                reasons[key] = "Insufficient recorded history; legacy data is not backfilled."
        if history_unknown:
            metrics["cosignup_reunion_share"] = math.nan
            criteria["A7"] = "n/a"
            reasons["A7"] = "Legacy co-signups lack snapshots; incomplete denominator."
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
        graduation_table = store._one(
            "SELECT name FROM sqlite_master WHERE name = 'alpha_graduations'"
        )
        graduation = (
            store._one(
                "SELECT COUNT(*) FROM alpha_graduations WHERE t >= ? AND t >= ? AND t < ?",
                cutoff,
                start,
                end,
            )[0]
            if graduation_table
            else 0
        )
        success = {
            "repeat_use": "pass" if repeat else ("FAIL" if seats else "n/a"),
            "reunions": "pass" if reunions else ("FAIL" if seats else "n/a"),
            "graduation": "pass" if graduation else "n/a",
            "overall": "FAIL"
            if seats and (not repeat or not reunions)
            else ("pass" if repeat and reunions and graduation else "n/a"),
            "graduation_reports": graduation,
            "graduation_reason": "Voluntary own-group self-reports; no response, inactivity and "
            "leaving do not establish graduation. Counts are reporters, not distinct groups.",
        }
        out.append(
            {
                "period": label,
                "coverage": "retained data; A5/A7 since follow-up; "
                "A6 new joiners only; A8 retrospective card-time score; no backfill",
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
                    **history_samples,
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
