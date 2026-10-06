# Philotes Phase 0 sweep

Means over replicates (± sd). Waits: minutes (live) or hours (async). Criteria columns check the arm's mean against the §12 live suggestions (C1–C5) or the proposed async criteria (A1–A8); n/a means the criterion does not apply at that size.

## async-density

Async R3: time-to-seed and fill by M and matcher cadence (6 h, 24 h, batch at close).

| M | cadence_hours | ladder_minutes | N online (peak) | N waiting (peak) | median wait | placed | locked sign-ups | pref_size_share | mean_lobby_size | cosignup_reunion_share | reunion_14d_share | players_in_stable_cluster_share | newcomer_within_horizon_share | detect_auc | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 50 | 6.0 | base | 25.3 ±2.3 | 7.4 ±2.4 | 33.4 ±6.7 | 91.7% ±2.3 | 0.9% ±1.0 | 82.0% ±2.6 | 4.14 ±0.17 | 36.0% ±5.6 | 18.0% ±7.7 | 64.7% ±8.6 | 50.0% | 0.69 ±0.021 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 50 | 24.0 | base | 25.3 ±2.3 | 7.4 ±2.4 | 43.6 ±6.2 | 90.8% ±2.7 | 0.4% ±0.4 | 82.5% ±3.6 | 4.22 ±0.16 | 41.7% ±5.0 | 28.2% ±9.3 | 66.0% ±4.0 | 58.6% | 0.681 ±0.013 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 50 | 168.0 | close | 25.3 ±2.3 | 7.4 ±2.4 | 146 ±1.5 | 90.9% ±1.8 | 0.8% ±1.0 | 88.3% ±3.5 | 4.43 ±0.16 | 54.1% ±6.8 | 34.0% ±2.1 | 71.8% ±8.6 | 63.2% | 0.706 ±0.0072 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 100 | 6.0 | base | 49.3 ±3.8 | 13.8 ±5.1 | 12.8 ±1.8 | 95.3% ±0.8 | 0.1% ±0.2 | 91.2% ±1.7 | 4.4 ±0.097 | 25.1% ±3.5 | 19.2% ±2.1 | 59.3% ±4.0 | 53.8% | 0.671 ±0.016 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 100 | 24.0 | base | 49.3 ±3.8 | 13.8 ±5.1 | 20.1 ±0.91 | 95.4% ±0.6 | 0.1% ±0.2 | 92.3% ±1.1 | 4.5 ±0.09 | 31.5% ±5.5 | 20.3% ±5.5 | 59.9% ±2.9 | 45.0% | 0.659 ±0.014 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 100 | 168.0 | close | 49.3 ±3.8 | 13.8 ±5.1 | 145 ±0.65 | 96.0% ±1.1 | 0.7% ±0.6 | 97.2% ±0.8 | 4.71 ±0.093 | 57.2% ±3.5 | 35.8% ±5.6 | 69.2% ±4.6 | 59.3% | 0.686 ±0.016 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 200 | 6.0 | base | 98.8 ±3.5 | 26.5 ±4.8 | 5.6 ±0.14 | 97.9% ±0.5 | 0.1% ±0.2 | 96.8% ±0.5 | 4.67 ±0.061 | 15.6% ±0.5 | 11.0% ±2.5 | 50.8% ±2.7 | 49.0% | 0.626 ±0.0073 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 200 | 24.0 | base | 98.8 ±3.5 | 26.5 ±4.8 | 16.5 ±0.26 | 97.9% ±0.2 | 0.1% ±0.1 | 97.0% ±0.4 | 4.73 ±0.1 | 25.6% ±1.9 | 18.1% ±1.9 | 54.2% ±4.2 | 54.8% | 0.64 ±0.0061 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 200 | 168.0 | close | 98.8 ±3.5 | 26.5 ±4.8 | 143 ±0.67 | 99.5% ±0.3 | 0.0% | 99.9% ±0.1 | 4.93 ±0.049 | 57.1% ±1.8 | 36.4% ±2.0 | 66.3% ±3.8 | 63.4% | 0.659 ±0.003 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 350 | 6.0 | base | 174 ±11 | 46.1 ±5.3 | 4.4 ±0.13 | 98.9% ±0.1 | 0.0% | 98.4% ±0.4 | 4.72 ±0.077 | 10.7% ±1.3 | 7.9% ±1.5 | 38.3% ±2.1 | 50.6% | 0.594 ±0.0019 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 350 | 24.0 | base | 174 ±11 | 46.1 ±5.3 | 15.2 ±0.3 | 98.9% ±0.2 | 0.0% ±0.0 | 98.4% ±0.1 | 4.77 ±0.055 | 24.0% ±1.3 | 16.7% ±2.2 | 48.5% ±3.4 | 55.6% | 0.607 ±0.0043 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 350 | 168.0 | close | 174 ±11 | 46.1 ±5.3 | 143 ±0.73 | 100.0% ±0.0 | 0.0% | 100.0% | 5 ±0.054 | 61.2% ±1.6 | 38.6% ±3.4 | 64.8% ±3.2 | 62.0% | 0.639 ±0.0041 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 500 | 6.0 | base | 252 ±14 | 69.4 ±7.5 | 3.92 ±0.068 | 99.3% ±0.2 | 0.0% ±0.0 | 98.9% ±0.3 | 4.76 ±0.072 | 9.1% ±1.5 | 6.0% ±1.4 | 31.0% ±1.9 | 52.7% | 0.573 ±0.0044 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 500 | 24.0 | base | 252 ±14 | 69.4 ±7.5 | 14.7 ±0.26 | 99.2% ±0.1 | 0.0% | 99.2% ±0.2 | 4.87 ±0.062 | 24.6% ±1.4 | 17.5% ±1.9 | 47.1% ±2.0 | 55.4% | 0.594 ±0.0041 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 500 | 168.0 | close | 252 ±14 | 69.4 ±7.5 | 143 ±0.78 | 100.0% | 0.0% | 100.0% | 5.05 ±0.036 | 61.5% ±1.6 | 38.7% ±0.6 | 65.3% ±1.3 | 65.9% | 0.626 ±0.0045 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |

## matcher-validation

Heuristic vs hybrid (exact CP-SAT on pools ≤ 40): do the headline metrics move?

| matcher | M | median wait | placed (peak) | hard lockout (peak ticks) | reunion_14d_share | match_rate_p10_over_median | newcomer_within_horizon_share | detect_auc | matcher_ms_per_run | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| heuristic | 100 | 32 ±3.5 | 86.7% ±1.6 | 2.8% ±0.7 | 24.8% ±1.9 | 67.1% ±7.6 | 59.2% | 0.551 ±0.013 | 0.258 ±0.0064 | FAIL | FAIL | pass | pass | n/a |
| heuristic | 200 | 17.3 ±1.6 | 96.4% ±0.9 | 2.8% ±0.9 | 16.3% ±1.5 | 79.3% ±2.5 | 60.1% | 0.557 ±0.0044 | 0.256 ±0.0083 | FAIL | FAIL | pass | pass | n/a |
| hybrid | 100 | 32.2 ±3.4 | 87.1% ±1.7 | 3.0% ±0.9 | 24.6% ±2.5 | 66.3% ±7.5 | 54.6% | 0.554 ±0.013 | 2.55 ±0.13 | FAIL | FAIL | pass | pass | n/a |
| hybrid | 200 | 17.6 ±1.5 | 96.3% ±0.8 | 2.9% ±0.9 | 17.5% ±1.9 | 79.5% ±1.8 | 56.2% | 0.559 ±0.0082 | 2.31 ±0.064 | FAIL | FAIL | pass | pass | n/a |

## async-more-weight

R2 vs silent rejection, async M = 100: `more` weight, rolling 24 h vs batch at close.

| more | cadence_hours | ladder_minutes | median wait | cosignup_reunion_share | reunion_14d_share | players_in_stable_cluster_share | mutual_pair_hours_per_week_p90 | detect_auc | detect_auc_more | newcomer_within_horizon_share | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30.0 | 24.0 | base | 20 ±0.78 | 31.0% ±2.1 | 20.2% ±5.9 | 59.6% ±3.9 | 1.86 ±0.31 | 0.667 ±0.016 | 0.705 ±0.025 | 52.9% | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 30.0 | 168.0 | close | 145 ±0.65 | 54.4% ±2.3 | 36.9% ±6.2 | 68.1% ±1.5 | 2.77 ±0.18 | 0.683 ±0.016 | 0.764 ±0.027 | 53.5% | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 60.0 | 24.0 | base | 20.1 ±0.91 | 31.5% ±5.5 | 20.3% ±5.5 | 59.9% ±2.9 | 1.76 ±0.28 | 0.659 ±0.014 | 0.726 ±0.019 | 45.0% | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 60.0 | 168.0 | close | 145 ±0.65 | 57.2% ±3.5 | 35.8% ±5.6 | 69.2% ±4.6 | 2.99 ±0.3 | 0.686 ±0.016 | 0.785 ±0.029 | 59.3% | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 120.0 | 24.0 | base | 20.2 ±0.97 | 28.7% ±4.4 | 20.8% ±4.0 | 60.2% ±4.1 | 1.86 ±0.4 | 0.659 ±0.02 | 0.717 ±0.019 | 55.5% | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 120.0 | 168.0 | close | 145 ±0.93 | 54.9% ±4.0 | 38.9% ±6.2 | 70.0% ±3.9 | 2.87 ±0.4 | 0.677 ±0.021 | 0.792 ±0.011 | 61.0% | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 240.0 | 24.0 | base | 20 ±0.54 | 29.9% ±1.4 | 23.3% ±4.2 | 60.0% ±4.4 | 1.72 ±0.16 | 0.665 ±0.016 | 0.724 ±0.02 | 55.8% | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 240.0 | 168.0 | close | 144 ±0.83 | 56.8% ±2.2 | 37.8% ±3.9 | 69.9% ±3.5 | 2.92 ±0.34 | 0.687 ±0.021 | 0.788 ±0.027 | 54.1% | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 480.0 | 24.0 | base | 20 ±0.5 | 31.1% ±4.0 | 23.5% ±5.2 | 61.6% ±4.0 | 1.8 ±0.29 | 0.663 ±0.016 | 0.74 ±0.025 | 58.7% | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 480.0 | 168.0 | close | 144 ±0.6 | 53.9% ±4.9 | 39.3% ±4.0 | 71.1% ±2.3 | 2.77 ±0.36 | 0.692 ±0.017 | 0.801 ±0.014 | 57.1% | pass | FAIL | pass | pass | pass | pass | pass | FAIL |

