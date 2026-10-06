"""Hand-built scoring contexts for matcher tests."""

from __future__ import annotations

import random

from philotes_sim.scoring import ScoringContext


def make_ctx(
    n: int,
    lo: int | list[int] = 4,
    hi: int | list[int] = 4,
    conflicts: list[tuple[int, int]] = (),
    pair_w: dict[tuple[int, int], int] | None = None,
    more_pairs: set[tuple[int, int]] | None = None,
    hist: list[set[int]] | None = None,
    style: list[tuple[int, ...]] | None = None,
    tags: list[tuple[int, ...]] | None = None,
    player_w: list[int] | None = None,
    w_style: int = 80,
    w_interest: int = 10,
    w_comp: int = 50,
) -> ScoringContext:
    los = lo if isinstance(lo, list) else [lo] * n
    his = hi if isinstance(hi, list) else [hi] * n
    conflict: list[set[int]] = [set() for _ in range(n)]
    for a, b in conflicts:
        conflict[a].add(b)
        conflict[b].add(a)
    pw = player_w if player_w is not None else [1000] * n
    return ScoringContext(
        pids=list(range(100, 100 + n)),
        lo=los,
        hi=his,
        player_w=pw,
        seed_priority=[float(w) for w in pw],
        conflict=conflict,
        pair_w=dict(pair_w or {}),
        more_pairs=set(more_pairs or set()),
        soft_pairs=set(),
        hist=hist if hist is not None else [set() for _ in range(n)],
        style=style if style is not None else [(0, 0, 0)] * n,
        tags=tags if tags is not None else [()] * n,
        w_style=w_style,
        w_interest=w_interest,
        w_comp=w_comp,
    )


def random_ctx(seed: int, n: int | None = None) -> ScoringContext:
    r = random.Random(seed)
    n = n if n is not None else r.randint(5, 16)
    lo = [r.choice([2, 3, 3, 4, 4]) for _ in range(n)]
    hi = [x + r.choice([0, 0, 1, 2]) for x in lo]
    conflicts = [(a, b) for a in range(n) for b in range(a + 1, n) if r.random() < 0.12]
    pair_w = {}
    more = set()
    for a in range(n):
        for b in range(a + 1, n):
            u = r.random()
            if u < 0.15:
                pair_w[(a, b)] = r.randint(20, 120)
                more.add((a, b))
            elif u < 0.2:
                pair_w[(a, b)] = -r.randint(10, 300)
    hist = [set() for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            if r.random() < 0.2:
                hist[a].add(b)
                hist[b].add(a)
    style = [tuple(r.choice([-1, 0, 1]) for _ in range(3)) for _ in range(n)]
    tags = [tuple(sorted(r.sample(range(6), r.randint(0, 2)))) for _ in range(n)]
    player_w = [1000 + r.randint(0, 200) for _ in range(n)]
    return make_ctx(
        n,
        lo=lo,
        hi=hi,
        conflicts=conflicts,
        pair_w=pair_w,
        more_pairs=more,
        hist=hist,
        style=style,
        tags=tags,
        player_w=player_w,
    )
