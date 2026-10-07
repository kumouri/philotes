"""``philotes-bot``: run the Phase 1 bot core locally.

* ``philotes-bot demo`` — a scripted two-week run on the in-memory transport, printed.
* ``philotes-bot console`` — type commands as any user and move the clock yourself.
* ``philotes-bot check`` — show the resolved configuration, and whether a Discord token is set
  (never the token itself).

Only the explicit run command connects to Discord.
"""

from __future__ import annotations

import argparse
import sqlite3
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
    metrics = sub.add_parser("metrics", help="local anonymous alpha report (read-only)")
    metrics.add_argument("--db", type=Path, help="existing SQLite path (default: configured path)")
    metrics.add_argument("--out", type=Path, help="aggregate export path ending in .csv or .json")
    sub.add_parser("run", help="connect to Discord (host setup required)")
    a = ap.parse_args(argv)

    cfg = load_config(a.config, a.env_file)
    if a.cmd == "metrics":
        from .measurement import export, render, report
        from .store import Store

        path = (a.db or Path(cfg.db_path)).resolve()
        if not path.is_file():
            ap.error("metrics requires an existing database")
        if a.out and a.out.suffix.lower() not in (".csv", ".json"):
            ap.error("--out must end in .csv or .json")
        if a.out and a.out.resolve() == path:
            ap.error("--out cannot overwrite the database")
        store = Store.__new__(Store)
        store.db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            store.db.execute("BEGIN")  # consistent snapshot across all report reads
            rows = report(store, cfg, datetime.now(UTC).timestamp())
            store.db.rollback()
            if a.out:
                export(rows, a.out)
            print(render(rows))
        finally:
            store.close()
        return 0
    if a.cmd == "run":
        from .discord_adapter import run

        return run(cfg)
    if a.cmd == "check":
        print(f"config file: {a.config} ({'found' if a.config.is_file() else 'not found'})")
        print(f"community: {cfg.community}")
        print(f"window: {cfg.window}")
        print(f"safety: {cfg.safety}")
        print(f"archipelago: {cfg.archipelago}")
        print(f"database: {cfg.db_path}")
        print(f"DISCORD_TOKEN: {'set' if cfg.discord_token else 'absent'}")
        print("transports: local in-memory; Discord gateway via run")
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
