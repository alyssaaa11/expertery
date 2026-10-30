# Answer: why LoRA training doesn't make Glimmer better, and the next recipe (superintel, 2026-10-30)

For hivey / Alyssa (brief: superintel-task-training-diagnosis-2026-10-30.md). Read-only, $0 spent. **verified** = recomputed
from the files; **hypothesis** = my judgement, not yet tested.

## Bottom line
1. **R3 learned two things, and they cancel out** (verified). Wrong-shape fails fell 22 → 13 of 60 (bounding-box fails 15 → 4), but
   crashes rose 7 → 18. Net: 31 → 29 passes.
2. **Most likely main cause: the manual gap** (hypothesis, strongly suggested by the data). Spark reasons *with* the manual in
   view ("Check CadQuery manual: cut(self, toCut…)"). Glimmer is trained to produce that recall without the manual, so it invents arguments.
3. **The dev set can't see ±10 points** (verified). 20 jobs × 3 gives a paired SE ≈ 8 points: R3 − A = −3.3 (95% CI −18 to +12),
   R1 − A = −13.3 (CI −30 to +3).
4. **Recipe:** one round of rejection-sampling *self*-distillation with a short rule card in every prompt, plus 120 fresh dev jobs. About $15–23.

## a) Causes, ranked
1. **Manual gap** (hypothesis; no ablation yet). Evidence (verified, from dev-r3 calls.jsonl and factory-r3 train_records.jsonl):
   - 15 of R3's 18 crashes are an invented keyword or method.
   - 6 of them use `pnt`, `yDir`, `inPlane` or `direct`. Spark's reasoning names these in 100 / 61 / 62 / 58 of 159 records, but its code uses them in only 15 / 0 / 0 / 0 (word match). Base Glimmer used `pnt`, `yDir` and `inPlane` 0 times in 60 answers, and `direct` once.
   - 104/159 reasonings say "manual".
   - Base Glimmer invents API too (`cq.Box`, `cq.Cylinder`), but only 2 times in 60.
   Literature: training on knowledge the model doesn't have is learned late and then raises hallucination (Gekhman et al., 2405.05904). Context distillation works when the *same* model produces the with-context outputs (Snell et al., 2209.15189).
2. **Off-policy teacher style** (hypothesis). R3's loss is 0.95 at step 1, about 0.74 over steps 5–20 and 0.67 in epoch 2; code-only R1 reaches 0.16 (train.json). Glimmer never learns to predict Spark's reasoning well. R3 answers average 6.9k tokens vs 4.5k for base. Own-style data trains better (2402.11192; SDFT 2402.13669). Off-policy distillation has a train/inference mismatch (GKD, 2306.13649). The "learnability gap" for long teacher chains of thought (2502.12143) was shown only for students of ≤ 3B, so it is weak support for a 30B student.
3. **R1 only: answer-only targets switched the thinking off** (verified; already fixed in R3). R1's first loss tokens are ` to`, `=user`, and its dev answers had 0 reasoning in 60/60.
4. **Evaluation noise** (verified, job-level bootstrap). Families swing 3–4 passes out of 6 between arms. The old dev set has been looked at twice, and RULE_CARD.md was written from R3's dev crashes, so it can't test the card fairly.
5. **Data size (154 examples)**: secondary (hypothesis). LIMO (2502.03387: Qwen2.5-32B, base 16.5 → 63.3 AIME24 with 800 examples, full fine-tuning) and s1 (2501.19393, 1k) show small data *elicits* what the base knows. More of the same Spark data would also add more hidden-manual recall.
6. **LoRA settings**: not the cause. R1 fitted its targets with r 16 and lr 1e-4. LoRA does learn less than full fine-tuning: r 16–64 is too little for large code corpora (2405.09673 §4.1), but that holds at billions of tokens, not 300 examples.
7. **Template / sampling**: minor. R3's format check passed; the served sampling settings (D3) are still unrecorded.

