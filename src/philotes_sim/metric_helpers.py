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
