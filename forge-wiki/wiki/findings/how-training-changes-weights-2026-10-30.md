# How training changes Glimmer's weights, and which knobs you drive

**Summary**: plain-words guide (user asked 2026-10-29 night: "how to change the weights, important to know to drive it
correctly"). What one training step does, what LoRA changes, every knob in our pipeline with its value, and what to
do when a number looks wrong. Diagram: `forge-wiki/wiki/assets/diagrams/forge-how-training.png`.

**Sources**: experiments/train/forge_train.py (lr 1e-4, r 16, alpha 32 at lines 566-568; cosine schedule lines
687-693); Glimmer sizes from ~/models/muse-glimmer-30b-radixark-q4-mlx/config.json (hidden 6,656, MLP 19,968,
52 layers); smoke test [[training-smoke-2026-10-29]] (104.8M trainable, loss 1.03 → 0.33); research
[[learn-training-and-verifiers-2026-10-29]].

**Last updated**: 2026-10-30

---

![[assets/diagrams/forge-how-training.png]]
Interactive (zoom, dark mode): `forge-wiki/wiki/assets/diagrams/forge-how-training.html`.

## 1. What "weights" are
Glimmer is ~29.6 billion numbers (weights) arranged in big tables (matrices), 7 tables in each of its 52 layers.
Reading a job, it turns each word piece (token) into a list of 6,656 numbers and pushes it through the tables. At
the end it gives a probability for every possible next token (202,048 of them). Writing an answer = picking a
token, appending it, repeating. Everything Glimmer "knows" is in those numbers. **Training = nudging the numbers so
the correct next token gets a higher probability.**

## 2. One training step (the loop in the diagram)
1. **Example in.** Job text + the teacher's correct code (only referee-passed, exact to 1e-6).
2. **Guess.** Glimmer reads the job and, at every position of the correct code, guesses the next token.
3. **Score the guess (loss).** If it gave the correct token 90% probability, the loss is small (0.1); if 1%, the loss is
   big (4.6). Loss = −log(probability of the correct token), averaged over the answer tokens only. The job text
   itself is not scored: we teach answering, not copying the question.
4. **Blame (gradient).** Backpropagation computes, for each trainable number, "if I raise you a tiny bit, does the loss
   go up or down, and how much?"
5. **Nudge (optimizer step).** Each trainable number moves a small step in the direction that lowers the loss. The
   size of that step is the **learning rate**. We add up 8 examples before each nudge (**gradient accumulation 8**),
   so one odd example can't yank the weights.
6. Repeat over all examples, twice (**2 epochs**).
Smoke test (verified): the loss fell 1.03 → 0.33 in 8 steps. Falling loss = the model is giving the teacher's answers
more probability.

## 3. LoRA: we don't touch the 29.6B numbers
Changing all 29.6B numbers needs ~4× the memory of the model (no single GPU can) and can wreck what Glimmer already
knows. LoRA freezes all of them and adds a small **patch** next to each big table:
- Example: one MLP table in one layer is 6,656 × 19,968 ≈ **133 million** numbers (W).
- The patch is two thin tables: A (16 × 6,656) and B (19,968 × 16), ≈ **426 thousand** numbers, 0.3% of W.
- The table's output becomes W·x + (alpha/r)·B·A·x. Only A and B learn. **16 = the rank r**: how many "directions of
  change" the patch can express. alpha/r = 32/16 = 2 is how loudly the patch speaks.
- B starts at zero, so at step 0 the trained model is exactly Glimmer; it drifts away only as far as the data pushes.
- In total: **104.8M trainable numbers (0.35%)** across the 7 table types of all 52 layers (verified, smoke test).
- **Merge:** after training, W' = W + 2·B·A is computed once for every table. The result is a normal Glimmer-sized
  model with no patch and no extra cost per answer. (We merge because vLLM crashes loading a separate patch.)

## 4. The knobs you drive (our values, what happens if you turn them)
| Knob | Ours | Too low | Too high |
|---|---|---|---|
| **Data quality** (referee 1e-6) | exact only | — | the most important knob: one wrong example teaches a wrong habit; papers: 8k clean > 70k medium |
| **Data variety** | 10 families, ~150 jobs, 1 answer each | model learns one family's shape only | — (more different jobs is good; copies of the same job are bad) |
| **Learning rate** | 1e-4, warm-up 5%, then cosine down | loss barely moves; nothing learned | loss jumps around or explodes; model forgets general skills |
| **Epochs** (passes over data) | 2 | under-learned: dev low, train loss still high | memorises: train loss near 0, dev drops (overfitting) |
| **Rank r / alpha** | 16 / 32 | patch too small to hold the skill | more memory, easier to overfit small data |
| **Grad accumulation** | 8 | noisy nudges | fewer nudges per epoch (slower learning) |
| **Max tokens per example** | 4,096 | long examples dropped (count is logged) | GPU runs out of memory (8,192 did, smoke test) |
| **Prompt format** | short: system + job, no manual | — | must be identical at training and at the exam, or the model is confused |

## 5. How to read the run (what to watch, what to do)
- **Loss falls smoothly, e.g. ~1.0 → ~0.2-0.4:** normal. hypothesis: our final loss will be in that range.
- **Loss flat from the start:** learning rate too low or the loss is not on the answer tokens → check the train log's
  "first 40 tokens that carry loss" (it logs them).
- **Loss near 0 quickly:** memorising; trust the dev check, not the loss.
- **Dev check ≥ 80%:** go to the exam. **Below:** stop (pre-registered). The usual next try is more varied data or
  epochs 3 — a new run needs your yes; we never tune on the exam.
- **Answers never stop / get cut off at the limit:** the end-of-answer token was not trained. Check the rendered
  example ends with Glimmer's end token (logged in train_log.json).
- **Peak memory > 76 GB after step 1:** the run stops itself (built in); shorten examples.

## 6. What training can and cannot do (honest)
- It moves the manual's knowledge into the weights, so the prompt can drop 5,700 tokens and retries. That is where
  the "cheaper and faster" comes from.
- It copies the teacher's style; it does not make Glimmer smarter than the teacher. Learning from failures (DPO) or
  from the referee as a reward (RL) are the next levels and cost far more ([[learn-training-and-verifiers-2026-10-29]]).
