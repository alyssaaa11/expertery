# R5: train Glimmer on its own guided solutions (plan v2, 2026-10-31; nothing run)

## Goal (user, 2026-10-31, in their words: "one model guides the little one; the little one becomes more powerful by itself")
Two private models: Spark guides, Glimmer learns. Today Glimmer + rule card needs many steps and still fails about 2 in 5
hard factory jobs. After training, Glimmer must (1) get it right on the FIRST try more often, and (2) fix its own
mistakes from the referee's error message alone, with no Spark and no hints, in the product.
Decisions (user, 2026-10-31): plan accepted; option **B** (no CAD-Coder: licence lineage is non-commercial, and its style
and missing thinking were risks; verifier forge-r5-plan-2026-10-31 P1); large data; Modal only for Glimmer; **Modal
budget $90** (billing baseline 19.89 on 2026-10-31); Spark hints on Baseten cap $10; Muse Code writes the scripts
(≈ $3-5 Meta credit); **this is the last training method**: the exam result is what we submit.
Supersedes plan v1 (ac1bfa6). Verifier must-fixes M1-M10 are marked [Mx] where they are handled.

## Data (all code runs in the cloud box; nothing AI-written runs on the Mac)
1. **New job sets** [M8]: make_jobs with new seeds and id prefixes, written here before any run:
   train `R5T` seed 20261031, 200 per family = 2,000 jobs; dev `R5D` seed 20261131, 10 per family = 100 jobs.
   Dedup against jobs.jsonl, jobs_dev.jsonl, the exam (experiments/first-test), and R5T vs R5D: same text, same rounded
   parameter tuple, or same measured volume + bbox (1e-6) → dropped and counted [W2]. The volume/bbox measure and the
   reference self-check run in the cloud box (cloud_cq measure_brep), cap $1. After building: write both files' sha256
   and job counts here before any GPU step.
   - verified (2026-10-31 15:01, results/r5-jobsets-2026-10-31/r5d.log + r5t.log, verifier GO forge-r5b2): **R5D 100 jobs**
     sha256 5919bb3fad92e22ad4f9cd0456c625e5284bb57638c0f753b7280335bc192172, 100/100 refs ok, 0 dropped, $0.073;
     **R5T 2,000 jobs** sha256 c836dbe17eeb890949b791554cbca8bfe8a9da83cd38bfd26736369de531458e, 2,000/2,000 refs ok,
     0 dropped (text/params/volume+bbox vs jobs, dev, exam, R5D), $0.443. Modal billing 19.89 → 20.38.
2. **Pilot** [M6, W1]: base Glimmer + card (arm A, A100-80GB, deploy/modal_glimmer.py) on the first 200 R5T jobs, k = 1,
   **16 workers** (the servers accept at most 16 requests at a time: max_inputs=16, one container; 200 jobs ≈ 12 waves).
   Check on the first records: prompt_tokens ≈ 830+ (card in the prompt) and stored `reasoning` length equals
   `reasoning_len` [M2]; otherwise STOP. Steady-state $/answer = $2.50/h × (wall − cold start) ÷ answers. Continue only if
   ≤ $0.013 (the A + card rate today is $0.0138 at 8 workers). Pre-registered job count N = min(2,000, floor($24 ÷
   rate)); the pilot's 200 count toward N. Never raise the cap.
