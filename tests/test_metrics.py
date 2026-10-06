"""Metric helpers and metrics on tiny hand-built records."""

import math

import numpy as np
import pytest

from philotes_sim.config import MINUTES_PER_DAY, MINUTES_PER_WEEK, async_baseline, live_baseline
from philotes_sim.edges import SOFT, EdgeStore
from philotes_sim.metrics import (
    auc,
    censored_quantile,
    compute,
    cosignup_reunion,
    maximal_cliques,
    rankdata,
)
from philotes_sim.population import Player
from philotes_sim.sim import Entry, Record, Session


def test_auc_hand_cases():
    assert auc([3, 4], [1, 2]) == 1.0
    assert auc([1, 2], [3, 4]) == 0.0
    assert auc([1, 1], [1, 1]) == 0.5
    # pos {2, 4} vs neg {1, 3}: pairs (2>1), (2<3), (4>1), (4>3) → 3 of 4.
    assert auc([2, 4], [1, 3]) == 0.75
    assert math.isnan(auc([], [1]))


def test_rankdata_averages_ties():
    assert list(rankdata(np.array([10.0, 20.0, 10.0, 30.0]))) == [1.5, 3.0, 1.5, 4.0]


def test_censored_quantile_treats_inf_as_never():
    assert censored_quantile([1, 2, 3, math.inf], 0.5) == 2
    assert censored_quantile([1, math.inf, math.inf], 0.5) == math.inf
    assert math.isnan(censored_quantile([], 0.5))


def test_maximal_cliques_small_graph():
    # Triangle 1-2-3 plus a pendant 3-4.
    adj = {1: {2, 3}, 2: {1, 3}, 3: {1, 2, 4}, 4: {3}}
    cl = sorted(sorted(c) for c in maximal_cliques(adj))
    assert cl == [[1, 2, 3], [3, 4]]


def _player(pid, sessions=0, first=None, newcomer=False):
    return Player(
        pid=pid,
        games=(0,),
        pref_lo=2,
        pref_hi=2,
        acc_lo=2,
        acc_hi=2,
        tz=0,
        activity=1.0,
        style=(0, 0, 0),
        tags=(),
        compat=np.ones(3) / np.sqrt(3),
        sessions=sessions,
        first_mutual_session=first,
        measured_newcomer=newcomer,
    )


def _record(entries, sessions, players, mutual=(), first_cards=None, store=None, kind="live"):
    scn = live_baseline(weeks=4, burn_in_weeks=0)
    if kind == "async":
        scn = async_baseline(weeks=4, burn_in_weeks=0)
    return Record(
        scn=scn,
        players={p.pid: p for p in players},
        entries=entries,
        sessions=sessions,
        store=store or EdgeStore(30, 0.05, 5),
        mutual_events=list(mutual),
        first_cards=first_cards or {},
        lockout=[],
        target_minutes_waiting=0.0,
        target_minutes_locked=0.0,
        concurrency=[],
        opportunities=set(),
        opportunity_hits=set(),
        matcher_runs=1,
        matcher_seconds=0.0,
        measure_start=0.0,
        end=4 * MINUTES_PER_WEEK,
    )


def test_wait_and_placement_by_hand():
    # Four peak windows: waits 4, 6 and 10 minutes, and one never placed.
    entries = [
        Entry(0, 1, 100.0, 220.0, (0,), True, placed_t=104.0, sid=0),
        Entry(1, 2, 100.0, 220.0, (0,), True, placed_t=106.0, sid=0),
        Entry(2, 3, 100.0, 220.0, (0,), True, placed_t=110.0, sid=1),
        Entry(3, 4, 100.0, 220.0, (0,), True),
    ]
    sessions = [
        Session(0, 104.0, 224.0, 0, [1, 2], 2.0, 0, {1: 0, 2: 0}),
        Session(1, 110.0, 230.0, 0, [3, 5], 2.0, 0, {3: 0, 5: 0}),
    ]
    m = compute(_record(entries, sessions, [_player(i) for i in range(1, 6)]))
    assert m["placed_share_peak"] == 0.75
    assert m["wait_median_peak"] == 6.0  # sorted 4, 6, 10, inf → 2nd of 4
    assert m["wait_p90_peak"] == math.inf
    assert m["wait_median_peak_placed"] == 6.0


def test_reunion_by_hand():
    # Pair (1, 2) turns mutual at day 1 and is co-matched again at day 4 → reunited in 3 days.
    d = MINUTES_PER_DAY
    sessions = [
        Session(0, 0.5 * d, d, 0, [1, 2], 2.0, 0, {1: 0, 2: 0}),
        Session(1, 4 * d, 4.1 * d, 0, [1, 2], 2.0, 0, {1: 1, 2: 1}),
    ]
    m = compute(_record([], sessions, [_player(1), _player(2)], mutual=[(d, 1, 2)]))
    assert m["reunion_14d_share"] == 1.0
    assert m["reunion_median_days"] == pytest.approx(3.0)


def test_newcomer_share_by_hand():
    players = [
        _player(1, sessions=6, first=2, newcomer=True),  # reached within 5
        _player(2, sessions=7, first=None, newcomer=True),  # 7 sessions, never
        _player(3, sessions=2, first=None, newcomer=True),  # too few sessions: not eligible
        _player(4, sessions=3, first=3, newcomer=True),  # reached at 3: eligible, yes
    ]
    m = compute(_record([], [], players))
    assert m["newcomers"] == 4
    assert m["newcomers_eligible"] == 3
    assert m["newcomer_within_horizon_share"] == pytest.approx(2 / 3)


def test_detection_perfect_separation():
    # 12 avoiders never seen again; 12 neutral co-players seen again every time.
    d = MINUTES_PER_DAY
    sessions, cards, players = [], {}, [_player(0)]
    for c in range(1, 25):
        players.append(_player(c))
        cards[(c, 0)] = (0.0, SOFT if c <= 12 else None)
    for k in range(6):
        members = [0, *range(13, 25)]
        links = {p: 0 for p in members}
        sessions.append(Session(k, d * (k + 1), d * (k + 1.1), 0, members, 2.0, 0, links))
    rec = _record([], sessions, players, first_cards=cards)
    m = compute(rec)
    assert m["detect_auc"] == 1.0
    assert m["detect_pos"] == 12 and m["detect_neg"] == 12


def test_cosignup_reunion_by_hand():
    entries = [
        Entry(0, 1, 10.0, 99.0, (0,), True, window=0, placed_t=20.0, sid=0),
        Entry(1, 2, 11.0, 99.0, (0, 1), True, window=0, placed_t=20.0, sid=0),
        Entry(2, 1, 110.0, 199.0, (0,), True, window=1, placed_t=120.0, sid=1),
        Entry(3, 2, 111.0, 199.0, (1,), True, window=1, placed_t=120.0, sid=2),  # no shared game
        Entry(4, 1, 210.0, 299.0, (2,), True, window=2, placed_t=220.0, sid=3),
        Entry(5, 2, 211.0, 299.0, (2,), True, window=2, placed_t=220.0, sid=4),
    ]
    rec = _record(entries, [], [_player(1), _player(2)], mutual=[(0.0, 1, 2)], kind="async")
    # Window 0: same seed (hit). Window 1: no shared goal length (not a try). Window 2: missed.
    assert cosignup_reunion(rec) == 0.5
