# First-test report

Decision (PLAN.md section 7): **grey zone**
Run valid: True
Calls: 90  Skipped by budget guard: 0  (budget $5.0, stopped: False; arm-C budget $3.0, stopped: False)

## Cost estimate
- Arm A: $0.4206
- Arm B: $0.4206
- Arm C: $0.7785
- Total: $1.6197
GPU estimate covers only the runner's own wall-clock; the real Modal cost (incl. cold start) comes from `modal billing report`.

## Per arm (PASS / FAIL / INVALID, pass rate, INVALID rate)
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| A | 16 | 14 | 0 | 53.3% | 0.0% |
| B | 20 | 10 | 0 | 66.7% | 0.0% |
| C | 30 | 0 | 0 | 100.0% | 0.0% |

## Level hard
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| A | 6 | 9 | 0 | 40.0% | 0.0% |
| B | 9 | 6 | 0 | 60.0% | 0.0% |
| C | 15 | 0 | 0 | 100.0% | 0.0% |

## Level medium
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| A | 10 | 5 | 0 | 66.7% | 0.0% |
| B | 11 | 4 | 0 | 73.3% | 0.0% |
| C | 15 | 0 | 0 | 100.0% | 0.0% |

## Per-job outcomes
| Job | A | B | C |
|---|---|---|---|
| H1 | FAIL | FAIL | PASS |
| H10 | PASS | PASS | PASS |
| H11 | FAIL | PASS | PASS |
| H12 | PASS | PASS | PASS |
| H13 | FAIL | FAIL | PASS |
| H14 | FAIL | PASS | PASS |
| H15 | FAIL | FAIL | PASS |
| H2 | FAIL | FAIL | PASS |
| H3 | PASS | PASS | PASS |
| H4 | PASS | PASS | PASS |
| H5 | FAIL | PASS | PASS |
| H6 | PASS | FAIL | PASS |
| H7 | FAIL | FAIL | PASS |
| H8 | FAIL | PASS | PASS |
| H9 | PASS | PASS | PASS |
| M1 | PASS | PASS | PASS |
| M10 | FAIL | FAIL | PASS |
| M11 | FAIL | PASS | PASS |
| M12 | FAIL | FAIL | PASS |
| M13 | FAIL | PASS | PASS |
| M14 | FAIL | PASS | PASS |
| M15 | PASS | PASS | PASS |
| M2 | PASS | PASS | PASS |
| M3 | PASS | FAIL | PASS |
| M4 | PASS | PASS | PASS |
| M5 | PASS | FAIL | PASS |
| M6 | PASS | PASS | PASS |
| M7 | PASS | PASS | PASS |
| M8 | PASS | PASS | PASS |
| M9 | PASS | PASS | PASS |