3. **First try** on all 2,000 R5T jobs (the pilot's 200 count). The referee (0.2%) marks PASS / FAIL. The runner stores
   the full thinking text (`reasoning`) from whichever field holds it (reasoning_content, reasoning, or text before
   the code) [M2]. Cap **$24** including the pilot.
4. **Self-fix** (no Spark) on every FAIL: Glimmer gets the job + its own wrong code + **reference-free feedback** and
   tries once more. PASS (by the full referee) → a **self-fix row**. Feedback = the last 15 lines of the error trace if
   it crashed, the number of separate solids, and the answer's OWN measured volume and bounding box; never the expected
   values or check names that reveal them. The same feedback function is used in the product (no reference needed
   there), so self-fix is a real product feature. Cap **$9** (≈ 633 FAILs × $0.013).
5. **Spark hint** on what still fails: Spark Open (Baseten) sees the job, Glimmer's attempt and the failed checks, and
   returns ONE hint, ≤ 60 words, no code (replies with a code fence, `cq.` or `import` are rejected). Glimmer retries
   with the hint. PASS → kept, but [M7] dropped if its reasoning mentions the hint ("hint", "tutor", or ≥ 8 words copied
   from the hint), and trained WITHOUT the hint. At most **230 hints** (the shortest-failing jobs first by family
   balance). Caps: Baseten $10, Glimmer retries $3 [W3].

## Pilot result and card v2 (2026-10-31)
- verified (results/r5-pilot-2026-10-31/pilot-A/summary.json, session.log): pilot A + card v1 on 200 R5T jobs (20 per
  family), 16 workers, A100-80GB: **149/200 = 74.5%** PASS at 0.2% (74% tight), 0 INVALID, **47 crashes**; reasoning
  stored for 200/200 (len == reasoning_len); prompt ≈ 834 tokens (card in). Steady-state $/answer = $2.50/h × (2008 −
  285 s) ÷ 200 = $0.006 by my count; **verifier: $0.0070** (cold start double-subtracted); either way ≤ $0.013 → N = **2,000**. Modal 20.43 → 22.36
  (incl. cold start).
- Per family: F1 17/20, F2 20/20, F3 10/20 (10 crashes), F4 6/20 (14), F5 18/20, F6 15/20, F7 20/20, F8 11/20, F9 16/20, F10 16/20.
- Crash causes (last error line): 28 `Workplane has no attribute 'solid'`, 7 `no attribute 'wrapped'` (a Workplane passed
  to Solid.cut), 1 `Workplane has no attribute 'fuse'`, 8 `makeCylinder() unexpected keyword 'start'`, 3 other.
- decision (user, 2026-10-31, option B): **rule card v2** adds two lines (Solid vs Workplane: `.val()`, no `.solid()`/
  `.fuse()` on Workplanes; makeCylinder positional only). Every signature checked with `inspect` in CadQuery 2.8. All
  later steps (first try, self-fix, hints, training, dev, exam) use v2. The v1 pilot is kept as a record and is NOT
  used for training (prompt mismatch). The pilot is redone with v2 on the same 200 jobs (cap $4), which also gives a
  paired v1 vs v2 comparison.

## Plan change: option B, train WITHOUT the card (user, 2026-10-31 ~19:20)
- Why: card v2 lifted base Glimmer to 94% on the pilot jobs (in-sample), so a trained model can hardly beat "A + card"
  on accuracy. decision (user): "straight to B": generate WITH card v2 (first try, self-fix, hints), but TRAIN with the
  short prompt WITHOUT the card (context distillation: the rules move into the weights). The A-on-R5D baseline is not
  run separately; it is measured in the dev step.
- Training rows: prompt = the FT system prompt WITHOUT the card + the job text (self-fix rows: + wrong code + feedback);
  target = Glimmer's thinking + code generated WITH the card. Drop rows whose thinking mentions the card/rule card/
  cheat sheet ("rule card", "card says", "per the card") or ≥ 8 words copied from the card (same idea as M7).
- FT is served WITHOUT the card (FORGE_RULE_CARD unset). Dev arms on the 100 R5D jobs, k = 1: A (no card), A + card v2,
  FT (no card). Pre-registered reading:
  - **as good as the card**: FT − (A + card) ≥ −3 points AND 95% CI lower bound ≥ −10;
  - **beats plain Glimmer**: FT − A ≥ +10 points;
  - **cheaper**: FT tokens per correct part ≤ (A + card)'s.
  - All readings on FIRST try. CI = paired bootstrap over the 100 jobs, 10,000 resamples [P2]. "Cheaper" is measured
    on COMPLETION tokens per correct part (dropping the card saves prompt tokens automatically). Thinking check kept:
    FT answers with reasoning ≥ 200 chars must be ≥ 90%, else STOP ("thinking suppressed").
  - Card-name filter: drop rows whose reasoning NAMES the card; rows that quote true rules are kept (verifier S3);
    stop if > 20% dropped.
  The exam runs once with FT (no card) and A + card; this amendment is written into experiments/final/PLAN.md step 6
  before the exam [P3]. Cap $5 (≈ $3.3).
- Rest run (started 19:23 after the user's "straight to B", before a verifier check of its command; the command is
  logged here): `WORKERS=16 caffeinate -is zsh experiments/final/run_base_session.sh results/r5-first-2026-10-31 18.00
  --pilot '' --run 'experiments/r5/jobs_r5t_rest.jsonl:rest-A:A:1'` with FORGE_RULE_CARD = card v2 (sha checked).
  Expected ≈ $14.5 (verifier: pilot v2 $0.0080/answer).

## Training rows (two kinds, all with thinking) [M1, M3, M4]
**(REPLACED for the prompt/arms by "Plan change: option B" below/above: rows are trained WITHOUT the card; dev arms A / A + card / FT no card. Kept parts: row kinds, filters, LoRA settings, caps, thinking check.)**
- **First-try rows**: prompt = FT system prompt + RULE_CARD v2 (sha256 9d0929b2…29c7; v1 586b5960…e80b kept as RULE_CARD_V1.md) + job text; target = Glimmer's
  thinking + code. From step-3 PASSes and step-5 PASSes (hint removed).
- **Self-fix rows**: prompt = the same + "Your code:\n…\nWhat happened:\n<reference-free feedback>"; target = thinking +
  fixed code. From step-4 PASSes and step-5 PASSes (hint removed).
- Every row must have non-empty thinking (≥ 200 chars); rows without are dropped and counted (no code-only rows: the
  R1 failure). At most 2 rows per job. No dev/exam id or text, no Wonder output, no hint text (asserted).
- The card goes into the training container as a file baked into the image (not an env var); its sha256 is checked
  inside the container before training [M4].
- The loader accepts sources `glimmer-first`, `glimmer-selffix`, `glimmer-hinted` with R5T ids only (provenance check
  replaces the "Spark PASS in calls.jsonl" rule) [M3]. Shuffle with seed 20261031. Log rows, tokens and the first
  loss tokens per source; the first loss tokens must open the thinking turn for every source.
- Expected size (hypothesis): ≈ 1,350 first-try + ≈ 250-400 self-fix/hinted ≈ 1,600-1,750 rows, about 10× R3.

## Training [M5]
**(REPLACED for the prompt/arms by "Plan change: option B" below/above: rows are trained WITHOUT the card; dev arms A / A + card / FT no card. Kept parts: row kinds, filters, LoRA settings, caps, thinking check.)**
LoRA r 16, alpha 32, lr 1e-4, 2 epochs, max 8,192 tokens, H200, loss on thinking + code. Cap $18. Before starting,
estimate the cost from tokens × the measured R3 throughput; if the estimate is over 75% of the cap ($13.50), subsample
first-try rows (seed 20261031) until it fits, keeping all self-fix rows. Save the adapter every half epoch; if the cap
stops training, the last saved adapter is used for dev and the stop is disclosed (amends the R3 rule for this run).

## Dev check (pre-registered; on the 100 R5D jobs, k = 1, same runner, referee, 16,000 tokens) [M9]
**(REPLACED for the prompt/arms by "Plan change: option B" below/above: rows are trained WITHOUT the card; dev arms A / A + card / FT no card. Kept parts: row kinds, filters, LoRA settings, caps, thinking check.)**
Arms: A + card, R3 + card, FT + card. Product mode for each arm [E3]: one self-fix retry, triggered ONLY by
reference-free signals (crash, invalid shape, or solids ≠ 1) and using selffix_feedback; then the full referee scores it.
- **GO to the exam** if FT + card − max(A + card, R3 + card) ≥ +6 points on first try.
- Otherwise the exam runs once with the **best arm** (= highest first-try pass rate on R5D; ties → cheaper tokens per
  correct), and the report says that R5 training did not beat it.
- Thinking check: share of FT answers with reasoning ≥ 200 chars must be ≥ 90%; below that = "thinking suppressed",
  STOP and report.
- Also report the hard-family failure rate (F3, F4, F8) for each arm: the user's "2 of 5" target.
Cap $9.

## Final exam [M10]
**(REPLACED for the prompt/arms by "Plan change: option B" below/above: rows are trained WITHOUT the card; dev arms A / A + card / FT no card. Kept parts: row kinds, filters, LoRA settings, caps, thinking check.)**
Frozen rules of experiments/final/PLAN.md step 6, amended BEFORE any exam run: the FT arm = short prompt + RULE_CARD
(v2 sha256 above); the report says B-max had the 5.7k manual and no card. Report first try and product mode (one self-fix).
Cap $5. Run once.

## Money [N2]
Modal: 1 (job sets) + 24 + 9 + 3 + 18 + 9 + 5 = $69 worst case → 19.89 + 69 ≈ $89 of the $90 Modal budget. Baseten (Spark hints) $10.
Muse Code ≈ $3-5 Meta credit. Every paid step: verifier check + user yes first.

## Risks
- Glimmer's own thinking is not always good thinking. The referee filter keeps only rows whose code passed.
- Self-fix rows teach fixing from reference-free feedback; the product uses the same selffix_feedback function. In the
  TRAINING data the retry was triggered by a full-referee FAIL (reference-assisted trigger); disclosed [E3].
- Only ~10 families: the trained model may be narrow. The exam's 30 jobs are hand-made and different, so it tests transfer.
