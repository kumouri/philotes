"""Measurement-only review signals from retained state; never expose edge identities."""

from collections import defaultdict
from itertools import combinations

from .store import DAY, Store


def coordinated(store: Store, now: float) -> dict[str, str]:
    recent = [
        e for e in store.edges() if e.kind in ("soft", "hard") and now - 30 * DAY <= e.t <= now
    ]
    flags = {}
    targets = defaultdict(list)
    for e in recent:
        targets[e.target].append(e)
    for target, edges in targets.items():
        ordered = sorted(edges, key=lambda e: e.t)
        for first in ordered:
            batch = [e for e in ordered if first.t <= e.t <= first.t + DAY]
            if len(batch) >= 3:
                flags[f"burst:{target}"] = (
                    f"Coordinated-avoidance review: target {target}; {len(batch)} accounts "
                    f"marked avoid/block within 24 hours; UTC epoch range "
                    f"{first.t:g}–{max(e.t for e in batch):g}. "
                    "Aggregate evidence only; this is not a verdict."
                )
                break
    # Three accounts sharing at least three targets in the rolling month.
    signatures = defaultdict(set)
    for target, edges in targets.items():
        for group in combinations(sorted(e.author for e in edges), 3):
            signatures[group].add(target)
    groups = sum(len(v) >= 3 for v in signatures.values())
    if groups:
        flags["together"] = (
            f"Coordinated-pattern review: {groups} account triples each marked "
            "at least 3 shared targets in 30 days. Identities withheld; "
            "this is not a verdict."
        )
    return flags


def abusive(store: Store) -> dict[str, str]:
    counts = defaultdict(lambda: [0, 0])
    for report in store.reports():
        counts[report.reporter][0] += 1
        counts[report.reporter][1] += report.status in ("abusive", "false")
    return {
        f"reporter:{u}": f"Reporter {u}: {bad}/{total} retained reports marked abusive/false "
        f"({bad / total:.0%}). Human review only."
        for u, (total, bad) in counts.items()
        if bad >= 3 and bad / total >= 0.5
    }
