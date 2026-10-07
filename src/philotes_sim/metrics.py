"""Every metric in the docs/spec.md §12 table, computed from a finished ``Record``.

Only the measured period counts (after ``burn_in_weeks``), except where a metric needs a pair's
whole history (edges, first co-play). Each metric's definition is in its function's docstring and
in docs/phase0-results.md. Pure helpers (``auc``, ``maximal_cliques``, ``censored_quantile``) are
separate so the tests can check them on hand-worked cases.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from collections import defaultdict

import numpy as np

from .config import MINUTES_PER_DAY, MINUTES_PER_HOUR, MINUTES_PER_WEEK
from .edges import HARD, MORE, SOFT
from .metric_helpers import (
    cosignup_metrics,
    match_rate_metrics,
    newcomer_metrics,
    placement_metrics,
    rejection_score,
    share,
)
from .sim import Record

HALL_CASUAL_FRIEND_HOURS = 50.0  # §2: Hall (2018)
N_BUCKETS = ((2, 4), (5, 7), (8, 10), (11, 15), (16, 20), (21, 30), (31, 10**9))

# --- pure helpers ------------------------------------------------------------------------------


def censored_quantile(values: list[float], q: float) -> float:
    """Quantile where ``inf`` marks "never happened": returns inf if the quantile falls there."""
    if not values:
        return math.nan
    arr = np.sort(np.asarray(values, dtype=float))
    k = math.ceil(q * len(arr)) - 1
    return float(arr[max(0, min(len(arr) - 1, k))])


def rankdata(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    xs = x[order]
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def auc(pos: list[float], neg: list[float]) -> float:
    """P(score of a random positive > score of a random negative), ties counting one half."""
    if not pos or not neg:
        return math.nan
    x = np.asarray(pos + neg, dtype=float)
    r = rankdata(x)
    n1, n0 = len(pos), len(neg)
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def maximal_cliques(adj: dict[int, set[int]]) -> list[set[int]]:
    """Bron–Kerbosch with pivoting."""
    out: list[set[int]] = []

    def bk(r: set[int], p: set[int], x: set[int]) -> None:
        if not p and not x:
            out.append(r)
            return
        pivot = max(p | x, key=lambda u: len(adj[u] & p))
        for v in sorted(p - adj[pivot]):
            bk(r | {v}, p & adj[v], x & adj[v])
            p = p - {v}
            x = x | {v}

    bk(set(), set(adj), set())
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3:
        return math.nan
    x, y = np.asarray(xs, float), np.asarray(ys, float)
    if x.std() == 0 or y.std() == 0:
        return math.nan
    return float(np.corrcoef(x, y)[0, 1])


def _bucket(n: int) -> str:
    for lo, hi in N_BUCKETS:
        if lo <= n <= hi:
            return f"{lo}-{hi}" if hi < 10**9 else f"{lo}+"
    return "<2"


# --- the metrics -------------------------------------------------------------------------------


def compute(rec: Record) -> dict[str, float]:
    scn = rec.scn
    live = scn.shape.kind == "live"
    ms, end = rec.measure_start, rec.end
    weeks = (end - ms) / MINUTES_PER_WEEK
    unit = 1.0 if live else MINUTES_PER_HOUR  # live waits in minutes, async in hours
    m: dict[str, float] = {}

    # Index sessions by player and by pair.
    by_player: dict[int, list[float]] = defaultdict(list)
    by_pair: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for s in rec.sessions:
        for i, a in enumerate(s.members):
            by_player[a].append(s.t)
            for b in s.members[i + 1 :]:
                by_pair[(min(a, b), max(a, b))].append((s.t, s.hours))
    measured_sessions = [s for s in rec.sessions if s.t >= ms]

    # R3 density: wait to placement. Unplaced windows count as "never" (inf).
    ents = [e for e in rec.entries if e.open_t >= ms and e.close_t <= end]
    target = next((p for p in rec.players.values() if p.target), None)
    tpid = target.pid if target else None
    organic = [e for e in ents if e.pid != tpid]
    waits = [
        (e.placed_t - e.open_t) / unit if e.placed_t is not None else math.inf for e in organic
    ]
    peak_waits = [
        (e.placed_t - e.open_t) / unit if e.placed_t is not None else math.inf
        for e in organic
        if e.peak
    ]
    m["entries"] = len(organic)
    m["placed_share_peak"] = _share([w < math.inf for w in peak_waits])
    m["wait_median_peak"] = censored_quantile(peak_waits, 0.5)
    m["wait_p90_peak"] = censored_quantile(peak_waits, 0.9)
    placed_peak = [w for w in peak_waits if w < math.inf]
    m["wait_median_peak_placed"] = float(np.median(placed_peak)) if placed_peak else math.nan

    # Concurrency: who is waiting, and who is online (waiting or playing), at peak.
    if live:
        conc = [c for c in rec.concurrency if c[0] >= ms and c[1]]
        m["peak_waiting_median"] = float(np.median([c[2] for c in conc])) if conc else math.nan
        m["peak_online_median"] = float(np.median([c[3] for c in conc])) if conc else math.nan
    else:
        per_window: dict[int, int] = defaultdict(int)
        per_window_game: dict[tuple[int, int], int] = defaultdict(int)
        for e in ents:
            per_window[e.window] += 1
            per_window_game[(e.window, e.games[0])] += 1
        m["peak_online_median"] = float(np.median(list(per_window.values()))) if per_window else 0
        m["peak_waiting_median"] = (
            float(np.median(list(per_window_game.values()))) if per_window_game else 0
        )
    m["sessions_per_week"] = len(measured_sessions) / weeks
    pref = [
        rec.players[p].pref_lo <= len(s.members) <= rec.players[p].pref_hi
        for s in measured_sessions
        for p in s.members
    ]
    m["mean_lobby_size"] = (
        float(np.mean([len(s.members) for s in measured_sessions])) if measured_sessions else 0
    )

    # R8 lockout.
    samples = [s for s in rec.lockout if s.t >= ms and s.peak]
    m["lockout_samples"] = len(samples)
    m["lockout_tick_share"] = _share([any(p != tpid for p in s.hard_locked) for s in samples])
    m["lockout_tick_share_incl_target"] = _share([bool(s.hard_locked) for s in samples])
    m["avoid_held_tick_share"] = _share([any(p != tpid for p in s.avoid_held) for s in samples])
    m["lockout_unknown"] = float(sum(s.unknown for s in samples))
    # Consequence per window: it closed unplaced after being hard-locked at least once.
    m["window_lost_to_hard_blocks_share"] = _share(
        [e.placed_t is None and e.locked_samples > 0 for e in organic]
    )
    if not live:
        n_signups = len(organic)
        locked = sum(sum(1 for p in s.hard_locked if p != tpid) for s in samples)
        m.update(
            placement_metrics(
                n_signups, sum(w < math.inf for w in waits), len(pref), sum(pref), locked
            )
        )
    else:
        m["placed_share"] = share(sum(w < math.inf for w in waits), len(waits))
        m["pref_size_share"] = share(sum(pref), len(pref))
    if target is not None:
        t_ents = [e for e in ents if e.pid == tpid]
        m["target_entries"] = len(t_ents)
        m["target_placed_share"] = _share([e.placed_t is not None for e in t_ents])
        if live:
            m["target_locked_hours_per_week"] = rec.target_minutes_locked / 60.0 / weeks
            m["target_waiting_hours_per_week"] = rec.target_minutes_waiting / 60.0 / weeks
        else:
            m["target_locked_windows"] = rec.target_minutes_locked
    else:
        m["target_placed_share"] = math.nan

    # R2 rematch: mutual `more` pairs, time to the next co-match after the mutual forms.
    gaps, gaps_obs = [], []
    for t_m, a, b in rec.mutual_events:
        times = [t for t, _ in by_pair[(min(a, b), max(a, b))]]
        k = bisect_right(times, t_m)
        gap = (times[k] - t_m) / MINUTES_PER_DAY if k < len(times) else math.inf
        gaps.append(gap)
        if t_m + 14 * MINUTES_PER_DAY <= end:
            gaps_obs.append(gap)
    m["mutual_pairs"] = len(rec.mutual_events)
    m["mutual_pairs_per_100_players"] = 100.0 * len(rec.mutual_events) / max(1, len(rec.players))
    m["reunion_14d_share"] = _share([g <= 14 for g in gaps_obs])
    m["reunion_median_days"] = censored_quantile(gaps_obs, 0.5)
    opp = {o for o in rec.opportunities if rec.entries[o[0]].open_t >= ms}
    hits = opp & rec.opportunity_hits
    m["reunion_opportunities"] = len(opp)
    m["reunion_opportunity_hit_share"] = len(hits) / len(opp) if opp else math.nan
    if not live:
        m["cosignup_reunion_share"] = cosignup_reunion(rec, first_choice=True)
        m["cosignup_reunion_share_any"] = cosignup_reunion(rec, first_choice=False)

    # Groups forming: stable clusters, and hours per mutual pair against Hall's 50 h.
    k = scn.cluster_min_comatches
    adj: dict[int, set[int]] = defaultdict(set)
    for (a, b), ss in by_pair.items():
        if len(ss) >= k:
            adj[a].add(b)
            adj[b].add(a)
    cliques = [c for c in maximal_cliques(dict(adj)) if len(c) >= 3] if adj else []
    in_cluster = set().union(*cliques) if cliques else set()
    played = [p for p in by_player if by_player[p]]
    m["stable_clusters"] = len(cliques)
    m["stable_clusters_per_100_players"] = 100.0 * len(cliques) / max(1, len(played))
    m["players_in_stable_cluster_share"] = len(in_cluster) / max(1, len(played))
    rates = []
    for t_m, a, b in rec.mutual_events:
        span = (end - t_m) / MINUTES_PER_WEEK
        if span < 2:
            continue
        hrs = sum(h for t, h in by_pair[(min(a, b), max(a, b))] if t > t_m)
        rates.append(hrs / span)
    for q, name in ((50, "median"), (90, "p90")):
        rate = float(np.percentile(rates, q)) if rates else math.nan
        m[f"mutual_pair_hours_per_week_{name}"] = rate
        m[f"weeks_to_hall_50h_{name}"] = HALL_CASUAL_FRIEND_HOURS / rate if rate > 0 else math.inf
    all_hours = [sum(h for _, h in ss) for ss in by_pair.values()]
    m["pair_hours_max"] = float(max(all_hours)) if all_hours else 0.0

    # R5 rich-get-richer: match rate, lobby affinity, avoid assortativity.
    per_ent: dict[int, list[bool]] = defaultdict(list)
    for e in organic:
        per_ent[e.pid].append(e.placed_t is not None)
    m.update(match_rate_metrics([(len(v), sum(v)) for v in per_ent.values()]))
    aff: dict[int, list[float]] = defaultdict(list)
    for s in measured_sessions:
        for p in s.members:
            aff[p].append(s.more_links[p] / max(1, len(s.members) - 1))
    affs = [float(np.mean(v)) for v in aff.values() if len(v) >= 3]
    m["affinity_p10"] = float(np.percentile(affs, 10)) if affs else math.nan
    m["affinity_median"] = float(np.median(affs)) if affs else math.nan
    inbound = rec.store.inbound_avoid_counts(end)
    counts = [inbound.get(p, 0) for p in played]
    cutoff = max(1.0, float(np.percentile(counts, 90))) if counts else 1.0
    top = {p for p in played if inbound.get(p, 0) >= cutoff}
    slots = sum(len(s.members) for s in measured_sessions)
    q = sum(1 for s in measured_sessions for p in s.members if p in top) / max(1, slots)
    only, null, n_top_sessions = 0, 0.0, 0
    xs, ys = [], []
    for s in measured_sessions:
        for i, a in enumerate(s.members):
            for b in s.members[i + 1 :]:
                xs += [inbound.get(a, 0), inbound.get(b, 0)]
                ys += [inbound.get(b, 0), inbound.get(a, 0)]
            if a in top:
                n_top_sessions += 1
                others = [o for o in s.members if o != a]
                only += all(o in top for o in others)
                null += q ** len(others)
    m["high_avoid_players"] = len(top)
    m["high_avoid_only_share"] = only / n_top_sessions if n_top_sessions else math.nan
    m["high_avoid_only_null"] = null / n_top_sessions if n_top_sessions else math.nan
    m["avoid_assortativity"] = pearson(xs, ys)

    # Newcomers / anchors: sessions until a newcomer's first mutual `more`.
    horizon = 5 if live else 3
    newcomers = [p for p in rec.players.values() if p.measured_newcomer]
    # Mechanism check for §7.4: how often a newcomer's first sessions include an anchor.
    nc = {p.pid for p in newcomers}
    early: dict[int, list[bool]] = defaultdict(list)
    for s in rec.sessions:
        for p in s.members:
            if p in nc and len(early[p]) < horizon:
                early[p].append(any(rec.players[o].anchor for o in s.members if o != p))
    flags = [f for v in early.values() for f in v]
    m["newcomer_early_sessions_with_anchor"] = _share(flags)
    m.update(newcomer_metrics([(p.sessions, p.first_mutual_session) for p in newcomers], horizon))
    firsts = [
        float(p.first_mutual_session) if p.first_mutual_session is not None else math.inf
        for p in newcomers
        if p.sessions >= 1
    ]
    m["newcomer_sessions_to_mutual_median"] = censored_quantile(firsts, 0.5)
    # Same measure over everyone, which has far more data than the newcomer cohort.
    everyone = [
        p
        for p in rec.players.values()
        if p.sessions >= horizon
        or (p.first_mutual_session is not None and p.first_mutual_session <= horizon)
    ]
    m["all_within_horizon_share"] = _share(
        [p.first_mutual_session is not None and p.first_mutual_session <= horizon for p in everyone]
    )

    # R5 silent rejection: the detection test.
    det = detection(rec, by_player, by_pair, tpid)
    m.update(det)

    # Soft-avoid handling (half-life sweep).
    m["soft_broken_per_100_sessions"] = (
        100.0 * sum(1 for s in measured_sessions if s.soft_broken) / len(measured_sessions)
        if measured_sessions
        else math.nan
    )
    live_avoids = sum(
        1
        for a in list(rec.store.out)
        for b in list(rec.store.out[a])
        if rec.store.avoids(a, b, end)
    )
    m["active_avoids_per_player"] = live_avoids / max(1, len(played))
    hard = sum(1 for a in rec.store.out for e in rec.store.out[a].values() if e.kind == HARD)
    m["hard_blocks_per_player"] = hard / max(1, len(played))
    m["matcher_ms_per_run"] = 1000.0 * rec.matcher_seconds / max(1, rec.matcher_runs)
    return m


def detection(rec: Record, by_player, by_pair, tpid) -> dict[str, float]:
    """§7.6 detection test, from ``b``'s side.

    For each ordered pair ``(b, c)`` that played together for the first time, ``c``'s card from
    that session is the label: avoid (soft or hard) or nothing (neutral). ``b`` then sees only their
    own lobbies. The statistic ``b`` can compute is how often ``c`` turned up again, per later
    session of ``b``'s. The AUC is how well that statistic separates "c avoided me" from "c set
    nothing": 0.5 is chance, 1.0 is certainty. ``b`` needs ``detect_min_sessions`` later sessions.

    ``detect_auc_more`` restricts to pairs where ``b`` marked ``more`` on ``c`` — the motivated
    case, "my favourite never shows up".
    """
    scn = rec.scn
    min_s = scn.detect_min_sessions
    pos, neg, pos_m, neg_m = [], [], [], []
    rematch = []
    for (c, b), (t_end, kind) in rec.first_cards.items():
        if tpid is not None and tpid in (b, c):
            continue
        if kind == MORE:
            continue
        later_b = len(by_player[b]) - bisect_right(by_player[b], t_end)
        if later_b < min_s:
            continue
        times = [t for t, _ in by_pair[(min(b, c), max(b, c))]]
        again = len(times) - bisect_right(times, t_end)
        stat = rejection_score(again, later_b, min_s)
        b_card = rec.first_cards.get((b, c), (0.0, None))[1]
        if kind in (SOFT, HARD):
            pos.append(stat)
            rematch.append(again > 0)
            if b_card == MORE:
                pos_m.append(stat)
        elif kind is None:
            neg.append(stat)
            if b_card == MORE:
                neg_m.append(stat)
    return {
        "detect_auc": auc(pos, neg) if len(pos) >= 10 else math.nan,
        "detect_auc_more": auc(pos_m, neg_m) if len(pos_m) >= 10 else math.nan,
        "detect_pos": float(len(pos)),
        "detect_neg": float(len(neg)),
        "detect_pos_more": float(len(pos_m)),
        "avoided_pair_rematch_share": _share(rematch),
    }


def mutual_spans(rec: Record) -> dict[tuple[int, int], list[tuple[float, bool]]]:
    """Per pair, the time-ordered (t, became_mutual) events: True = became mutual, False = broke."""
    spans: dict[tuple[int, int], list[tuple[float, bool]]] = defaultdict(list)
    for t, a, b in rec.mutual_events:
        spans[(min(a, b), max(a, b))].append((t, True))
    for t, a, b in rec.mutual_breaks:
        spans[(min(a, b), max(a, b))].append((t, False))
    for v in spans.values():
        v.sort()
    return spans


def is_mutual_at(events: list[tuple[float, bool]], t: float) -> bool:
    state = False
    for te, became in events:
        if te > t:
            break
        state = became
    return state


def cosignup_reunion(rec: Record, first_choice: bool = True) -> float:
    """Async R2: of pairs who were mutual `more` when both had signed up for the same window,
    asking for the same goal length first (``first_choice``) or sharing any listed length, the
    share placed in the same seed."""
    ms = rec.measure_start
    by_window: dict[tuple[int, int], object] = {}
    for e in rec.entries:
        if e.open_t >= ms:
            by_window[(e.pid, e.window)] = e
    windows = sorted({e.window for e in rec.entries if e.open_t >= ms})
    spans = mutual_spans(rec)
    tries, hits = 0, 0
    for (a, b), events in spans.items():
        for w in windows:
            ea, eb = by_window.get((a, w)), by_window.get((b, w))
            if ea is None or eb is None or not is_mutual_at(events, max(ea.open_t, eb.open_t)):
                continue
            if first_choice and ea.games[0] != eb.games[0]:
                continue
            if not set(ea.games) & set(eb.games):
                continue
            tries += 1
            hits += ea.sid is not None and ea.sid == eb.sid
    return cosignup_metrics(tries, hits)["cosignup_reunion_share"]


def lockout_by_n(rec: Record) -> list[dict[str, float | str]]:
    """Per (game pool, peak sample): share with someone hard-locked, by waiting-pool size N."""
    ms = rec.measure_start
    L = rec.scn.population.lobby_size if rec.scn.shape.kind == "live" else 0
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for s in rec.lockout:
        if s.t < ms or not s.peak:
            continue
        for _g, n, locked in s.game_pools:
            b = _bucket(n)
            agg[b][0] += 1
            agg[b][1] += 1 if locked else 0
    return [
        {"N": b, "L": L, "samples": v[0], "locked_share": v[1] / v[0] if v[0] else math.nan}
        for b, v in sorted(agg.items(), key=lambda kv: int(kv[0].split("-")[0].rstrip("+")))
    ]


def _share(flags: list[bool]) -> float:
    return share(sum(flags), len(flags))
