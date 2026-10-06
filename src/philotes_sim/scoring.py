"""The lobby objective of docs/spec.md §7, in one place for both matchers.

``build_context`` turns one game's pool at one moment into integer coefficients:

* per-player terms: placement, wait-time priority, newcomer / low-connectivity boost, the avoider's
  own cost for each avoid they hold (§8 "the avoider waits"), and noise (§7.6);
* pairwise terms: ``more`` with diminishing returns, mutual bonus and reunion bump (§7.3), broken
  soft avoids (§7.5 step 6), anchor + newcomer (§7.4), and noise on ``more`` pairs (§7.6);
* lobby terms: comm-style conflicts and shared interests (§6), and the "core + one or two"
  composition bonus (§7.3);
* hard constraints: lobby size inside every member's range, hard blocks, and soft avoids that the
  relaxation ladder has not yet allowed to break (§7.2, §7.5).

``lobby_score`` evaluates the same objective for one lobby. The CP-SAT model in ``matcher.py`` is
built from the same coefficients, and a test checks the two agree exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import MINUTES_PER_DAY, MINUTES_PER_HOUR, Policy, Shape, Weights
from .edges import HARD, MORE, SOFT, EdgeStore, more_weight, newness, reunion_bump
from .population import Player

LEVEL_SIZE, LEVEL_GAMES, LEVEL_BREAK_SOFT = 1, 2, 3  # §7.5 ladder rungs that the sim models


@dataclass(frozen=True)
class Candidate:
    """One open window (live) or sign-up (async) offered to the matcher for one game."""

    pid: int
    wait_min: float
    level: int  # relaxation rung reached (0 strict … 3 soft avoids against this player may break)


@dataclass
class ScoringContext:
    pids: list[int]
    lo: list[int]
    hi: list[int]
    player_w: list[int]
    seed_priority: list[float]
    conflict: list[set[int]]
    pair_w: dict[tuple[int, int], int]
    more_pairs: set[tuple[int, int]]
    soft_pairs: set[tuple[int, int]]  # pairs whose penalty is a broken soft avoid
    hist: list[set[int]]
    style: list[tuple[int, ...]]
    tags: list[tuple[int, ...]]
    w_style: int
    w_interest: int
    w_comp: int
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.pids)


def _key(i: int, j: int) -> tuple[int, int]:
    return (i, j) if i < j else (j, i)


def build_context(
    cands: list[Candidate],
    players: dict[int, Player],
    store: EdgeStore,
    now: float,
    weights: Weights,
    policy: Policy,
    shape: Shape,
    rng: np.random.Generator,
) -> ScoringContext:
    n = len(cands)
    pids = [c.pid for c in cands]
    idx = {pid: i for i, pid in enumerate(pids)}
    lo, hi = [], []
    for c in cands:
        p = players[c.pid]
        if c.level >= LEVEL_SIZE:
            lo.append(p.acc_lo)
            hi.append(p.acc_hi)
        else:
            lo.append(p.pref_lo)
            hi.append(p.pref_hi)
    new = [newness(players[pid].sessions, policy.newcomer_decay_sessions) for pid in pids]
    noise_sd = weights.noise * weights.more

    conflict: list[set[int]] = [set() for _ in range(n)]
    pair_f: dict[tuple[int, int], float] = {}
    more_pairs: set[tuple[int, int]] = set()
    soft_pairs: set[tuple[int, int]] = set()
    avoids_held = [0] * n
    more_in_pool = [0] * n

    for i, a in enumerate(pids):
        for b, _e in list(store.out.get(a, {}).items()):
            j = idx.get(b)
            if j is None:
                continue
            e = store.get(a, b, now)  # applies soft-avoid expiry
            if e is None:
                continue
            k = _key(i, j)
            if e.kind in (HARD, SOFT) and not policy.honor_avoids:
                continue  # placebo: the matcher behaves as if no avoid had been set
            if e.kind == HARD:
                conflict[i].add(j)
                conflict[j].add(i)
                avoids_held[i] += 1
            elif e.kind == SOFT:
                avoids_held[i] += 1
                if cands[j].level >= LEVEL_BREAK_SOFT:  # §7.5 step 6, gated on the avoided player
                    pair_f[k] = pair_f.get(k, 0.0) - weights.soft_avoid * store.soft_weight(e, now)
                    soft_pairs.add(k)
                else:
                    conflict[i].add(j)
                    conflict[j].add(i)
            elif e.kind == MORE and not (policy.honor_avoids and store.avoids(b, a, now)):
                # §7.3: the other person's avoid wins over this `more`.
                cp = store.coplay_of(a, b)
                count = cp.count if cp else 0
                since = (now - cp.last_t) / MINUTES_PER_DAY if cp else weights.reunion_days
                w = more_weight(weights.more, weights.more_k, count)
                w += reunion_bump(weights.reunion_bump, weights.reunion_days, since)
                pair_f[k] = pair_f.get(k, 0.0) + w
                more_pairs.add(k)
                more_in_pool[i] += 1
                back = store.get(b, a, now)
                if back is not None and back.kind == MORE:
                    pair_f[k] += weights.mutual_bonus / 2.0  # counted once from each side

    if policy.anchors_enabled:
        anchors = [i for i, pid in enumerate(pids) if players[pid].anchor]
        for a in anchors:
            for j in range(n):
                if j != a and new[j] > 0 and j not in conflict[a]:
                    k = _key(a, j)
                    pair_f[k] = pair_f.get(k, 0.0) + weights.anchor * new[j]

    if noise_sd > 0:
        for k in sorted(more_pairs):
            pair_f[k] = pair_f.get(k, 0.0) + float(rng.normal(0.0, noise_sd))

    pair_w = {k: round(v) for k, v in pair_f.items() if round(v) != 0 or k in more_pairs}

    player_w: list[int] = []
    seed_priority: list[float] = []
    jitter = rng.normal(0.0, noise_sd / 2.0, size=n) if noise_sd > 0 else np.zeros(n)
    for i, c in enumerate(cands):
        p = players[c.pid]
        w = weights.placement + shape.wait_per_hour * c.wait_min / MINUTES_PER_HOUR
        w += weights.newcomer * new[i]
        if new[i] == 0 and p.mutual_count == 0:
            w += weights.low_connectivity
        w -= weights.avoider_pays * avoids_held[i]
        w += jitter[i]
        player_w.append(round(w))
        seed_priority.append(w + weights.more * more_in_pool[i])

    hist = []
    for pid in pids:
        h = store.hist.get(pid, set())
        hist.append({idx[b] for b in h if b in idx})

    return ScoringContext(
        pids=pids,
        lo=lo,
        hi=hi,
        player_w=player_w,
        seed_priority=seed_priority,
        conflict=conflict,
        pair_w=pair_w,
        more_pairs=more_pairs,
        soft_pairs=soft_pairs,
        hist=hist,
        style=[players[pid].style for pid in pids],
        tags=[players[pid].tags for pid in pids],
        w_style=round(weights.style_conflict),
        w_interest=round(weights.interest),
        w_comp=round(weights.composition) if policy.composition_enabled else 0,
    )


# --- evaluation --------------------------------------------------------------------------------


def size_range(ctx: ScoringContext, members: list[int]) -> tuple[int, int]:
    return max(ctx.lo[i] for i in members), min(ctx.hi[i] for i in members)


def lobby_feasible(ctx: ScoringContext, members: list[int]) -> bool:
    """Hard constraints (§7.2): size inside every member's range, and no conflicting pair."""
    if not members:
        return False
    lo, hi = size_range(ctx, members)
    if not lo <= len(members) <= hi:
        return False
    s = set(members)
    return all(not (ctx.conflict[i] & s) for i in members)


