# Keel v2 baseline: NO ROOM (Oct 28)

**Summary**: On the private tool Keel 2.1 (fictional Quillon Orbital Works), with the company manual in the prompt,
Glimmer already scores 97.8% and Spark Open 100%. The pre-registered rule says **NO ROOM**: training cannot show much
on this tool. A private tool alone does not create a gap when its whole manual fits in the prompt.

**Sources**: `results/keel-v2-main/` (report.md, summary.json, calls.jsonl, breps/), `results/keel-v2-main.log`,
plan `experiments/keel-exam-v2/PLAN.md` (frozen, sha256), verifier GO `~/agents/verifier/reports/forge-keel-v2-exam-2026-10-28.md`.

**Last updated**: 2026-10-28

---

## Result (verified, results/keel-v2-main/report.md)
| Arm | Mean pass rate (90 answers) | pass@3 | medium / hard pass@3 |
|---|---|---|---|
| B Glimmer + manual | **97.8%** (88/90) | 100% | 100% / 100% |
| C Spark Open + manual | **100%** (90/90) | 100% | 100% / 100% |
- Decision by the frozen rules: rule 0 no (0 INVALID), rule 1 no (C pass@3 100%), **rule 2 NO ROOM (B 98% ≥ 80%)**.
- C − B = 2.2 points, bootstrap 95% CI [0.0, 6.7]; McNemar sample 1 p = 1.0.
- Glimmer's only 2 failures: M1 samples 1 and 3, `p.pattern(2, 1, 0, 20)` instead of `(1, 2, 0, 20)` (second hole on
  top of the first). Real model mistakes, not harness errors.
- verified clean: 0 records with PermissionError or a harness error (grep of calls.jsonl, case-sensitive; the
  case-insensitive hits were the mount name HARNESS-P2). App stopped (`modal app list` 23:29: stopped).
- Pilot before it: 3/3 PASS (results/keel-v2-pilot), $0.03.

## Cost (verified where marked)
- Run time: Glimmer cold start 4 min 16 s, 180 answers in 523 s.
- Modal: `modal billing summary` metered $2.22 for the whole period so far (≈ $0.55 for this run), billed $0.00
  (credits). Baseten ≈ $0.97 (runner token estimate) + pilot $0.03.
- Total project ≈ $9.8 of $30 (Meta/Muse Code ≈ $5.7, Modal $2.22, Baseten ≈ $1.85).

## What it means (hypothesis until tested)
- In the first test (CadQuery, public) Glimmer + manual scored 67% vs 100%. The gap there came from geometry and
  position work in a large, general API, not from the tool being unknown.
- Keel is small and regular (~3.5k-token manual, few calls, explicit rules). A 30B model follows a short, complete
  manual almost perfectly. The traps (materials, flight class, FRM centre datum, mirror) did not trip it.
- So "private" is not what makes a gap. Candidates that might: a manual too big to put in every prompt, company
  knowledge that lives only in past designs (not written down), or long multi-step work.
