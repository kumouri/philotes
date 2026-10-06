"""Directed edges, co-play records and the decay maths (docs/spec.md §6, §7.2–§7.4).

An edge ``a → b`` is set only by ``a``, only about someone ``a`` has played with, and is one of
``more``, ``soft`` (avoid-soft, decays) or ``hard`` (avoid-hard, capped, never decays). No edge is
neutral. Nothing here is ever shown to ``b``; the simulator only feeds edges to the matcher.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .config import MINUTES_PER_DAY

MORE = "more"
SOFT = "soft"
HARD = "hard"


def soft_avoid_weight(age_minutes: float, half_life_days: float) -> float:
    """Weight of a soft avoid after ``age_minutes``: 1 when set, halving every half-life (§7.2)."""
    if age_minutes <= 0:
        return 1.0
    return 0.5 ** (age_minutes / (half_life_days * MINUTES_PER_DAY))


def newness(sessions_played: int, decay_sessions: int) -> float:
    """Newcomer factor: 1 at session 0, falling linearly to 0 at ``decay_sessions`` (§7.4).

    ``decay_sessions == 0`` turns the boost off.
    """
    if decay_sessions <= 0:
        return 0.0
    return max(0.0, 1.0 - sessions_played / decay_sessions)


def more_weight(base: float, k: float, coplay_count: int) -> float:
    """§7.3 diminishing returns: ``M / (1 + k·ln(1 + n_ab))``."""
    return base / (1.0 + k * math.log1p(coplay_count))


def reunion_bump(bump: float, full_days: float, days_since_last: float) -> float:
    """§7.3 recency: rises linearly with time since the pair last co-played, capped at ``bump``."""
    if full_days <= 0:
        return bump
    return bump * min(1.0, max(0.0, days_since_last) / full_days)


@dataclass
class Edge:
    kind: str
    t: float  # minutes; for soft avoids this is the (re)applied time that decay counts from


@dataclass
class CoPlay:
    count: int = 0
    last_t: float = 0.0
    hours: float = 0.0


class EdgeStore:
    """All edges plus co-play records, with the cap and decay rules applied on write and read."""

    def __init__(self, half_life_days: float, negligible: float, hard_cap: int) -> None:
        self.half_life_days = half_life_days
        self.negligible = negligible
        self.hard_cap = hard_cap
        self.out: dict[int, dict[int, Edge]] = {}
        self.coplay: dict[tuple[int, int], CoPlay] = {}
        self.hist: dict[int, set[int]] = {}

    # --- edges -------------------------------------------------------------------------------

    def get(self, a: int, b: int, now: float) -> Edge | None:
        """Edge ``a → b`` if it is still live; soft avoids below the threshold are deleted (§11)."""
        e = self.out.get(a, {}).get(b)
        if e is None:
            return None
        if e.kind == SOFT and self.soft_weight(e, now) < self.negligible:
            del self.out[a][b]
            return None
        return e

    def soft_weight(self, e: Edge, now: float) -> float:
        return soft_avoid_weight(now - e.t, self.half_life_days)

    def avoids(self, a: int, b: int, now: float) -> bool:
        e = self.get(a, b, now)
        return e is not None and e.kind in (SOFT, HARD)

    def hard_count(self, a: int) -> int:
        return sum(1 for e in self.out.get(a, {}).values() if e.kind == HARD)

    def set_more(self, a: int, b: int, now: float) -> None:
        self.out.setdefault(a, {})[b] = Edge(MORE, now)

    def set_soft(self, a: int, b: int, now: float) -> None:
        """Set or refresh a soft avoid (§7.2: refreshed if re-applied). Never downgrades a hard."""
        cur = self.out.get(a, {}).get(b)
        if cur is not None and cur.kind == HARD:
            return
        self.out.setdefault(a, {})[b] = Edge(SOFT, now)

    def set_hard(self, a: int, b: int, now: float) -> str:
        """Hard-block ``b``; over the cap it falls back to a soft avoid. Returns the kind set."""
        cur = self.out.get(a, {}).get(b)
        if cur is not None and cur.kind == HARD:
            return HARD
        if self.hard_count(a) >= self.hard_cap:
            self.set_soft(a, b, now)
            return SOFT
        self.out.setdefault(a, {})[b] = Edge(HARD, now)
        return HARD

    def mutual_more(self, a: int, b: int, now: float) -> bool:
        ea, eb = self.get(a, b, now), self.get(b, a, now)
        return ea is not None and eb is not None and ea.kind == MORE and eb.kind == MORE

    def valid_more(self, a: int, b: int, now: float) -> bool:
        """``a → b`` is `more` and not overridden by any avoid ``b → a`` (§7.3 asymmetry rule)."""
        e = self.get(a, b, now)
        return e is not None and e.kind == MORE and not self.avoids(b, a, now)

    def inbound_avoid_counts(self, now: float) -> dict[int, int]:
        counts: dict[int, int] = {}
        for a in list(self.out):
            for b in list(self.out[a]):
                if self.avoids(a, b, now):
                    counts[b] = counts.get(b, 0) + 1
        return counts

    def mutual_partners(self, a: int, now: float) -> list[int]:
        return [b for b in list(self.out.get(a, {})) if self.mutual_more(a, b, now)]

    # --- co-play -----------------------------------------------------------------------------

    def record_coplay(self, a: int, b: int, now: float, hours: float) -> CoPlay:
        key = (a, b) if a < b else (b, a)
        cp = self.coplay.get(key)
        if cp is None:
            cp = self.coplay[key] = CoPlay()
            self.hist.setdefault(a, set()).add(b)
            self.hist.setdefault(b, set()).add(a)
        cp.count += 1
        cp.last_t = now
        cp.hours += hours
        return cp

    def coplay_of(self, a: int, b: int) -> CoPlay | None:
        return self.coplay.get((a, b) if a < b else (b, a))