## async-detection-placebo

Validation: async detection AUC with avoids ignored, rolling 6 h and batch at close.

| honor_avoids | cadence_hours | ladder_minutes | N online (peak) | detect_auc | detect_auc_more | cosignup_reunion_share | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| True | 6.0 | base | 49.3 ±3.8 | 0.671 ±0.016 | 0.721 ±0.036 | 25.1% ±3.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| True | 168.0 | close | 49.3 ±3.8 | 0.686 ±0.016 | 0.785 ±0.029 | 57.2% ±3.5 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| False | 6.0 | base | 49.3 ±3.8 | 0.504 ±0.0077 | 0.534 ±0.03 | 22.3% ±2.1 | pass | pass | pass | pass | pass | pass | FAIL | pass |
| False | 168.0 | close | 49.3 ±3.8 | 0.505 ±0.015 | 0.525 ±0.098 | 74.1% ±4.5 | pass | FAIL | pass | pass | pass | pass | pass | pass |

## live-density

R3: wait and placement by community size M and window habit (§9.1).

| M | habit | N online (peak) | N waiting (peak) | median wait | placed (peak) | hard lockout (peak ticks) | reunion_14d_share | reunion_opportunity_hit_share | players_in_stable_cluster_share | match_rate_p10_over_median | newcomer_within_horizon_share | detect_auc | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 50 | live | 1 | 1 | never | 18.4% ±1.2 | 0.7% ±0.9 | 27.3% ±22.0 | 35.4% ±20.2 | 13.7% ±4.5 | 0.8% ±1.8 | 68.8% | 0.607 ±0.044 | FAIL | pass | FAIL | pass | n/a |
| 50 | windows | 3.6 ±0.55 | 2 | 76.7 ±8.7 | 62.5% ±5.0 | 1.8% ±0.6 | 34.4% ±7.1 | 58.7% ±3.7 | 50.7% ±7.2 | 53.4% ±11.4 | 54.7% | 0.538 ±0.033 | FAIL | FAIL | pass | pass | n/a |
| 50 | generous | 5.2 ±0.45 | 2.2 ±0.45 | 51.2 ±5.2 | 78.8% ±1.6 | 5.3% ±2.3 | 46.5% ±5.0 | 63.5% ±6.0 | 68.8% ±5.9 | 62.7% ±5.5 | 52.5% | 0.581 ±0.014 | FAIL | FAIL | pass | pass | n/a |
| 100 | live | 4.8 ±0.45 | 1.4 ±0.55 | never | 43.0% ±3.9 | 0.7% ±0.6 | 18.9% ±7.2 | 47.0% ±9.2 | 18.1% ±7.8 | 40.6% ±7.5 | 56.2% | 0.561 ±0.019 | FAIL | pass | FAIL | pass | n/a |
| 100 | windows | 7.4 ±0.55 | 2 | 32 ±3.5 | 86.7% ±1.6 | 2.8% ±0.7 | 24.8% ±1.9 | 66.2% ±3.1 | 46.6% ±4.1 | 67.1% ±7.6 | 59.2% | 0.551 ±0.013 | FAIL | FAIL | pass | pass | n/a |
| 100 | generous | 9.6 ±0.55 | 3 | 24.8 ±1.8 | 93.5% ±0.9 | 5.5% ±0.8 | 30.7% ±3.8 | 72.6% ±4.0 | 63.3% ±2.8 | 72.8% ±5.1 | 55.9% | 0.579 ±0.0095 | FAIL | FAIL | pass | pass | n/a |
| 200 | live | 14 ±1.6 | 2 | 14.6 ±2.3 | 72.6% ±5.0 | 1.4% ±0.4 | 12.9% ±1.7 | 58.7% ±7.3 | 21.9% ±4.5 | 55.1% ±3.4 | 54.7% | 0.564 ±0.0075 | FAIL | FAIL | pass | pass | n/a |
| 200 | windows | 14.2 ±0.84 | 3 | 17.3 ±1.6 | 96.4% ±0.9 | 2.8% ±0.9 | 16.3% ±1.5 | 73.9% ±4.1 | 31.5% ±5.8 | 79.3% ±2.5 | 60.1% | 0.557 ±0.0044 | FAIL | FAIL | pass | pass | n/a |
| 200 | generous | 18.8 ±1.3 | 3 | 14.8 ±1.4 | 98.5% ±0.6 | 4.2% ±0.9 | 22.2% ±1.2 | 72.8% ±3.9 | 47.8% ±2.1 | 87.1% ±1.8 | 53.1% | 0.578 ±0.0078 | FAIL | FAIL | pass | pass | n/a |
| 350 | live | 27 ±1.4 | 3 | 8.35 ±0.49 | 88.8% ±1.4 | 1.4% ±0.4 | 11.1% ±1.2 | 67.5% ±3.5 | 16.2% ±2.4 | 69.7% ±2.9 | 58.8% | 0.553 ±0.0054 | pass | FAIL | pass | pass | FAIL |
| 350 | windows | 23.4 ±0.55 | 3 | 10.8 ±0.49 | 98.9% ±0.3 | 1.9% ±0.4 | 11.0% ±1.3 | 76.6% ±1.8 | 17.5% ±3.3 | 86.7% ±1.1 | 57.1% | 0.554 ±0.0061 | FAIL | FAIL | pass | pass | FAIL |
| 350 | generous | 30.4 ±1.1 | 3.4 ±0.55 | 10.3 ±0.09 | 99.6% ±0.1 | 3.0% ±0.9 | 15.1% ±1.3 | 75.1% ±1.8 | 31.6% ±3.6 | 91.9% ±0.8 | 54.3% | 0.571 ±0.0027 | FAIL | FAIL | pass | pass | FAIL |
| 500 | live | 41.8 ±1.8 | 3 | 6.35 ±0.078 | 94.1% ±0.8 | 1.6% ±0.5 | 8.9% ±0.7 | 70.8% ±2.6 | 11.7% ±2.8 | 74.8% ±2.9 | 52.8% | 0.553 ±0.0055 | pass | FAIL | pass | pass | FAIL |
| 500 | windows | 34.6 ±1.5 | 3.2 ±0.45 | 9.69 ±0.27 | 99.6% ±0.1 | 1.4% ±0.2 | 8.4% ±1.3 | 75.7% ±2.5 | 11.0% ±1.6 | 90.5% ±1.5 | 51.3% | 0.551 ±0.0032 | pass | FAIL | pass | pass | FAIL |
| 500 | generous | 44.8 ±1.1 | 4 | 8.22 ±0.52 | 99.9% ±0.1 | 2.6% ±0.4 | 11.8% ±1.8 | 77.2% ±1.2 | 22.6% ±3.6 | 95.1% ±0.5 | 53.6% | 0.566 ±0.0036 | pass | FAIL | pass | pass | FAIL |

## live-noise

§7.6: matching noise against the detection test and reunions, by M.

