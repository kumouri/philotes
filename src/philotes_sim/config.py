"""Scenario configuration for the Phase 0 simulator (docs/spec.md §12).

Every knob the §12 sweep mentions lives here: pool size, lobby size, window habit, weights, noise,
hard-block cap and both decay lengths. A scenario is a frozen tree of dataclasses, so it can be
hashed, written to CSV and overridden by dotted path (``policy.hard_cap=3``) from the CLI.

Times inside the simulator are minutes. Weights are objective points; they are rounded to integers
once per solve (CP-SAT needs integers), so both matchers score lobbies identically.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

MINUTES_PER_HOUR = 60.0
MINUTES_PER_DAY = 1440.0
MINUTES_PER_WEEK = 10080.0


@dataclass(frozen=True)
class Weights:
    """Objective weights (§7.2–§7.4), in points."""

    placement: float = 1000.0  # per placed player; dominates, so the matcher places all it can
    more: float = 60.0  # base M for a directed `more` edge (§7.3)
    more_k: float = 1.0  # diminishing returns: M / (1 + k·ln(1 + n_ab))
    mutual_bonus: float = 40.0  # extra when the `more` is mutual (internal only, §7.6)
    reunion_bump: float = 20.0  # recency bump at full strength (§7.3)
    reunion_days: float = 14.0  # days since last co-play for the full bump
    soft_avoid: float = 300.0  # penalty for a soft avoid at full weight, once breakable (§7.5)
    style_conflict: float = 80.0  # per comm-style axis with both extremes in the lobby (§6)
    interest: float = 10.0  # per interest tag shared by ≥ 2 members (§6: tiebreaker)
    composition: float = 50.0  # "core + one or two" bonus (§7.3)
    newcomer: float = 100.0  # placement boost at session 0, decaying (§7.4)
    anchor: float = 80.0  # anchor + newcomer pair bonus at session 0, decaying (§7.4)
    low_connectivity: float = 30.0  # past the newcomer period with no mutual `more` yet (§7.4)
    avoider_pays: float = 5.0  # per active avoid a player holds on someone in the pool (§8)
    noise: float = 0.25  # σ of the random term, as a fraction of `more` (§7.6)


@dataclass(frozen=True)
class Policy:
    """Matcher policy: the tunables Ceryce rules on after Phase 0 (§14 #8, #9, §7.4)."""

    hard_cap: int = 10  # hard blocks per player (§7.2, §14 #8); over the cap a block becomes soft
    soft_half_life_days: float = 30.0  # soft-avoid decay (§7.2, §14 #9)
    soft_negligible: float = 0.05  # a soft avoid below this weight is deleted (§11)
    newcomer_decay_sessions: int = 20  # boost reaches 0 after this many sessions; 0 = no boost
    anchors_enabled: bool = True  # R7 / §7.4
    composition_enabled: bool = True  # §7.3 "core + one or two"
    honor_avoids: bool = True  # False only for the detection test's placebo run (validation)
    matcher: str = "heuristic"  # "heuristic" | "cpsat" | "hybrid" (CP-SAT when pool ≤ cpsat_max)
    cpsat_max_pool: int = 40
    cpsat_det_time: float = 5.0  # CP-SAT deterministic time budget per solve (reproducible)
    local_search_passes: int = 4
    dfs_node_limit: int = 4000
    repack_node_limit: int = 30000  # bounded exhaustive re-partition of ≤ 20 players


@dataclass(frozen=True)
class Population:
    """Synthetic population (§12 "Population generator")."""

    M: int = 200  # opted-in players for this region / community
    n_games: int = 3  # live: games; async: goal-length buckets (short/medium/long)
    game_zipf: float = 1.0  # popularity skew across games
    max_games_per_player: int = 3
    lobby_size: int = 4  # live: preferred lobby size L
    flex_share: float = 0.5  # live: share who accept L-1..L+1 rather than exactly L (§8 point 3)
    async_pref_sizes: tuple[int, ...] = (4, 5, 6)  # async: preferred seed size centres
    tz_offsets: tuple[int, ...] = (0, -1, -2, -3)  # hours, one region (e.g. a continent)
    tz_weights: tuple[float, ...] = (0.40, 0.25, 0.10, 0.25)
    compat_dim: int = 3  # hidden compatibility vector (§12)
    style_either_share: float = 0.4  # per comm-style axis, share answering "either"
    n_tags: int = 12
    abrasive_share: float = 0.05
    avoid_happy_share: float = 0.10
    anchor_share: float = 0.08
    clique_size: int = 5  # coordinated clique hard-blocking one target; 0 disables (§12)
    clique_together: float = 0.85  # chance each member joins a clique window
    newcomer_rate: float = 0.03  # arrivals per week as a share of M; churn matches it
    activity_shape: float = 2.0  # gamma shape of per-player activity (mean 1)


@dataclass(frozen=True)
class Behavior:
    """Ground-truth session outcomes → edges (§12). These rates are assumptions, not data."""

    enjoy_base: float = 0.6  # logit of enjoying a co-player at zero compatibility
    enjoy_compat: float = 2.0  # logit per unit of hidden compatibility (dot product, [-1, 1])
    abrasive_penalty: float = 2.0  # logit cost of sharing a lobby with an abrasive player
    style_penalty: float = 0.8  # logit cost per comm-style axis the two are opposite on
    anchor_tolerance: float = 0.8  # anchors enjoy strangers more
    p_more: float = 0.35  # P(mark `more` | enjoyed)
    p_more_anchor: float = 0.55
    p_avoid: float = 0.25  # P(mark avoid | did not enjoy)
    p_avoid_happy: float = 0.70
    p_hard: float = 0.08  # P(hard block rather than soft | avoiding)
    p_hard_abrasive: float = 0.35  # same, when the avoided player is abrasive


@dataclass(frozen=True)
class Shape:
    """Pool shape: a live co-op queue, or an async Archipelago sign-up window (§9.2)."""

    kind: str = "live"  # "live" | "async"
    # Live queue (§6 queue entry; §9.1 window habits).
    habit: str = "windows"  # label only; the numbers below carry the meaning
    tick_seconds: float = 30.0  # §7.1 lean: 20–30 s
    window_hours: float = 2.0
    windows_per_week: float = 3.0
    session_hours: float = 2.0  # mean live session length
    # Async sign-up window (§9.2).
    signup_days: float = 7.0
    cadence_hours: float = 6.0  # matcher runs this often inside the window
    signup_prob: float = 0.5  # mean weekly sign-up probability
    seed_days: tuple[float, ...] = (7.0, 14.0, 28.0)  # seed length per goal-length bucket
    seed_pair_hours: float = 8.0  # hours each pair "plays together" per seed (async, caveated)
    # Relaxation ladder thresholds, minutes waited (§7.5 steps 3, 4 and 6).
    ladder_minutes: tuple[float, float, float] = (5.0, 10.0, 20.0)
    wait_per_hour: float = 30.0  # wait-time priority, points per hour waited


HABITS: dict[str, dict[str, float]] = {
    # §9.1 window habits: h = window_hours × windows_per_week hours per week.
    "live": {"window_hours": 0.5, "windows_per_week": 4.0},  # h = 2, "I'm on now"
    "windows": {"window_hours": 2.0, "windows_per_week": 3.0},  # h = 6, "ping me"
    "generous": {"window_hours": 2.5, "windows_per_week": 4.0},  # h = 10
}

LIVE_LADDER = {
    "live": (3.0, 6.0, 12.0),
    "windows": (5.0, 10.0, 20.0),
    "generous": (5.0, 10.0, 20.0),
}


def live_shape(habit: str = "windows") -> Shape:
    return Shape(kind="live", habit=habit, ladder_minutes=LIVE_LADDER[habit], **HABITS[habit])


def async_shape() -> Shape:
    return Shape(
        kind="async",
        habit="signup",
        ladder_minutes=(48 * 60.0, 72 * 60.0, 96 * 60.0),
        wait_per_hour=2.0,
    )


@dataclass(frozen=True)
class Scenario:
    name: str = "baseline"
    seed: int = 1
    weeks: int = 8  # total simulated weeks (live) or sign-up windows (async)
    burn_in_weeks: int = 2  # edges accumulate but nothing is measured
    lockout_sample_minutes: float = 5.0
    detect_min_sessions: int = 5  # b needs this many later sessions for the detection test
    cluster_min_comatches: int = 3  # "co-matched ≥ k times" for stable clusters (§12)
    shape: Shape = field(default_factory=live_shape)
    population: Population = field(default_factory=Population)
    behavior: Behavior = field(default_factory=Behavior)
    weights: Weights = field(default_factory=Weights)
    policy: Policy = field(default_factory=Policy)


def live_baseline(**kw: Any) -> Scenario:
    """Live 4-player co-op, one region, availability windows: the §12 exit-criteria setting."""
    base: dict[str, Any] = {"name": "live-baseline", "shape": live_shape("windows")}
    return Scenario(**{**base, **kw})


def async_baseline(**kw: Any) -> Scenario:
    """Async Archipelago (§9.2, §14 #3): weekly sign-up window, seeds of 3–8, 3 goal lengths."""
    base: dict[str, Any] = {
        "name": "async-baseline",
        "weeks": 16,
        "burn_in_weeks": 4,
        "detect_min_sessions": 3,
        "cluster_min_comatches": 2,
        "shape": async_shape(),
        "population": Population(M=100),
    }
    return Scenario(**{**base, **kw})


def with_overrides(scn: Scenario, overrides: dict[str, Any]) -> Scenario:
    """Return a copy with dotted-path overrides applied, e.g. ``{"policy.hard_cap": 3}``.

    ``shape.habit`` is special: setting it swaps in that habit's window numbers and ladder.
    """
    for path, value in overrides.items():
        if path == "shape.habit":
            scn = dataclasses.replace(scn, shape=live_shape(str(value)))
            continue
        parts = path.split(".")
        scn = _replace_path(scn, parts, value)
    return scn


def _replace_path(obj: Any, parts: list[str], value: Any) -> Any:
    name = parts[0]
    if not hasattr(obj, name):
        raise KeyError(f"unknown config field {name!r} on {type(obj).__name__}")
    if len(parts) == 1:
        current = getattr(obj, name)
        return dataclasses.replace(obj, **{name: _coerce(value, current)})
    child = _replace_path(getattr(obj, name), parts[1:], value)
    return dataclasses.replace(obj, **{name: child})


def _coerce(value: Any, current: Any) -> Any:
    if not isinstance(value, str):
        return value
    if isinstance(current, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(current, int):
        return int(value)
    if isinstance(current, float):
        return float(value)
    if isinstance(current, tuple):
        return tuple(type(current[0])(v) for v in value.split(",")) if current else ()
    return value


def flatten(scn: Scenario) -> dict[str, Any]:
    """Flat ``section.field → value`` view, for CSV rows."""
    out: dict[str, Any] = {"name": scn.name, "seed": scn.seed, "weeks": scn.weeks}
    for section in ("shape", "population", "behavior", "weights", "policy"):
        for k, v in dataclasses.asdict(getattr(scn, section)).items():
            out[f"{section}.{k}"] = ",".join(map(str, v)) if isinstance(v, tuple) else v
    return out
