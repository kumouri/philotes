"""The simulation loop (docs/spec.md §12 "Simulation harness").

Two pool shapes share one loop:

* **live** (the co-op fallback niche, §9.2): players open availability windows (§6, §9.1); the
  matcher runs every tick (§7.1, 30 s) when the pool changed or someone climbed a relaxation rung;
  a session runs for about two hours and its members are busy meanwhile.
* **async** (the first niche, async Archipelago, §9.2, §14 #3): a weekly sign-up window; sign-ups
  arrive front-loaded through the week; the matcher runs every ``cadence_hours`` and makes a final
  pass at close with every rung relaxed. A placed sign-up becomes a seed that runs for its goal
  length (1, 2 or 4 weeks). Players may sign up again the next week while a seed is still running.

Time is in minutes. A run is deterministic for a given ``Scenario`` (seed included): every random
draw comes from one of five named streams split from the scenario seed, so a policy change does not
reshuffle who exists or when they queue.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

import numpy as np

from . import matcher
from .config import MINUTES_PER_HOUR, MINUTES_PER_WEEK, Scenario
from .edges import HARD, SOFT, EdgeStore
from .lockout import check_pool
from .population import Player, PopulationFactory, peak_hours
from .rounds import eligible_games, match_round
from .scoring import LEVEL_BREAK_SOFT, ScoringContext

_OPEN, _END, _WEEK, _CLOSE = 0, 1, 2, 9  # CLOSE sorts last so a closing entry gets the final pass


@dataclass
class Entry:
    eid: int
    pid: int
    open_t: float
    close_t: float
    games: tuple[int, ...]
    peak: bool
    window: int = -1
    level: int = 0
    placed_t: float | None = None
    sid: int | None = None
    locked_samples: int = 0  # lockout samples in which this entry was hard-locked


@dataclass
class Session:
    sid: int
    t: float
    end_t: float
    game: int
    members: list[int]
    hours: float  # co-play hours credited to each pair
    soft_broken: int  # pairs here with a live soft avoid, i.e. §7.5 step 6 happened
    more_links: dict[int, int]  # per member: co-members joined to them by a valid `more`


@dataclass
class LockoutSample:
    t: float
    peak: bool
    pool: int  # everyone waiting
    game_pools: list[tuple[int, int, int]]  # (game, N waiting for it, hard-locked in it)
    hard_locked: list[int]
    avoid_held: list[int]
    unknown: int


@dataclass
class Record:
    scn: Scenario
    players: dict[int, Player]
    entries: list[Entry]
    sessions: list[Session]
    store: EdgeStore
    mutual_events: list[tuple[float, int, int]]
    mutual_breaks: list[tuple[float, int, int]]  # a mutual pair stopped being mutual
    first_cards: dict[tuple[int, int], tuple[float, str | None]]  # (a,b) → (t_end, a's edge on b)
    lockout: list[LockoutSample]
    target_minutes_waiting: float
    target_minutes_locked: float
    concurrency: list[tuple[float, bool, int, int]]  # (t, peak, waiting, online)
    opportunities: set[tuple[int, int]]
    opportunity_hits: set[tuple[int, int]]
    matcher_runs: int
    matcher_seconds: float
    measure_start: float
    end: float
    contexts: list[ScoringContext] = field(default_factory=list)


class Simulation:
    def __init__(self, scn: Scenario, capture_contexts: int = 0) -> None:
        self.scn = scn
        streams = np.random.SeedSequence(scn.seed).spawn(5)
        rng_pop, self.rng_sched, self.rng_out, self.rng_match, self.rng_churn = (
            np.random.default_rng(s) for s in streams
        )
        self.factory = PopulationFactory(scn.population, scn.shape, rng_pop)
        pol = scn.policy
        self.store = EdgeStore(pol.soft_half_life_days, pol.soft_negligible, pol.hard_cap)
        self.players: dict[int, Player] = {p.pid: p for p in self.factory.initial()}
        self.peak = peak_hours(list(self.players.values()))
        self.live = scn.shape.kind == "live"
        self.heap: list[tuple[float, int, int, int, object]] = []
        self.seq = 0
        self.pool: dict[int, Entry] = {}
        self.open_by_pid: dict[int, int] = {}
        self.busy_until: dict[int, float] = {}
        self.entries: list[Entry] = []
        self.sessions: list[Session] = []
        self.mutual_events: list[tuple[float, int, int]] = []
        self.mutual_breaks: list[tuple[float, int, int]] = []
        self.first_cards: dict[tuple[int, int], tuple[float, str | None]] = {}
        self.pending_first: dict[int, list[tuple[int, int]]] = {}
        self.lockout: list[LockoutSample] = []
        self.concurrency: list[tuple[float, bool, int, int]] = []
        self.opportunities: set[tuple[int, int]] = set()
        self.opportunity_hits: set[tuple[int, int]] = set()
        self.matcher_runs = 0
        self.matcher_seconds = 0.0
        self.target_wait = 0.0
        self.target_locked = 0.0
        self.capture = capture_contexts
        self.contexts: list[ScoringContext] = []
        self.dirty = False
        self.measure_start = scn.burn_in_weeks * MINUTES_PER_WEEK
        self.target = next((p.pid for p in self.players.values() if p.target), None)
        self.clique = [p.pid for p in self.players.values() if p.clique]
        for c in self.clique:  # the coordinated clique hard-blocks its target from the start
            self.store.set_hard(c, self.target, 0.0)

    # --- event plumbing ----------------------------------------------------------------------

    def _push(self, t: float, kind: int, payload: object) -> None:
        heapq.heappush(self.heap, (t, kind, self.seq, kind, payload))
        self.seq += 1

    def _pop_until(self, T: float, include_close: bool) -> None:
        while self.heap:
            t, prio, _, kind, payload = self.heap[0]
            if t > T or (t == T and prio == _CLOSE and not include_close):
                return
            heapq.heappop(self.heap)
            if kind == _OPEN:
                self._open(t, payload)
            elif kind == _CLOSE:
                self._close(payload)
            elif kind == _END:
                self._end_session(t, payload)
            elif kind == _WEEK:
                self._week(int(payload))

    # --- run ---------------------------------------------------------------------------------

    def run(self) -> Record:
        scn, sh = self.scn, self.scn.shape
        end = scn.weeks * MINUTES_PER_WEEK
        for w in range(scn.weeks):
            self._push(w * MINUTES_PER_WEEK, _WEEK, w)
        step = sh.tick_seconds / 60.0 if self.live else sh.cadence_hours * MINUTES_PER_HOUR
        sample_every = max(1, round(scn.lockout_sample_minutes / step)) if self.live else 0
        n_steps = round(end / step)
        for si in range(n_steps + 1):
            T = si * step
            self._pop_until(T, include_close=False)
            if self._update_levels(T) or self.dirty:
                self._run_matcher(T)
                self.dirty = False
            if not self.live:
                self._closing_passes(T)
            if self.live and si % sample_every == 0:
                self._sample_live(T, sample_every * step)
            elif not self.live and self._closing_now(T):
                self._sample_lockout(T, peak=True, closing_only=True)
            self._pop_until(T, include_close=True)
        return Record(
            scn=scn,
            players=self.players,
            entries=self.entries,
            sessions=self.sessions,
            store=self.store,
            mutual_events=self.mutual_events,
            mutual_breaks=self.mutual_breaks,
            first_cards=self.first_cards,
            lockout=self.lockout,
            target_minutes_waiting=self.target_wait,
            target_minutes_locked=self.target_locked,
            concurrency=self.concurrency,
            opportunities=self.opportunities,
            opportunity_hits=self.opportunity_hits,
            matcher_runs=self.matcher_runs,
            matcher_seconds=self.matcher_seconds,
            measure_start=self.measure_start,
            end=end,
            contexts=self.contexts,
        )

    # --- arrivals, churn and schedules -------------------------------------------------------

    def _week(self, w: int) -> None:
        ws = w * MINUTES_PER_WEEK
        pop = self.scn.population
        rng = self.rng_churn
        if w > 0:
            protected = {self.target, *self.clique}
            for _ in range(int(rng.poisson(pop.newcomer_rate * pop.M))):
                active = [
                    p for p in self.players.values() if p.active(ws) and p.pid not in protected
                ]
                if active:
                    gone = active[int(rng.integers(len(active)))]
                    gone.left = ws + float(rng.random()) * MINUTES_PER_WEEK
            for _ in range(int(rng.poisson(pop.newcomer_rate * pop.M))):
                t = ws + float(rng.random()) * MINUTES_PER_WEEK
                p = self.factory.make(t)
                p.measured_newcomer = t >= self.measure_start
                self.players[p.pid] = p
        if self.live:
            self._schedule_live_week(w, ws)
        else:
            self._schedule_async_window(w, ws)

    def _schedule_live_week(self, w: int, ws: float) -> None:
        sh = self.scn.shape
        rng = self.rng_sched
        clique = set(self.clique)
        for p in list(self.players.values()):
            if p.pid in clique or (p.left is not None and p.left <= ws):
                continue
            start = max(ws, p.arrived)
            for t in PopulationFactory.window_starts(p, ws, start, sh.windows_per_week, rng):
                self._push(t, _OPEN, (p.pid, -1))
        if clique:
            # The clique queues together: shared start times, each member joining most of them.
            lead = self.players[self.clique[0]]
            rate = sh.windows_per_week * 1.5
            for t in PopulationFactory.window_starts(lead, ws, ws, rate, rng):
                for c in self.clique:
                    if rng.random() < self.scn.population.clique_together:
                        self._push(t + float(rng.random()) * 5.0, _OPEN, (c, -1))

    def _schedule_async_window(self, w: int, ws: float) -> None:
        sh = self.scn.shape
        rng = self.rng_sched
        minutes = sh.signup_days * 24 * MINUTES_PER_HOUR
        clique = set(self.clique)
        clique_on = bool(clique) and rng.random() < 0.8
        for p in list(self.players.values()):
            if p.left is not None and p.left <= ws:
                continue
            if p.pid in clique:
                if clique_on and rng.random() < self.scn.population.clique_together:
                    t = PopulationFactory.signup_time(ws, minutes, rng)
                    self._push(t, _OPEN, (p.pid, w))
                continue
            if rng.random() < min(1.0, sh.signup_prob * p.activity):
                t = PopulationFactory.signup_time(ws, minutes, rng)
                if p.arrived > t:
                    t = p.arrived
                if t < ws + minutes - 12 * MINUTES_PER_HOUR:
                    self._push(t, _OPEN, (p.pid, w))

    # --- entries -----------------------------------------------------------------------------

    def _open(self, t: float, payload: object) -> None:
        pid, window = payload  # type: ignore[misc]
        p = self.players[pid]
        if not p.active(t) or pid in self.open_by_pid:
            return
        if self.live and self.busy_until.get(pid, -1.0) > t:
            return
        sh = self.scn.shape
        if self.live:
            jitter = 0.75 + 0.5 * float(self.rng_sched.random())
            close = t + sh.window_hours * MINUTES_PER_HOUR * jitter
            peak = bool(self.peak[int(t // MINUTES_PER_HOUR) % 168])
        else:
            close = (window * MINUTES_PER_WEEK) + sh.signup_days * 24 * MINUTES_PER_HOUR
            peak = True
        e = Entry(len(self.entries), pid, t, close, p.games, peak, window)
        self.entries.append(e)
        self.pool[e.eid] = e
        self.open_by_pid[pid] = e.eid
        self._push(close, _CLOSE, e.eid)
        self.dirty = True

    def _close(self, eid: object) -> None:
        e = self.pool.pop(int(eid), None)  # type: ignore[arg-type]
        if e is not None:
            self.open_by_pid.pop(e.pid, None)

    def _closing_now(self, T: float) -> bool:
        return any(abs(e.close_t - T) < 1e-6 for e in self.pool.values())

    def _update_levels(self, T: float) -> bool:
        ladder = self.scn.shape.ladder_minutes
        changed = False
        for e in self.pool.values():
            lvl = max(e.level, sum(1 for th in ladder if T - e.open_t >= th))
            if lvl != e.level:
                e.level = lvl
                changed = True
        return changed

    def _closing_passes(self, T: float) -> None:
        """Async close: widen one rung at a time for whoever is still unplaced (§7.5).

        Only the sign-ups closing now are escalated, and only after the regular run, so nobody's
        soft avoid is broken while a stricter lobby was still possible.
        """
        for rung in range(1, LEVEL_BREAK_SOFT + 1):
            closing = [e for e in self.pool.values() if abs(e.close_t - T) < 1e-6]
            if not closing:
                return
            bumped = False
            for e in closing:
                if e.level < rung:
                    e.level = rung
                    bumped = True
            if bumped:
                self._run_matcher(T)

    # --- matching ----------------------------------------------------------------------------

    def _run_matcher(self, T: float) -> None:
        waiting = sorted(self.pool.values(), key=lambda e: e.eid)
        if len(waiting) < 2:
            return
        self._note_opportunities(waiting, T)
        scn = self.scn

        def on_solve(ctx: ScoringContext, res: matcher.MatchResult) -> None:
            self.matcher_runs += 1
            self.matcher_seconds += res.seconds
            if self.capture and ctx.n >= 6 and len(self.contexts) < self.capture:
                self.contexts.append(ctx)

        formed = match_round(
            waiting,
            self.players,
            self.store,
            T,
            scn.weights,
            scn.policy,
            scn.shape,
            self.rng_match,
            seed=scn.seed,
            on_solve=on_solve,
        )
        # Starting a session only touches its own members' records, so starting them after the
        # whole round is the same as starting each as its game is solved.
        for g, members in formed:
            self._start_session(T, g, members)

    def _note_opportunities(self, waiting: list[Entry], T: float) -> None:
        """R2 opportunities: two mutual-`more` players waiting at once for a shared game."""
        by_pid = {e.pid: e for e in waiting}
        for e in waiting:
            for b in self.store.mutual_partners(e.pid, T):
                o = by_pid.get(b)
                if o is None or e.pid > b:
                    continue
                if set(eligible_games(e)) & set(eligible_games(o)):
                    self.opportunities.add((min(e.eid, o.eid), max(e.eid, o.eid)))

    def _start_session(self, T: float, game: int, members: list[Entry]) -> None:
        sh = self.scn.shape
        pids = [e.pid for e in members]
        if self.live:
            sd = 0.35
            z = float(self.rng_out.normal(0.0, sd))
            dur = sh.session_hours * MINUTES_PER_HOUR * math.exp(z - sd * sd / 2)
            hours = dur / MINUTES_PER_HOUR
        else:
            dur = sh.seed_days[game % len(sh.seed_days)] * 24 * MINUTES_PER_HOUR
            hours = sh.seed_pair_hours
        sid = len(self.sessions)
        soft_broken = 0
        more_links = {p: 0 for p in pids}
        first: list[tuple[int, int]] = []
        for a_i in range(len(pids)):
            for b_i in range(a_i + 1, len(pids)):
                a, b = pids[a_i], pids[b_i]
                for x, y in ((a, b), (b, a)):
                    ex = self.store.get(x, y, T)
                    if ex is not None and ex.kind == SOFT:
                        soft_broken += 1
                if self.store.valid_more(a, b, T) or self.store.valid_more(b, a, T):
                    more_links[a] += 1
                    more_links[b] += 1
                if self.store.coplay_of(a, b) is None:
                    first.extend([(a, b), (b, a)])
                self.store.record_coplay(a, b, T, hours)
        ids = {(min(m.eid, o.eid), max(m.eid, o.eid)) for m in members for o in members}
        self.opportunity_hits |= ids & self.opportunities
        s = Session(sid, T, T + dur, game, pids, hours, soft_broken, more_links)
        self.sessions.append(s)
        self.pending_first[sid] = first
        for e in members:
            e.placed_t = T
            e.sid = sid
            self.pool.pop(e.eid, None)
            self.open_by_pid.pop(e.pid, None)
            if self.live:
                self.busy_until[e.pid] = T + dur
        self._push(T + dur, _END, sid)

    # --- outcomes → edges (§12: ground-truth enjoyment with noise) ---------------------------

    def _end_session(self, t: float, sid: object) -> None:
        s = self.sessions[int(sid)]  # type: ignore[arg-type]
        b = self.scn.behavior
        pids = s.members
        before = {(x, y): self.store.mutual_more(x, y, t) for x in pids for y in pids if x < y}
        for p in pids:
            self.players[p].sessions += 1
        for a in pids:
            pa = self.players[a]
            for c in pids:
                if c == a:
                    continue
                pc = self.players[c]
                logit = b.enjoy_base + b.enjoy_compat * float(pa.compat @ pc.compat)
                if pc.abrasive:
                    logit -= b.abrasive_penalty
                opposite = sum(1 for u, v in zip(pa.style, pc.style, strict=True) if u * v == -1)
                logit -= b.style_penalty * opposite
                if pa.anchor:
                    logit += b.anchor_tolerance
                enjoyed = self.rng_out.random() < 1.0 / (1.0 + math.exp(-logit))
                if enjoyed:
                    p_more = b.p_more_anchor if pa.anchor else b.p_more
                    if self.rng_out.random() < p_more:
                        cur = self.store.get(a, c, t)
                        if cur is None or cur.kind != HARD:
                            self.store.set_more(a, c, t)
                else:
                    p_av = b.p_avoid_happy if pa.avoid_happy else b.p_avoid
                    if self.rng_out.random() < p_av:
                        p_hard = b.p_hard_abrasive if pc.abrasive else b.p_hard
                        if self.rng_out.random() < p_hard:
                            self.store.set_hard(a, c, t)
                        else:
                            self.store.set_soft(a, c, t)
        for (x, y), was in before.items():
            if was and not self.store.mutual_more(x, y, t):
                self.mutual_breaks.append((t, x, y))
            if not was and self.store.mutual_more(x, y, t):
                self.mutual_events.append((t, x, y))
                for z in (x, y):
                    pz = self.players[z]
                    pz.mutual_count += 1
                    if pz.first_mutual_session is None:
                        pz.first_mutual_session = pz.sessions
        for a, c in self.pending_first.pop(s.sid, []):
            e = self.store.get(a, c, t)
            self.first_cards[(a, c)] = (t, e.kind if e is not None else None)

    # --- sampling ------------------------------------------------------------------------------

    def _sample_live(self, T: float, interval: float) -> None:
        busy = sum(1 for u in self.busy_until.values() if u > T)
        peak = bool(self.peak[int(T // MINUTES_PER_HOUR) % 168])
        self.concurrency.append((T, peak, len(self.pool), len(self.pool) + busy))
        target_waiting = self.target is not None and self.target in self.open_by_pid
        if target_waiting and self.measure_start <= T:
            self.target_wait += interval
        if peak or target_waiting:
            res = self._sample_lockout(T, peak=peak, closing_only=False, record=peak)
            if target_waiting and self.measure_start <= T and self.target in res:
                self.target_locked += interval

    def _sample_lockout(
        self, T: float, peak: bool, closing_only: bool, record: bool = True
    ) -> set[int]:
        waiting = sorted(self.pool.values(), key=lambda e: e.eid)
        if closing_only:
            waiting = [e for e in waiting if abs(e.close_t - T) < 1e-6]
        games = sorted({g for e in waiting for g in e.games})
        free_any: set[int] = set()
        hard_any: set[int] = set()
        both_any: set[int] = set()
        unknown = 0
        game_pools = []
        for g in games:
            pids = [e.pid for e in waiting if g in e.games]
            if len(pids) < 2:
                continue
            r = check_pool(pids, self.players, self.store, T)
            free_any |= r.free_ok
            hard_any |= r.hard_ok
            both_any |= r.both_ok
            unknown += r.unknown
            game_pools.append((g, len(pids), sum(1 for p in r.hard_locked if p != self.target)))
        locked = sorted(free_any - hard_any)
        held = sorted(hard_any - both_any)
        if record and self.measure_start <= T:
            locked_set = set(locked)
            for e in waiting:
                if e.pid in locked_set:
                    e.locked_samples += 1
        if record:
            self.lockout.append(
                LockoutSample(T, peak, len(waiting), game_pools, locked, held, unknown)
            )
        # Async: count the target's windows that closed unplaced, and those it was locked out of.
        target_left = any(e.pid == self.target for e in waiting)
        if not self.live and self.measure_start <= T and target_left:
            self.target_wait += 1
            if self.target in locked:
                self.target_locked += 1
        return set(locked)