| noise | M | N online (peak) | detect_auc | detect_auc_more | reunion_14d_share | reunion_opportunity_hit_share | affinity_median | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 50 | 3.8 ±0.45 | 0.549 ±0.036 | 0.521 ±0.066 | 35.0% ±6.2 | 56.4% ±4.1 | 0.153 ±0.014 | FAIL | FAIL | pass | pass | n/a |
| 0.0 | 200 | 14.2 ±0.84 | 0.554 ±0.0077 | 0.564 ±0.026 | 16.1% ±1.3 | 72.5% ±4.5 | 0.077 ±0.0065 | FAIL | FAIL | pass | pass | n/a |
| 0.0 | 500 | 34.6 ±0.89 | 0.552 ±0.0037 | 0.558 ±0.0084 | 8.7% ±1.9 | 77.3% ±3.1 | 0.0362 ±0.0043 | pass | FAIL | pass | pass | FAIL |
| 0.25 | 50 | 3.6 ±0.55 | 0.538 ±0.033 | 0.506 ±0.067 | 34.4% ±7.1 | 58.7% ±3.7 | 0.156 ±0.014 | FAIL | FAIL | pass | pass | n/a |
| 0.25 | 200 | 14.2 ±0.84 | 0.557 ±0.0044 | 0.563 ±0.0076 | 16.3% ±1.5 | 73.9% ±4.1 | 0.0796 ±0.0039 | FAIL | FAIL | pass | pass | n/a |
| 0.25 | 500 | 34.6 ±1.5 | 0.551 ±0.0032 | 0.561 ±0.0086 | 8.4% ±1.3 | 75.7% ±2.5 | 0.0386 ±0.0036 | pass | FAIL | pass | pass | FAIL |
| 0.5 | 50 | 3.8 ±0.45 | 0.537 ±0.032 | 0.512 ±0.071 | 34.8% ±6.6 | 57.9% ±4.6 | 0.15 ±0.021 | FAIL | FAIL | pass | pass | n/a |
| 0.5 | 200 | 14.2 ±0.84 | 0.555 ±0.01 | 0.557 ±0.031 | 15.8% ±1.0 | 72.1% ±3.2 | 0.0789 ±0.0084 | FAIL | FAIL | pass | pass | n/a |
| 0.5 | 500 | 34.6 ±1.1 | 0.555 ±0.0034 | 0.559 ±0.003 | 8.9% ±1.8 | 78.0% ±3.2 | 0.0384 ±0.004 | pass | FAIL | pass | pass | FAIL |
| 1.0 | 50 | 3.8 ±0.45 | 0.545 ±0.019 | 0.517 ±0.062 | 33.2% ±5.7 | 58.5% ±4.8 | 0.142 ±0.024 | FAIL | FAIL | pass | pass | n/a |
| 1.0 | 200 | 14.2 ±0.84 | 0.561 ±0.0085 | 0.563 ±0.011 | 16.6% ±0.7 | 73.6% ±4.0 | 0.076 ±0.006 | FAIL | FAIL | pass | pass | n/a |
| 1.0 | 500 | 34.6 ±1.1 | 0.553 ±0.0041 | 0.561 ±0.0094 | 8.7% ±0.9 | 77.5% ±3.0 | 0.0367 ±0.0035 | pass | FAIL | pass | pass | FAIL |
| 2.0 | 50 | 3 | 0.555 ±0.017 | 0.522 ±0.083 | 35.6% ±5.6 | 57.4% ±4.8 | 0.137 ±0.02 | FAIL | FAIL | pass | pass | n/a |
| 2.0 | 200 | 14.2 ±0.84 | 0.56 ±0.0043 | 0.555 ±0.018 | 17.0% ±1.7 | 72.3% ±2.3 | 0.0781 ±0.0052 | FAIL | FAIL | pass | pass | n/a |
| 2.0 | 500 | 34.4 ±0.89 | 0.552 ±0.0043 | 0.559 ±0.0074 | 8.6% ±1.2 | 74.7% ±2.7 | 0.0364 ±0.0036 | pass | FAIL | pass | pass | FAIL |

## live-tick

Matcher cadence: does batching the queue (bigger pools per run) buy reunions for wait?

| tick_seconds | M | median wait | placed (peak) | hard lockout (peak ticks) | reunion_14d_share | reunion_opportunity_hit_share | players_in_stable_cluster_share | detect_auc | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30.0 | 200 | 17.3 ±1.6 | 96.4% ±0.9 | 2.8% ±0.9 | 16.3% ±1.5 | 73.9% ±4.1 | 31.5% ±5.8 | 0.557 ±0.0044 | FAIL | FAIL | pass | pass | n/a |
| 30.0 | 500 | 9.69 ±0.27 | 99.6% ±0.1 | 1.4% ±0.2 | 8.4% ±1.3 | 75.7% ±2.5 | 11.0% ±1.6 | 0.551 ±0.0032 | pass | FAIL | pass | pass | FAIL |
| 300.0 | 200 | 18.8 ±1.5 | 96.2% ±0.9 | 2.6% ±0.7 | 16.6% ±2.1 | 73.1% ±1.3 | 31.7% ±6.0 | 0.561 ±0.012 | FAIL | FAIL | pass | pass | n/a |
| 300.0 | 500 | 11.1 ±0.31 | 99.3% ±0.1 | 1.9% ±0.4 | 10.5% ±1.2 | 77.2% ±4.3 | 11.2% ±2.1 | 0.556 ±0.0042 | FAIL | FAIL | pass | pass | FAIL |
| 900.0 | 200 | 22.8 ±1.5 | 94.5% ±1.2 | 2.7% ±1.2 | 19.5% ±1.4 | 69.3% ±4.9 | 31.0% ±5.1 | 0.572 ±0.0066 | FAIL | FAIL | pass | pass | n/a |
| 900.0 | 500 | 13.8 ±0.27 | 98.8% ±0.2 | 1.7% ±0.4 | 12.7% ±1.7 | 73.1% ±1.4 | 12.1% ±2.7 | 0.562 ±0.0037 | FAIL | FAIL | pass | pass | FAIL |

## live-search

Kill/rethink check: can any combination of levers meet C1–C5 at M ≤ 500 (L = 4)?

| habit | M | flex_share | n_games | N online (peak) | median wait | placed (peak) | hard lockout (peak ticks) | match_rate_p10_over_median | newcomer_within_horizon_share | detect_auc | reunion_14d_share | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| windows | 200 | 0.5 | 1 | 13.8 ±0.84 | 11.4 ±0.84 | 99.7% ±0.2 | 2.2% ±0.2 | 89.6% ±0.9 | 50.9% | 0.567 ±0.0062 | 17.7% ±2.6 | FAIL | FAIL | pass | pass | n/a |
| windows | 200 | 0.5 | 3 | 14.2 ±0.84 | 17.3 ±1.6 | 96.4% ±0.9 | 2.8% ±0.9 | 79.3% ±2.5 | 60.1% | 0.557 ±0.0044 | 16.3% ±1.5 | FAIL | FAIL | pass | pass | n/a |
| windows | 200 | 1.0 | 1 | 13.8 ±0.84 | 7.92 ±0.46 | 100.0% ±0.0 | 1.4% ±0.4 | 90.5% ±1.0 | 46.9% | 0.565 ±0.0062 | 16.8% ±2.2 | pass | FAIL | pass | FAIL | n/a |
| windows | 200 | 1.0 | 3 | 14.2 ±1.1 | 11.8 ±0.95 | 98.5% ±0.3 | 1.5% ±0.5 | 85.3% ±2.1 | 44.2% | 0.556 ±0.01 | 14.3% ±3.2 | FAIL | FAIL | pass | FAIL | n/a |
| windows | 350 | 0.5 | 1 | 23.6 ±0.89 | 5.84 ±0.11 | 100.0% ±0.0 | 1.3% ±0.3 | 93.4% ±0.8 | 54.0% | 0.564 ±0.0026 | 11.7% ±1.5 | pass | FAIL | pass | pass | FAIL |
| windows | 350 | 0.5 | 3 | 23.4 ±0.55 | 10.8 ±0.49 | 98.9% ±0.3 | 1.9% ±0.4 | 86.7% ±1.1 | 57.1% | 0.554 ±0.0061 | 11.0% ±1.3 | FAIL | FAIL | pass | pass | FAIL |
| windows | 350 | 1.0 | 1 | 23.4 ±0.55 | 5.39 ±0.013 | 100.0% | 0.9% ±0.2 | 95.6% ±0.5 | 50.5% | 0.565 ±0.0041 | 9.4% ±1.4 | pass | pass | pass | pass | FAIL |
| windows | 350 | 1.0 | 3 | 23.2 ±0.84 | 10.2 ±0.085 | 99.6% ±0.1 | 1.0% ±0.2 | 90.9% ±1.0 | 50.0% | 0.556 ±0.002 | 10.1% ±1.8 | FAIL | FAIL | pass | FAIL | FAIL |
| windows | 500 | 0.5 | 1 | 33.4 ±0.55 | 4.19 ±0.18 | 100.0% ±0.0 | 1.0% ±0.3 | 95.4% ±0.2 | 56.5% | 0.558 ±0.0034 | 7.9% ±0.9 | pass | FAIL | pass | pass | FAIL |
| windows | 500 | 0.5 | 3 | 34.6 ±1.5 | 9.69 ±0.27 | 99.6% ±0.1 | 1.4% ±0.2 | 90.5% ±1.5 | 51.3% | 0.551 ±0.0032 | 8.4% ±1.3 | pass | FAIL | pass | pass | FAIL |
| windows | 500 | 1.0 | 1 | 33.6 ±1.3 | 4.72 ±0.2 | 100.0% | 0.4% ±0.0 | 97.4% ±0.3 | 49.4% | 0.555 ±0.0034 | 7.2% ±0.9 | pass | pass | pass | FAIL | FAIL |
| windows | 500 | 1.0 | 3 | 34 ±1.6 | 8.23 ±0.47 | 99.9% ±0.1 | 1.0% ±0.4 | 94.5% ±0.6 | 48.0% | 0.551 ±0.003 | 7.1% ±1.0 | pass | pass | pass | FAIL | FAIL |
| generous | 200 | 0.5 | 1 | 18.2 ±1.1 | 9.39 ±0.66 | 99.9% ±0.1 | 3.5% ±0.9 | 92.4% ±1.0 | 56.4% | 0.582 ±0.0032 | 21.1% ±2.3 | pass | FAIL | pass | pass | n/a |
| generous | 200 | 0.5 | 3 | 18.8 ±1.3 | 14.8 ±1.4 | 98.5% ±0.6 | 4.2% ±0.9 | 87.1% ±1.8 | 53.1% | 0.578 ±0.0078 | 22.2% ±1.2 | FAIL | FAIL | pass | pass | n/a |
| generous | 200 | 1.0 | 1 | 18 ±1.2 | 6.94 ±0.45 | 100.0% ±0.0 | 1.7% ±0.4 | 94.7% ±0.7 | 52.0% | 0.584 ±0.0072 | 18.0% ±3.4 | pass | FAIL | pass | pass | n/a |
| generous | 200 | 1.0 | 3 | 18 ±1.6 | 10.8 ±0.49 | 99.6% ±0.3 | 2.0% ±0.4 | 91.3% ±1.6 | 42.9% | 0.573 ±0.0045 | 18.1% ±2.0 | FAIL | FAIL | pass | FAIL | n/a |
| generous | 350 | 0.5 | 1 | 30.4 ±0.55 | 5.11 ±0.078 | 100.0% | 2.0% ±0.5 | 96.1% ±0.4 | 55.2% | 0.582 ±0.0035 | 13.8% ±1.3 | pass | FAIL | pass | pass | FAIL |
| generous | 350 | 0.5 | 3 | 30.4 ±1.1 | 10.3 ±0.09 | 99.6% ±0.1 | 3.0% ±0.9 | 91.9% ±0.8 | 54.3% | 0.571 ±0.0027 | 15.1% ±1.3 | FAIL | FAIL | pass | pass | FAIL |
| generous | 350 | 1.0 | 1 | 30.4 ±1.1 | 5.18 ±0.068 | 100.0% | 1.0% ±0.4 | 97.8% ±0.5 | 47.2% | 0.581 ±0.0048 | 13.1% ±1.2 | pass | pass | pass | FAIL | FAIL |
| generous | 350 | 1.0 | 3 | 29.8 ±1.6 | 9.7 ±0.46 | 99.9% ±0.0 | 1.3% ±0.1 | 95.4% ±0.3 | 48.8% | 0.569 ±0.0048 | 12.9% ±1.5 | pass | FAIL | pass | FAIL | FAIL |
| generous | 500 | 0.5 | 1 | 43.8 ±1.9 | 3.26 ±0.088 | 100.0% | 1.3% ±0.3 | 98.1% ±0.3 | 56.6% | 0.572 ±0.0025 | 10.0% ±1.0 | pass | FAIL | pass | pass | FAIL |
| generous | 500 | 0.5 | 3 | 44.8 ±1.1 | 8.22 ±0.52 | 99.9% ±0.1 | 2.6% ±0.4 | 95.1% ±0.5 | 53.6% | 0.566 ±0.0036 | 11.8% ±1.8 | pass | FAIL | pass | pass | FAIL |
| generous | 500 | 1.0 | 1 | 43.2 ±1.6 | 3.61 ±0.12 | 100.0% | 0.6% ±0.1 | 99.8% ±0.5 | 49.5% | 0.57 ±0.0034 | 9.4% ±0.4 | pass | pass | pass | FAIL | FAIL |
| generous | 500 | 1.0 | 3 | 44.6 ±1.7 | 6.93 ±0.37 | 100.0% ±0.0 | 1.3% ±0.2 | 97.4% ±0.4 | 48.7% | 0.568 ±0.0038 | 10.3% ±1.3 | pass | FAIL | pass | FAIL | FAIL |

