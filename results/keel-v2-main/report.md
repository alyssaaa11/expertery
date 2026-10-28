# Keel v2 baseline report

Mode: main
Decision (PLAN.md 4): **NO ROOM: arm B scores 98% (>= 80%): Glimmer + manual is already good**
Run valid: True
Calls: 180  Skipped by caps: 0  (modal budget $2.5, baseten budget $4.0, glimmer limit 60 min; stopped by: none)

## Cost estimate
- Modal (Glimmer arm): $0.5429
- Baseten (arm C): $0.9741
- Total: $1.5170
Modal estimate covers wall-clock since deploy start (incl. cold start); confirm with `modal billing summary`.

## Per arm (score = mean pass rate over complete samples %, PLAN.md 4/5)
| Arm | Score % | complete samples | PASS | FAIL | INVALID | NOT RUN | INVALID rate | stopped by |
|---|---|---|---|---|---|---|---|---|
| B | 97.8% | 1,2,3 | 88 | 2 | 0 | 0 | 0.0% | none |
| C | 100.0% | 1,2,3 | 90 | 0 | 0 | 0 | 0.0% | none |

## Rule 1 (STOP on C pass@k < 30 whole points, PLAN.md 4)
- C mean pass rate: 100.0% (k=3)
- C pass@k overall: 100.0% (k=3)
- C pass@k medium (M*): 100.0%; hard (H*): 100.0%
- EASY-ONLY: no
- B pass@k (informational) overall: 100.0% (k=3); medium: 100.0%; hard: 100.0%

## pass@1 per sample (%)
| Arm | sample 1 | sample 2 | sample 3 |
|---|---|---|---|
| B | 96.7% | 100.0% | 96.7% |
| C | 100.0% | 100.0% | 100.0% |

## Per-job passes in complete samples (passes/scored samples)
| Job | B | C |
|---|---|---|
| H1 | 3/3 | 3/3 |
| H10 | 3/3 | 3/3 |
| H11 | 3/3 | 3/3 |
| H12 | 3/3 | 3/3 |
| H13 | 3/3 | 3/3 |
| H14 | 3/3 | 3/3 |
| H15 | 3/3 | 3/3 |
| H2 | 3/3 | 3/3 |
| H3 | 3/3 | 3/3 |
| H4 | 3/3 | 3/3 |
| H5 | 3/3 | 3/3 |
| H6 | 3/3 | 3/3 |
| H7 | 3/3 | 3/3 |
| H8 | 3/3 | 3/3 |
| H9 | 3/3 | 3/3 |
| M1 | 1/3 | 3/3 |
| M10 | 3/3 | 3/3 |
| M11 | 3/3 | 3/3 |
| M12 | 3/3 | 3/3 |
| M13 | 3/3 | 3/3 |
| M14 | 3/3 | 3/3 |
| M15 | 3/3 | 3/3 |
| M2 | 3/3 | 3/3 |
| M3 | 3/3 | 3/3 |
| M4 | 3/3 | 3/3 |
| M5 | 3/3 | 3/3 |
| M6 | 3/3 | 3/3 |
| M7 | 3/3 | 3/3 |
| M8 | 3/3 | 3/3 |
| M9 | 3/3 | 3/3 |

## C − B (paired bootstrap over jobs, 10000 resamples, seed 0)
- Observed C − B: 2.2 points
- 95% CI: [0.0, 6.7]

## McNemar on sample 1 (informational)
- Paired jobs: 30; C-only passes: 1; B-only passes: 0; both pass: 29; neither: 0
- Exact two-sided p-value: 1.0
