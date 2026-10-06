"""Synthetic players and their availability (docs/spec.md §6 Player, §12 Population generator).

Each player has a game list, accepted and preferred lobby sizes, a coarse time zone, comm-style on
three axes, interest tags, a hidden compatibility vector that drives ground-truth enjoyment, and an
archetype: abrasive, avoid-happy, anchor, clique member or clique target. Newcomers arrive over
time.
Everything is synthetic (§11: Phase 0 uses no real person's data).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import MINUTES_PER_HOUR, MINUTES_PER_WEEK, Population, Shape

STYLE_AXES = ("comms", "talk", "intensity")  # voice/text, chatty/heads-down, sweaty/chill (§6)


@dataclass
class Player:
    pid: int
    games: tuple[int, ...]  # listed games; games[0] is the one a window asks for first
    pref_lo: int
    pref_hi: int
    acc_lo: int
    acc_hi: int
    tz: int
    activity: float
    style: tuple[int, ...]  # per axis: -1 / +1 for the two extremes, 0 for "either"
    tags: tuple[int, ...]
    compat: np.ndarray
    abrasive: bool = False
    avoid_happy: bool = False
    anchor: bool = False
    clique: bool = False
    target: bool = False
    arrived: float = 0.0
    left: float | None = None
    sessions: int = 0
    first_mutual_session: int | None = None
    mutual_count: int = 0
    measured_newcomer: bool = False  # arrived after burn-in, so counts for the newcomer metric
    extra: dict = field(default_factory=dict)

    def active(self, t: float) -> bool:
        return self.arrived <= t and (self.left is None or t < self.left)


def hour_of_week_profile() -> np.ndarray:
    """Relative chance a window opens in each local hour of the week (Mon 00:00 = hour 0).

    Weekday evenings peak, weekend afternoons and evenings are broad, nights are near-empty.
    """
    day = np.full(24, 0.02)
    day[8:12] = 0.15
    day[12:18] = 0.30
    day[18:23] = 1.00
    day[23] = 0.5
    day[0:2] = 0.30
    weekend = np.full(24, 0.03)
    weekend[10:18] = 0.70
    weekend[18:24] = 0.90
    weekend[0:2] = 0.50
    prof = np.concatenate([day] * 5 + [weekend] * 2)
    return prof / prof.sum()


def sim_clock_profile(tz: int) -> np.ndarray:
    """The local profile shifted onto the simulation clock (sim time = local time - tz)."""
    return np.roll(hour_of_week_profile(), -tz)


class PopulationFactory:
    """Draws players. One instance per simulation so its RNG stream stays isolated."""

    def __init__(self, cfg: Population, shape: Shape, rng: np.random.Generator) -> None:
        self.cfg = cfg
        self.shape = shape
        self.rng = rng
        pop = 1.0 / np.arange(1, cfg.n_games + 1) ** cfg.game_zipf
        self.game_p = pop / pop.sum()
        self.next_pid = 0

    def make(self, arrived: float) -> Player:
        c, r = self.cfg, self.rng
        n_games = int(r.integers(1, min(c.max_games_per_player, c.n_games) + 1))
        games = tuple(
            int(g) for g in r.choice(c.n_games, size=n_games, replace=False, p=self.game_p)
        )
        if self.shape.kind == "live":
            L = c.lobby_size
            pref_lo = pref_hi = L
            if r.random() < c.flex_share:
                acc_lo, acc_hi = max(2, L - 1), L + 1
            else:
                acc_lo, acc_hi = L, L
        else:
            centre = int(r.choice(c.async_pref_sizes))
            pref_lo, pref_hi = max(2, centre - 1), centre + 1
            acc_lo, acc_hi = max(2, centre - 2), centre + 3
        tz = int(r.choice(c.tz_offsets, p=np.asarray(c.tz_weights) / sum(c.tz_weights)))
        activity = float(r.gamma(c.activity_shape, 1.0 / c.activity_shape))
        style = tuple(
            0 if r.random() < c.style_either_share else int(r.choice((-1, 1))) for _ in STYLE_AXES
        )
        n_tags = int(r.integers(0, 4))
        tags = tuple(sorted(int(t) for t in r.choice(c.n_tags, size=n_tags, replace=False)))
        v = r.normal(size=c.compat_dim)
        compat = v / np.linalg.norm(v)
        u = r.random()
        abrasive = u < c.abrasive_share
        avoid_happy = c.abrasive_share <= u < c.abrasive_share + c.avoid_happy_share
        lo_anchor = c.abrasive_share + c.avoid_happy_share
        anchor = lo_anchor <= u < lo_anchor + c.anchor_share
        p = Player(
            pid=self.next_pid,
            games=games,
            pref_lo=pref_lo,
            pref_hi=pref_hi,
            acc_lo=acc_lo,
            acc_hi=acc_hi,
            tz=tz,
            activity=activity,
            style=style,
            tags=tags,
            compat=compat,
            abrasive=bool(abrasive),
            avoid_happy=bool(avoid_happy),
            anchor=bool(anchor),
            arrived=arrived,
        )
        self.next_pid += 1
        return p

    def initial(self) -> list[Player]:
        players = [self.make(0.0) for _ in range(self.cfg.M)]
        k = self.cfg.clique_size
        if k > 0 and len(players) > k + 1:
            # The target and the clique share the target's first game, so they meet in its pool.
            # The target is a regular (activity 1.5), so the attack has exposure to measure.
            target = players[0]
            target.target = True
            target.activity = 1.5
            target.abrasive = target.avoid_happy = target.anchor = False
            for p in players[1 : k + 1]:
                p.clique = True
                p.abrasive = p.avoid_happy = p.anchor = False
                rest = tuple(g for g in p.games if g != target.games[0])
                p.games = (target.games[0], *rest)
                p.tz = target.tz
        return players

    # --- availability -------------------------------------------------------------------------

    @staticmethod
    def window_starts(
        p: Player, week_start: float, from_t: float, rate: float, rng: np.random.Generator
    ) -> list[float]:
        """Live window open times for one player in one week, from ``from_t`` onwards."""
        frac = max(0.0, (week_start + MINUTES_PER_WEEK - from_t) / MINUTES_PER_WEEK)
        n = int(rng.poisson(rate * p.activity * frac))
        if n == 0:
            return []
        prof = sim_clock_profile(p.tz)
        first_hour = int(max(0.0, from_t - week_start) // MINUTES_PER_HOUR)
        prof = prof.copy()
        prof[:first_hour] = 0.0
        if prof.sum() <= 0:
            return []
        hours = rng.choice(168, size=n, p=prof / prof.sum())
        mins = rng.random(n) * MINUTES_PER_HOUR
        starts = week_start + hours * MINUTES_PER_HOUR + mins
        return sorted(float(s) for s in starts if s >= from_t)

    @staticmethod
    def signup_time(window_start: float, window_minutes: float, rng: np.random.Generator) -> float:
        """Async sign-up time: front-loaded (mean ~1.5 days), never in the window's last 12 h."""
        latest = window_minutes - 12 * MINUTES_PER_HOUR
        while True:
            dt = float(rng.exponential(1.5 * 24 * MINUTES_PER_HOUR))
            if dt < latest:
                return window_start + dt


def peak_hours(players: list[Player], top_share: float = 0.25) -> np.ndarray:
    """Boolean mask over the 168 sim-clock hours: the busiest ``top_share`` by expected opens."""
    load = np.zeros(168)
    for p in players:
        load += p.activity * sim_clock_profile(p.tz)
    cutoff = np.quantile(load, 1.0 - top_share)
    return load >= cutoff