## live-newcomer-batch

§7.4 again where the matcher has choice: 15-minute batches, M = 200 and 500.

| newcomer_decay_sessions | anchors_enabled | M | newcomers_eligible | newcomer_early_sessions_with_anchor | newcomer_within_horizon_share | newcomer_sessions_to_mutual_median | all_within_horizon_share | median wait | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | True | 200 | 764 | 0.204 ±0.068 | 59.8% | 7.6 ±2.1 | 56.0% ±3.1 | 22.7 ±1.2 | FAIL | FAIL | pass | pass | n/a |
| 0 | True | 500 | 2157 | 0.219 ±0.02 | 57.6% | 6.7 ±1.3 | 55.8% ±2.6 | 13.9 ±0.33 | FAIL | FAIL | pass | pass | FAIL |
| 0 | False | 200 | 764 | 0.204 ±0.068 | 59.8% | 7.6 ±2.1 | 56.0% ±3.1 | 22.7 ±1.2 | FAIL | FAIL | pass | pass | n/a |
| 0 | False | 500 | 2157 | 0.219 ±0.02 | 57.6% | 6.7 ±1.3 | 55.8% ±2.6 | 13.9 ±0.33 | FAIL | FAIL | pass | pass | FAIL |
| 5 | True | 200 | 774 | 0.197 ±0.081 | 56.3% | 7.7 ±1.1 | 55.9% ±3.6 | 22.5 ±1.1 | FAIL | FAIL | pass | pass | n/a |
| 5 | True | 500 | 2163 | 0.254 ±0.032 | 60.0% | 6.4 ±1.1 | 56.5% ±2.9 | 14 ±0.34 | FAIL | FAIL | pass | pass | FAIL |
| 5 | False | 200 | 797 | 0.195 ±0.063 | 57.8% | 7.5 ±1.4 | 55.6% ±3.6 | 22.4 ±1.2 | FAIL | FAIL | pass | pass | n/a |
| 5 | False | 500 | 2149 | 0.213 ±0.026 | 58.7% | 6.7 ±0.95 | 55.2% ±3.1 | 14 ±0.3 | FAIL | FAIL | pass | pass | FAIL |
| 10 | True | 200 | 793 | 0.214 ±0.077 | 53.7% | 7.5 | 52.4% ±2.7 | 22.6 ±1.4 | FAIL | FAIL | pass | pass | n/a |
| 10 | True | 500 | 2175 | 0.25 ±0.033 | 58.4% | 6.5 ±0.85 | 55.5% ±2.0 | 14 ±0.31 | FAIL | FAIL | pass | pass | FAIL |
| 10 | False | 200 | 767 | 0.197 ±0.057 | 58.3% | 8.5 ±2.5 | 55.3% ±3.0 | 22.7 ±1.2 | FAIL | FAIL | pass | pass | n/a |
| 10 | False | 500 | 2152 | 0.214 ±0.022 | 57.9% | 6.8 ±0.92 | 56.0% ±2.6 | 13.9 ±0.44 | FAIL | FAIL | pass | pass | FAIL |
| 20 | True | 200 | 776 | 0.211 ±0.079 | 58.2% | 7.9 ±3.2 | 55.4% ±3.9 | 22.7 ±1.4 | FAIL | FAIL | pass | pass | n/a |
| 20 | True | 500 | 2162 | 0.252 ±0.026 | 57.1% | 6.7 ±0.67 | 55.9% ±2.4 | 13.9 ±0.36 | FAIL | FAIL | pass | pass | FAIL |
| 20 | False | 200 | 784 | 0.202 ±0.067 | 60.1% | 7.4 ±2.6 | 56.3% ±2.0 | 22.5 ±1.3 | FAIL | FAIL | pass | pass | n/a |
| 20 | False | 500 | 2171 | 0.22 ±0.023 | 57.8% | 6.7 ±1.3 | 54.9% ±2.6 | 13.9 ±0.3 | FAIL | FAIL | pass | pass | FAIL |
| 40 | True | 200 | 784 | 0.216 ±0.074 | 60.5% | 7.5 ±2.4 | 56.3% ±2.5 | 22.3 ±1.1 | FAIL | FAIL | pass | pass | n/a |
| 40 | True | 500 | 2154 | 0.247 ±0.029 | 58.2% | 6.5 ±0.53 | 55.2% ±2.1 | 13.9 ±0.31 | FAIL | FAIL | pass | pass | FAIL |
| 40 | False | 200 | 783 | 0.198 ±0.045 | 57.0% | 8.4 ±2.8 | 55.0% ±2.9 | 22.4 ±1 | FAIL | FAIL | pass | pass | n/a |
| 40 | False | 500 | 2180 | 0.217 ±0.021 | 58.4% | 6.4 ±0.52 | 55.9% ±1.9 | 13.9 ±0.34 | FAIL | FAIL | pass | pass | FAIL |

## detection-placebo

Validation: detection AUC with avoids ignored by the matcher (the other-channel floor).

| honor_avoids | M | N online (peak) | detect_auc | detect_auc_more | reunion_14d_share | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|
| True | 200 | 14.2 ±0.84 | 0.557 ±0.0044 | 0.563 ±0.0076 | 16.3% ±1.5 | FAIL | FAIL | pass | pass | n/a |
| True | 500 | 34.6 ±1.5 | 0.551 ±0.0032 | 0.561 ±0.0086 | 8.4% ±1.3 | pass | FAIL | pass | pass | FAIL |
| False | 200 | 14.2 ±0.84 | 0.501 ±0.0048 | 0.507 ±0.011 | 16.4% ±1.9 | FAIL | pass | pass | pass | n/a |
| False | 500 | 34.4 ±1.1 | 0.501 ±0.0044 | 0.503 ±0.015 | 8.0% ±1.3 | pass | pass | pass | pass | pass |

## async-matcher-validation

Heuristic vs hybrid for async, rolling and batch-at-close.

| matcher | M | cadence_hours | ladder_minutes | median wait | placed | locked sign-ups | pref_size_share | cosignup_reunion_share | detect_auc | matcher_ms_per_run | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| heuristic | 50 | 6.0 | base | 33.4 ±6.7 | 91.7% ±2.3 | 0.9% ±1.0 | 82.0% ±2.6 | 36.0% ±5.6 | 0.69 ±0.021 | 0.327 ±0.013 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| heuristic | 50 | 168.0 | close | 146 ±1.5 | 90.9% ±1.8 | 0.8% ±1.0 | 88.3% ±3.5 | 54.1% ±6.8 | 0.706 ±0.0072 | 3.05 ±1.7 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| hybrid | 50 | 6.0 | base | 32.9 ±5.8 | 91.6% ±2.1 | 0.7% ±0.5 | 81.3% ±3.4 | 37.7% ±5.8 | 0.696 ±0.026 | 2.88 ±0.18 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| hybrid | 50 | 168.0 | close | 146 ±1 | 91.0% ±2.1 | 1.2% ±1.1 | 88.0% ±2.7 | 53.9% ±6.0 | 0.713 ±0.033 | 379 ±3.9e+02 | pass | FAIL | pass | FAIL | pass | pass | pass | FAIL |

