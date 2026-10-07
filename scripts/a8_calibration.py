"""Offline Phase 0 calibration: ruled M=100, close-only, seven-day half-life."""

import json
from bisect import bisect_right
from collections import defaultdict

from philotes_sim.edges import HARD, MORE, SOFT
from philotes_sim.experiments import CLOSE_ONLY, GROUPS, scenario_for
from philotes_sim.metric_helpers import A8_BINS, histogram_auc, rejection_score, score_bin
from philotes_sim.metrics import auc
from philotes_sim.sim import Simulation


def main():
    rows = []
    for seed in range(1, 6):
        scn = scenario_for(
            GROUPS["async-density"],
            {"population.M": 100, "policy.soft_half_life_days": 7.0, **CLOSE_ONLY},
            seed,
        )
        rec = Simulation(scn).run()
        players, pairs = defaultdict(list), defaultdict(list)
        for session in rec.sessions:
            for a in session.members:
                players[a].append(session.t)
                for b in session.members:
                    if a != b:
                        pairs[a, b].append(session.t)
        pos, neg = [], []
        for (a, b), (t, kind) in rec.first_cards.items():
            if kind == MORE:
                continue
            later = len(players[b]) - bisect_right(players[b], t)
            again = len(pairs[a, b]) - bisect_right(pairs[a, b], t)
            score = rejection_score(again, later, scn.detect_min_sessions)
            if later >= scn.detect_min_sessions:
                (pos if kind in (HARD, SOFT) else neg).append(score)
        hp, hn = [0] * A8_BINS, [0] * A8_BINS
        for scores, hist in ((pos, hp), (neg, hn)):
            for score in scores:
                hist[score_bin(score)] += 1
        exact, binned = auc(pos, neg), histogram_auc(hp, hn)
        rows.append(
            dict(
                seed=seed,
                positive=len(pos),
                negative=len(neg),
                exact=exact,
                binned=binned,
                absolute_error=abs(exact - binned),
            )
        )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
