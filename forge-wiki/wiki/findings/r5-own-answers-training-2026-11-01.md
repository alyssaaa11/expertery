# R5: training Glimmer on its own checked answers (Oct 31 – Nov 1)

**Summary**: The R5 training round. Base Glimmer + a short rule card solved 2,000 new factory jobs (94%). Its own
correct answers, with their full thinking, became 1,680 lessons. Glimmer was LoRA-trained on them WITHOUT the card, so
the rules should move into the weights. Untrained baselines on 100 held-out jobs: 62% without the card, **96% with
it**. The trained model's own test is next (user OK pending). Related: [[status]], [[training-experiments-2026-10-30]],
[[spark-vs-glimmer-2026-10-31]], [[fireworks-workshop-lessons-2026-10-31]], [[huggingface-cadquery-data-2026-10-31]],
[[r5-decisions-2026-10-31]], [[scoreboard]], [[lessons]].

**Last updated**: 2026-11-01 16:45

---

## 1. Plan and gate (verified: experiments/r5/PLAN.md, commits 9fc3fce → bd2e3df)
- Plan v1 (CAD-Coder + own answers) → v2 (option B: own answers only, no CAD-Coder) → v3 (verifier fixes) → card v2 →
  "Plan change: option B" (generate WITH the card, train WITHOUT it = context distillation).
- Pre-registered dev reading on 100 held-out R5D jobs, first try (written before any dev run; tool
  experiments/r5/compare_dev.py, paired bootstrap 10,000 resamples):
  - **as good as the card**: FT − (A + card) ≥ −3 points AND 95% CI lower bound ≥ −10;
  - **beats plain**: FT − A ≥ +10 points;
  - **cheaper**: completion tokens per correct part FT ≤ A + card;
  - thinking check: FT answers with reasoning ≥ 200 chars ≥ 90%, else STOP.
- Exam amendment written into experiments/final/PLAN.md step 6 before any exam run: arms FT (no card) + A + card v2.

## 2. Data (verified)
| Step | Result | Cost (Modal) | Source |
|---|---|---|---|
| Job sets (cloud build + dedup vs jobs, dev, exam, each other) | R5D 100 (sha 5919bb3f…2172), R5T 2,000 (c836dbe1…458e), 0 dropped; refs 100/100 + 2000/2000 PASS | $0.49 + ≈ $0.05 | results/r5-jobsets-2026-10-31, r5-checkrefs-2026-10-31 |
| Pilot, card v1, 200 R5T (20/family) | 149/200 = 74.5%, 47 crashes | ≈ $1.9 | results/r5-pilot-2026-10-31 |
| Pilot, card v2, same 200 | **188/200 = 94%**, 3 crashes (in-sample) | $1.98 | results/r5-pilot-v2-2026-10-31 |
| First try, card v2, other 1,800 | **1694/1800 = 94.1%**, 35 crashes, reasoning stored 1800/1800 | ≈ $13.6 | results/r5-first-2026-10-31 |
| Self-fix of the 118 FAILs (reference-free feedback) | 42 PASS, 29 FAIL, 47 INVALID (cut at 16k tokens) | $3.14 (cap $3, slightly over) | results/r5-selffix-2026-11-01 |
| Mix (build_mix --drop-card-mentions) | 1,696 rows = 1,678 first-try + 18 self-fix; 228 card-naming rows dropped (11.9%; self-fix 57%) | $0 | results/r5-train-2026-11-01/train_records.jsonl (sha 7565edae…3105) |
- Per family, first try (rest run): F1 159/180, F2 180, F3 178, F4 148, F5 176, F6 179, F7 179, F8 162, F9 170, F10 163.
- Card v1 → v2 crash causes (v1 pilot): 28 `Workplane has no .solid()`, 7 `no attribute 'wrapped'`, 1 `.fuse` on a
  Workplane, 8 `makeCylinder(start=…)`. Card v2 added two lines (Solid vs Workplane + `.val()`; makeCylinder
  positional only); every line checked with `inspect` in CadQuery 2.8 and by the verifier.
- Spark hints were NOT run (user chose "yes" without Spark on 11-01). decision (user, 11-01 16:30): Spark must guide;
  proposal pending: Spark hints on the ≈ 76 still-unsolved jobs → a final training with those lessons.

## 3. Training (verified: results/train-r5/train.json, merge.json, results/r5-train-2026-11-01/train.log)
- Exam guard: 0/1,696 refused. FORMAT_CHECK PASS: thinking first, prompt equals the no-card FT prompt.
- LoRA r 16, alpha 32, all attention + MLP projections (104.8M trainable), lr 1e-4, 2 epochs, max 8,192 tokens,
  H200: 1,680 examples (16 too long: 10 first-try, 6 self-fix), **420 optimizer steps, 6,806 s**, peak 75.6 GB of
  150, no deadline stop. Loss 0.63 → 0.32 (mean of the last 50 steps: epoch 1 0.343, epoch 2 0.322). R3 never got
  below ≈ 0.67. Merged to /vol/r5/merged (195 s). Cost ≈ $9.5 (estimate $9.29 + guard + merge).

## 4. Dev results so far (verified: results/r5-dev-a-2026-11-01, r5-dev-acard-2026-11-01)
| Arm (100 R5D jobs, k = 1, first try) | Pass | Crashes | Completion tokens / correct | Prompt tokens |
|---|---|---|---|---|
| A: base Glimmer, short prompt, no card | **62/100** | 12 | 7,637 | 156-373 |
| A + card v2 | **96/100** | 0 | 3,580 | 862-1,079 |
| FT: R5-trained, no card | not run yet (user OK pending) | | | |
- So the bars for FT: beats plain needs ≥ 72; "as good as the card" needs ≈ 93+.
- Card effect on unseen jobs: +34 points and half the completion tokens. This is a real result on its own.
- Superintel prediction (raw/superintel-answer-r5-validation-2026-11-01.md, before the runs): A 50-68 (58), A + card
  90-96 (93), FT 85-94 (90); "beats plain" ≈ 95% likely, "as good as the card" ≈ 55%.

## 5. Money (verified, Modal billing)
October total $37.47 (`modal billing summary --for 'last month'`). November so far $15.33 → **$52.80 of $90**.
Muse Code (Meta credit, estimates from run.usage): R5 build ≈ $1.8, R5b fixes ≈ $2.8, viewer ≈ $0.55, R5c ≈ $0.9.

## 6. Tools added (all by Muse Code unless noted)
make_jobs seeds/dedup/cloud check; runner reasoning capture, self-fix (reference-free feedback), hints; hints.py;
build_mix.py; forge_train full-r5 (--no-card); answer viewer (experiments/viewer). Claude small fixes, each disclosed in
the README: B3b, B6b, B7, session-script `.jsonl` spec / WORKERS / RUNNER_EXTRA (both scripts), viewer render path,
card v2 + sha, compare_dev.py (analysis only).
