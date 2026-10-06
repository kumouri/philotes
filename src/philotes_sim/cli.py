"""``philotes-sim``: run one scenario, run the Phase 0 sweeps, or compare the matchers.

philotes-sim run --shape live --set population.M=200 --set shape.habit=generous
philotes-sim run --shape async --set shape.cadence_hours=24 --out results/one
philotes-sim sweep --out results/phase0 [--groups live-density,async-density] [--replicates 5]
philotes-sim report --from results/phase0
philotes-sim compare-matchers --out results/quality
philotes-sim list
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from .config import async_baseline, flatten, live_baseline, with_overrides


def _overrides(pairs: list[str]) -> dict[str, str]:
    out = {}
    for p in pairs:
        if "=" not in p:
            raise SystemExit(f"--set expects key=value, got {p!r}")
        k, v = p.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def cmd_run(args: argparse.Namespace) -> None:
    from .metrics import compute, lockout_by_n
    from .report import fmt
    from .sim import Simulation

    base = live_baseline() if args.shape == "live" else async_baseline()
    scn = with_overrides(base, {**_overrides(args.set), "seed": args.seed})
    rec = Simulation(scn).run()
    m = compute(rec)
    for k, v in m.items():
        print(f"{k:42s} {fmt(k, v)}")
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        clean = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in m.items()}
        payload = {"scenario": flatten(scn), "metrics": clean, "lockout_by_n": lockout_by_n(rec)}
        (out / "metrics.json").write_text(json.dumps(payload, indent=2, default=str), "utf-8")
        print(f"wrote {out / 'metrics.json'}")


def cmd_sweep(args: argparse.Namespace) -> None:
    from .experiments import GROUPS, run_groups
    from .report import save_rows, write_outputs

    names = args.groups.split(",") if args.groups else list(GROUPS)
    unknown = [n for n in names if n not in GROUPS]
    if unknown:
        raise SystemExit(f"unknown groups: {unknown}; see `philotes-sim list`")
    rows = run_groups(names, args.replicates, args.workers, lambda s: print(s, flush=True))
    save_rows(rows, Path(args.out))
    write_outputs(rows, Path(args.out), "Philotes Phase 0 sweep")
    print(f"wrote {args.out}/runs.csv, summary.csv, lockout_by_n.csv, report.md")


def cmd_report(args: argparse.Namespace) -> None:
    from .report import load_rows, write_outputs

    out = Path(args.from_dir)
    write_outputs(load_rows(out), out, "Philotes Phase 0 sweep")
    print(f"rebuilt {out}/summary.csv, lockout_by_n.csv, report.md")


def cmd_compare(args: argparse.Namespace) -> None:
    from .quality import compare, summary_md
    from .report import _csv

    rows = compare(args.pools, args.det_time, args.workers)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    _csv(out / "matcher_quality.csv", rows)
    md = summary_md(rows)
    (out / "matcher_quality.md").write_text(md + "\n", "utf-8")
    print(md)


def cmd_list(_: argparse.Namespace) -> None:
    from .experiments import GROUPS

    for g in GROUPS.values():
        print(f"{g.name:26s} {g.shape:5s} {len(g.arms):3d} arms  {g.question}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="philotes-sim", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run one scenario and print its metrics")
    r.add_argument("--shape", choices=["live", "async"], default="live")
    r.add_argument("--seed", type=int, default=1)
    r.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="dotted override, e.g. policy.hard_cap=3 (repeatable)",
    )
    r.add_argument("--out", help="directory for metrics.json")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("sweep", help="run sweep groups and write CSV + Markdown")
    s.add_argument("--groups", help="comma-separated group names (default: all)")
    s.add_argument("--replicates", type=int, default=5)
    s.add_argument("--workers", type=int, default=None)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_sweep)

    rp = sub.add_parser("report", help="rebuild summary and report.md from a sweep's runs.jsonl")
    rp.add_argument("--from", dest="from_dir", required=True)
    rp.set_defaults(func=cmd_report)

    c = sub.add_parser("compare-matchers", help="heuristic vs exact CP-SAT on captured pools")
    c.add_argument("--pools", type=int, default=30, help="pools per source")
    c.add_argument("--det-time", type=float, default=30.0, help="CP-SAT deterministic budget")
    c.add_argument("--workers", type=int, default=None)
    c.add_argument("--out", required=True)
    c.set_defaults(func=cmd_compare)

    ls = sub.add_parser("list", help="list sweep groups")
    ls.set_defaults(func=cmd_list)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
