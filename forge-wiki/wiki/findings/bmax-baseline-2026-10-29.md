# Step-2 baseline: Glimmer without training (plain, hint 1 try, all fair fixes), 2026-10-29

**Summary**: verified (results/bmax-baseline-2026-10-29/*/summary.json). On the 30 held-out CadQuery jobs: plain
Glimmer **87%** (26/30, 1 answer per job), Glimmer + hint, 1 try **88%** (79/90, 3 answers per job), Glimmer + all fair
fixes (B-max) **95%** (75/79 answers; 11 hard-job answers not run because of the cap). Stop rule (B2 ≥ 90%) not
triggered (88%), so the bar for the trained Glimmer is set. But medium jobs are saturated (B2 100%); only the hard jobs
leave room (B2 76%, B-max 91%). Run valid: 0 INVALID, 0 harness errors. Modal ≈ $4.5 (over the $3 cap, see the lesson).

**Sources**: `results/bmax-baseline-2026-10-29/main-BR/summary.json`, `main-B2BX/summary.json`, `session.log`,
`PILOT_NOTE.md`; plan `experiments/bmax/PLAN.md` (frozen cd0716e); dashboard [[glimmer-dashboard-2026-10-29]].

**Last updated**: 2026-10-29

---

## Results (verified)
| Version | Pass rate | Medium | Hard | pass@3 | Calls per answer | Tokens per correct part | Model time per correct part |
|---|---|---|---|---|---|---|---|
| Plain (BR), k=1 | 87% (26/30) | 87% | 87% | – | 1.0 | 11,044 | 184 s |
| Hint, 1 try (B2), k=3 | **88%** (79/90) | 100% | 76% | 97% | 1.0 | **10,662** | 171 s |
| All fair fixes (BX), k=3 | **95%** (75/79) | 98% | 91% (31/34) | 100% | 2.05 | **21,314** | 295 s |
- BX: 11 of 90 answers were not run (the cap stopped new calls); all 45 medium answers ran, 34 of 45 hard. Its hard
  rate is from 34 answers, so it is less certain.
- BR 87% vs the first test's 67% (same prompt): +20 points, at the edge of the luck check (67 ± 20). The first test was
  probably unlucky, or the serving changed slightly; noted, not a stop rule.
- Pilot: xhigh did not clearly lengthen reasoning (see PILOT_NOTE.md); BX ran with xhigh unchanged.

## What it means for the new goal (hypothesis until the final exam)
Pre-registered bars for the trained Glimmer (PLAN rule 3): (a) ≥ BX − 5 points (≈ 90%) with CI lower bound ≥ −15;
(b) the CI of trained − B2 entirely above 0; (c) tokens per correct part ≤ 1.5 × B2 (≤ ~16k); (d) ≤ BX ÷ 3 (≤ ~7.1k).
- (a), (c), (d) look reachable: a trained Glimmer with a short prompt (no 5.5k-token manual) and one try would need
  ≤ 7.1k tokens per correct part and ~90%+.
- (b) is the hard one: B2 is already 88%, and only the 15 hard jobs leave room. With 30 jobs, the CI of a gain of a few
  points will almost surely include 0. Honest risk: the "clearly beats the cheap one-try prompt" claim may fail even if
  training works.

## Money
Modal metered $2.22 → $6.75 (`modal billing summary`, before/after) ⇒ this run ≈ **$4.5** (10:45-12:32, one session,
pilot + 3 arms). Cause of the overshoot: [[lessons]] "A per-call budget is not a session budget"; fixed in
run_session_v2.sh. Forge total ≈ **$17 of $30**.
