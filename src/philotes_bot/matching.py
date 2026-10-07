"""Form seeds from a closed sign-up window with matcher v0 from Phase 0 (§12 Phase 1).

The bot does not have its own matcher. It loads the database into the simulator's ``EdgeStore``,
turns each sign-up into a pool entry, and calls ``philotes_sim.rounds.batch_at_close``: the same
objective (``scoring.py``), heuristic (``matcher.py``) and relaxation ladder the Phase 0 sweep
measured, at the ruled settings in ``BotConfig.policy()``.

Goal lengths play the part of the simulator's async "games": a sign-up lists the goal lengths it is
up for, first choice first, and is offered its other choices only at the §7.5 step 4 rung.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from philotes_sim.edges import CoPlay, Edge, EdgeStore
from philotes_sim.rounds import batch_at_close

from .config import BotConfig
from .store import SignupRow, Store

MINUTE = 60.0


@dataclass
class Entry:
    """One sign-up as the matcher sees it (``rounds.PoolEntry`` and ``scoring.MatchPlayer``)."""

    pid: int
    open_t: float  # minutes since the epoch
    games: tuple[int, ...]
    level: int
    pref_lo: int
    pref_hi: int
    acc_lo: int
    acc_hi: int
    style: tuple[int, ...]
    tags: tuple[int, ...]
    sessions: int = 0
    mutual_count: int = 0
    anchor: bool = False  # anchors are not in v1 (§14 #18)


def edge_snapshot(store: Store, cfg: BotConfig) -> EdgeStore:
    """The database's edges and co-play records as a Phase 0 ``EdgeStore`` (times in minutes)."""
    pol = cfg.policy()
    es = EdgeStore(pol.soft_half_life_days, pol.soft_negligible, pol.hard_cap)
    for e in store.edges():
        es.out.setdefault(e.author, {})[e.target] = Edge(e.kind, e.t / MINUTE)
    for a, b, count, last_t in store.coplay():
        es.coplay[(a, b)] = CoPlay(count=count, last_t=last_t / MINUTE)
        es.hist.setdefault(a, set()).add(b)
        es.hist.setdefault(b, set()).add(a)
    return es


def form_seeds(
    store: Store,
    cfg: BotConfig,
    signups: list[SignupRow],
    now: float,
    rng: np.random.Generator,
) -> list[tuple[int, list[int]]]:
    """Batch-at-close over ``signups``. Returns ``(goal index, member user IDs)`` per seed."""
    es = edge_snapshot(store, cfg)
    now_min = now / MINUTE
    tag_ids: dict[str, int] = {}
    entries: list[Entry] = []
    for s in signups:
        p = store.player(s.user_id)
        if p is None or p.removed_at is not None:
            continue
        tags = tuple(sorted(tag_ids.setdefault(t, len(tag_ids)) for t in p.interests))
        entries.append(
            Entry(
                pid=s.user_id,
                open_t=s.signed_at / MINUTE,
                games=s.goals,
                level=0,
                pref_lo=s.pref[0],
                pref_hi=s.pref[1],
                acc_lo=s.acc[0],
                acc_hi=s.acc[1],
                style=p.style,
                tags=tags,
                sessions=p.seeds_played,
                mutual_count=len(es.mutual_partners(s.user_id, now_min)),
            )
        )
    players = {e.pid: e for e in entries}
    formed = batch_at_close(
        entries, players, es, now_min, cfg.weights(), cfg.policy(), cfg.shape(), rng
    )
    return [(g, sorted(e.pid for e in members)) for g, members in formed]
