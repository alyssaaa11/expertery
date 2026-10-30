# Training experiments, Oct 30: what we trained, what happened, and why

**Summary**: Two LoRA trainings of Glimmer on factory data, both measured on the same 20 hidden factory dev jobs × 3
tries with the strict referee and the short prompt (no manual). Neither beat untrained Glimmer. The cause is now
diagnosed (manual gap + off-policy teacher style), and a cheaper, better recipe is proposed. Related:
[[status]], [[scoreboard]], [[how-training-changes-weights-2026-10-30]], [[learn-training-and-verifiers-2026-10-29]],
[[lessons]], [[tools-and-services]].

**Last updated**: 2026-10-30 ~21:40

## The three numbers (verified)
| Model | Dev pass (0.2%) | pass@3 | tokens/correct | crashes | Source |
|---|---|---|---|---|---|
| Untrained Glimmer, short prompt (arm A) | **51.7%** (31/60) | 85% | 9.2k | 7 | results/dev-base-2026-10-30/dev-A/summary.json |
| R1: trained on 167 × {job → Spark code only} | 38.3% (23/60) | 75% | 1.7k | many | results/dev-2026-10-30/dev-FT/summary.json |
| R3: trained on 154 × {job → Spark thinking → code} | 48.3% (29/60) | 85% | 14.8k | 18 | results/dev-r3-2026-10-30/dev-FT/summary.json |
All runs COMPLETE (60/60, not budget-stopped); the verifier recounted each one (reports forge-dev-result,
forge-r3-dev-result). By the rule written before the runs (PLAN "Retry R3" item 10), FT < A means training did not help.

## What each training was (verified, results/train-final/train.json, results/train-r3/train.json)
| | R1 | R3 |
|---|---|---|
| Data | 167 factory records, Spark's code only | 154 records (5 too long dropped), Spark's reasoning (~5k tokens) in Glimmer's `to=self` thinking turn + code |
| Prompt | system line + "Reasoning strength: high." + job text (no manual) | same |
| LoRA | r 16, alpha 32, all attention + MLP projections, 104.8M trainable of ~30B | same |
| Optimizer | lr 1e-4, grad accumulation 8, 2 epochs, 42 steps | same, 39 steps |
| GPU | H100, max 4,096 tokens, 231 s, peak 64 GB | H200, max 12,288 tokens, 1,177 s, peak 94 GB |
| Loss | 0.42 → 0.16 | 0.95 → ~0.67 (never low) |
| First loss tokens | ` to`, `=user` (answer directly) | ` to`, `=self` (think first) |
| Cost (Modal) | ≈ $0.89 | ≈ $1.99 |

## Why it did not work (diagnosis by superintel, raw/superintel-answer-training-diagnosis-2026-10-30.md)
1. verified: **R1 taught "skip thinking".** Every example's first loss tokens were ` to`, `=user`; 0 reasoning in
   60/60 dev answers. Glimmer copied Spark's look (even its comments) but not the work.
2. verified: **R3 learned two things that cancel out.** Better geometry (wrong-shape fails 22 → 13, bbox fails 15 → 4)
   but more crashes (7 → 18), so net 31 → 29 passes.
3. verified: **the crashes come from the "manual gap".** Spark reasons with the 5.7k manual in view ("Check CadQuery
   manual: …", "Workplane(inPlane=…)"); the student is trained to reproduce that recall without the manual and invents
   signatures. 15 of R3's 18 crashes are wrong keywords or missing methods; `pnt`, `yDir`, `inPlane`, `direct` appear in
   Spark's reasoning in 100/61/62/58 of 159 records but in its code 15/0/0/0 times; untrained Glimmer used none of them.
   Literature: fine-tuning on knowledge the model lacks raises hallucination (arXiv 2405.05904); context distillation
   works when the student's own model produced the outputs (2209.15189).
4. verified: **off-policy teacher style.** R3's loss stayed ≈ 0.7: Glimmer never learned to predict Spark's words.
   Small students learn worse from long chains of a much stronger teacher (2502.12143, 2402.11192, 2306.13649).
5. verified: **the dev set is too small for ±10 points.** 20 jobs × 3 → job-paired SE ≈ 8 points; R3 − A = −3.3,
   95% CI [−18, +12]. A fair verdict needs ~100 fresh jobs. The old dev set has been looked at three times now.
6. Not the cause: LoRA settings (R1 fitted its targets), chat template (R3 format check passed).
7. hypothesis: data size (154) is secondary; more of the same data would add more manual-recall targets.

## Other findings from the day (verified)
- Baseten returns Spark's thinking in `message.reasoning_content`; the first factory never stored it (fixed in round 3).
- Glimmer's chat template renders an assistant `reasoning_content` as `<|start|>assistant to=self<|message|>…<|eom|>`
  for any assistant message (.cache/glimmer-tokenizer/chat_template.jinja:179-182); default sampling temperature 1.0,
  top_p 0.95, top_k 64 (generation_config.json).
- The served model must be checked: modal_forge read FORGE_MODEL_NAME at import, so the container served the old model
  until round 3c baked the name into the image and the session checks `/v1/models` root.
- Base Glimmer is 85% pass@3 but 52% pass@1 on factory dev jobs: it can solve most jobs, not reliably.
- The rule card (experiments/final/RULE_CARD.md, ≈ 400 tokens) lists the correct CadQuery 2.8 calls; every line was
  checked against the installed signatures. The verifier says it covers 12 of 18 R3 crashes (+ arcs/revolve added).
  Even if all crashes passed, R3 would reach 47/60 = 78% < 80%: geometry must improve too.

## Recommended next recipe (superintel; decision pending, user)
**Card-conditioned self-distillation** (one round of rejection-sampling fine-tuning, STaR 2203.14465 / ReST-EM 2312.06585):
1. Prompt = short prompt + rule card, the same for generating, training and serving (no hidden context).
2. Base Glimmer answers 240 jobs (180 non-dev + 60 new in F5/F8/F10) × 3 → the referee keeps the correct ones → up to 2
   shortest per job, no "manual" mentions, ≤ 8,192 tokens → ≈ 300-380 examples in Glimmer's own words.
3. Train: r 16, alpha 32, lr 1e-4, 2 epochs, loss on thinking + code.
4. Evaluate on **100 fresh dev jobs**, k = 1, three arms: A, A + card (fair control), FT + card. Pre-registered:
   training helps if FT+card − A+card ≥ +6; headline "beats untrained" if FT+card − A ≥ +10.
Cost ≈ $14-21. **Cheap check first (≈ $1.5-2):** R3 + card and A + card on the old 20 dev jobs: if R3's crashes fall
from 18 to ≤ 8, the manual-gap diagnosis holds.
