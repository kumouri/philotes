"""One matcher round over a waiting pool, shared by the simulator and the Phase 1 bot (§7.1, §7.5).

A round goes game by game, most-demanded game first. An entry is offered for its first-choice game
only, or for every game it listed once it has reached the "other listed games" rung (§7.5 step 4).
Players placed in one game are not offered to the next.

``batch_at_close`` is the ruled async cadence (§12, §14 #15): one strict round when the sign-up
window closes, then one more round per ladder rung (§7.5 steps 3, 4 and 6) for whoever is still
unplaced, so nobody's soft avoid is broken while a stricter seed was still possible.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Protocol

import numpy as np

from . import matcher
from .config import Policy, Shape, Weights
from .edges import EdgeStore
from .scoring import (
    LEVEL_BREAK_SOFT,
    LEVEL_GAMES,
    LEVEL_SIZE,
    Candidate,
    MatchPlayer,
    ScoringContext,
    build_context,
)


class PoolEntry(Protocol):
    """A waiting window or sign-up: whose it is, when it opened, its games, its ladder rung."""

    pid: int
    open_t: float  # minutes, on the same clock as ``now``
    games: tuple[int, ...]  # listed games, first choice first
    level: int


def eligible_games(e: PoolEntry) -> tuple[int, ...]:
    return e.games if e.level >= LEVEL_GAMES else e.games[:1]


def match_round[E: PoolEntry](
    waiting: Sequence[E],
    players: Mapping[int, MatchPlayer],
    store: EdgeStore,
    now: float,
    weights: Weights,
    policy: Policy,
    shape: Shape,
    rng: np.random.Generator,
    seed: int = 0,
    on_solve: Callable[[ScoringContext, matcher.MatchResult], None] | None = None,
) -> list[tuple[int, list[E]]]:
    """Place what can be placed from ``waiting``. Returns ``(game, members)`` per lobby formed."""
    if len(waiting) < 2:
        return []
    counts: dict[int, int] = {}
    for e in waiting:
        for g in eligible_games(e):
            counts[g] = counts.get(g, 0) + 1
    placed: set[int] = set()  # positions in ``waiting``
    out: list[tuple[int, list[E]]] = []
    for g in sorted(counts, key=lambda g: (-counts[g], g)):
        idx = [i for i, e in enumerate(waiting) if i not in placed and g in eligible_games(e)]
        if len(idx) < 2:
            continue
        min_lo = min(
            players[waiting[i].pid].acc_lo
            if waiting[i].level >= LEVEL_SIZE
            else players[waiting[i].pid].pref_lo
            for i in idx
        )
        if len(idx) < min_lo:
            continue
        cands = [Candidate(waiting[i].pid, now - waiting[i].open_t, waiting[i].level) for i in idx]
        ctx = build_context(cands, players, store, now, weights, policy, shape, rng)
        res = matcher.solve(ctx, policy, seed=seed)
        if on_solve is not None:
            on_solve(ctx, res)
        for lob in res.lobbies:
            out.append((g, [waiting[idx[k]] for k in lob]))
            placed.update(idx[k] for k in lob)
    return out


def batch_at_close[E: PoolEntry](
    waiting: Sequence[E],
    players: Mapping[int, MatchPlayer],
    store: EdgeStore,
    now: float,
    weights: Weights,
    policy: Policy,
    shape: Shape,
    rng: np.random.Generator,
    seed: int = 0,
) -> list[tuple[int, list[E]]]:
    """A strict round, then a round per ladder rung for the unplaced. Raises entries' ``level``."""
    out: list[tuple[int, list[E]]] = []
    pool = list(waiting)
    for rung in range(LEVEL_BREAK_SOFT + 1):
        if rung:
            bumped = False
            for e in pool:
                if e.level < rung:
                    e.level = rung
                    bumped = True
            if not bumped:
                continue
        formed = match_round(pool, players, store, now, weights, policy, shape, rng, seed)
        out += formed
        taken = {id(e) for _, members in formed for e in members}
        pool = [e for e in pool if id(e) not in taken]
        if len(pool) < 2:
            break
    return out