## live-lobby

Lobby size L and size flexibility (§8 point 3) against lockout and wait.

| lobby_size | M | flex_share | median wait | placed (peak) | hard lockout (peak ticks) | window_lost_to_hard_blocks_share | target_locked_hours_per_week | match_rate_p10_over_median | reunion_14d_share | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 100 | base | 15.9 ±1.5 | 94.3% ±0.9 | 1.6% ±0.6 | 0.3% ±0.1 | 0.13 ±0.15 | 78.0% ±3.7 | 19.0% ±3.8 | FAIL | FAIL | pass | FAIL | n/a |
| 3 | 200 | base | 10.2 ±0.058 | 98.9% ±0.2 | 1.3% ±0.3 | 0.1% ±0.0 | 0.0633 ±0.043 | 87.0% ±2.3 | 13.4% ±3.2 | FAIL | FAIL | pass | FAIL | n/a |
| 4 | 100 | base | 32 ±3.5 | 86.7% ±1.6 | 2.8% ±0.7 | 1.3% ±0.3 | 0.262 ±0.25 | 67.1% ±7.6 | 24.8% ±1.9 | FAIL | FAIL | pass | pass | n/a |
| 4 | 200 | base | 17.3 ±1.6 | 96.4% ±0.9 | 2.8% ±0.9 | 0.3% ±0.1 | 0.105 ±0.16 | 79.3% ±2.5 | 16.3% ±1.5 | FAIL | FAIL | pass | pass | n/a |
| 5 | 100 | base | 52.2 ±4 | 75.7% ±3.4 | 4.4% ±1.4 | 3.1% ±0.5 | 0.43 ±0.24 | 49.0% ±4.2 | 23.4% ±2.7 | FAIL | FAIL | FAIL | pass | n/a |
| 5 | 200 | base | 24.7 ±2.3 | 93.0% ±1.8 | 4.4% ±1.6 | 0.9% ±0.3 | 0.173 ±0.15 | 71.2% ±2.8 | 19.1% ±1.8 | FAIL | FAIL | pass | pass | n/a |
| base | 200 | 0.0 | 18.3 ±1.4 | 96.2% ±0.8 | 2.7% ±0.4 | 0.4% ±0.2 | 0.065 ±0.064 | 78.7% ±2.8 | 17.1% ±2.4 | FAIL | FAIL | pass | pass | n/a |
| base | 200 | 1.0 | 11.8 ±0.95 | 98.5% ±0.3 | 1.5% ±0.5 | 0.1% ±0.0 | 0.035 ±0.061 | 85.3% ±2.1 | 14.3% ±3.2 | FAIL | FAIL | pass | FAIL | n/a |

## live-cap

§14 #8: hard-block cap against lockout, at three hard-block propensities.

| hard_cap | p_hard | hard_blocks_per_player | hard lockout (peak ticks) | window_lost_to_hard_blocks_share | avoid_held_tick_share | target_locked_hours_per_week | target_placed_share | soft_broken_per_100_sessions | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.08 | 0.494 ±0.024 | 1.5% ±0.3 | 0.2% ±0.1 | 9.3% ±0.9 | 0.0233 ±0.023 | 92.2% ±2.2 | 28.7 ±2 | FAIL | FAIL | pass | pass | n/a |
| 1 | 0.2 | 0.702 ±0.041 | 2.0% ±0.3 | 0.2% ±0.0 | 8.8% ±1.3 | 0.04 ±0.045 | 90.2% ±8.1 | 25.8 ±1.8 | FAIL | FAIL | pass | FAIL | n/a |
| 1 | 0.4 | 0.826 ±0.018 | 2.3% ±0.6 | 0.3% ±0.1 | 8.2% ±1.4 | 0.125 ±0.08 | 88.1% ±7.8 | 25.7 ±2 | FAIL | FAIL | pass | pass | n/a |
| 3 | 0.08 | 0.829 ±0.084 | 2.6% ±0.9 | 0.3% ±0.1 | 8.7% ±1.3 | 0.122 ±0.18 | 86.4% ±4.6 | 27.4 ±2.5 | FAIL | FAIL | pass | pass | n/a |
| 3 | 0.2 | 1.43 ±0.027 | 4.0% ±0.7 | 0.5% ±0.2 | 8.1% ±1.2 | 0.16 ±0.12 | 88.6% ±3.7 | 25.4 ±0.94 | FAIL | FAIL | pass | pass | n/a |
| 3 | 0.4 | 1.98 ±0.082 | 5.3% ±0.8 | 0.6% ±0.2 | 7.4% ±1.6 | 0.282 ±0.12 | 84.0% ±10.6 | 22 ±1.7 | FAIL | FAIL | pass | pass | n/a |
| 5 | 0.08 | 0.886 ±0.096 | 2.8% ±0.9 | 0.3% ±0.1 | 8.5% ±1.1 | 0.105 ±0.16 | 90.4% ±2.4 | 26.4 ±1.9 | FAIL | FAIL | pass | pass | n/a |
| 5 | 0.2 | 1.75 ±0.061 | 4.8% ±0.7 | 0.6% ±0.2 | 7.5% ±0.9 | 0.193 ±0.11 | 86.1% ±3.5 | 23.3 ±1.5 | FAIL | FAIL | pass | pass | n/a |
| 5 | 0.4 | 2.65 ±0.1 | 7.0% ±1.2 | 0.9% ±0.4 | 6.6% ±1.7 | 0.257 ±0.24 | 85.9% ±6.9 | 19.9 ±2.9 | FAIL | FAIL | pass | pass | n/a |
| 10 | 0.08 | 0.912 ±0.093 | 2.8% ±0.9 | 0.3% ±0.1 | 8.5% ±1.2 | 0.105 ±0.16 | 90.4% ±2.4 | 26.5 ±1.8 | FAIL | FAIL | pass | pass | n/a |
| 10 | 0.2 | 1.9 ±0.083 | 5.3% ±1.1 | 0.7% ±0.2 | 7.7% ±1.1 | 0.163 ±0.17 | 85.2% ±6.1 | 23.2 ±2.1 | FAIL | FAIL | pass | pass | n/a |
| 10 | 0.4 | 3.3 ±0.28 | 9.1% ±1.8 | 1.0% ±0.3 | 6.1% ±1.4 | 0.327 ±0.19 | 85.0% ±4.5 | 18.4 ±2.3 | FAIL | FAIL | pass | pass | n/a |
| 25 | 0.08 | 0.912 ±0.093 | 2.8% ±0.9 | 0.3% ±0.1 | 8.5% ±1.2 | 0.105 ±0.16 | 90.4% ±2.4 | 26.5 ±1.8 | FAIL | FAIL | pass | pass | n/a |
| 25 | 0.2 | 1.9 ±0.1 | 5.6% ±1.4 | 0.7% ±0.3 | 7.7% ±1.0 | 0.253 ±0.31 | 85.6% ±6.5 | 23.2 ±2.4 | FAIL | FAIL | pass | pass | n/a |
| 25 | 0.4 | 3.53 ±0.3 | 9.6% ±1.5 | 1.1% ±0.4 | 6.1% ±1.3 | 0.482 ±0.21 | 82.1% ±7.1 | 18.4 ±2.3 | FAIL | FAIL | pass | pass | n/a |

## live-newcomer

§7.4: newcomer-boost decay (0 = off) and anchors vs sessions to first mutual `more`.

| newcomer_decay_sessions | anchors_enabled | newcomers_eligible | newcomer_early_sessions_with_anchor | newcomer_within_horizon_share | newcomer_sessions_to_mutual_median | all_within_horizon_share | match_rate_p10_over_median | median wait | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | True | 767 | 0.187 ±0.06 | 57.8% | 8.4 ±2.5 | 55.1% ±2.9 | 78.1% ±3.2 | 16.9 ±1.6 | FAIL | FAIL | pass | pass | n/a |
| 0 | False | 767 | 0.187 ±0.06 | 57.8% | 8.4 ±2.5 | 55.1% ±2.9 | 78.1% ±3.2 | 16.9 ±1.6 | FAIL | FAIL | pass | pass | n/a |
| 5 | True | 775 | 0.199 ±0.068 | 53.5% | 9.1 ±2.6 | 53.7% ±2.7 | 77.5% ±3.5 | 17 ±1.8 | FAIL | FAIL | pass | pass | n/a |
| 5 | False | 775 | 0.192 ±0.067 | 54.2% | 8.9 ±2.3 | 53.8% ±3.6 | 77.1% ±3.4 | 17.3 ±1.8 | FAIL | FAIL | pass | pass | n/a |
| 10 | True | 766 | 0.197 ±0.064 | 56.7% | 9.7 ±3.7 | 54.5% ±3.8 | 77.1% ±4.6 | 17.3 ±1.8 | FAIL | FAIL | pass | pass | n/a |
| 10 | False | 763 | 0.2 ±0.075 | 55.8% | 9.4 ±3.2 | 54.0% ±3.3 | 78.6% ±3.6 | 17.1 ±1.8 | FAIL | FAIL | pass | pass | n/a |
| 20 | True | 794 | 0.206 ±0.071 | 56.9% | 8.7 ±3.2 | 55.2% ±3.9 | 77.5% ±4.3 | 17.1 ±1.5 | FAIL | FAIL | pass | pass | n/a |
| 20 | False | 779 | 0.199 ±0.059 | 56.1% | 7.5 ±1.6 | 53.9% ±3.0 | 77.5% ±3.2 | 17 ±1.9 | FAIL | FAIL | pass | pass | n/a |
| 40 | True | 783 | 0.182 ±0.068 | 55.9% | 7.7 ±2.6 | 54.9% ±5.0 | 77.5% ±2.4 | 17 ±1.4 | FAIL | FAIL | pass | pass | n/a |
| 40 | False | 783 | 0.191 ±0.065 | 55.6% | 8.6 ±1.6 | 54.0% ±2.6 | 77.2% ±3.8 | 17.1 ±1.9 | FAIL | FAIL | pass | pass | n/a |

