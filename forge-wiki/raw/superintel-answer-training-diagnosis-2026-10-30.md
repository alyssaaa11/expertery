# Answer: why LoRA training doesn't make Glimmer better, and the next recipe (superintel, 2026-10-30)

Asked by hivey for Alyssa (brief: forge-wiki/raw/superintel-task-training-diagnosis-2026-10-30.md). Read-only, $0 spent.
Labels: **verified** = I recomputed it from the files named; **literature** = paper result (arXiv id); **hypothesis** = my judgement.

## Bottom line
1. **R3 didn't fail at learning. It learned two things, and they cancel out.** Spark's worked solutions taught Glimmer
   better geometry (wrong-shape fails 22 → 13 of 60; bounding-box fails 15 → 4). They also taught it to "recall" API
   signatures from a manual it never sees (crashes 7 → 18). Net 31 → 29 passes. The main cause is the **manual gap**:
   distilling reasoning that rests on information the student lacks.
2. **The dev set can't see ±10 points.** With 20 jobs × 3, the job-paired standard error is about 8 points. R3 − A = −3.3,
   95% CI [−18, +12]. R1 − A = −13.3, CI [−30, +3]. "+10 points clearly" needs about 100 *fresh* jobs.
3. **Recipe:** one round of rejection-sampling **self**-distillation. Glimmer writes its own traces with the rule card in
   the prompt, the referee keeps the correct ones, and Glimmer is trained on them with the *same* card + short prompt.
   It's on-policy, it leaves no hidden context, and it costs about $14–21 including a proper fresh-dev evaluation.

## a) Causes, ranked (main first)
| # | Cause | Evidence (our files) | Literature |
|---|---|---|---|
| 1 | **Manual gap (privileged-information distillation)**. Spark reasons *with* the manual in view ("Check CadQuery manual: cut(self, toCut…)", "Workplane init: Workplane(inPlane='XY', origin, obj)"). The student is trained to produce that recall with no manual, so it confabulates signatures. | **verified:** 15 of R3's 18 crashes are a wrong keyword or a missing method (results/dev-r3-2026-10-30/dev-FT/calls.jsonl `run_error`). 6 of them use 4 names: `pnt`, `yDir`, `inPlane`, `direct`. Untrained Glimmer used none of them in its 60 answers. Spark's reasoning mentions them in 100 / 61 / 62 / 58 of 159 records, but its code uses them in only 15 / 0 / 0 / 0. 104/159 reasonings say "manual"; 157/159 discuss params/signatures. | Fine-tuning on knowledge the model doesn't already have is learned slowly and raises hallucination (Gekhman et al., 2405.05904). Context distillation works when the *student's own* model produced the with-context outputs (Snell et al., 2209.15189). |
| 2 | **Off-policy teacher style** (816B Spark's words and length, not Glimmer's). | **verified:** R3 loss is 0.95 at step 1, 0.74 on average over steps 5–20 and still 0.67 in epoch 2 (results/train-r3/train.json); code-only R1 gets to 0.16. Glimmer never learns to predict Spark's reasoning tokens well. R3 answers are 6.9k tokens on average vs 4.5k for base (calls.jsonl `completion_tokens`). | Small students learn worse from long CoT of much stronger teachers ("learnability gap", Li et al., 2502.12143). Models learn better from data in their own style (Ren et al., 2402.11192). Off-policy KD causes a train/inference mismatch that on-policy KD fixes (Agarwal et al., 2306.13649). |
| 3 | **R1 only: answer-only targets removed the thinking turn.** Already fixed in R3. | **verified:** R1's first loss tokens are ` to`, `=user` (results/train-final/train.json); 0 reasoning in 60/60 dev answers; 388 completion tokens median. | Reasoning skill lives in the CoT; LIMO (2502.03387) and s1 (2501.19393) train *with* the reasoning. |
| 4 | **Evaluation noise.** | **verified:** job-level bootstrap (20k resamples) on the 3 calls.jsonl files; numbers in Bottom line 2. Per-family swings between arms reach 3–4 passes out of 6 (e.g. F3: A 6, R1 2; F5: A 0, R3 3). The old dev set has now been looked at twice, and RULE_CARD.md was written from R3's dev crashes, so it's no longer a clean test for anything card-related. | — |
| 5 | **Data size (154 examples, 39 optimizer steps)**: secondary. More of *the same* data would also mean more manual-recall targets. | **hypothesis**, based on 1 + 2. | 800–1,000 curated traces are enough to *elicit* reasoning a 32B base already has (LIMO 2502.03387: full FT, AIME24 16.5 → 63.3; s1 2501.19393). Neither teacher had hidden context. Unknown facts are learned slowly and harm at convergence (2405.05904 §4.2). |
| 6 | **LoRA settings** (r 16, α 32, lr 1e-4, all linear layers, 2 epochs): not the cause. | **verified:** R1 fitted its targets (loss 0.42 → 0.16 in epoch 2), so capacity and LR were enough to learn format and style. | LoRA learns less and forgets less than full FT. On large code sets, r 16–64 "tend not to suffice" and r 256 matches full FT (Biderman et al., 2405.09673 §4.1, §4.7), but that is billions of tokens; 300 examples won't hit the rank limit. |
| 7 | **Template / sampling**: minor. R3's format check passed (first loss tokens ` to`, `=self`). D3 (served sampling settings) is still unrecorded. | verified (train.json) / open | — |

