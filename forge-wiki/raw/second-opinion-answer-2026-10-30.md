# Second opinion: why training made Glimmer worse, and the best fix (2026-10-30, independent Claude, read-only, $0)

**Recommendation in one line:** don't retry with 3 epochs, and don't pay for Spark's reasoning yet. Run one cheap base-Glimmer
session on the 20 dev jobs first (≈ $0.5-0.8). Then do **self-distillation with the manual in the generation prompt and
without it in the training prompt**: base Glimmer + manual (+ hint) answers the training jobs with its own reasoning, the
referee keeps the correct ones, and Glimmer is trained on reasoning + code with the short prompt. ≈ $3-5 in total.

## a) Is the diagnosis right?
Yes, and the mechanism is sharper than "no reasoning in the data":
- verified: the first loss tokens of every example are ` to` `=user` (results/train-final/train.json, `first_loss_tokens`).
  So all 167 examples rewarded one decision first: "after `assistant`, skip the thinking turn and answer". The system
  prompt still says "Reasoning strength: high", and the model learned to ignore it. 0 reasoning in 60/60 answers fits this.
- verified: the skill lives in the reasoning. Example F8-6 (dev): the trained model copied all the hole coordinates
  correctly but built all four tabs at the origin (`box(..., centered=False)` with no move). It reads the numbers but
  skips the bookkeeping that the thinking turn used to do. It imitated Spark's *look* (comments, layout), not the work
  behind it, and Spark's work was never in the data.
- **One correction to the framing (verified, experiments/bmax/PLAN.md:20):** "plain Glimmer 87%" is arm BR = **manual +
  job**. Base Glimmer with the short prompt and no manual (first-test arm A) got **16/30 = 53%** on the exam. So the
  training was asked to replace a 5.7k-token manual *and* to keep the reasoning, starting from about 53%, not 87%. The
  80% dev gate was always a big jump. Write this in the report.
- Other parts of the method look fine and aren't the cause. Loss masking covers only the assistant tokens (correct).
  LR 1e-4, r16 and 2 epochs are normal, and 167 examples are enough to learn a format, which is exactly what happened.
  Loss falling to about 0.2 means it memorised Spark's style. 3 epochs would push further in the same wrong direction.
  hypothesis: temperature 1.0 hurts more without a thinking turn, because sampling noise goes straight into the
  coordinates. A minor effect. D3 (served sampling + image digest) is still open.

## b) Best option for a correct, honest result by Nov 1
**Option 2, upgraded (context distillation + rejection sampling).** The reasons:
1. **On-policy:** the reasoning is Glimmer's own: its words, its length, its `to=self` channel. Training on its own
   correct traces strengthens the thinking turn instead of replacing it. This is a well-known recipe that works
   (STaR / rejection-sampling fine-tuning).
2. **Generate *with* the manual (+ hint), train *without* it.** Glimmer + manual is 87-95% on the exam, against 53% without
   it, so the data yield is much higher, especially on hard jobs. The model learns to answer without the 5.7k-token
   manual. That is exactly the stated goal: B-max quality from a short prompt.
3. **Cheapest and no unknowns:** no Baseten risk, and it runs on the Modal stack you already have. It also measures base
   Glimmer on factory jobs.
4. **Cost goal still holds:** a trained model with about 1.5-3k reasoning tokens and a ~220-token prompt is still several
   times cheaper per correct part than B2 (10.7k) or BX (21.3k). Keep the **shortest** passing trace per job to push
   the length down.

Why not option 3 now: you don't know yet whether Baseten returns Spark's reasoning text, and a "Plan:" prompt is a
different output from Spark's real thinking. It would also use $7.5 of the $18 left, and the result is still off-policy
imitation from 167 examples. Keep it as plan B if self-distillation gives too few correct traces on hard families (F5,
F8, F10). Honest story either way: **the referee is the real teacher.** Spark supplies verified answers, and the new
part is referee-verified data. Glimmer generating its own traces doesn't weaken that.

Training details to get right (each one could quietly sink the retry):
- The target must be `assistant to=self<|message|>{reasoning}<|eot|><|start|>assistant to=user<|message|>{code}`, with
  the loss on both parts. **Check this free first:** run one stored base answer through the chat template and compare
  it token by token with what vLLM serves.
- **Memory:** the smoke test ran out of memory on an 8,192-token step. Drop traces over about 6k tokens. The shortest-trace
  rule helps here.
- Remove or skip traces whose reasoning quotes the manual ("the manual says…"), because the student won't have it.
- Up to 2 passing traces per job (about 250-320 examples), same LR, 2 epochs. Pre-register the target and the dev gate
  before the next dev run, and say openly that the dev set is now "seen".

## c) The one cheap check to run first
**One Modal session on the same stack as modal_forge (D3 captured), base Glimmer on the 20 dev jobs × 3, in two arms:
A (short prompt) and B2 (manual + hint).** ≈ $0.5-0.8. It answers three questions at once:
- A against FT 38%: did training make it worse?
- B2's pass rate: how many correct traces will the generator give? (≥ 80% → go.)
- whether 80% on dev is reachable at all. If even B2 is below about 75% on factory jobs, these jobs are harder than the
  exam, so the gate (not the method) needs a new user decision before more money is spent.

Then: if B2 ≥ 80% → generate traces on the 160 training jobs (k = 2-3) → train → dev check. Otherwise → report the honest
finding, with option 3 as the only paid fallback.
