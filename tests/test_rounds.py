"""The shared matcher round (philotes_sim.rounds): batch at close and the relaxation ladder."""

from dataclasses import dataclass

import numpy as np

from philotes_sim.config import Policy, Weights, async_shape
from philotes_sim.edges import EdgeStore
from philotes_sim.rounds import batch_at_close, eligible_games, match_round
from philotes_sim.scoring import LEVEL_BREAK_SOFT, LEVEL_GAMES


@dataclass
class P:
    pid: int
    open_t: float = 0.0
    games: tuple[int, ...] = (0,)
    level: int = 0
    pref_lo: int = 4
    pref_hi: int = 4
    acc_lo: int = 3
    acc_hi: int = 5
    sessions: int = 0
    mutual_count: int = 0
    anchor: bool = False
    style: tuple[int, ...] = (0, 0, 0)
    tags: tuple[int, ...] = ()


POLICY = Policy(soft_half_life_days=7.0, newcomer_decay_sessions=0, anchors_enabled=False)


def run(entries, store=None, seed=0):
    store = store or EdgeStore(7.0, 0.05, 10)
    players = {e.pid: e for e in entries}
    rng = np.random.default_rng(seed)
    return batch_at_close(entries, players, store, 100.0, Weights(), POLICY, async_shape(), rng)


def test_eligible_games_widen_at_the_games_rung():
    e = P(1, games=(2, 0))
    assert eligible_games(e) == (2,)
    e.level = LEVEL_GAMES
    assert eligible_games(e) == (2, 0)


def test_strict_round_places_at_preferred_size():
    formed = run([P(i) for i in range(8)])
    assert sorted(len(m) for _, m in formed) == [4, 4]


def test_size_rung_rescues_a_short_pool():
    # Three people who prefer exactly 4 but accept 3–5: strict can't, the size rung can.
    entries = [P(i) for i in range(3)]
    formed = run(entries)
    assert [len(m) for _, m in formed] == [3]


def test_a_formed_seed_is_not_reopened_for_a_leftover():
    # As measured in Phase 0: the strict round's seed stands; the fifth person carries over.
    formed = run([P(i) for i in range(5)])
    assert [len(m) for _, m in formed] == [4]


def test_games_rung_offers_second_choices():
    exact4 = {"pref_lo": 4, "pref_hi": 4, "acc_lo": 4, "acc_hi": 4}
    entries = [P(i, games=(0,), **exact4) for i in range(3)] + [P(9, games=(1, 0), **exact4)]
    formed = run(entries)
    assert [(g, sorted(e.pid for e in m)) for g, m in formed] == [(0, [0, 1, 2, 9])]
    assert next(e for e in entries if e.pid == 9).level >= LEVEL_GAMES


def test_hard_block_never_breaks_and_soft_only_at_the_last_rung():
    store = EdgeStore(7.0, 0.05, 10)
    store.set_hard(0, 1, 0.0)
    entries = [P(i, pref_lo=3, pref_hi=3, acc_lo=3, acc_hi=3) for i in range(3)]
    assert run(entries, store) == []  # only one possible seed of 3, and it holds a hard block

    store = EdgeStore(7.0, 0.05, 10)
    store.set_soft(0, 1, 90.0)
    entries = [P(i, pref_lo=3, pref_hi=3, acc_lo=3, acc_hi=3) for i in range(3)]
    formed = run(entries, store)
    assert len(formed) == 1 and all(e.level == LEVEL_BREAK_SOFT for e in entries)


def test_match_round_reports_each_solve():
    seen = []
    entries = [P(i) for i in range(4)]
    match_round(
        entries,
        {e.pid: e for e in entries},
        EdgeStore(7.0, 0.05, 10),
        0.0,
        Weights(),
        POLICY,
        async_shape(),
        np.random.default_rng(0),
        on_solve=lambda ctx, res: seen.append((ctx.n, len(res.lobbies))),
    )
    assert seen == [(4, 1)]
