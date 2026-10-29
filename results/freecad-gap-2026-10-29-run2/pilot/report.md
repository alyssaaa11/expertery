# FreeCAD gap-test report

Teacher T = S ∪ W-rescues per job (S INVALID jobs are never escalated).
Decision on T: **stay on hard CadQuery jobs**
Decision on S alone: **stay on hard CadQuery jobs**
Report decision: **stay on hard CadQuery jobs**
Governing rule: PLAN rule 5: disagreement → stay on CadQuery
Wonder's share of T's passes: 0.0%
Rates: G 100.0%, T 100.0%, S 100.0%

## Per arm (PASS / FAIL / INVALID, pass rate)
Pass rates are PASS / (PASS + FAIL); INVALID and harness are counted, never folded in.
| Arm | PASS | FAIL | INVALID | pass rate | api_error | wrong_geometry | harness |
|---|---|---|---|---|---|---|---|
| G | 3 | 0 | 0 | 100.0% | 0 | 0 | 0 |
| S | 3 | 0 | 0 | 100.0% | 0 | 0 | 0 |

Jobs passed by S but not G: -
Tokens/cost: {"S_tokens": 0.0447, "W_tokens": 0, "gpu": 0.1616, "total": 0.2063}

Honest caveat: FreeCAD's Part API has no counterbore/slot/polar-pattern helpers (CadQuery has them), so part of a G-vs-S gap measures that the tool is harder to use, which is exactly the kind of difficulty a company tool has.

## Per-job outcomes
| Job | G | S |
|---|---|---|
| D1 | PASS | PASS |
| D2 | PASS | PASS |
| D3 | PASS | PASS |
