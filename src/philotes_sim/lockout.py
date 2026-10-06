"""R8 lockout detection (docs/spec.md §8, §12 "R8 lockout").

A waiting player ``P`` is **hard-locked** when some lobby containing ``P`` could be formed from the
current pool if hard blocks were ignored, but none can be formed with them. Size ranges are taken at
their widest (accepted, not preferred) and soft avoids count as breakable, so the only thing
standing between ``P`` and a lobby is somebody's hard block. That is §8's arithmetic, evaluated on
the real pool instead of the table's worst case.

``P`` is **avoid-held** when the lobby exists with soft avoids broken but not with them honoured: a
delay, not a lockout, because §7.5 eventually breaks soft avoids.
"""

from __future__ import annotations

from dataclasses import dataclass

from .edges import HARD, SOFT, EdgeStore
from .matcher import find_lobby
from .population import Player


@dataclass
class LockoutResult:
    pool_size: int
    hard_locked: list[int]
    avoid_held: list[int]
    unknown: int  # searches that hit the node limit (counted as not locked)
    free_ok: set[int]  # a lobby exists with hard blocks ignored
    hard_ok: set[int]  # a lobby exists with hard blocks honoured
    both_ok: set[int]  # a lobby exists with hard blocks and soft avoids honoured


def check_pool(
    pids: list[int],
    players: dict[int, Player],
    store: EdgeStore,
    now: float,
    node_limit: int = 20000,
) -> LockoutResult:
    n = len(pids)
    lo = [players[p].acc_lo for p in pids]
    hi = [players[p].acc_hi for p in pids]
    idx = {p: i for i, p in enumerate(pids)}
    none: list[set[int]] = [set() for _ in range(n)]
    hard: list[set[int]] = [set() for _ in range(n)]
    both: list[set[int]] = [set() for _ in range(n)]
    for i, a in enumerate(pids):
        for b in list(store.out.get(a, {})):
            j = idx.get(b)
            if j is None:
                continue
            e = store.get(a, b, now)
            if e is None:
                continue
            if e.kind == HARD:
                hard[i].add(j)
                hard[j].add(i)
            if e.kind in (HARD, SOFT):
                both[i].add(j)
                both[j].add(i)
    hard_locked: list[int] = []
    avoid_held: list[int] = []
    free_ok: set[int] = set()
    hard_ok: set[int] = set()
    both_ok: set[int] = set()
    unknown = 0
    pool = list(range(n))
    for i in range(n):
        free_lobby, done = find_lobby(i, pool, lo, hi, none, node_limit)
        if free_lobby is None:
            unknown += 0 if done else 1
            continue
        free_ok.add(pids[i])
        with_hard, done_h = find_lobby(i, pool, lo, hi, hard, node_limit)
        if with_hard is None:
            if done_h:
                hard_locked.append(pids[i])
            else:
                unknown += 1
                hard_ok.add(pids[i])  # unknown counts as not locked
            continue
        hard_ok.add(pids[i])
        with_both, done_b = find_lobby(i, pool, lo, hi, both, node_limit)
        if with_both is None and done_b:
            avoid_held.append(pids[i])
        else:
            both_ok.add(pids[i])
    return LockoutResult(n, hard_locked, avoid_held, unknown, free_ok, hard_ok, both_ok)
