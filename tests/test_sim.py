"""Whole-simulation properties: determinism and constraints held across every session."""

import math

import pytest

from philotes_sim.config import async_baseline, live_baseline, with_overrides
from philotes_sim.edges import HARD
from philotes_sim.metrics import compute
from philotes_sim.sim import Simulation


def small_live(seed=7, **ov):
    return with_overrides(
        live_baseline(seed=seed, weeks=3, burn_in_weeks=1),
        {"population.M": 80, **ov},
    )


def small_async(seed=7, **ov):
    return with_overrides(
        async_baseline(seed=seed, weeks=6, burn_in_weeks=2),
        {"population.M": 60, **ov},
    )


def _same(a, b):
    assert a.keys() == b.keys()
    for k in a:
        if isinstance(a[k], float) and math.isnan(a[k]):
            assert math.isnan(b[k]), k
        else:
            assert a[k] == b[k], k


@pytest.mark.parametrize("make", [small_live, small_async])
def test_same_seed_same_result(make):
    r1, r2 = Simulation(make()).run(), Simulation(make()).run()
    assert [(s.t, s.members) for s in r1.sessions] == [(s.t, s.members) for s in r2.sessions]
    m1, m2 = compute(r1), compute(r2)
    m1.pop("matcher_ms_per_run")
    m2.pop("matcher_ms_per_run")
    _same(m1, m2)


def test_different_seed_different_result():
    a = Simulation(small_live(seed=1)).run()
    b = Simulation(small_live(seed=2)).run()
    assert [s.members for s in a.sessions] != [s.members for s in b.sessions]


def test_cpsat_runs_are_deterministic():
    scn = small_live(**{"policy.matcher": "hybrid", "population.M": 50, "weeks": 2})
    a, b = Simulation(scn).run(), Simulation(scn).run()
    assert [(s.t, s.members) for s in a.sessions] == [(s.t, s.members) for s in b.sessions]


@pytest.mark.parametrize("make", [small_live, small_async])
def test_no_session_ever_contains_an_earlier_hard_block(make):
    rec = Simulation(make()).run()
    hard = {
        (a, b): e.t for a, out in rec.store.out.items() for b, e in out.items() if e.kind == HARD
    }
    assert hard, "scenario should produce some hard blocks (the clique at least)"
    for s in rec.sessions:
        for a in s.members:
            for b in s.members:
                t = hard.get((a, b))
                assert t is None or t >= s.t, (s.sid, a, b)


@pytest.mark.parametrize("make", [small_live, small_async])
def test_sessions_respect_size_ranges_and_games(make):
    rec = Simulation(make()).run()
    for s in rec.sessions:
        for p in s.members:
            pl = rec.players[p]
            assert pl.acc_lo <= len(s.members) <= pl.acc_hi
            assert s.game in pl.games
        assert len(set(s.members)) == len(s.members)


def test_clique_target_is_never_placed_with_the_clique():
    rec = Simulation(small_live()).run()
    target = next(p.pid for p in rec.players.values() if p.target)
    clique = {p.pid for p in rec.players.values() if p.clique}
    assert clique
    for s in rec.sessions:
        if target in s.members:
            assert not (clique & set(s.members))


def test_hard_cap_is_never_exceeded():
    rec = Simulation(small_live(**{"policy.hard_cap": 1})).run()
    for out in rec.store.out.values():
        assert sum(1 for e in out.values() if e.kind == HARD) <= 1