## live-more-weight

R2 vs silent rejection: does a stronger `more` buy reunions, and at what detection cost?

| more | tick_seconds | median wait | reunion_14d_share | reunion_opportunity_hit_share | players_in_stable_cluster_share | mutual_pair_hours_per_week_p90 | detect_auc | detect_auc_more | newcomer_within_horizon_share | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30.0 | 30.0 | 17.3 ±1.4 | 15.6% ±2.0 | 73.5% ±4.8 | 31.8% ±5.0 | 0.579 ±0.066 | 0.559 ±0.0072 | 0.555 ±0.016 | 58.9% | FAIL | FAIL | pass | pass | n/a |
| 30.0 | 900.0 | 22.6 ±1 | 19.0% ±0.9 | 70.0% ±5.5 | 32.6% ±4.5 | 0.641 ±0.084 | 0.571 ±0.0091 | 0.596 ±0.017 | 58.4% | FAIL | FAIL | pass | pass | n/a |
| 60.0 | 30.0 | 17.3 ±1.6 | 16.3% ±1.5 | 73.9% ±4.1 | 31.5% ±5.8 | 0.552 ±0.055 | 0.557 ±0.0044 | 0.563 ±0.0076 | 60.1% | FAIL | FAIL | pass | pass | n/a |
| 60.0 | 900.0 | 22.8 ±1.5 | 19.5% ±1.4 | 69.3% ±4.9 | 31.0% ±5.1 | 0.66 ±0.065 | 0.572 ±0.0066 | 0.594 ±0.0095 | 56.9% | FAIL | FAIL | pass | pass | n/a |
| 120.0 | 30.0 | 17.2 ±1.1 | 16.9% ±1.0 | 72.4% ±2.1 | 33.3% ±4.5 | 0.561 ±0.05 | 0.561 ±0.0069 | 0.554 ±0.023 | 57.6% | FAIL | FAIL | pass | pass | n/a |
| 120.0 | 900.0 | 22.7 ±1.2 | 18.0% ±2.0 | 72.8% ±4.2 | 31.4% ±3.0 | 0.608 ±0.058 | 0.571 ±0.0048 | 0.599 ±0.018 | 59.1% | FAIL | FAIL | pass | pass | n/a |
| 240.0 | 30.0 | 17.4 ±1.4 | 16.7% ±1.1 | 75.8% ±3.4 | 33.7% ±3.2 | 0.592 ±0.051 | 0.558 ±0.01 | 0.554 ±0.029 | 52.2% | FAIL | FAIL | pass | pass | n/a |
| 240.0 | 900.0 | 22.7 ±1.2 | 17.6% ±2.0 | 73.2% ±4.8 | 32.1% ±4.6 | 0.605 ±0.063 | 0.57 ±0.0096 | 0.594 ±0.013 | 52.8% | FAIL | FAIL | pass | pass | n/a |
| 480.0 | 30.0 | 17.4 ±2.3 | 16.5% ±1.6 | 74.5% ±2.6 | 32.9% ±3.8 | 0.578 ±0.075 | 0.551 ±0.012 | 0.559 ±0.019 | 57.6% | FAIL | FAIL | pass | pass | n/a |
| 480.0 | 900.0 | 22.8 ±1.4 | 18.6% ±1.8 | 74.5% ±2.1 | 30.8% ±4.1 | 0.631 ±0.074 | 0.571 ±0.0033 | 0.596 ±0.018 | 51.3% | FAIL | FAIL | pass | pass | n/a |

## async-noise

§7.6 for async: noise against the detection test, by M.

| noise | M | N online (peak) | detect_auc | detect_auc_more | cosignup_reunion_share | reunion_14d_share | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 50 | 25.3 ±2.3 | 0.699 ±0.02 | 0.737 ±0.059 | 36.9% ±6.5 | 21.0% ±7.1 | pass | pass | pass | FAIL | pass | pass | FAIL | FAIL |
| 0.0 | 100 | 49.3 ±3.8 | 0.665 ±0.014 | 0.704 ±0.017 | 24.7% ±2.4 | 16.8% ±3.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 0.0 | 200 | 98.8 ±3.5 | 0.626 ±0.0058 | 0.666 ±0.018 | 15.6% ±0.8 | 11.9% ±2.0 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 0.0 | 500 | 252 ±14 | 0.574 ±0.0032 | 0.619 ±0.0044 | 9.4% ±0.1 | 6.1% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 0.5 | 50 | 25.3 ±2.3 | 0.695 ±0.012 | 0.742 ±0.032 | 36.1% ±5.7 | 21.1% ±3.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 0.5 | 100 | 49.3 ±3.8 | 0.668 ±0.01 | 0.704 ±0.0088 | 24.6% ±3.3 | 16.0% ±6.2 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 0.5 | 200 | 98.8 ±3.5 | 0.627 ±0.0058 | 0.668 ±0.011 | 15.7% ±1.3 | 12.2% ±2.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 0.5 | 500 | 252 ±14 | 0.575 ±0.0028 | 0.624 ±0.0055 | 8.9% ±0.8 | 6.4% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 2.0 | 50 | 25.3 ±2.3 | 0.677 ±0.024 | 0.715 ±0.041 | 35.3% ±5.2 | 21.3% ±9.4 | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL |
| 2.0 | 100 | 49.3 ±3.8 | 0.665 ±0.012 | 0.693 ±0.025 | 22.7% ±2.3 | 14.6% ±2.6 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 2.0 | 200 | 98.8 ±3.5 | 0.628 ±0.0057 | 0.65 ±0.014 | 14.5% ±1.3 | 10.1% ±1.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 2.0 | 500 | 252 ±14 | 0.573 ±0.0036 | 0.609 ±0.009 | 8.0% ±0.3 | 6.0% ±0.9 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |

## async-cap

§14 #8 for async: hard-block cap against locked sign-ups.

| hard_cap | p_hard | M | hard_blocks_per_player | locked sign-ups | hard lockout (peak ticks) | target_placed_share | placed | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.08 | 50 | 0.25 ±0.019 | 0.6% ±1.0 | 3.7% ±5.7 | 63.6% ±13.6 | 92.0% ±2.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 1 | 0.08 | 100 | 0.267 ±0.025 | 0.1% ±0.2 | 1.1% ±2.4 | 90.7% ±7.3 | 95.5% ±0.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 1 | 0.4 | 50 | 0.607 ±0.033 | 1.3% ±1.3 | 8.6% ±7.3 | 55.3% ±18.8 | 91.4% ±2.5 | pass | pass | pass | FAIL | pass | pass | FAIL | FAIL |
| 1 | 0.4 | 100 | 0.601 ±0.06 | 0.1% ±0.2 | 1.0% ±2.1 | 93.6% ±7.7 | 95.7% ±0.5 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 3 | 0.08 | 50 | 0.316 ±0.056 | 0.7% ±1.0 | 4.7% ±5.3 | 64.8% ±14.6 | 91.8% ±2.4 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 3 | 0.08 | 100 | 0.351 ±0.061 | 0.1% ±0.2 | 1.9% ±2.7 | 92.0% ±5.6 | 95.3% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 3 | 0.4 | 50 | 1.18 ±0.13 | 0.9% ±0.8 | 6.8% ±6.4 | 58.3% ±18.2 | 91.4% ±3.1 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 3 | 0.4 | 100 | 1.15 ±0.073 | 0.5% ±0.5 | 5.4% ±5.9 | 89.1% ±8.1 | 95.0% ±1.0 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 5 | 0.08 | 50 | 0.324 ±0.061 | 0.9% ±1.0 | 5.8% ±6.0 | 62.7% ±14.7 | 91.7% ±2.3 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 5 | 0.08 | 100 | 0.358 ±0.059 | 0.1% ±0.2 | 1.9% ±2.7 | 92.0% ±5.6 | 95.3% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 5 | 0.4 | 50 | 1.31 ±0.12 | 0.9% ±0.8 | 6.7% ±6.3 | 65.6% ±10.9 | 90.6% ±2.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 5 | 0.4 | 100 | 1.33 ±0.094 | 0.5% ±0.6 | 6.2% ±7.6 | 89.1% ±8.1 | 95.0% ±1.0 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 10 | 0.08 | 50 | 0.324 ±0.061 | 0.9% ±1.0 | 5.8% ±6.0 | 62.7% ±14.7 | 91.7% ±2.3 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 10 | 0.08 | 100 | 0.361 ±0.056 | 0.1% ±0.2 | 1.9% ±2.7 | 92.0% ±5.6 | 95.3% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 10 | 0.4 | 50 | 1.33 ±0.13 | 0.9% ±0.8 | 6.7% ±6.3 | 65.6% ±10.9 | 90.6% ±2.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 10 | 0.4 | 100 | 1.39 ±0.1 | 0.5% ±0.6 | 6.2% ±7.6 | 89.1% ±8.1 | 95.0% ±1.0 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 25 | 0.08 | 50 | 0.324 ±0.061 | 0.9% ±1.0 | 5.8% ±6.0 | 62.7% ±14.7 | 91.7% ±2.3 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 25 | 0.08 | 100 | 0.361 ±0.056 | 0.1% ±0.2 | 1.9% ±2.7 | 92.0% ±5.6 | 95.3% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 25 | 0.4 | 50 | 1.33 ±0.13 | 0.9% ±0.8 | 6.7% ±6.3 | 65.6% ±10.9 | 90.6% ±2.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 25 | 0.4 | 100 | 1.41 ±0.1 | 0.5% ±0.6 | 6.2% ±7.6 | 89.1% ±8.1 | 95.0% ±1.0 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |

