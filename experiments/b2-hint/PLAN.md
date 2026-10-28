# B2: does one hint sentence close the gap? (plan, written before any run)

Status: FROZEN 2026-10-28 after verifier GO (2cea384) + the best-of clarification; user asked for the run. User asked for "another experiment so we can build the factory". Frozen once the verifier says
GO. No changes during the run.

## Question
3 of Glimmer + manual's 10 first-test failures were position-only (right shape, wrong place). Does one general hint
about placing parts at the given coordinates fix that without training? This is the cheap-fix baseline (lesson: run the
cheapest fix before building), and it sets the bar the trained Glimmer must beat.

## Arms (Glimmer only; same session, same GPU)
| Arm | Prompt |
|---|---|
| B′ (B-repeat; `BR` in the code) | exactly arm B of the first test: system message + manual + job |
| B2 | the same, plus the hint below appended to the system message |
- Same 30 jobs (15 medium + 15 hard), same manual.md, same settings (max_tokens 16,000, temperature 1.0, top_p 0.95,
  top_k 64), one try per job, fresh conversation. Arm C is not re-run: Spark Open scored 30/30 in the first test.
- Why B′: at temperature 1.0, one run of B (67%) has luck in it. B2 is compared with B′ from the same session.

## The hint (exact words, general, nothing job-specific)
> Place the part exactly at the coordinates given in the job. CadQuery centres boxes, cylinders and many 2D shapes on the workplane origin by default, so check where each shape ends up and move it so that every face is exactly where the job says.
- Revised before freezing: an earlier draft advised `centered=(False, False, False)`, which would push round parts off
  their axis, so the hint now only says to check and move.

## Scoring
The same runner and checks.py as the first test: PASS / FAIL / INVALID, pass rate = PASS ÷ (PASS + FAIL) in whole
points. Also report, for every FAIL, whether it is position-only (shift to the reference bounding box; mismatch ≤ 0.2%)
or a wrong shape.

## Decision rules (first match wins; C = 100% from the first test)
1. INVALID > 5% in either arm → run not valid (report it; no re-run without a new approval).
Let **best = max(B′, B2)** (revised before freezing after the verifier's B2 check: either cheap version reaching the bar
means training on plain CadQuery is not needed; luck alone can give B2 24/30 in 8–16% of runs).
2. best ≥ 80% → **a cheap prompt closes most of the gap: do not build the factory on plain CadQuery.** Next: discuss the
   "private company tool" version (AcmeCAD) or STOP.
3. best ≤ 75% → **build the factory on CadQuery.** The bar for the trained Glimmer = max(B′, B2, first-test B).
4. best 76–79% (i.e. 23/30) → grey zone: decide with the user from the data.
- Attribution: say "the hint helped" only if B2 beats B′ on the paired jobs (jobs where only one passed); otherwise the
  difference may be luck. Also reported: position-only failures remaining in each arm.

## Budget
Modal only: one deploy (weights already cached), 60 Glimmer calls, ~20 min of A100 → **~$0.60–0.90**. Abort at $3
(runner --budget). Spent before: ≈ $3.6 of $30.

## Who builds what
- This plan and the hint: Claude (planning). The runner change (arms B′/B2, `--arms`, hint) and position-only analysis
  script: **Muse Code**, from SPEC.md. Verifier check before the paid run.
