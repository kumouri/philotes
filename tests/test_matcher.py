"""Matcher hard constraints, objective consistency and the §8 lockout arithmetic."""

import pytest

from philotes_sim.config import Policy
from philotes_sim.edges import EdgeStore
from philotes_sim.lockout import check_pool
from philotes_sim.matcher import find_lobby, solve, solve_cpsat, solve_heuristic
from philotes_sim.population import Player
from philotes_sim.scoring import lobby_feasible, lobby_score, total_score

from .helpers import make_ctx, random_ctx

POLICY = Policy(cpsat_det_time=20.0)


def assert_valid(ctx, lobbies):
    seen = set()
    for lob in lobbies:
        assert lobby_feasible(ctx, lob), lob
        lo = max(ctx.lo[i] for i in lob)
        hi = min(ctx.hi[i] for i in lob)
        assert lo <= len(lob) <= hi  # every member's size range admits the lobby
        for i in lob:
            assert not (ctx.conflict[i] & set(lob))  # no hard block inside a lobby
            assert i not in seen  # nobody in two lobbies
            seen.add(i)


@pytest.mark.parametrize("seed", range(40))
def test_heuristic_respects_hard_constraints(seed):
    ctx = random_ctx(seed)
    assert_valid(ctx, solve_heuristic(ctx, POLICY).lobbies)


@pytest.mark.parametrize("seed", range(15))
def test_cpsat_respects_hard_constraints_and_bounds_heuristic(seed):
    ctx = random_ctx(seed, n=10)
    exact = solve_cpsat(ctx, POLICY)
    heur = solve_heuristic(ctx, POLICY)
    assert_valid(ctx, exact.lobbies)
    assert exact.optimal
    # The CP-SAT model and lobby_score are the same objective: the solver's bound is the score.
    assert exact.bound == pytest.approx(exact.score)
    assert heur.score <= exact.score


def test_hard_block_pair_is_split():
    ctx = make_ctx(8, lo=4, hi=4, conflicts=[(0, 1)])
    for res in (solve_heuristic(ctx, POLICY), solve_cpsat(ctx, POLICY)):
        assert_valid(ctx, res.lobbies)
        assert sum(len(lob) for lob in res.lobbies) == 8
        assert not any({0, 1} <= set(lob) for lob in res.lobbies)


def test_size_ranges_are_respected():
    # Six players; two accept only 3, four accept only 4: one lobby of 4, the 3s cannot play.
    ctx = make_ctx(6, lo=[3, 3, 4, 4, 4, 4], hi=[3, 3, 4, 4, 4, 4])
    for res in (solve_heuristic(ctx, POLICY), solve_cpsat(ctx, POLICY)):
        assert_valid(ctx, res.lobbies)
        assert [sorted(lob) for lob in res.lobbies] == [[2, 3, 4, 5]]


def test_unplaceable_when_conflicts_leave_too_few():
    ctx = make_ctx(4, lo=4, hi=4, conflicts=[(0, 1)])
    for res in (solve_heuristic(ctx, POLICY), solve_cpsat(ctx, POLICY)):
        assert res.lobbies == []


def test_lobby_score_by_hand():
    # Players 0..3. 0→1 is a `more` pair worth 70; 2 and 3 are on opposite ends of axis 0;
    # 0, 1 share tag 5; 3 has no history with anyone, and 0–1 have history.
    ctx = make_ctx(
        4,
        pair_w={(0, 1): 70},
        more_pairs={(0, 1)},
        hist=[{1}, {0}, set(), set()],
        style=[(0, 0, 0), (0, 0, 0), (-1, 0, 0), (1, 0, 0)],
        tags=[(5,), (5, 6), (), ()],
    )
    expected = 4 * 1000 + 70 - 80 + 10 + 50  # players + more − style + interest + composition
    assert lobby_score(ctx, [0, 1, 2, 3]) == expected
    # Just the core: no fresh member, so no composition bonus.
    assert lobby_score(ctx, [0, 1]) == 2 * 1000 + 70 + 10
    assert total_score(ctx, [[0, 1, 2, 3]]) == expected


def test_hybrid_dispatch_uses_cpsat_for_small_pools():
    ctx = random_ctx(3, n=8)
    assert solve(ctx, Policy(matcher="hybrid", cpsat_max_pool=10)).method == "cpsat"
    assert solve(ctx, Policy(matcher="hybrid", cpsat_max_pool=5)).method == "heuristic"


def test_find_lobby_reports_exhaustion():
    n = 6
    conflict = [set() for _ in range(n)]
    lobby, done = find_lobby(0, range(n), [3] * n, [3] * n, conflict, node_limit=1000)
    assert lobby is not None and len(lobby) == 3 and done
    for j in range(1, n):
        conflict[0].add(j)
        conflict[j].add(0)
    lobby, done = find_lobby(0, range(n), [3] * n, [3] * n, conflict, node_limit=1000)
    assert lobby is None and done