## b) Recommended recipe: "card-conditioned self-distillation" (one round of RFT / ReST-EM)
Why this one: base Glimmer already solves 85% of dev jobs within 3 tries but only 52% per try
(results/dev-base-2026-10-30/dev-A/summary.json). Training on its own correct traces is the standard way to move pass@1
toward pass@k (STaR 2203.14465; RFT 2308.01825: about +5–6 points at 7–13B; ReST-EM 2312.06585: +5.6 to +6.4 on APPS code, and it overfits by
iteration 2 on small sets, so do **one** round). It needs a strict filter (2402.11192 §4.2), and the referee is one. Its own words keep the loss low and the targets
on-policy (2402.13669, 2402.11192). Putting the ≈350-token card in **both** the generator and the student prompt closes
the manual gap by construction: nothing the reasoning refers to is hidden from the student.
1. **Prompt (train = serve = generate):** today's short prompt + RULE_CARD.md (add the verifier's arc/revolve/slot2D lines), "Reasoning strength: high".
2. **Jobs:** the 180 existing non-dev jobs + 60 new generator jobs (20 each from the hardest families F5, F8, F10) = **240**.
   Also draw **100 fresh dev jobs** (10 per family, new seed) now, and never look at them until the final eval.
3. **Generate:** base Glimmer, **k = 3** samples per job at the serve temperature, **16 concurrent** (modal max_inputs) → 720
   answers ≈ 3.2M tokens ≈ **$6–11** on A100 (base ran at ≈ 217 tok/s with 8 workers; ~2× with 16). Referee as usual.
4. **Select:** keep passing traces only; up to **2 per job, the shortest**; drop > 8,192 tokens; drop any reasoning that
   mentions "manual". Expect ≈ **300–380 examples** (at ~55% per-sample pass and ~88% of jobs with ≥ 1 pass).
   Don't mix in the Spark R3 records (that would bring the manual gap back).
5. **Train:** same stack. LoRA **r 16, α 32, lr 1e-4**, all attention + MLP, **2 epochs** (not 3: own-style targets are
   already low-loss, and more epochs mainly cut diversity), GA 8, max 8,192 tokens, loss on thinking + code. Format check
   first (` to`, `=self`). ≈ 45 steps, ≈ **$2–3** on H200.
6. **Evaluate on the 100 fresh jobs, k = 1, three arms:** A (short prompt), **A + card** (the fair control: the card
   alone may give a lot), FT + card. 300 answers ≈ **$4–6**. SE of a paired difference ≈ 6 points, so +10 is about 1.7 SE.
   Pre-register: training "helps" if FT+card − A+card ≥ +6. The headline "beats untrained" is FT+card − A ≥ +10.
**Total ≈ $14–21** including the check in (c), which leaves a few dollars for one retry. Timeline: generate tonight/Sat morning, train Sat midday, eval Sat evening.
Expected result (**hypothesis**): FT+card ≈ 60–68% on fresh dev, crashes ≤ base. P(FT+card ≥ A + 10) ≈ 50%, but much of
that may come from the card, so report both deltas.

**The four plans on the table:**
- (1) R4 with Spark + card: it keeps the off-policy style, and Spark still reasons from the 5.7k manual unless it too only gets the card. It costs the whole budget, with no money left for a fair eval. Second choice only if Spark gets *card-only* prompts.
- (2) Self-distillation **with the manual** in generation: a better yield on hard jobs, but Glimmer's reasoning will quote the manual too (the same gap, smaller). The card version above is the safe form of (2).
- (3) Teacher fixes the student's failures: needs the trained model first plus Spark calls. A good round 2, not now.
- (4) Card only, no training: run it as the control arm in step 6 anyway. If A+card ≈ FT+card, ship the card and say so honestly.

## c) The cheap check before spending (≈ $1.5–2, user yes needed)
On the old 20 dev jobs × 3, run **R3 + card** (the existing /vol/r3/merged model) and **A + card**.
- If the diagnosis is right, R3 + card crashes fall from 18 to ≤ 8 while its geometry fails stay ≤ ~15, so R3 + card ≥ A + card.
- If R3 + card still crashes ≥ 15 times, the manual-gap story is wrong (the model ignores the prompt), and the card has to be trained in, not just served.
- A + card's pass rate is also the generator's expected yield for step 3: if it is < 45%, use k = 4.
Free first: the crash attribution above (done) and a template token check of one generated trace.

## Sources
Our files: results/dev-base-2026-10-30/dev-A/{calls.jsonl,summary.json}; results/dev-2026-10-30/dev-FT/calls.jsonl;
results/dev-r3-2026-10-30/dev-FT/calls.jsonl; results/factory-r3-train-2026-10-30/train_records.jsonl;
results/train-final/train.json; results/train-r3/train.json; experiments/final/RULE_CARD.md; deploy/modal_forge.py (A100-80GB,
max_inputs 16); ~/agents/verifier/reports/forge-r3-dev-result-2026-10-30.md. Papers (full texts in
~/agents/superintel/superintel-wiki/raw/papers/training-diagnosis-2026-10-30/): 2405.05904, 2209.15189, 2502.12143, 2402.11192,
2306.13649, 2502.03387, 2501.19393, 2405.09673, 2203.14465, 2308.01825, 2312.06585, 2402.13669.
