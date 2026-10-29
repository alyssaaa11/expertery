# First-test report

Decision (PLAN.md section 7): **decision: see experiments/bmax/PLAN.md**
Run valid: True
Calls: 169  Skipped by budget guard: 11  (budget $3.0, stopped: True; arm-C budget $3.0, stopped: False)

## Cost estimate
- Arm B2: $1.2980
- Arm BX: $2.1181
- Total: $4.4486
Each arm ran alone on the GPU; per-arm cost is its own wall-clock at $2.50/h (A100-80GB Modal rate). The estimate covers only the runner's own wall-clock; the real Modal cost (incl. cold start) comes from `modal billing report`.

## Per arm (PASS / FAIL / INVALID, pass rate, INVALID rate)
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| B2 | 79 | 11 | 0 | 87.8% | 0.0% |
| BX | 75 | 4 | 0 | 94.9% | 0.0% |

## Cost and speed (all arms)
| Arm | mean calls/job | mean tokens/job | mean latency/job (s) | tokens/correct | latency/correct (s) | in tokens | out tokens | calls | wall (s) | $/correct | pass@3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 | 3.00 | 28077.27 | 451.43 | 10662.25 | 171.43 | 510147 | 332171 | 90 | 1869.13 | 0.02 | 96.7% |
| BX | 6.00 | 59205.26 | 819.21 | 21313.89 | 294.92 | 1057543 | 540999 | 162 | 3050.11 | 0.03 | 100.0% |

## Level hard
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| B2 | 34 | 11 | 0 | 75.6% | 0.0% |
| BX | 31 | 3 | 0 | 91.2% | 0.0% |

## Level medium
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| B2 | 45 | 0 | 0 | 100.0% | 0.0% |
| BX | 44 | 1 | 0 | 97.8% | 0.0% |

## Per-job outcomes
(k = 3: one outcome per sample)
| Job | B2 | BX |
|---|---|---|
| H1 | PASS,PASS,PASS | PASS,PASS,PASS |
| H10 | PASS,PASS,FAIL | PASS,PASS,PASS |
| H11 | FAIL,PASS,FAIL | PASS,PASS,PASS |
| H12 | FAIL,PASS,PASS | PASS |
| H13 | FAIL,FAIL,FAIL | - |
| H14 | PASS,PASS,PASS | - |
| H15 | PASS,PASS,PASS | - |
| H2 | PASS,PASS,PASS | PASS,PASS,PASS |
| H3 | FAIL,PASS,PASS | PASS,PASS,PASS |
| H4 | PASS,PASS,PASS | FAIL,PASS,PASS |
| H5 | PASS,FAIL,PASS | PASS,PASS,PASS |
| H6 | PASS,FAIL,PASS | PASS,PASS,PASS |
| H7 | PASS,PASS,PASS | FAIL,PASS,FAIL |
| H8 | PASS,PASS,PASS | PASS,PASS,PASS |
| H9 | FAIL,PASS,PASS | PASS,PASS,PASS |
| M1 | PASS,PASS,PASS | PASS,PASS,PASS |
| M10 | PASS,PASS,PASS | PASS,PASS,PASS |
| M11 | PASS,PASS,PASS | PASS,PASS,PASS |
| M12 | PASS,PASS,PASS | PASS,PASS,PASS |
| M13 | PASS,PASS,PASS | PASS,PASS,FAIL |
| M14 | PASS,PASS,PASS | PASS,PASS,PASS |
| M15 | PASS,PASS,PASS | PASS,PASS,PASS |
| M2 | PASS,PASS,PASS | PASS,PASS,PASS |
| M3 | PASS,PASS,PASS | PASS,PASS,PASS |
| M4 | PASS,PASS,PASS | PASS,PASS,PASS |
| M5 | PASS,PASS,PASS | PASS,PASS,PASS |
| M6 | PASS,PASS,PASS | PASS,PASS,PASS |
| M7 | PASS,PASS,PASS | PASS,PASS,PASS |
| M8 | PASS,PASS,PASS | PASS,PASS,PASS |
| M9 | PASS,PASS,PASS | PASS,PASS,PASS |
