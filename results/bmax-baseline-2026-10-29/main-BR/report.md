# First-test report

Decision (PLAN.md section 7): **decision: see experiments/bmax/PLAN.md**
Run valid: True
Calls: 30  Skipped by budget guard: 0  (budget $3.0, stopped: False; arm-C budget $3.0, stopped: False)

## Cost estimate
- Arm BR: $0.6034
- Total: $1.0315
Each arm ran alone on the GPU; per-arm cost is its own wall-clock at $2.50/h (A100-80GB Modal rate). The estimate covers only the runner's own wall-clock; the real Modal cost (incl. cold start) comes from `modal billing report`.

## Per arm (PASS / FAIL / INVALID, pass rate, INVALID rate)
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| BR | 26 | 4 | 0 | 86.7% | 0.0% |

## Cost and speed (all arms)
| Arm | mean calls/job | mean tokens/job | mean latency/job (s) | tokens/correct | latency/correct (s) | in tokens | out tokens | calls | wall (s) | $/correct | pass@1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 1.00 | 9571.77 | 159.64 | 11044.35 | 184.20 | 168459 | 118694 | 30 | 868.82 | 0.02 | 86.7% |

## Level hard
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| BR | 13 | 2 | 0 | 86.7% | 0.0% |

## Level medium
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| BR | 13 | 2 | 0 | 86.7% | 0.0% |

## Per-job outcomes
| Job | BR |
|---|---|
| H1 | PASS |
| H10 | PASS |
| H11 | PASS |
| H12 | PASS |
| H13 | PASS |
| H14 | PASS |
| H15 | PASS |
| H2 | FAIL |
| H3 | PASS |
| H4 | PASS |
| H5 | PASS |
| H6 | FAIL |
| H7 | PASS |
| H8 | PASS |
| H9 | PASS |
| M1 | PASS |
| M10 | PASS |
| M11 | PASS |
| M12 | FAIL |
| M13 | PASS |
| M14 | FAIL |
| M15 | PASS |
| M2 | PASS |
| M3 | PASS |
| M4 | PASS |
| M5 | PASS |
| M6 | PASS |
| M7 | PASS |
| M8 | PASS |
| M9 | PASS |
