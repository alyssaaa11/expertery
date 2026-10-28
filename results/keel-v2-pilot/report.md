# Keel v2 baseline report

Mode: pilot
Decision (PLAN.md 4): **GREY: pilot run, no decision (see PLAN.md 4d)**
Run valid: True
Pilot passed: True
Calls: 3  Skipped by caps: 0  (modal budget $2.5, baseten budget $4.0, glimmer limit 60 min; stopped by: none)

## Cost estimate
- Modal (Glimmer arm): $0.0072
- Baseten (arm C): $0.0291
- Total: $0.0362
Modal estimate covers wall-clock since deploy start (incl. cold start); confirm with `modal billing summary`.

## Per arm (score = mean pass rate over complete samples %, PLAN.md 4/5)
| Arm | Score % | complete samples | PASS | FAIL | INVALID | NOT RUN | INVALID rate | stopped by |
|---|---|---|---|---|---|---|---|---|
| C | 100.0% | 1 | 3 | 0 | 0 | 0 | 0.0% | none |

## Rule 1 (STOP on C pass@k < 30 whole points, PLAN.md 4)
- C mean pass rate: 100.0% (k=1)
- C pass@k overall: 100.0% (k=1)
- C pass@k medium (M*): 100.0%; hard (H*): 100.0%
- EASY-ONLY: no

## pass@1 per sample (%)
| Arm | sample 1 |
|---|---|
| C | 100.0% |

## Per-job passes in complete samples (passes/scored samples)
| Job | C |
|---|---|
| H9 | 1/1 |
| M1 | 1/1 |
| M7 | 1/1 |

## C − B (paired bootstrap over jobs, 10000 resamples, seed 0)
- n/a (needs both arms B and C)

## McNemar on sample 1 (informational)
- Paired jobs: 0; C-only passes: 0; B-only passes: 0; both pass: 0; neither: 0
- Exact two-sided p-value: 1.0
