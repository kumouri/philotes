"""Bot configuration: one TOML file per host community, plus secrets from an untracked env file.

Nothing here names a community. The host community is a config value (``[community]``), chosen by
Ceryce (§14 #3, still open), so the same code runs anywhere. ``philotes-bot.example.toml`` at the
repo root lists every key; the real ``philotes-bot.toml`` is git-ignored.

Secrets never go in the TOML. ``DISCORD_TOKEN`` is read only from
an untracked ``.env`` file. When it is absent the bot still runs on the local in-memory transport;
the explicit run command requires a token before connecting to Discord.

The matcher settings are the ruled v1 values, not the Phase 0 simulator's defaults: soft-avoid
half-life ~7 days (§14 #9), hard-block cap 10 (§14 #8), no newcomer boost and no anchors (§14 #18),
seeds formed in one batch when the sign-up window closes (§14 #15).
"""

from __future__ import annotations

import dataclasses
import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from philotes_sim.config import Policy, Shape, Weights, async_shape

TOKEN_ENV = "DISCORD_TOKEN"


@dataclass(frozen=True)
class Community:
    """The one host community (Phase 1 is single-community, §12). Discord IDs are snowflakes."""

    name: str = "unconfigured"
    guild_id: int | None = None  # commands from any other guild are refused
    mod_role_id: int | None = None  # holders may use /mod commands
    mod_channel_id: int | None = None  # reports are posted here (§10)
    seed_category_id: int | None = None  # private seed channels are created under this category


@dataclass(frozen=True)
class Window:
    """The weekly sign-up window. Seeds form once, when it closes (§14 #15)."""

    close_weekday: int = 6  # 0 = Monday … 6 = Sunday
    close_hour_utc: int = 23  # UTC, so the close time doesn't move with daylight saving
    goals: tuple[str, ...] = ("short", "medium", "long")  # goal lengths, offered in this order
    goal_days: tuple[int, ...] = (7, 14, 28)  # how long a seed of each goal length runs
    size_min: int = 3  # smallest seed the community allows
    size_max: int = 8
    default_preferred: tuple[int, int] = (4, 6)
    default_accepted: tuple[int, int] = (3, 8)


@dataclass(frozen=True)
class Safety:
    hard_cap: int = 10  # hard blocks per player (§7.2, §14 #8); report blocks don't count (§10)
    soft_half_life_days: float = 7.0  # §7.2, §14 #9
    recently_played_days: int = 14  # how long after a seed ends you can still set an edge (§9.3)
    min_account_age_days: int = 30  # ban-evasion mitigation (§10, lean); 0 turns it off
    coplay_retention_days: int = 365  # §11


@dataclass(frozen=True)
class Archipelago:
    enabled: bool = False
    version: str = "0.6.8"
    install_path: str = ""
    games_manifest: str = ""  # trusted offline export from this install
    data_path: str = "philotes-seeds"
    generator_command: tuple[str, ...] = ("ArchipelagoGenerate.exe",)
    server_command: tuple[str, ...] = ("ArchipelagoServer.exe",)
    submission_hours: float = 48
    reminder_hours: float = 24
    max_yaml_bytes: int = 65536
    generation_timeout_seconds: float = 600
    max_artifact_bytes: int = 100 * 1024 * 1024
    hosting_mode: str = "self_host"
    upload_enabled: bool = False  # Ceryce's explicit opt-in, separate from mode
    public_host: str = "localhost"
    bind_host: str = "127.0.0.1"
    port_start: int = 38281
    port_end: int = 38300
    restart_seconds: float = 60
    max_restarts: int = 3


@dataclass(frozen=True)
class BotConfig:
    community: Community = field(default_factory=Community)
    window: Window = field(default_factory=Window)
    safety: Safety = field(default_factory=Safety)
    archipelago: Archipelago = field(default_factory=Archipelago)
    db_path: str = "philotes.db"
    discord_token: str | None = field(default=None, repr=False)

    def weights(self) -> Weights:
        """§7 weights as simulated, with the v1 drops (§14 #18) zeroed."""
        return Weights(newcomer=0.0, anchor=0.0, low_connectivity=0.0)

    def policy(self) -> Policy:
        return Policy(
            hard_cap=self.safety.hard_cap,
            soft_half_life_days=self.safety.soft_half_life_days,
            newcomer_decay_sessions=0,
            anchors_enabled=False,
            matcher="heuristic",
        )

    def shape(self) -> Shape:
        return async_shape()


