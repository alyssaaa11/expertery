# Thinking-jobs gap-test report

Teacher T = S ∪ W-rescues per (job, rep) sample.
The decision rates PASS/FAIL at 1e-6 (`tight`).
Decision on T: **no gap: next test = same jobs without the standard**
Decision on S alone: **no gap: next test = same jobs without the standard**
Report decision: **no gap: next test = same jobs without the standard**
Wonder's share of T's passes: 0.0%
Rates: G 93.3%, T 100.0%, S 100.0%
Win jobs (X >= 2/3, G <= 1/3): S 0, T 0

## Accuracy (tight 1e-6: the decision)
| Arm | PASS | FAIL | INVALID | pass rate |
|---|---|---|---|---|
| G | 14 | 1 | 0 | 93.3% |
| S | 15 | 0 | 0 | 100.0% |

## 0.2% (for reference, not the decision)
| Arm | PASS | FAIL | INVALID | pass rate |
|---|---|---|---|---|
| G | 15 | 0 | 0 | 100.0% |
| S | 15 | 0 | 0 | 100.0% |

## Speed and cost per answer
Wall time is request sent to response received, per answer.
| Arm | answers | median s | mean s | mean in | mean cached | mean out | $ / answer | answers / $ |
|---|---|---|---|---|---|---|---|---|
| G | 15 | 167.48 | 178.52 | 8189 | 0 | 4267 | n/a | n/a |
| S | 15 | 17.74 | 19.43 | 8307 | 0 | 3438 | $0.0250 | 40.0 |
Ratios: time G÷S 9.19, S÷G 0.11; $ G÷S n/a, S÷G n/a (n/a: Glimmer calls are not metered).
