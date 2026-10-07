"""``philotes-bot``: run the Phase 1 bot core locally.

* ``philotes-bot demo`` — a scripted two-week run on the in-memory transport, printed.
* ``philotes-bot console`` — type commands as any user and move the clock yourself.
* ``philotes-bot check`` — show the resolved configuration, and whether a Discord token is set
  (never the token itself).

Nothing here connects to Discord. The gateway transport is a later slice (docs/phase1-bot.md).
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from .config import load_config
from .console import Console, demo_lines, repl

DEMO_START = datetime(2026, 10, 12, 12, 0, tzinfo=UTC).timestamp()  # a Monday


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="philotes-bot", description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", type=Path, default=Path("philotes-bot.toml"))
    ap.add_argument("--env-file", type=Path, default=Path(".env"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="scripted local run, printed")
    con = sub.add_parser("console", help="interactive local run")
    con.add_argument("--db", default=":memory:", help="SQLite path (default: in memory)")
    con.add_argument("--seed", type=int, default=0, help="matcher noise seed")
    sub.add_parser("check", help="show the resolved configuration")
    a = ap.parse_args(argv)

    cfg = load_config(a.config, a.env_file)
    if a.cmd == "check":
        print(f"config file: {a.config} ({'found' if a.config.is_file() else 'not found'})")
        print(f"community: {cfg.community}")
        print(f"window: {cfg.window}")
        print(f"safety: {cfg.safety}")
        print(f"database: {cfg.db_path}")
        print(f"DISCORD_TOKEN: {'set' if cfg.discord_token else 'absent'}")
        print("transport: in-memory only in this slice (the Discord gateway is slice 2)")
        return 0
    if a.cmd == "demo":
        console = Console(cfg, DEMO_START, seed=1)
        for line in demo_lines(console):
            print(line)
        return 0
    console = Console(cfg, datetime.now(UTC).timestamp(), db=a.db, seed=a.seed)
    repl(console)
    return 0


if __name__ == "__main__":
    sys.exit(main())