## async-newcomer

§7.4 for async: newcomer-boost decay and anchors against seeds to first mutual `more`.

| newcomer_decay_sessions | anchors_enabled | newcomers_eligible | newcomer_early_sessions_with_anchor | newcomer_within_horizon_share | newcomer_sessions_to_mutual_median | all_within_horizon_share | placed | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | True | 704 | 0.238 ±0.036 | 54.0% | never | 50.7% ±4.4 | 96.1% ±0.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 0 | False | 704 | 0.238 ±0.036 | 54.0% | never | 50.7% ±4.4 | 96.1% ±0.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 5 | True | 702 | 0.255 ±0.037 | 50.9% | never | 51.7% ±5.8 | 96.1% ±0.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 5 | False | 690 | 0.241 ±0.03 | 50.6% | never | 48.9% ±3.3 | 96.2% ±0.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 10 | True | 685 | 0.249 ±0.034 | 51.8% | never | 52.3% ±7.0 | 96.2% ±0.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 10 | False | 701 | 0.236 ±0.04 | 51.8% | 9.5 | 51.2% ±6.1 | 96.2% ±0.6 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 20 | True | 691 | 0.253 ±0.044 | 51.2% | never | 51.4% ±6.1 | 96.1% ±0.7 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 20 | False | 704 | 0.238 ±0.034 | 53.3% | 8.5 | 50.7% ±6.5 | 96.2% ±0.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 40 | True | 706 | 0.243 ±0.036 | 50.6% | never | 51.1% ±7.6 | 96.1% ±0.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 40 | False | 689 | 0.232 ±0.038 | 51.4% | never | 50.9% ±6.0 | 95.9% ±0.7 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |

## async-newcomer-batch

§7.4 again where the matcher has choice: async batch at close, M = 100.

| newcomer_decay_sessions | anchors_enabled | newcomers_eligible | newcomer_early_sessions_with_anchor | newcomer_within_horizon_share | newcomer_sessions_to_mutual_median | all_within_horizon_share | placed | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | True | 729 | 0.24 ±0.031 | 59.0% | 5.5 | 60.8% ±6.0 | 97.2% ±0.7 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 0 | False | 729 | 0.24 ±0.031 | 59.0% | 5.5 | 60.8% ±6.0 | 97.2% ±0.7 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 5 | True | 732 | 0.373 ±0.035 | 64.2% | 5 | 62.2% ±3.9 | 97.2% ±0.8 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 5 | False | 734 | 0.259 ±0.04 | 60.8% | 5 | 61.4% ±4.9 | 97.3% ±0.8 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 10 | True | 728 | 0.343 ±0.049 | 61.1% | 5 | 59.6% ±5.4 | 97.3% ±0.8 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 10 | False | 700 | 0.25 ±0.035 | 56.3% | 6 | 59.6% ±5.0 | 97.4% ±0.9 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 20 | True | 717 | 0.308 ±0.034 | 57.2% | 6.5 | 60.9% ±3.7 | 97.6% ±0.7 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 20 | False | 726 | 0.252 ±0.052 | 59.6% | 5.5 | 60.4% ±5.6 | 97.7% ±0.5 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 40 | True | 735 | 0.298 ±0.042 | 63.3% | 4 | 62.6% ±3.9 | 97.5% ±0.8 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 40 | False | 734 | 0.258 ±0.045 | 62.1% | 4 | 61.3% ±5.7 | 97.4% ±0.8 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |

## async-half-life

§14 #9 for async: soft-avoid half-life, rolling 6 h cadence and batch at close.

| soft_half_life_days | M | cadence_hours | ladder_minutes | locked sign-ups | soft_broken_per_100_sessions | avoided_pair_rematch_share | active_avoids_per_player | cosignup_reunion_share | placed | median wait | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7.0 | 50 | 6.0 | base | 0.6% ±0.4 | 2.87 ±0.68 | 37.4% ±2.9 | 0.865 ±0.076 | 32.9% ±3.0 | 92.5% ±1.7 | 24.9 ±7.8 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 7.0 | 50 | 168.0 | close | 0.6% ±0.4 | 1.6 ±0.62 | 40.3% ±6.7 | 0.974 ±0.11 | 53.0% ±3.8 | 92.7% ±1.9 | 145 ±0.78 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 7.0 | 100 | 6.0 | base | 0.3% ±0.2 | 0.947 ±0.55 | 27.7% ±1.9 | 0.888 ±0.12 | 24.1% ±3.0 | 95.7% ±0.5 | 11.1 ±1.8 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 7.0 | 100 | 168.0 | close | 0.2% ±0.3 | 0.502 ±0.32 | 31.1% ±3.0 | 0.898 ±0.086 | 54.9% ±2.3 | 97.0% ±1.0 | 144 ±0.7 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 14.0 | 50 | 6.0 | base | 0.6% ±0.2 | 4.81 ±1 | 29.0% ±2.8 | 1.18 ±0.12 | 32.2% ±4.6 | 92.1% ±2.0 | 28.1 ±7.3 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 14.0 | 50 | 168.0 | close | 0.5% ±0.6 | 3.31 ±1.1 | 32.1% ±6.1 | 1.24 ±0.19 | 52.6% ±4.7 | 92.9% ±1.4 | 145 ±0.79 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 14.0 | 100 | 6.0 | base | 0.3% ±0.2 | 2.16 ±0.95 | 22.8% ±2.5 | 1.16 ±0.13 | 23.5% ±1.8 | 95.6% ±0.5 | 12.1 ±1.9 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 14.0 | 100 | 168.0 | close | 0.4% ±0.5 | 0.908 ±0.3 | 23.9% ±1.9 | 1.13 ±0.14 | 53.0% ±2.1 | 96.4% ±1.2 | 144 ±1 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 30.0 | 50 | 6.0 | base | 0.7% ±0.3 | 9.61 ±3.7 | 15.8% ±3.7 | 1.83 ±0.23 | 31.7% ±1.6 | 92.4% ±1.5 | 33.5 ±10 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 30.0 | 50 | 168.0 | close | 1.0% ±0.3 | 4.05 ±0.8 | 17.0% ±5.3 | 1.95 ±0.32 | 48.3% ±3.9 | 91.7% ±1.6 | 145 ±0.96 | pass | FAIL | pass | FAIL | pass | pass | FAIL | FAIL |
| 30.0 | 100 | 6.0 | base | 0.3% ±0.1 | 3.24 ±1.4 | 11.7% ±1.0 | 1.84 ±0.22 | 25.1% ±2.4 | 95.5% ±0.5 | 13.3 ±2.1 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 30.0 | 100 | 168.0 | close | 0.5% ±0.4 | 1.67 ±0.49 | 12.2% ±1.8 | 1.84 ±0.19 | 50.8% ±1.0 | 95.8% ±0.9 | 145 ±0.77 | pass | FAIL | pass | pass | pass | pass | pass | FAIL |
| 60.0 | 50 | 6.0 | base | 0.9% ±0.9 | 11.6 ±3 | 11.9% ±2.1 | 2.91 ±0.29 | 33.4% ±4.0 | 91.9% ±1.7 | 37 ±8.7 | pass | pass | pass | pass | pass | FAIL | FAIL | FAIL |
| 60.0 | 50 | 168.0 | close | 0.9% ±0.8 | 4.3 ±2 | 9.2% ±5.4 | 3.09 ±0.48 | 46.0% ±5.8 | 91.3% ±1.8 | 146 ±0.95 | pass | FAIL | pass | pass | pass | pass | FAIL | FAIL |
| 60.0 | 100 | 6.0 | base | 0.2% ±0.1 | 4.52 ±0.9 | 4.9% ±1.0 | 3.19 ±0.33 | 24.6% ±1.6 | 95.4% ±0.9 | 14.4 ±2.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 60.0 | 100 | 168.0 | close | 0.7% ±0.2 | 2.73 ±1.2 | 5.2% ±1.1 | 3.2 ±0.37 | 49.5% ±2.4 | 95.7% ±0.9 | 145 ±0.93 | pass | FAIL | pass | pass | pass | pass | FAIL | FAIL |
| 90.0 | 50 | 6.0 | base | 1.2% ±0.7 | 11.5 ±2.7 | 9.6% ±2.6 | 4.1 ±0.34 | 34.2% ±3.9 | 91.8% ±1.5 | 37.5 ±8.8 | pass | pass | pass | FAIL | pass | FAIL | FAIL | FAIL |
| 90.0 | 50 | 168.0 | close | 0.8% ±0.6 | 4.34 ±1.3 | 7.3% ±4.6 | 4.24 ±0.44 | 46.6% ±5.8 | 91.3% ±1.9 | 146 ±1 | pass | FAIL | pass | pass | pass | pass | FAIL | FAIL |
| 90.0 | 100 | 6.0 | base | 0.3% ±0.2 | 4.79 ±1.7 | 3.3% ±0.9 | 4.56 ±0.25 | 24.9% ±1.9 | 95.5% ±0.5 | 14.4 ±2.5 | pass | pass | pass | pass | pass | pass | FAIL | FAIL |
| 90.0 | 100 | 168.0 | close | 0.6% ±0.2 | 2.7 ±0.89 | 2.6% ±0.7 | 4.52 ±0.36 | 49.3% ±3.1 | 95.8% ±0.8 | 145 ±0.88 | pass | FAIL | pass | pass | pass | pass | FAIL | FAIL |

