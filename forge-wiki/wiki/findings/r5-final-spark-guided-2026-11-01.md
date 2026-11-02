# R5 final: dev test of r5, Spark hints, tutoring lessons (2026-11-01)

**Summary**: The r5 model (trained on Glimmer's own referee-checked answers) solves 94/100 held-out R5D jobs with no
card (plain 62, plain + card 96). Spark Open hints then rescued 52 of 54 jobs Glimmer could not solve; those become 46
tutoring lessons in the final training r5f (running).

## 1. Dev test of r5 (verified: results/r5-dev-ft-2026-11-01, compare_dev.json, commit 49b69d8)
| Arm (100 R5D jobs, k=1, 0.2%) | Pass | Crashes | Completion tokens / correct |
|---|---|---|---|
| A, plain Glimmer, no card | 62 | 12 | 7,637 |
| **FT r5, no card** | **94** | 2 | 3,596 |
| A + card v2 | 96 | 0 | 3,580 |
- Paired bootstrap: FT−A +32 [22, 42]; FT−(A+card) −2 [−8, 3]. Reading: beats plain ✓, as good as card ✓, cheaper ✗.
- Command: verifier report forge-r5-dev-pre-2026-11-01 (FT line); 16 workers; served root /vol/r5/merged checked.

## 2. Spark hints (verified: results/r5-hints-2026-11-01)
- Input: the 76 R5T jobs still failing after self-fix; first-try code + failed checks; crash rows get the last error line.
- First try at max_tokens 1,000: 74/76 empty (Spark reasons first) — **how learned**: verifier predicted it from R3's
  median 5,419 reasoning tokens; hints.jsonl had empty text; fixed by 16,000 + storing finish_reason (check: count
  finish_reason == "length").
- Final: 54 usable, 22 cut at 16k (F4 11, F8 9, F3 2), $2.67. Hints are short and specific (e.g. "your slot runs Z −1
  to 4.2 instead of 0 to 3.2").
- Verifier finding: 32 of 76 leftovers were near-misses caused by card v2's own "cutter 1 mm longer" rule. Card v3 (one
  line: extend only past outside faces) used for retries only (user decision).

## 3. Hinted retries (verified: results/r5-hints-2026-11-01/retry)
- Base Glimmer + card v3 + "Hint from a tutor: …", k=3: 135/162 PASS, **52/54 jobs**; F8 4/6, others all.
- All 52 first PASSes cite the hint (~6× per answer) → M7 would drop all. decision (user): keep the hint in the lesson
  (tutoring rows). 46 kept after the card-naming filter.

## 4. Final training r5f (verified: results/train-r5f/train.json, merge.json, commit 96945e8)
- Mix 1,742 rows, sha fbd62681; exam guard 1,742 kept / 0 refused (≈ 2.5 h of one-sandbox-per-row checks, before training).
- Trained 1,722 rows (first 1,668, self-fix 12, tutoring 42; 20 dropped for length), 431 optimizer steps, loss 0.63 →
  0.32, peak 76.5 GB, 6,993 s; merged /vol/r5f/merged (151 s). Cost ≈ $10-11 (estimate $9.71 + guard).
- Pre-registered exam pick in experiments/r5/PLAN.md (end). Dev 2 not run yet (waits for the user's start).
- Lesson (how learned): my 2-hour estimate ignored the exam guard; the verifier had flagged "≈ 2-3 h" (forge-r5-train-pre
  N1). Check: read train.log for EXAM_GUARD before quoting an end time.

## Lessons (how learned)
- A reasoning teacher needs a large max_tokens even for a 60-word reply; always store finish_reason (seen: 74/76 empty).
- Retry answers cite the help they got; plan the training format for that BEFORE paying (seen: M7 dropped 52/52).
  Check: grep the reasoning for the help's keywords on the first 3 retries.
- Two Modal sessions that rewrite the same secret must not overlap (verifier, run_*_session.sh:72).
