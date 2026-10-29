# FreeCAD gap-test report

Teacher T = S ∪ W-rescues per job (S INVALID jobs are never escalated).
Decision on T: **INVALID (no scored calls)**
Decision on S alone: **INVALID (no scored calls)**
Report decision: **INVALID (no scored calls)**
Governing rule: PLAN rule 5: disagreement → stay on CadQuery
Wonder's share of T's passes: 0.0%
Rates: G 0.0%, T 0.0%, S 0.0%

## Per arm (PASS / FAIL / INVALID, pass rate)
Pass rates are PASS / (PASS + FAIL); INVALID and harness are counted, never folded in.
| Arm | PASS | FAIL | INVALID | pass rate | api_error | wrong_geometry | harness |
|---|---|---|---|---|---|---|---|
| W | 0 | 0 | 0 | n/a | 0 | 0 | 0 |

Jobs passed by S but not G: -
Tokens/cost: {"S_tokens": 0, "W_tokens": 0, "gpu": 0.0, "total": 0.0}

Honest caveat: FreeCAD's Part API has no counterbore/slot/polar-pattern helpers (CadQuery has them), so part of a G-vs-S gap measures that the tool is harder to use, which is exactly the kind of difficulty a company tool has.

## Per-job outcomes
| Job | W |
|---|---|
