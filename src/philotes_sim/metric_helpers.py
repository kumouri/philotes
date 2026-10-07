"""Aggregate reducers shared by synthetic and real histories. No identity output."""

import math


def share(hits: int, samples: int) -> float:
    return hits / samples if samples else math.nan


def placement_metrics(entries: int, placed: int, slots: int, preferred: int, locked: int):
    """The async A1, A3 and A4 ratios, with their distinct denominators."""
    return {
        "placed_share": share(placed, entries),
        "pref_size_share": share(preferred, slots),
        "locked_signup_share": share(locked, entries),
    }


def match_rate_metrics(counts):
    """A5: per-player (entries, placements), at least three entries."""
    import numpy as np

    rates = [placed / entries for entries, placed in counts if entries >= 3]
    if not rates:
        return dict(
            match_rate_p10=math.nan, match_rate_median=math.nan, match_rate_p10_over_median=math.nan
        )
    p10, median = float(np.percentile(rates, 10)), float(np.median(rates))
    return dict(
        match_rate_p10=p10,
        match_rate_median=median,
        match_rate_p10_over_median=p10 / median if median > 0 else 0.0,
    )


def newcomer_metrics(players, horizon):
    """A6: (sessions, first mutual session); early successes or full horizon."""
    eligible = [
        (n, first)
        for n, first in players
        if n >= horizon or (first is not None and first <= horizon)
    ]
    return {
        "newcomers": len(players),
        "newcomers_eligible": len(eligible),
        "newcomer_within_horizon_share": share(
            sum(first is not None and first <= horizon for _, first in eligible), len(eligible)
        ),
    }


def cosignup_metrics(tries, hits):
    """A7: qualifying mutual co-signups and same-seed hits."""
    return {"cosignup_reunion_share": share(hits, tries)}
