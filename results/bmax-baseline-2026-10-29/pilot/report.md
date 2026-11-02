# First-test report

Decision (PLAN.md section 7): **decision: see experiments/bmax/PLAN.md**
Run valid: True
Calls: 6  Skipped by budget guard: 0  (budget $3.0, stopped: False; arm-C budget $3.0, stopped: False)

## Cost estimate
- Arm BR: $0.1218
- Arm BX: $0.1379
- Total: $0.4060
Each arm ran alone on the GPU; per-arm cost is its own wall-clock at $2.50/h (A100-80GB Modal rate). The estimate covers only the runner's own wall-clock; the real Modal cost (incl. cold start) comes from `modal billing report`.

## Per arm (PASS / FAIL / INVALID, pass rate, INVALID rate)
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| BR | 3 | 0 | 0 | 100.0% | 0.0% |
| BX | 3 | 0 | 0 | 100.0% | 0.0% |

## Cost and speed (all arms)
| Arm | mean calls/job | mean tokens/job | mean latency/job (s) | tokens/correct | latency/correct (s) | in tokens | out tokens | calls | wall (s) | $/correct | pass@1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BR | 1.00 | 8339.67 | 106.40 | 8339.67 | 106.40 | 16731 | 8288 | 3 | 175.33 | 0.04 | 100.0% |
| BX | 2.00 | 16180.00 | 123.17 | 16180.00 | 123.17 | 38899 | 9641 | 6 | 198.54 | 0.05 | 100.0% |

## Level dry
| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |
|---|---|---|---|---|---|
| BR | 3 | 0 | 0 | 100.0% | 0.0% |
| BX | 3 | 0 | 0 | 100.0% | 0.0% |

## Per-job outcomes
| Job | BR | BX |
|---|---|---|
| D1 | PASS | PASS |
| D2 | PASS | PASS |
| D3 | PASS | PASS |
