"""Decay maths and edge rules (spec §7.2–§7.4, §11)."""

import math

import pytest

from philotes_sim.config import MINUTES_PER_DAY
from philotes_sim.edges import (
    HARD,
    MORE,
    SOFT,
    EdgeStore,
    more_weight,
    newness,
    reunion_bump,
    soft_avoid_weight,
)


@pytest.mark.parametrize("half_life", [7, 14, 30, 60, 90])
def test_soft_avoid_halves_every_half_life(half_life):
    day = MINUTES_PER_DAY
    assert soft_avoid_weight(0, half_life) == 1.0
    assert soft_avoid_weight(half_life * day, half_life) == pytest.approx(0.5)
    assert soft_avoid_weight(2 * half_life * day, half_life) == pytest.approx(0.25)
    assert soft_avoid_weight(-5, half_life) == 1.0  # set in the future: treated as fresh


def test_newcomer_boost_decays_linearly_to_zero():
    assert newness(0, 20) == 1.0
    assert newness(5, 20) == pytest.approx(0.75)
    assert newness(10, 20) == pytest.approx(0.5)
    assert newness(20, 20) == 0.0
    assert newness(40, 20) == 0.0
    assert newness(0, 0) == 0.0  # decay length 0 = boost off


def test_more_weight_diminishing_returns():
    assert more_weight(60, 1.0, 0) == 60
    assert more_weight(60, 1.0, round(math.e - 1)) < 60
    # n such that ln(1+n) = 1 gives M / 2.
    assert 60 / (1 + math.log1p(math.e - 1)) == pytest.approx(30)
    assert more_weight(60, 1.0, 40) < more_weight(60, 1.0, 10) < more_weight(60, 1.0, 1)


def test_reunion_bump_rises_with_time_apart():
    assert reunion_bump(20, 14, 0) == 0
    assert reunion_bump(20, 14, 7) == pytest.approx(10)
    assert reunion_bump(20, 14, 14) == 20
    assert reunion_bump(20, 14, 100) == 20


def test_soft_avoid_expires_below_negligible_weight():
    s = EdgeStore(half_life_days=10, negligible=0.25, hard_cap=5)
    s.set_soft(1, 2, 0.0)
    assert s.avoids(1, 2, 19.9 * MINUTES_PER_DAY)  # weight just above 0.25
    assert not s.avoids(1, 2, 20.1 * MINUTES_PER_DAY)  # two half-lives: below → deleted
    assert 2 not in s.out[1]


def test_soft_avoid_refresh_restarts_decay():
    s = EdgeStore(half_life_days=10, negligible=0.05, hard_cap=5)
    s.set_soft(1, 2, 0.0)
    s.set_soft(1, 2, 10 * MINUTES_PER_DAY)
    e = s.get(1, 2, 10 * MINUTES_PER_DAY)
    assert s.soft_weight(e, 10 * MINUTES_PER_DAY) == 1.0


def test_hard_block_cap_falls_back_to_soft():
    s = EdgeStore(half_life_days=30, negligible=0.05, hard_cap=2)
    assert s.set_hard(1, 2, 0) == HARD
    assert s.set_hard(1, 3, 0) == HARD
    assert s.set_hard(1, 4, 0) == SOFT
    assert s.hard_count(1) == 2
    assert s.get(1, 4, 0).kind == SOFT


def test_hard_blocks_never_decay_or_downgrade():
    s = EdgeStore(half_life_days=1, negligible=0.05, hard_cap=5)
    s.set_hard(1, 2, 0)
    s.set_soft(1, 2, 0)
    assert s.get(1, 2, 10_000 * MINUTES_PER_DAY).kind == HARD


def test_avoid_overrides_the_other_persons_more():
    """§7.3 asymmetry rule: a `more` never overrides the other person's avoid."""
    s = EdgeStore(half_life_days=30, negligible=0.05, hard_cap=5)
    s.set_more(1, 2, 0)
    assert s.valid_more(1, 2, 0)
    s.set_soft(2, 1, 0)
    assert not s.valid_more(1, 2, 0)
    assert s.get(1, 2, 0).kind == MORE


def test_mutual_more_and_coplay_records():
    s = EdgeStore(half_life_days=30, negligible=0.05, hard_cap=5)
    s.set_more(1, 2, 0)
    assert not s.mutual_more(1, 2, 0)
    s.set_more(2, 1, 0)
    assert s.mutual_more(1, 2, 0) and s.mutual_more(2, 1, 0)
    cp = s.record_coplay(2, 1, 5.0, 2.0)
    s.record_coplay(1, 2, 9.0, 1.5)
    assert cp.count == 2 and cp.last_t == 9.0 and cp.hours == 3.5
    assert s.hist[1] == {2} and s.hist[2] == {1}


def test_reads_that_expire_soft_avoids_are_safe_mid_iteration():
    s = EdgeStore(half_life_days=1, negligible=0.5, hard_cap=5)
    s.set_more(1, 2, 0)
    s.set_more(2, 1, 0)
    s.set_soft(1, 3, 0)
    later = 3 * MINUTES_PER_DAY  # the soft avoid 1 → 3 has decayed below the threshold
    assert s.mutual_partners(1, later) == [2]
    assert s.inbound_avoid_counts(later) == {}