def read_env_file(path: Path) -> dict[str, str]:
    """``KEY=value`` lines; ``#`` comments and blank lines skipped; optional surrounding quotes."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        out[key.strip()] = value
    return out


def _section(cls: type, data: dict[str, Any]) -> Any:
    names = {f.name for f in dataclasses.fields(cls)}
    unknown = set(data) - names
    if unknown:
        raise KeyError(f"unknown {cls.__name__.lower()} keys: {', '.join(sorted(unknown))}")
    kw = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items()}
    return cls(**kw)


def load_config(
    path: Path | None = None, env_file: Path | None = None, environ: dict[str, str] | None = None
) -> BotConfig:
    """Read TOML and token only from the env file; environ is ignored for compatibility."""
    data: dict[str, Any] = {}
    if path is not None and path.is_file():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    token = read_env_file(env_file or Path(".env")).get(TOKEN_ENV) or None
    cfg = BotConfig(
        community=_section(Community, data.get("community", {})),
        window=_section(Window, data.get("window", {})),
        safety=_section(Safety, data.get("safety", {})),
        archipelago=_section(Archipelago, data.get("archipelago", {})),
        db_path=str(data.get("db_path", "philotes.db")),
        discord_token=token,
    )
    validate(cfg)
    return cfg


def validate(cfg: BotConfig) -> None:
    a = cfg.archipelago
    if type(a.enabled) is not bool or type(a.upload_enabled) is not bool:
        raise ValueError("Archipelago enabled and upload_enabled must be TOML booleans")
    if a.hosting_mode not in {"self_host", "upload"}:
        raise ValueError("archipelago.hosting_mode must be self_host or upload")
    if a.enabled and (not a.install_path or not a.games_manifest):
        raise ValueError("Archipelago needs install_path and games_manifest")
    if a.enabled and a.hosting_mode == "upload" and not a.upload_enabled:
        raise ValueError("Upload requires explicit archipelago.upload_enabled = true")
    if not 0 < a.reminder_hours < a.submission_hours:
        raise ValueError("Archipelago reminder must precede the positive submission deadline")
    if (
        any(
            not math.isfinite(v) or v <= 0
            for v in (
                a.max_yaml_bytes,
                a.generation_timeout_seconds,
                a.max_artifact_bytes,
                a.restart_seconds,
            )
        )
        or a.max_restarts < 0
    ):
        raise ValueError("Archipelago limits must be positive; max_restarts must be nonnegative")
    if not 1 <= a.port_start <= a.port_end <= 65535:
        raise ValueError("Archipelago ports must be within 1..65535")
    for command in (a.generator_command, a.server_command):
        if (
            not isinstance(command, tuple)
            or not command
            or any(not isinstance(c, str) or not c for c in command)
        ):
            raise ValueError("Archipelago commands must be nonempty arrays of strings")
    w = cfg.window
    if len(w.goals) != len(w.goal_days) or not w.goals:
        raise ValueError("window.goals and window.goal_days must be the same, non-zero length")
    if not 0 <= w.close_weekday <= 6 or not 0 <= w.close_hour_utc <= 23:
        raise ValueError("window.close_weekday must be 0–6 and window.close_hour_utc 0–23")
    if not 2 <= w.size_min <= w.size_max:
        raise ValueError("window.size_min must be at least 2 and no more than size_max")
    for lo, hi in (w.default_preferred, w.default_accepted):
        if not w.size_min <= lo <= hi <= w.size_max:
            raise ValueError("default size ranges must sit inside size_min..size_max")
    if cfg.safety.hard_cap < 0 or cfg.safety.soft_half_life_days <= 0:
        raise ValueError("safety.hard_cap must be ≥ 0 and safety.soft_half_life_days > 0")