## b) Recipe: card-conditioned self-distillation (one round of RFT / ReST-EM)
Base Glimmer solves 85% of dev jobs within 3 tries but only 52% per try. Training on its own *correct* traces moves pass@1
toward pass@k (STaR 2203.14465; RFT 2308.01825: +5–6 points at 7–13B; ReST-EM 2312.06585: +5.6 to +6.4 on APPS code, overfitting
by iteration 2, so do one round). The referee is the strict filter this needs (2402.11192 §4.2). With the card in every prompt,
no trace relies on context the student can't see.
1. **Prompt (generate = train = serve):** short prompt + RULE_CARD.md (add arc / revolve / slot2D lines) + "Reasoning strength: high".
2. **Jobs:** 180 existing non-dev jobs + 60 new (20 each from F5, F8, F10) = 240. Draw **120 fresh dev jobs** now (12 per family, new seed) and don't look at them.
3. **Generate:** base Glimmer, k = 3 per job, 16 concurrent → 720 answers ≈ 3.2M tokens ≈ $6–11 (A100; base ran at ≈ 217 tok/s with 8 workers).
4. **Select:** passing traces only, up to 2 shortest per job, ≤ 8,192 tokens, drop any reasoning that says "manual"; expect ≈ 300–380 examples. No Spark records.
5. **Train:** LoRA r 16, α 32, lr 1e-4, all attention + MLP, 2 epochs, GA 8, loss on thinking + code, format check first. ≈ 45 steps, ≈ $2–3 on H200.
6. **Eval:** 120 fresh jobs × 1, arms A, A + card, FT + card. That is 360 answers ≈ $5–7, and a paired SE ≈ 6 points. Pre-register two readings: "training helps" if FT+card − (A+card) ≥ +6, and the headline "beats untrained" if FT+card − A ≥ +10.

Total with (c): ≈ $15–23. Generate Fri night or Sat morning, train Sat midday, eval Sat evening.
Expected (hypothesis): FT+card 60–68%. P(≥ A + 10) ≈ 50%, and part of that may come from the card, so report both deltas.

**The four plans on the table:**
- (1) R4 with Spark: style still off-policy, and Spark still reads the manual unless it gets the card only. It uses the whole budget. Second choice, and only if Spark gets card-only prompts.
- (2) Self-distillation with the manual: the same gap, smaller. The card version above is its safe form.
- (3) Teacher corrects the student's failures: a good round 2, not now.
- (4) Card only: it is the control arm in step 6. If A+card ≈ FT+card, ship the card and say so.

## c) Cheap check before spending (≈ $1.5–2, needs a user yes)
Run R3 + card (/vol/r3/merged) and A + card on the old 20 dev jobs × 3.
- If the manual-gap diagnosis holds: R3 + card crashes fall from 18 to ≤ 8, and R3 + card ≥ A + card.
- If R3 + card still crashes ≥ 15 times: the diagnosis is wrong, or the model ignores the prompt.
- A + card's pass rate also gives the generator yield for step 3. Below 45%, use k = 4.

## Sources
Forge files: results/dev-base-2026-10-30/dev-A/{calls.jsonl,summary.json}, results/dev-2026-10-30/dev-FT/calls.jsonl,
results/dev-r3-2026-10-30/dev-FT/calls.jsonl, results/factory-r3-train-2026-10-30/train_records.jsonl,
results/train-final/train.json, results/train-r3/train.json, experiments/final/RULE_CARD.md, deploy/modal_forge.py. Papers (full
texts in ~/agents/superintel/superintel-wiki/raw/papers/training-diagnosis-2026-10-30/): 2405.05904, 2209.15189, 2402.11192,
2402.13669, 2306.13649, 2502.12143, 2502.03387, 2501.19393, 2405.09673, 2203.14465, 2308.01825, 2312.06585. Wiki: superintel-wiki/wiki/syntheses/2026-10-30-forge-lora-training-diagnosis.md.
