# Phase 0 results: matcher simulator, first sweep

| | |
|---|---|
| **What this is** | The first run of the Phase 0 simulator ([spec §12](spec.md#phase-0-matcher-simulator-nothing-user-facing)), measured against the §12 exit criteria for live co-op, and against the async criteria **proposed here for Ceryce to rule on**. |
| **Date** | 2026-10-05 |
| **Data** | [`phase0-data/`](phase0-data/): `summary.csv` (every arm, mean and sd of every metric), [`sweep-report.md`](phase0-data/sweep-report.md) (every group's table), `lockout_by_n.csv`, `matcher_quality.csv`. |
| **Reproduce** | `uv run philotes-sim sweep --replicates 5 --out results/phase0` (about 7 minutes on 48 cores), then `uv run philotes-sim compare-matchers --pools 40 --out results/quality`. Runs are deterministic: a clean rerun reproduced every committed number. |
| **Synthetic only** | No real person's data is involved (§11). |

## Read this first: the numbers are relative, not absolute

The matcher, the constraints and the metrics are real code. **The people are invented.** How often
someone enjoys a session, marks `more`, avoids or hard-blocks are assumptions (`Behavior` in
[`config.py`](../src/philotes_sim/config.py)): 35% mark `more` after a session they enjoyed, 25%
avoid after one they didn't, 8% of avoids are hard blocks. Several criteria, especially C4
(newcomers) and C2 (lockout), move with those rates as much as with any matcher setting. Use the
results to compare settings and shapes, and treat the absolute levels as a guess until Phase 1
gives real rates.

Every arm is the mean of 5 replicate seeds (10 for the newcomer groups). The replicates share
populations and schedules across arms, so a difference between arms is the knob, not the draw.
Unless stated otherwise, live runs are 12 simulated weeks and async runs are 26 weekly windows,
with the first 2 (live) or 4 (async) excluded as burn-in. The half-life sweeps and the second
kill-check pass run 60 weeks, because a soft avoid takes about 4.3 half-lives to expire.

## Headline

1. **Live 4-player co-op does not pass the §12 exit criteria at M ≤ 500.** At the spec's own
   reference point (M ≈ 200, availability windows) the median peak wait is **17 min** (target 10)
   and hard-block lockout is **2.8% of peak ticks** (target 1%). The best combination found
   (single game, everyone accepting 3–5, generous windows, 7-day half-life, M = 500) passes four of
   five, and misses C4 (newcomers) at 49.3% against a 50% line. That miss is a coin flip inside the
   noise of an invented behaviour rate, but it is a miss, so **the kill/rethink criterion is
   triggered for live co-op as written**. Live co-op is the fallback niche, so this supports the
   2026-10-05 ruling rather than reversing it.
2. **Async Archipelago fills easily.** At M = 50, 91–92% of sign-ups get a seed by window close,
   and at M ≥ 100, 95–100% do, mostly at the player's preferred seed size. Density, the risk R3
   names, is not the binding problem for async.
3. **For async, the cadence decides R2.** If the matcher forms seeds as they fill (every 6 h), only
   9–36% of mutual-`more` pairs who sign up together land in the same seed (up to 42% with a
   24 h cadence). If it holds sign-ups
   and **batches at window close**, 54–62% do, at every M from 50 to 500. The cost is time: a
   median of ~6 days from sign-up to seed, instead of 4–44 hours.
4. **Silent rejection is detectable, and noise does not help.** The detection test's AUC is
   0.54–0.58 for live (near chance) and **0.57–0.72 for async**. The proposed async criterion
   fails everywhere. Matching noise from 0 to 2× the `more` weight changes it by less than 0.02.
   A placebo run (matcher ignores avoids) drops it to 0.50, so the leak is honouring the avoid
   itself. The levers that move it are **pool size** and **a shorter soft-avoid half-life**.
5. **Reunions are limited by co-presence, not by the matcher.** When two mutual-`more` players
   are waiting at the same moment, the live matcher puts them together 59–77% of the time. But
   only 8–47% of mutual pairs are reunited within 14 days, because they are rarely queued at the
   same moment. That share *falls* as M grows. A bigger community fills lobbies faster, so windows
   close sooner and overlap less.
6. **The newcomer boost and anchors have no measurable effect on sessions to first mutual
   `more`**, at any decay length, in either shape. The anchor placement mechanically works in
   async batch (24% → 37% of a newcomer's first seeds include an anchor), but the outcome moves by
   at most ~5 points, inside the noise.
7. **Rich-get-richer did not appear.** Bottom-decile match rate stays at 53–100% of the median
   with availability windows (72–100% async), and high-avoid players are not concentrated together:
   assortativity ≈ 0, and the "only with each other" share sits at its random-mixing null.
8. **Matcher v0's heuristic is within 0.1–0.7% of the exact CP-SAT optimum** on pools captured
   from real runs, at 1–17 ms per solve. CP-SAT takes 9 ms to 16 s. An earlier version stranded
   players with narrow size ranges in up to two thirds of async pools; that was found by the
   comparison and fixed (see [Matcher quality](#matcher-quality)).

## What was simulated

The simulator is [`src/philotes_sim/`](../src/philotes_sim/). In brief:

- **Population** (§12): game lists (Zipf popularity across 3 games, or 3 Archipelago goal
  lengths), size ranges, four time zones in one region with weekday-evening and weekend peaks,
  comm-style on three axes, interest tags, a hidden compatibility vector, and archetypes: 5%
  abrasive, 10% avoid-happy, 8% anchors, newcomers arriving at 3% of M per week (matched by
  churn), and a coordinated clique of 5 who hard-block one regular target from day one.
- **Live shape:** players open availability windows (habits from §9.1: *live* 4 × 30 min a week,
  *windows* 3 × 2 h, *generous* 4 × 2.5 h). The matcher runs every 30 s tick when the pool
  changed. Sessions last ~2 h, and members are busy meanwhile. 4-player lobbies, half the players
  accepting 3–5.
- **Async shape:** a weekly sign-up window. Sign-ups arrive front-loaded through the week, with
  seed sizes 3–8 around a preferred 4–6. The matcher runs every 6 h, every 24 h, or once at close.
  At close it widens one ladder rung at a time for whoever is still unplaced. A seed runs 1, 2 or
  4 weeks by goal length, and edges are set when it ends.
- **Matcher v0** (§7): one objective (`scoring.py`) solved two ways. One is the §7.1 heuristic:
  priority seeding, greedy growth, packing repair, local search. The other is an exact CP-SAT
  model. Hard constraints are size ranges, hard blocks, and soft avoids the §7.5 ladder hasn't yet
  allowed to break. The ladder models steps 3 (size), 4 (other listed games) and 6 (break soft
  avoids, gated on the avoided player's wait). Steps 2 (region) and 5 (community) aren't modelled,
  because the sim is one region and one community.

## Live: against the §12 exit criteria

The §12 suggestions, as checked:

| # | Criterion | Metric used |
|---|---|---|
| C1 | Median peak wait under 10 min (at M ≈ 200, windows) | Median of peak-hour windows' wait to placement. Unplaced windows count as "never". |
| C2 | Hard-block lockout under 1% of peak ticks | Peak-hour samples (every 5 min) in which any waiting player could form a lobby if hard blocks were ignored, but cannot with them. The clique target is excluded and reported separately. |
| C3 | Bottom-decile match rate ≥ 50% of the median | Per player, placed windows / opened windows (≥ 3 windows). 10th percentile / median. |
| C4 | Most newcomers reach a mutual `more` within 5 sessions | Newcomers who arrived after burn-in, pooled over replicates. Denominator: those with ≥ 5 sessions or a mutual `more` sooner. |
| C5 | Detection advantage near chance at N ≥ 20 | **My operationalisation:** \|AUC − 0.5\| ≤ 0.05, where N = median players online (waiting or playing) at peak. Applies only where N ≥ 20. |

**Density by community size and window habit** (12 weeks):

| M | habit | N online at peak | median peak wait | placed (peak) | lockout (peak ticks) | 14-day reunion | bottom/median match | newcomers ≤ 5 | detect AUC | C1–C5 |
|---|---|---|---|---|---|---|---|---|---|---|
| 50 | windows | 3.6 | 77 min | 63% | 1.8% | 34% | 53% | 55% | 0.54 | ✗ ✗ ✓ ✓ – |
| 100 | windows | 7.4 | 32 min | 87% | 2.8% | 25% | 67% | 59% | 0.55 | ✗ ✗ ✓ ✓ – |
| 100 | generous | 9.6 | 25 min | 94% | 5.5% | 31% | 73% | 56% | 0.58 | ✗ ✗ ✓ ✓ – |
| **200** | **windows** | **14** | **17 min** | **96%** | **2.8%** | **16%** | **79%** | **60%** | **0.56** | **✗ ✗ ✓ ✓ –** |
| 200 | generous | 19 | 15 min | 99% | 4.2% | 22% | 87% | 53% | 0.58 | ✗ ✗ ✓ ✓ – |
| 350 | windows | 23 | 11 min | 99% | 1.9% | 11% | 87% | 57% | 0.55 | ✗ ✗ ✓ ✓ ✗ |
| 500 | windows | 35 | 9.7 min | 100% | 1.4% | 8% | 91% | 51% | 0.55 | ✓ ✗ ✓ ✓ ✗ |
| 500 | generous | 45 | 8.2 min | 100% | 2.6% | 12% | 95% | 54% | 0.57 | ✓ ✗ ✓ ✓ ✗ |
| 200 | live (30 min) | 14 | 15 min | 73% | 1.4% | 13% | 55% | 55% | 0.56 | ✗ ✗ ✓ ✓ – |

The *live* habit (queue only while on) leaves 27% of peak windows unplaced at M = 200, and 57% at
M = 100. §9.1's case for availability windows holds.

**Levers on wait and lockout** (M = 200, windows unless noted):

| Lever | Median peak wait | Lockout | Note |
|---|---|---|---|
| Baseline (L = 4, half accept 3–5, 3 games) | 17.3 min | 2.8% | |
| Everyone accepts 3–5 | 11.8 min | 1.5% | §8 point 3 confirmed: the strongest single lever on lockout |
| Nobody flexible | 18.3 min | 2.7% | |
| One game instead of three | 11.4 min | 2.2% | Splitting a community across games costs about 6 minutes |
| One game, everyone 3–5 | 7.9 min | 1.4% | |
| L = 3 | 10.2 min | 1.3% | |
| L = 5 | 24.7 min | 4.4% | |
| Batch the queue every 15 min instead of 30 s | 22.8 min | 2.7% | Reunions 16% → 20% |

### Kill / rethink check

§12: *"if no parameter set meets these at M ≤ ~500, the MVP shape needs rethinking."*

A first pass (`live-search`, 24 combinations of habit, M, size flexibility and game count, 12
weeks) found one set passing C1–C4: windows, M = 350, one game, everyone accepting 3–5. It failed
C5 with AUC 0.565. Short half-lives lower the AUC (below), so a second pass re-ran the best sets
with 7- and 14-day half-lives over **60 weeks**. The longer run matters, because hard blocks
never decay and lockout keeps climbing as they accumulate (M = 200: 2.8% at 12 weeks, 5.2% at 60).

| Best sets, 60 weeks, one game, everyone 3–5 | wait | lockout | bottom/median | newcomers ≤ 5 | AUC | C1–C5 |
|---|---|---|---|---|---|---|
| generous, M = 500, half-life 7 d | 3.5 min | 0.97% | 99% | **49.3%** | 0.543 | ✓ ✓ ✓ ✗ ✓ |
| windows, M = 500, half-life 7 d | 4.6 min | 1.0% | 98% | 48.8% | 0.536 | ✓ ✗ ✓ ✗ ✓ |
| windows, M = 500, half-life 14 d | 4.8 min | 0.8% | 98% | 48.4% | 0.553 | ✓ ✓ ✓ ✗ ✗ |
| windows, M = 350, half-life 7 d | 5.3 min | 1.3% | 97% | 47.3% | 0.540 | ✓ ✗ ✓ ✗ ✓ |

**Verdict: no parameter set meets all five at M ≤ 500, so the criterion as written is
triggered.** Three cautions:

- The closest miss is C4 by 0.7 points, with a standard error of about 0.8 points (about 4,000
  newcomers pooled). That's a coin flip, and C4 depends on the invented `more` rate more than on
  anything the matcher controls (the newcomer levers don't move it, below).
- Every passing-or-nearly set needs the community concentrated on **one game**, **everyone**
  accepting 3–5, and M near 500. That's a narrow target for a first community.
- C2 as written (share of peak *ticks*) is harsh. The consequence metric, the share of *windows*
  that close unplaced after being hard-locked, is 0.3% at the M = 200 baseline and 0.02–0.1% at
  M = 500. Ceryce may prefer to rule on that one.

## Async: proposed criteria (for Ceryce to rule)

§12 says async equivalents are still to be written. These are **proposed**. I fixed them before
the first full sweep, mirroring the live ones where an analogue exists. None of them is ruled.

| # | Proposed criterion | Why |
|---|---|---|
| A1 | ≥ 90% of sign-ups placed in a seed by window close | The async version of "a lobby forms". A sign-up that gets nothing that week is the async failure. |
| A2 | Median sign-up → seed ≤ 48 h **(rolling cadence only)** | "Time for a seed to fill". Batch at close takes ~6 days by design, so A2 only applies if Ceryce picks a rolling cadence. |
| A3 | ≥ 75% of placements at a size inside the player's preferred range | Filling seeds by widening everyone to 3–8 would pass A1 and disappoint people. |
| A4 | Sign-ups left unplaced at close because of hard blocks < 1% | The async form of C2, counted per sign-up. |
| A5 | Bottom-decile placement rate ≥ 50% of the median | Same as C3. |
| A6 | Most newcomers reach a mutual `more` within **3 seeds** | Seeds have 4–5 co-players and run for weeks, so fewer than live's 5 sessions. |
| A7 | ≥ 50% of mutual-`more` pairs who both sign up (same first-choice goal length) land in the same seed | R2 for async: "put us in the same next multiworld". |
| A8 | Detection advantage near chance (\|AUC − 0.5\| ≤ 0.05) at ≥ 20 sign-ups per window | Same as C5. |

**Results** (26 windows; "close" = batch once at window close):

| M | cadence | sign-ups / window | median to seed | placed | preferred size | locked sign-ups | bottom/median | newcomers ≤ 3 | co-signup reunion | AUC | A1–A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 50 | 6 h | 25 | 33 h | 92% | 82% | 0.9% | 75% | 50% | 36% | 0.69 | ✓ ✓ ✓ ✓ ✓ ✗ ✗ ✗ |
| 50 | close | 25 | 146 h | 91% | 88% | 0.8% | 72% | 63% | **54%** | 0.71 | ✓ ✗ ✓ ✓ ✓ ✓ ✓ ✗ |
| 100 | 6 h | 49 | 13 h | 95% | 91% | 0.1% | 84% | 54% | 25% | 0.67 | ✓ ✓ ✓ ✓ ✓ ✓ ✗ ✗ |
| 100 | 24 h | 49 | 20 h | 95% | 92% | 0.1% | 86% | 45% | 32% | 0.66 | ✓ ✓ ✓ ✓ ✓ ✗ ✗ ✗ |
| **100** | **close** | **49** | **145 h** | **96%** | **97%** | **0.7%** | **87%** | **59%** | **57%** | **0.69** | **✓ ✗ ✓ ✓ ✓ ✓ ✓ ✗** |
| 200 | close | 99 | 143 h | 99.5% | 100% | 0.0% | 100% | 63% | 57% | 0.66 | ✓ ✗ ✓ ✓ ✓ ✓ ✓ ✗ |
| 500 | 6 h | 252 | 4 h | 99% | 99% | 0.0% | 100% | 53% | 9% | 0.57 | ✓ ✓ ✓ ✓ ✓ ✓ ✗ ✗ |
| 500 | close | 252 | 143 h | 100% | 100% | 0.0% | 100% | 66% | 62% | 0.63 | ✓ ✗ ✓ ✓ ✓ ✓ ✓ ✗ |

**Reading it:**

- **Batch at close passes everything except A2 (by design) and A8, from M = 50 up.** No rolling
  cadence passes A7.
- **A8 fails everywhere.** The best async AUC in the whole sweep is 0.57 (M = 500, rolling). A
  7-day half-life brings batch-at-close M = 100 to 0.586. Nothing tried reaches 0.55. If Ceryce
  keeps A8 as written, async fails Phase 0 on silent rejection alone. The alternative is to
  rule that the §7.6 honest limit applies (see [Detection](#r5-silent-rejection-the-detection-test)).
- Placement isn't the risk. The async pool is "interested this week", not "queued now", exactly
  as §9.2 argued.

## The decay and cap sweeps (the data for §14 #8, #9 and §7.4)

### Soft-avoid half-life (§14 #9): 7 / 14 / 30 / 60 / 90 days

60-week runs. Live at M = 200, windows:

| Half-life | Live avoids per player | Sessions breaking a soft avoid (per 100) | Peak ticks with someone held by soft avoids | Avoided pairs matched again | Hard lockout | 14-day reunion | Detection AUC |
|---|---|---|---|---|---|---|---|
| 7 d | 3.2 | 20 | 6.7% | 35% | 4.2% | 15.5% | **0.542** |
| 14 d | 4.7 | 30 | 10.6% | 33% | 4.8% | 16.1% | 0.553 |
| 30 d | 7.5 | 38 | 13.7% | 31% | 5.2% | 16.1% | 0.568 |
| 60 d | 12.4 | 41 | 14.8% | 30% | 5.1% | 16.2% | 0.572 |
| 90 d | 16.9 | 42 | 15.5% | 29% | 4.9% | 16.0% | 0.575 |

Async at M = 100, batch at close:

| Half-life | Live avoids per player | Seeds breaking a soft avoid (per 100) | Avoided pairs matched again | Locked sign-ups | Co-signup reunion | Detection AUC |
|---|---|---|---|---|---|---|
| 7 d | 0.9 | 0.5 | 31% | 0.2% | 55% | **0.586** |
| 14 d | 1.1 | 0.9 | 24% | 0.4% | 53% | 0.626 |
| 30 d | 1.8 | 1.7 | 12% | 0.5% | 51% | 0.670 |
| 60 d | 3.2 | 2.7 | 5% | 0.7% | 50% | 0.696 |
| 90 d | 4.5 | 2.7 | 3% | 0.6% | 49% | 0.704 |

What it shows:

- **Half-life does not move hard lockout**, as §8 point 4 predicted. Soft avoids can't lock
  anyone out.
- **It does set the trade-off between protecting the avoider and hiding the avoid.** Shorter decay
  means more re-encounters with people you avoided (async 3% → 31% from 90 to 7 days). Longer decay
  means a more detectable absence (AUC 0.586 → 0.704) and, in live, more soft avoids broken anyway
  in thin pools, because more of them are live when the ladder reaches step 6.
- **In thin live pools, soft avoids get broken a lot.** At M = 100 with a 30-day half-life, 52 in
  100 sessions contain a pair where one had soft-avoided the other. The ladder reaches step 6 after
  20 minutes. That rung looks too early for small communities, whatever the half-life.
- Reunions don't care about the half-life.

### Newcomer-boost decay (§7.4): 0 (off) / 5 / 10 / 20 / 40 sessions, anchors on and off

| Shape | Decay → | off | 5 | 10 | 20 | 40 |
|---|---|---|---|---|---|---|
| Live M = 200, newcomers ≤ 5 sessions, anchors on | | 58% | 54% | 57% | 57% | 56% |
| Live M = 200, anchors off | | 58% | 54% | 56% | 56% | 56% |
| Live M = 500, 15-min batches, anchors on | | 58% | 60% | 58% | 57% | 58% |
| Async M = 100 batch, newcomers ≤ 3 seeds, anchors on | | 59% | 64% | 61% | 57% | 63% |
| Async M = 100 batch, anchors off | | 59% | 61% | 56% | 60% | 62% |
| *Async batch: newcomer's first seeds with an anchor, anchors on* | | *24%* | *37%* | *34%* | *31%* | *30%* |

Each cell pools 700–2,200 newcomers, so a standard error is about 2 points. **No decay length
reliably beats "off".** The mechanism check (last row) shows the anchor placement does fire in
async batch. It fires most at short decay, because a long decay spreads the few anchors across
more "new" players. But being placed with an anchor doesn't move the first-mutual-`more` rate
enough to see. In live queues the matcher barely has choice: at peak, a median of 3 people are
waiting when a lobby forms. So the boost reorders the queue and does little else. **The data gives
no reason to prefer any decay length.** If anchors stay, 5 sessions concentrates them best.

### Hard-block cap (§14 #8): 1 / 3 / 5 / 10 / 25

Live, M = 200, at three hard-block propensities (8% of avoids, the default; 20%; 40%):

| Cap | Hard blocks per player (8% / 20% / 40%) | Lockout, peak ticks (8% / 20% / 40%) | Windows lost to hard blocks (40%) | Clique target placed (40%) |
|---|---|---|---|---|
| 1 | 0.5 / 0.7 / 0.8 | 1.5% / 2.0% / 2.3% | 0.3% | 88% |
| 3 | 0.8 / 1.4 / 2.0 | 2.6% / 4.0% / 5.3% | 0.6% | 84% |
| **5** | 0.9 / 1.8 / 2.7 | 2.8% / 4.8% / 7.0% | 0.9% | 86% |
| 10 | 0.9 / 1.9 / 3.3 | 2.8% / 5.3% / 9.1% | 1.0% | 85% |
| 25 | 0.9 / 1.9 / 3.5 | 2.8% / 5.6% / 9.6% | 1.1% | 82% |

- At the default propensity the cap doesn't bind above 3. Players don't reach 5 hard blocks in 12
  weeks.
- If people hard-block readily (40% of avoids), lockout roughly scales with blocks per player, and
  **a cap of 5 vs 25 is 7.0% vs 9.6%**. Lower caps help, at the cost of people's real safety
  choices falling back to soft avoids.
- Async: the cap makes no difference at any propensity (0.3–1.4 blocks per player). Locked
  sign-ups stay at or below 1.3%.
- **The coordinated clique** (5 players hard-blocking one target) isn't stopped by any cap ≥ 1,
  because each member spends one slot. What protects the target is pool size. In live at M = 50 the
  target gets 31% of windows placed (everyone: 49%), at M = 100 66% (73%), at M = 200 90% (89%),
  and at M ≥ 350 it's unaffected. In async at M = 50 the target gets a seed in 63–72% of windows
  against 92% for everyone. At M = 100 it's 92–100%. The §8 "detect and review coordinated
  blocking" lean is the defence that matters for small communities.

**Lean from the data:** keep 5. The cap is not what drives lockout at realistic rates. If the alpha
shows people hard-blocking far more than 8% of the time, revisit downward.

## R2 rematch and groups forming

- **Live:** of mutual-`more` pairs, 8–47% are co-matched again within 14 days. The share falls
  with M (windows: M = 50 34%, M = 500 8%). When both are waiting at once, the matcher reunites
  them 59–77% of the time. Raising the `more` weight 16× (30 → 480) changes the 14-day share by
  about 2 points at most. **The limit is co-presence.** Batching the queue every 15 minutes helps a little
  (16% → 20% at M = 200, for +5 min wait).
- **Async:** batch at close reunites 54–62% of co-signed-up mutual pairs, against 9–42% for
  rolling cadences. In a placebo where the matcher ignores avoids, it's 74%, so honouring avoids
  costs some reunions. Typically that's a seed-mate one of the pair avoids.
- **Stable clusters** (≥ 3 players, every pair co-matched ≥ 3 times live, ≥ 2 seeds async): 32% of
  live players at M = 200 (windows) are in one, and 69% of async players at M = 100 (batch).
- **Hall's 50 hours:** even the top 10% of live mutual pairs log only 0.3–1.7 h a week together,
  which is **32–159 weeks to 50 h**. Async pairs reach ~3 h a week at batch close (17 weeks), but
  async "hours together" is credited at 8 h per shared seed and isn't co-present time. Friendship
  at Hall's thresholds is a many-month outcome on any setting tried.

## R5 rich-get-richer

- **Match rate:** bottom decile / median is 53–100% for every live arm with availability windows,
  and 72–100% for every async arm. It fails only on the *live* habit (queue only while on) at
  M ≤ 100, where most windows go unplaced.
- **Lobby affinity:** the bottom decile has no `more` link in its lobbies (affinity 0). The median
  is 0.04–0.19 of co-members. Most sessions are among strangers, as the composition bonus intends.
- **Assortativity of inbound avoids:** the correlation between co-matched players' inbound-avoid
  counts is −0.01 to +0.03. Top-decile avoided players are matched *only* with each other in
  2–6% of their sessions, against a random-mixing null of 2–5%. The concentration §7.4 worries about
  does not appear at these sizes and avoid rates. No mixing term is needed yet.

## R5 silent rejection: the detection test

**Definition.** For each pair (`b`, `c`) that played together for the first time, `c`'s card
from that session is the label: avoid (soft or hard) or nothing. `b` sees only their own
lobbies. The statistic `b` can compute is how often `c` turned up again per later session of
`b`'s (given ≥ 5 later sessions live, ≥ 3 async). The AUC is how well that separates "c avoided
me" from "c set nothing". 0.5 is chance, and 0.55 means a random avoider looks rarer than a random
neutral co-player 55% of the time. `detect_auc_more` restricts the test to pairs where `b` had
marked `more` on `c`: the motivated "my favourite never shows up" case.

| Finding | Evidence |
|---|---|
| The leak is honouring the avoid, nothing else | Placebo (matcher ignores avoids): AUC 0.501 live, 0.504–0.505 async. |
| Noise does not hide it | Live noise 0 → 2× `more`: AUC 0.537–0.562 across M = 50–500, flat in noise. Async: 0.57–0.70, flat within 0.02 at each M. |
| Bigger pools hide it | Async rolling: AUC 0.70 (M = 50) → 0.57 (M = 500). |
| Shorter decay hides it | Live M = 200: 0.542 (7 d) → 0.575 (90 d). Async batch M = 100: 0.586 → 0.704. |
| Stronger reunions expose it | Async batch, `detect_auc_more`: 0.76 (`more` = 30) → 0.80 (`more` = 480). |
| Batching exposes it slightly | Async M = 100: 0.67 rolling → 0.69 batch. Live M = 200: 0.557 → 0.572 at 15-min batches. |

So the §7.6 lean ("noise in matching… tune it against the detection test") **doesn't work as a
mechanism**. An avoid is honoured as a hard exclusion until the ladder breaks it, and no amount of
noise elsewhere makes "never" look like "sometimes". The honest limit in §7.6 is the operative one,
and it bites in async more than live: the async pool is the same few dozen people every week, which
makes absences visible.

## R8 lockout by pool size and lobby size

Live, peak samples, share of (sample, game pool) pairs in which someone waiting is hard-locked:

| L | N waiting 2–4 | 5–7 | 8–10 |
|---|---|---|---|
| 3 | 2.3% | 0% (93 samples) | – |
| 4 | 2.0% | 4.7% | 0% (744 samples) |
| 5 | 0.1% | **29.8%** | 1.6% (64 samples) |

This is §8's table played out. When N is just above L (L = 5, N = 5–7), a couple of hard blocks
lock someone out in nearly a third of samples. Waiting pools rarely exceed 7, because lobbies form
as soon as they can. So the realistic pool sizes are exactly the dangerous rows.

## Matcher quality

Heuristic vs exact CP-SAT on pools captured from real runs (CP-SAT with a 30 s deterministic
budget):

| Pools from | Pools | Mean N | CP-SAT proved optimal | Heuristic placed fewer | Mean objective gap | Worst gap | Heuristic ms | CP-SAT ms |
|---|---|---|---|---|---|---|---|---|
| live M = 500 generous, 5-min batches | 40 | 6.2 | 40/40 | 0/40 | 0.15% | 3.8% | 0.7 | 9 |
| live M = 200 windows, 15-min batches | 40 | 6.2 | 40/40 | 0/40 | 0.08% | 1.1% | 0.8 | 9 |
| async M = 50, batch at close | 13 | 15.1 | 9/13 | 1/13 | 0.68% | 5.7% | 17 | 16,354 |
| async M = 100, rolling 24 h | 37 | 9.8 | 35/37 | 1/37 | 0.56% | 11.5% | 9.8 | 3,254 |

The first version of the heuristic placed fewer than CP-SAT in 8/40 live and 10/15 async pools,
with a worst gap of 42%. Greedy growth spent the flexible players (3–5) on one lobby and stranded
the "exactly 4" players. Two repair moves fixed it: swap/spare-then-form, and a bounded exhaustive
re-partition of one or two lobbies with the leftovers. End-to-end, the heuristic and the hybrid
(CP-SAT on pools ≤ 40) give the same headline metrics within replicate noise
(`matcher-validation` groups in the sweep report). The heuristic is the default.

## What suggests the MVP shape needs rethinking

1. **Live co-op as the fallback niche is weak.** It needs about 500 opted-in players
   concentrated on one game, all accepting 3–5, to come close. A typical existing Discord community
   playing 2–3 games is well short of that. If the fallback is ever needed, plan for smaller
   lobbies or 3–5 ranges as the default, and expect waits of 15–30 minutes.
2. **For async, pick batch at close (or close to it) as the default cadence.** It is the only
   setting that passes the proposed R2 criterion, and Archipelago players already wait for
   organisers to collect YAMLs. The cost is that a sign-up on Monday gets its seed on Sunday.
3. **Rule on silent rejection explicitly.** As written (C5, A8), async fails and live squeaks by
   at best. The data says noise is not a fix. The real choices:
   - accept the §7.6 honest limit, and replace A8 with a ceiling Ceryce is comfortable with (e.g.
     AUC ≤ 0.65 at M ≥ 100);
   - choose a short soft-avoid half-life (7–14 days), which lowers detection and raises
     re-encounters with avoided people;
   - or soften what an avoid does in small pools. That conflicts with R4.
4. **The newcomer boost and anchors are not earning their complexity yet.** No measurable effect
   on first mutual `more` in either shape. Keep anchors for the wellbeing reason in §10 if wanted.
   Don't expect them to move the newcomer criterion. That criterion depends on how readily real
   people mark `more`, which only Phase 1 can tell us.
5. **The relaxation ladder breaks soft avoids too early in thin live pools.** Step 6 at 20 minutes
   breaks a soft avoid in 30–55% of sessions at M = 100. Worth a longer threshold, or a per-player
   cap on breaks.
6. **Hard blocks accumulate forever.** Lockout roughly doubled between 12 and 60 simulated weeks.
   §8's coordinated-blocking review covers abuse, but organic accumulation is a slow drift worth
   watching in the alpha.

## Limitations

- **Behaviour rates are assumptions** (see the top). So is the shape of availability (weekday
  evenings, four time zones in one region).
- No graduation: groups that move to their own Discord keep queuing in the sim.
- No reports, no moderation, no ban evasion. The clique is the only adversary modelled.
- Async "hours together" is a credited figure (8 h per shared seed), not co-present time.
- Regions, cross-community pooling (§7.5 steps 2 and 5), platforms, age bands and self-set
  mandatory filters aren't modelled: one region, one community, everyone compatible on those axes.
- The newcomer cohort is small per run. Shares are pooled across 5–10 replicates and carry about
  ±2 points of standard error.
- C5/A8's "near chance" threshold (|AUC − 0.5| ≤ 0.05) is my operationalisation, not a ruling.