## live-half-life

§14 #9: soft-avoid half-life against lockout, avoid-holds, broken avoids and reunions.

| soft_half_life_days | M | hard lockout (peak ticks) | avoid_held_tick_share | soft_broken_per_100_sessions | avoided_pair_rematch_share | active_avoids_per_player | reunion_14d_share | median wait | match_rate_p10_over_median | high_avoid_only_share | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7.0 | 100 | 5.3% ±1.5 | 4.2% ±0.7 | 32.1 ±2.8 | 44.9% ±2.7 | 2.34 ±0.35 | 22.0% ±1.8 | 33.2 ±5.6 | 65.2% ±4.0 | 4.4% ±0.7 | FAIL | FAIL | pass | pass | n/a |
| 7.0 | 200 | 4.2% ±0.8 | 6.7% ±0.7 | 19.9 ±1.4 | 35.0% ±0.7 | 3.23 ±0.37 | 15.5% ±1.0 | 15.9 ±0.8 | 81.3% ±2.1 | 4.3% ±1.4 | FAIL | FAIL | pass | pass | n/a |
| 7.0 | 500 | 3.1% ±0.6 | 7.3% ±0.7 | 7.28 ±0.27 | 21.7% ±1.0 | 3.46 ±0.18 | 8.9% ±0.3 | 9.53 ±0.15 | 92.4% ±0.5 | 4.5% ±0.8 | pass | FAIL | pass | FAIL | pass |
| 14.0 | 100 | 6.1% ±2.5 | 6.1% ±1.2 | 43.5 ±2.5 | 44.4% ±3.7 | 3.18 ±0.54 | 22.8% ±1.3 | 34.8 ±6.3 | 62.9% ±2.9 | 5.3% ±1.2 | FAIL | FAIL | pass | pass | n/a |
| 14.0 | 200 | 4.8% ±1.6 | 10.6% ±0.9 | 29.6 ±0.86 | 32.8% ±0.9 | 4.65 ±0.43 | 16.1% ±0.9 | 17.4 ±0.92 | 82.2% ±2.3 | 4.9% ±0.7 | FAIL | FAIL | pass | pass | n/a |
| 14.0 | 500 | 3.1% ±0.4 | 12.3% ±1.1 | 11.8 ±0.47 | 18.9% ±0.7 | 5.01 ±0.24 | 8.9% ±0.5 | 9.96 ±0.14 | 91.5% ±0.7 | 5.0% ±0.8 | pass | FAIL | pass | pass | pass |
| 30.0 | 100 | 5.5% ±1.0 | 7.5% ±1.5 | 52.5 ±1.7 | 43.2% ±1.8 | 5.01 ±0.95 | 23.4% ±2.5 | 35.5 ±5.8 | 62.8% ±3.0 | 7.3% ±1.0 | FAIL | FAIL | pass | pass | n/a |
| 30.0 | 200 | 5.2% ±2.2 | 13.7% ±1.1 | 38 ±1.5 | 30.6% ±1.3 | 7.47 ±0.77 | 16.1% ±1.0 | 18.6 ±1.1 | 82.5% ±0.7 | 5.1% ±0.5 | FAIL | FAIL | pass | pass | n/a |
| 30.0 | 500 | 3.4% ±0.3 | 17.5% ±1.5 | 17 ±0.7 | 15.2% ±0.5 | 8.43 ±0.54 | 9.0% ±0.5 | 10.1 ±0.029 | 92.1% ±0.5 | 5.6% ±1.0 | FAIL | FAIL | pass | pass | FAIL |
| 60.0 | 100 | 5.9% ±1.5 | 8.2% ±1.5 | 55.2 ±3.7 | 42.1% ±2.9 | 8.34 ±1.7 | 23.1% ±1.1 | 36 ±5.7 | 65.0% ±3.0 | 5.9% ±0.8 | FAIL | FAIL | pass | pass | n/a |
| 60.0 | 200 | 5.1% ±1.5 | 14.8% ±1.4 | 41.2 ±2.5 | 29.7% ±1.1 | 12.4 ±1.2 | 16.2% ±0.7 | 19 ±0.7 | 81.7% ±2.7 | 5.7% ±0.7 | FAIL | FAIL | pass | pass | n/a |
| 60.0 | 500 | 3.5% ±0.5 | 20.6% ±2.2 | 19.2 ±0.99 | 13.0% ±0.6 | 14.7 ±0.83 | 8.8% ±0.3 | 10.1 ±0.019 | 91.6% ±0.7 | 6.1% ±0.5 | FAIL | FAIL | pass | pass | FAIL |
| 90.0 | 100 | 5.6% ±1.3 | 8.2% ±1.6 | 55.4 ±3 | 42.0% ±1.8 | 11.6 ±1.8 | 22.8% ±1.6 | 35.7 ±5.6 | 67.3% ±3.2 | 6.1% ±2.8 | FAIL | FAIL | pass | pass | n/a |
| 90.0 | 200 | 4.9% ±1.3 | 15.5% ±1.4 | 41.9 ±1.6 | 29.2% ±0.9 | 16.9 ±0.97 | 16.0% ±0.7 | 19.2 ±0.67 | 81.6% ±2.8 | 6.0% ±0.8 | FAIL | FAIL | pass | pass | n/a |
| 90.0 | 500 | 3.5% ±0.3 | 20.9% ±2.3 | 19.6 ±1.2 | 12.7% ±0.6 | 21 ±0.85 | 8.9% ±0.5 | 10.1 ±0.027 | 91.9% ±1.0 | 5.8% ±0.2 | FAIL | FAIL | pass | pass | FAIL |

## live-search-half-life

Kill/rethink check, pass 2: best live-search sets, short avoid decay, 60-week horizon.

| habit | M | soft_half_life_days | N online (peak) | median wait | placed (peak) | hard lockout (peak ticks) | match_rate_p10_over_median | newcomer_within_horizon_share | detect_auc | avoided_pair_rematch_share | soft_broken_per_100_sessions | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| windows | 350 | 7.0 | 24.4 ±1.3 | 5.33 ±0.032 | 100.0% | 1.3% ±0.4 | 96.5% ±0.5 | 47.3% | 0.54 ±0.003 | 22.0% ±0.9 | 4.34 ±0.45 | pass | FAIL | pass | FAIL | pass |
| windows | 350 | 14.0 | 24 ±1 | 5.38 ±0.033 | 100.0% ±0.0 | 1.3% ±0.2 | 96.4% ±0.2 | 45.9% | 0.557 ±0.0052 | 18.6% ±0.7 | 7.38 ±0.55 | pass | FAIL | pass | FAIL | FAIL |
| windows | 500 | 7.0 | 33.2 ±2.2 | 4.59 ±0.34 | 100.0% | 1.0% ±0.2 | 97.7% ±0.2 | 48.8% | 0.536 ±0.0016 | 17.4% ±0.4 | 2.31 ±0.37 | pass | FAIL | pass | FAIL | pass |
| windows | 500 | 14.0 | 33.2 ±2.3 | 4.8 ±0.27 | 100.0% | 0.8% ±0.1 | 97.8% ±0.4 | 48.4% | 0.553 ±0.0012 | 13.9% ±0.5 | 4.12 ±0.43 | pass | pass | pass | FAIL | FAIL |
| generous | 350 | 7.0 | 31.4 ±1.3 | 5.08 ±0.061 | 100.0% | 1.6% ±0.5 | 98.2% ±0.2 | 47.6% | 0.548 ±0.0041 | 25.3% ±0.7 | 4.47 ±0.38 | pass | FAIL | pass | FAIL | pass |
| generous | 350 | 14.0 | 31.4 ±1.3 | 5.18 ±0.055 | 100.0% | 1.6% ±0.5 | 98.2% ±0.3 | 46.4% | 0.571 ±0.0046 | 20.8% ±0.6 | 7.56 ±0.57 | pass | FAIL | pass | FAIL | FAIL |
| generous | 500 | 7.0 | 43 ±2.9 | 3.54 ±0.27 | 100.0% | 1.0% ±0.1 | 99.1% ±0.2 | 49.3% | 0.543 ±0.00077 | 20.4% ±0.5 | 2.26 ±0.26 | pass | pass | pass | FAIL | pass |
| generous | 500 | 14.0 | 43.2 ±2.8 | 3.76 ±0.32 | 100.0% | 1.0% ±0.1 | 99.1% ±0.2 | 47.6% | 0.565 ±0.001 | 16.0% ±0.5 | 3.96 ±0.54 | pass | FAIL | pass | FAIL | FAIL |

## Live hard-block lockout by waiting pool N and lobby size L

| L | N waiting | peak samples | share with someone hard-locked |
|---|---|---|---|
| 3 | 2-4 | 47191 | 2.32% |
| 3 | 5-7 | 93 | 0.00% |
| 4 | 2-4 | 9966655 | 2.61% |
| 4 | 5-7 | 389522 | 7.20% |
| 4 | 8-10 | 1995 | 2.51% |
| 4 | 11-15 | 3 | 0.00% |
| 5 | 2-4 | 100314 | 0.14% |
| 5 | 5-7 | 9873 | 29.79% |
| 5 | 8-10 | 64 | 1.56% |