def style_conflicts(ctx: ScoringContext, members: list[int]) -> int:
    n = 0
    for axis in range(len(ctx.style[members[0]])):
        vals = {ctx.style[i][axis] for i in members}
        if -1 in vals and 1 in vals:
            n += 1
    return n


def shared_tags(ctx: ScoringContext, members: list[int]) -> int:
    seen: dict[int, int] = {}
    for i in members:
        for t in ctx.tags[i]:
            seen[t] = seen.get(t, 0) + 1
    return sum(1 for c in seen.values() if c >= 2)


def has_composition(ctx: ScoringContext, members: list[int]) -> bool:
    """§7.3: a `more`-connected core of ≥ 2 and at least one member new to everyone else here."""
    s = set(members)
    core = any(
        _key(members[a], members[b]) in ctx.more_pairs
        for a in range(len(members))
        for b in range(a + 1, len(members))
    )
    if not core:
        return False
    return any(not (ctx.hist[i] & (s - {i})) for i in members)


def lobby_score(ctx: ScoringContext, members: list[int]) -> int:
    score = sum(ctx.player_w[i] for i in members)
    for a in range(len(members)):
        for b in range(a + 1, len(members)):
            score += ctx.pair_w.get(_key(members[a], members[b]), 0)
    score -= ctx.w_style * style_conflicts(ctx, members)
    score += ctx.w_interest * shared_tags(ctx, members)
    if ctx.w_comp and has_composition(ctx, members):
        score += ctx.w_comp
    return score


def total_score(ctx: ScoringContext, lobbies: list[list[int]]) -> int:
    return sum(lobby_score(ctx, lob) for lob in lobbies)
