"""Summaries of sweep rows: CSV files plus a short Markdown report.

``summarise`` averages each (group, arm) over its replicates. ``write_outputs`` writes
``runs.csv`` (one row per run), ``summary.csv`` (mean and sd per arm), ``lockout_by_n.csv`` and
``report.md`` (one table per group, with the exit-criteria checks where they apply).
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from .experiments import ASYNC_CRITERIA, GROUPS, LIVE_CRITERIA, check

COMMON_LIVE = ["wait_median_peak", "placed_share_peak", "lockout_tick_share"]
COMMON_ASYNC = ["wait_median_peak", "placed_share", "locked_signup_share"]

COLUMNS: dict[str, list[str]] = {
    "live-density": [
        "peak_online_median",
        "peak_waiting_median",
        *COMMON_LIVE,
        "reunion_14d_share",
        "reunion_opportunity_hit_share",
        "players_in_stable_cluster_share",
        "match_rate_p10_over_median",
        "newcomer_within_horizon_share",
        "detect_auc",
    ],
    "live-lobby": [
        *COMMON_LIVE,
        "window_lost_to_hard_blocks_share",
        "target_locked_hours_per_week",
        "match_rate_p10_over_median",
        "reunion_14d_share",
    ],
    "live-half-life": [
        "lockout_tick_share",
        "avoid_held_tick_share",
        "soft_broken_per_100_sessions",
        "avoided_pair_rematch_share",
        "active_avoids_per_player",
        "reunion_14d_share",
        "wait_median_peak",
        "match_rate_p10_over_median",
        "high_avoid_only_share",
    ],
    "live-cap": [
        "hard_blocks_per_player",
        "lockout_tick_share",
        "window_lost_to_hard_blocks_share",
        "avoid_held_tick_share",
        "target_locked_hours_per_week",
        "target_placed_share",
        "soft_broken_per_100_sessions",
    ],
    "live-newcomer": [
        "newcomers_eligible",
        "newcomer_within_horizon_share",
        "newcomer_sessions_to_mutual_median",
        "all_within_horizon_share",
        "match_rate_p10_over_median",
        "wait_median_peak",
    ],
    "live-noise": [
        "peak_online_median",
        "detect_auc",
        "detect_auc_more",
        "reunion_14d_share",
        "reunion_opportunity_hit_share",
        "affinity_median",
    ],
    "live-tick": [
        *COMMON_LIVE,
        "reunion_14d_share",
        "reunion_opportunity_hit_share",
        "players_in_stable_cluster_share",
        "detect_auc",
    ],
    "async-density": [
        "peak_online_median",
        "peak_waiting_median",
        *COMMON_ASYNC,
        "pref_size_share",
        "mean_lobby_size",
        "cosignup_reunion_share",
        "reunion_14d_share",
        "players_in_stable_cluster_share",
        "newcomer_within_horizon_share",
        "detect_auc",
    ],
    "live-search": [
        "peak_online_median",
        *COMMON_LIVE,
        "match_rate_p10_over_median",
        "newcomer_within_horizon_share",
        "detect_auc",
        "reunion_14d_share",
    ],
    "async-half-life": [
        "locked_signup_share",
        "soft_broken_per_100_sessions",
        "avoided_pair_rematch_share",
        "active_avoids_per_player",
        "cosignup_reunion_share",
        "placed_share",
        "wait_median_peak",
    ],
    "async-cap": [
        "hard_blocks_per_player",
        "locked_signup_share",
        "lockout_tick_share",
        "target_placed_share",
        "placed_share",
    ],
    "async-newcomer": [
        "newcomers_eligible",
        "newcomer_within_horizon_share",
        "newcomer_sessions_to_mutual_median",
        "all_within_horizon_share",
        "placed_share",
    ],
    "async-noise": [
        "peak_online_median",
        "detect_auc",
        "detect_auc_more",
        "cosignup_reunion_share",
        "reunion_14d_share",
    ],
    "matcher-validation": [
        *COMMON_LIVE,
        "reunion_14d_share",
        "match_rate_p10_over_median",
        "newcomer_within_horizon_share",
        "detect_auc",
        "matcher_ms_per_run",
    ],
    "async-matcher-validation": [
        *COMMON_ASYNC,
        "pref_size_share",
        "cosignup_reunion_share",
        "detect_auc",
        "matcher_ms_per_run",
    ],
}

PERCENT = ("share", "_rate_p10_over")
LABEL = {
    "wait_median_peak": "median wait",
    "placed_share_peak": "placed (peak)",
    "placed_share": "placed",
    "lockout_tick_share": "hard lockout (peak ticks)",
    "locked_signup_share": "locked sign-ups",
    "peak_online_median": "N online (peak)",
    "peak_waiting_median": "N waiting (peak)",
}


def _numeric(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def summarise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_arm: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_arm[(r["group"], r["arm"])].append(r)
    out = []
    for (group, arm), rs in sorted(by_arm.items()):
        row: dict[str, Any] = {"group": group, "arm": arm, "replicates": len(rs)}
        for k, v in rs[0].items():
            if k.startswith("arm."):
                row[k] = v
        keys = [k for k, v in rs[0].items() if _numeric(v) and "." not in k]
        for k in keys:
            if k in ("arm", "replicate"):
                continue
            vals = np.asarray([r.get(k, math.nan) for r in rs], dtype=float)
            finite = vals[~np.isnan(vals)]
            if len(finite) == 0:
                row[k], row[f"{k}_sd"] = math.nan, math.nan
            elif np.isinf(finite).any():
                # Censored metrics ("never"): report the median across replicates.
                row[k], row[f"{k}_sd"] = float(np.median(finite)), math.nan
            else:
                row[k] = float(finite.mean())
                row[f"{k}_sd"] = float(finite.std(ddof=1)) if len(finite) > 1 else 0.0
        # Newcomer cohorts are small: pool them across replicates rather than average shares.
        elig = [r.get("newcomers_eligible", 0) or 0 for r in rs]
        if sum(elig):
            hit = sum(
                (r.get("newcomer_within_horizon_share") or 0) * e
                for r, e in zip(rs, elig, strict=True)
                if e
            )
            row["newcomer_within_horizon_share"] = hit / sum(elig)
            row["newcomer_within_horizon_share_sd"] = math.nan
            row["newcomers_eligible"] = float(sum(elig))
        row.update(check(row, GROUPS[group].shape))
        out.append(row)
    return out


def fmt(k: str, v: Any, sd: Any = None) -> str:
    if not _numeric(v) or (isinstance(v, float) and math.isnan(v)):
        return "–"
    if math.isinf(v):
        return "never"
    if any(p in k for p in PERCENT):
        s = f"{100 * v:.1f}%"
        if _numeric(sd) and not math.isnan(sd) and sd > 0:
            s += f" ±{100 * sd:.1f}"
        return s
    s = f"{v:.3g}" if abs(v) < 1000 else f"{v:.0f}"
    if _numeric(sd) and not math.isnan(sd) and sd > 0 and k != "newcomers_eligible":
        s += f" ±{sd:.2g}"
    return s


def group_table(group: str, summary: list[dict[str, Any]]) -> str:
    rows = [r for r in summary if r["group"] == group]
    if not rows:
        return ""
    params = [k for k in rows[0] if k.startswith("arm.")]
    metrics = COLUMNS.get(group, [])
    shape = GROUPS[group].shape
    crit = [c.key for c in (LIVE_CRITERIA if shape == "live" else ASYNC_CRITERIA)]
    head = [p.split(".", 2)[-1] for p in params] + [LABEL.get(m, m) for m in metrics] + crit
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        cells = [_param(r[p]) for p in params]
        cells += [fmt(m, r.get(m), r.get(f"{m}_sd")) for m in metrics]
        cells += [r.get(c, "n/a") for c in crit]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _param(v: Any) -> str:
    if isinstance(v, tuple):
        return "close" if v and v[0] >= 1e8 else ",".join(map(str, v))
    if isinstance(v, str) and v.startswith("1e9"):
        return "close"
    return str(v)


def lockout_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agg: dict[tuple[str, int], list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if GROUPS[r["group"]].shape != "live":
            continue
        for b in r["_lockout_by_n"]:
            key = (str(b["N"]), int(b["L"]))
            agg[key][0] += b["samples"]
            agg[key][1] += b["locked_share"] * b["samples"] if b["samples"] else 0
    out = []
    for (n, L), (samples, locked) in sorted(
        agg.items(), key=lambda kv: (kv[0][1], int(kv[0][0].split("-")[0].rstrip("+")))
    ):
        out.append({"N": n, "L": L, "samples": int(samples), "locked_share": locked / samples})
    return out


def write_outputs(rows: list[dict[str, Any]], out: Path, title: str) -> list[dict[str, Any]]:
    out.mkdir(parents=True, exist_ok=True)
    plain = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    _csv(out / "runs.csv", plain)
    summary = summarise(rows)
    _csv(out / "summary.csv", summary)
    lock = lockout_table(rows)
    _csv(out / "lockout_by_n.csv", lock)
    groups = list(dict.fromkeys(r["group"] for r in rows))
    md = [f"# {title}", ""]
    md.append(
        "Means over replicates (± sd). Waits: minutes (live) or hours (async). "
        "Criteria columns check the arm's mean against the §12 live suggestions (C1–C5) or the "
        "proposed async criteria (A1–A8); n/a means the criterion does not apply at that size."
    )
    md.append("")
    for g in groups:
        md += [f"## {g}", "", GROUPS[g].question, "", group_table(g, summary), ""]
    if lock:
        md += ["## Live hard-block lockout by waiting pool N and lobby size L", ""]
        md += [
            "| L | N waiting | peak samples | share with someone hard-locked |",
            "|---|---|---|---|",
        ]
        md += [
            f"| {r['L']} | {r['N']} | {r['samples']} | {100 * r['locked_share']:.2f}% |"
            for r in lock
        ]
        md.append("")
    (out / "report.md").write_text("\n".join(md), encoding="utf-8")
    return summary


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: _cell(r.get(k)) for k in keys})


def _cell(v: Any) -> Any:
    if isinstance(v, float):
        return "" if math.isnan(v) else ("inf" if math.isinf(v) else f"{v:.6g}")
    if isinstance(v, tuple):
        return ",".join(map(str, v))
    return v