def _players(n, lobby):
    import numpy as np

    return {
        i: Player(
            pid=i,
            games=(0,),
            pref_lo=lobby,
            pref_hi=lobby,
            acc_lo=lobby,
            acc_hi=lobby,
            tz=0,
            activity=1.0,
            style=(0, 0, 0),
            tags=(),
            compat=np.ones(3) / np.sqrt(3),
        )
        for i in range(n)
    }


@pytest.mark.parametrize(
    ("N", "L", "avoiders", "locked"),
    [
        (8, 5, 4, True),  # §8 worked example: 8 queued, lobby of 5, 4 online avoiders
        (8, 5, 3, False),  # one fewer avoider and P fits: A ≤ N − L
        (6, 5, 2, True),  # table row N=6, L=5: 2 of 5
        (10, 4, 7, True),  # table row N=10, L=4: 7 of 9
        (10, 4, 6, False),
    ],
)
def test_lockout_matches_spec_arithmetic(N, L, avoiders, locked):
    players = _players(N, L)
    store = EdgeStore(half_life_days=30, negligible=0.05, hard_cap=5)
    for a in range(1, avoiders + 1):
        store.set_hard(a, 0, 0.0)
    res = check_pool(list(range(N)), players, store, 0.0)
    assert (0 in res.hard_locked) is locked
    assert res.unknown == 0


def test_soft_avoids_hold_but_do_not_lock():
    players = _players(8, 5)
    store = EdgeStore(half_life_days=30, negligible=0.05, hard_cap=5)
    for a in range(1, 5):
        store.set_soft(a, 0, 0.0)
    res = check_pool(list(range(8)), players, store, 0.0)
    assert 0 not in res.hard_locked
    assert 0 in res.avoid_held


@pytest.mark.parametrize("seed", range(25))
def test_heuristic_valid_with_wide_async_ranges(seed):
    """Async-style ranges (preferred 3–7, accepted 2–9) mixed in one pool of up to 30."""
    import random

    r = random.Random(1000 + seed)
    n = r.randint(8, 30)
    centres = [r.choice([4, 5, 6]) for _ in range(n)]
    strict = [r.random() < 0.5 for _ in range(n)]
    lo = [c - 1 if s else c - 2 for c, s in zip(centres, strict, strict=True)]
    hi = [c + 1 if s else c + 3 for c, s in zip(centres, strict, strict=True)]
    base = random_ctx(seed, n=n)
    base.lo, base.hi = lo, hi
    assert_valid(base, solve_heuristic(base, POLICY).lobbies)


def test_heuristic_does_not_strand_fixed_size_players():
    """Captured from a real run: flexible players (3–5) spent on one lobby stranded three
    exactly-4 players. Exact CP-SAT places all seven as 4 + 3; the heuristic must too."""
    lo = [3, 4, 4, 3, 3, 3, 4]
    hi = [5, 4, 4, 5, 5, 5, 4]
    ctx = make_ctx(7, lo=lo, hi=hi, player_w=[1300, 1000, 1200, 1250, 1000, 1000, 1100])
    res = solve_heuristic(ctx, POLICY)
    assert_valid(ctx, res.lobbies)
    assert sum(len(lob) for lob in res.lobbies) == 7
    assert res.score == solve_cpsat(ctx, POLICY).score


def test_best_partition_places_everyone_when_possible():
    from philotes_sim.matcher import best_partition

    # Four exactly-4 players and four flexible (3–5): 4 + 4 places all eight.
    ctx = make_ctx(8, lo=[4, 4, 4, 4, 3, 3, 3, 3], hi=[4, 4, 4, 4, 5, 5, 5, 5])
    parts, placed = best_partition(ctx, list(range(8)), node_limit=10_000)
    assert placed == 8
    assert_valid(ctx, parts)
    # A block between two fixed players just splits them: still all eight.
    lo, hi = [4, 4, 4, 4, 3, 3, 3, 3], [4, 4, 4, 4, 5, 5, 5, 5]
    ctx = make_ctx(8, lo=lo, hi=hi, conflicts=[(0, 1)])
    parts, placed = best_partition(ctx, list(range(8)), node_limit=10_000)
    assert_valid(ctx, parts)
    assert placed == 8
    # Player 0 (exactly 4) is blocked with everyone but 1 and 2: 0 cannot play; the other 7 can.
    ctx = make_ctx(8, lo=lo, hi=hi, conflicts=[(0, j) for j in range(3, 8)])
    parts, placed = best_partition(ctx, list(range(8)), node_limit=10_000)
    assert_valid(ctx, parts)
    assert placed == 7
    assert not any(0 in lob for lob in parts)
