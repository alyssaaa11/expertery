# First-test report

Decision (PLAN.md section 7): **STOP (manual is enough)**
Run valid: True
Calls: 9  Skipped by budget guard: 0  (budget $5.0, stopped: False)

## Cost estimate
- Arm A: $0.0626
- Arm B: $0.0626
- Arm C: $0.0610
- Total: $0.1862

## Per arm (PASS / FAIL / INVALID, pass rate, INVALID rate)
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| A | 2 | 1 | 0 | 66.7% | 0.0% |
| B | 3 | 0 | 0 | 100.0% | 0.0% |
| C | 3 | 0 | 0 | 100.0% | 0.0% |

## Level dry
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| A | 2 | 1 | 0 | 66.7% | 0.0% |
| B | 3 | 0 | 0 | 100.0% | 0.0% |
| C | 3 | 0 | 0 | 100.0% | 0.0% |

## Per-job outcomes
| Job | A | B | C |
|---|---|---|---|
| D1 | PASS | PASS | PASS |
| D2 | PASS | PASS | PASS |
| D3 | FAIL | PASS | PASS |
