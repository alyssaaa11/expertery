# First test (Oct 28): is Forge needed? Result: grey zone with a large, real gap

**Summary**: 30 CadQuery jobs (15 medium, 15 hard), 3 contestants, one try each. Spark Open + manual passed **30/30**,
Glimmer + manual **20/30 (67%)**, Glimmer alone **16/30 (53%)**. The pre-registered rule gives **grey zone**: the gap is
33 points (GO needs ≥ 25), but Glimmer + manual is above the 60% GO ceiling. On the 10 jobs where B and C differ, C wins
all 10 (exact McNemar p = 0.002), so the gap is real. The decision goes to the user (grey zone = decide from the data,
no re-runs).

**Sources**: `~/projects/forge/results/first-test-main/` (report.md, summary.json, calls.jsonl); run log
`results/first-test-main.log`; plan `experiments/first-test/PLAN.md` at 78990b1; verifier pre-run audit + re-check GO
(`~/agents/verifier/reports/forge-2026-10-28.md`); `modal billing summary` (2026-10-28 ~18:45).

**Last updated**: 2026-10-28

---

## Results (verified, report.md)
| Arm | All 30 | Medium 15 | Hard 15 | INVALID |
|---|---|---|---|---|
| A Glimmer, no manual | 16 (53%) | 10 (67%) | 6 (40%) | 0 |
| B Glimmer + manual | 20 (67%) | 11 (73%) | 9 (60%) | 0 |
| C Spark Open + manual | **30 (100%)** | 15 | 15 | 0 |
- Decision (PLAN §7, applied by runner.compute_decision): **grey zone**. Rule 3 (GO) needs B ≤ 60, C ≥ 30 and C − B ≥ 25;
  B = 67 fails only the first part.
- Paired B vs C: C-only passes 10, B-only 0 → exact McNemar p = 0.0020 (computed from calls.jsonl).
- The manual helps Glimmer a little: A → B +4 jobs (+13 points).
- B's 10 failures: 1 code error (`NameError: Workplane`), 9 wrong geometry (several ~100% mismatch: parts misplaced or
  missing features; H2 and H7 small misses at 4.8% and 2.0%; H13 a countersink error at 1.8%).
- Answer length: max output A 9,352, B 8,196, C 12,768 tokens; one answer per arm went over 8,000, so the verifier's
  max_tokens raise (8,000 → 16,000) prevented 3 INVALIDs. Glimmer max 410 s per call (under Modal's ~750 s cap); Spark
  Open max 49 s.

## Cost (verified where marked)
- Modal: metered $1.65 for the day (`modal billing summary`), $0.99 before this run → **~$0.66 for the main run**
  (app 18:21:34–18:41:46, stopped and checked).
- Baseten (arm C): runner estimate **$0.78** (token usage × $1.25/$4.25 per M). Not yet visible on the dashboard.
- **Forge total so far ≈ $3.5 of $30** (Modal $1.65, Meta ~$1.02 for two Muse Code sessions, Baseten ~$0.85).

## What it means (hypothesis)
- The teacher works: Spark Open solved every job, so it can produce correct training examples reliably.
- There is a real gap (10 jobs, p = 0.002), concentrated in hard jobs (B 60% vs C 100%).
- But Glimmer + manual already solves two thirds, so the headroom is 33 points, and "the student beats the teacher"
  is impossible against a 100% teacher. The pitch would become "a small offline model that nearly matches the big one".
- Options for the user: GO (accept the grey zone because the gap is large and significant); GO focused on hard jobs
  (note: choosing a subset after seeing the data is post-hoc); or STOP and keep ~$26 for another project.
