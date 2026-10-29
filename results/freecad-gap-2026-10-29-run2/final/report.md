# FreeCAD gap-test report

Teacher T = S ∪ W-rescues per job (S INVALID jobs are never escalated).
Decision on T: **stay on hard CadQuery jobs**
Decision on S alone: **stay on hard CadQuery jobs**
Report decision: **stay on hard CadQuery jobs**
Governing rule: PLAN rule 5: disagreement → stay on CadQuery
Wonder's share of T's passes: 0.0%
Rates: G 93.3%, T 100.0%, S 100.0%

## Per arm (PASS / FAIL / INVALID, pass rate)
Pass rates are PASS / (PASS + FAIL); INVALID and harness are counted, never folded in.
| Arm | PASS | FAIL | INVALID | pass rate | api_error | wrong_geometry | harness |
|---|---|---|---|---|---|---|---|
| G | 28 | 2 | 0 | 93.3% | 2 | 0 | 0 |
| S | 30 | 0 | 0 | 100.0% | 0 | 0 | 0 |

Jobs passed by S but not G: H10, M12
Tokens/cost: {"S_tokens": 0, "W_tokens": 0, "gpu": 0.0, "total": 0.0}

Honest caveat: FreeCAD's Part API has no counterbore/slot/polar-pattern helpers (CadQuery has them), so part of a G-vs-S gap measures that the tool is harder to use, which is exactly the kind of difficulty a company tool has.

## Per-job outcomes
| Job | G | S |
|---|---|---|
| H1 | PASS | PASS |
| H10 | FAIL | PASS |
| H11 | PASS | PASS |
| H12 | PASS | PASS |
| H13 | PASS | PASS |
| H14 | PASS | PASS |
| H15 | PASS | PASS |
| H2 | PASS | PASS |
| H3 | PASS | PASS |
| H4 | PASS | PASS |
| H5 | PASS | PASS |
| H6 | PASS | PASS |
| H7 | PASS | PASS |
| H8 | PASS | PASS |
| H9 | PASS | PASS |
| M1 | PASS | PASS |
| M10 | PASS | PASS |
| M11 | PASS | PASS |
| M12 | FAIL | PASS |
| M13 | PASS | PASS |
| M14 | PASS | PASS |
| M15 | PASS | PASS |
| M2 | PASS | PASS |
| M3 | PASS | PASS |
| M4 | PASS | PASS |
| M5 | PASS | PASS |
| M6 | PASS | PASS |
| M7 | PASS | PASS |
| M8 | PASS | PASS |
| M9 | PASS | PASS |
