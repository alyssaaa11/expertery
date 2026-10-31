# R5: large-data SFT of Glimmer on Modal (ACCEPTED by the user 2026-10-31, pending verifier review; nothing run)

Why: the R1/R3 trainings used 154-167 examples. Generative code needs thousands (Fireworks workshop, transcript
[01:02:02]; Meta Glimmer post-training guide: ≥ 500, 5-10k for strong domain results). Free data exists:
gudo7208/CAD-Coder (Apache-2.0, arXiv 2505.19713). Wiki: findings/huggingface-cadquery-data-2026-10-31.md.
User decisions (2026-10-31): train more BEFORE the exam, with large data; use Modal (no Fireworks); **Modal budget
$90** (Modal billing ≈ $19.9 so far). **This is the last training method**: whatever the exam says is what we submit.

## Data (all built in the cloud; dataset code never runs on the Mac)
1. Download CAD-Coder `cad_data_train_high.json` (8,177) + `cad_data_train_cot.json` (1,503) straight into a Modal volume.
2. Validity: run every code in the CadQuery 2.8 cloud box; keep rows that build exactly one valid solid within 60 s.
   Exam guard on every row (refuse exam look-alikes; abort if > 5% refused). Report kept / dropped per file. Cap $3.
3. Own-words rows: base Glimmer + rule card answers ≈ 1,000 NEW factory jobs (new seed, 0 overlap with dev/exam ids),
   k = 1, more workers per GPU (first a 64-worker throughput pilot on 50 jobs; continue only if ≤ $0.006 per answer).
   The referee (0.2%) keeps the correct ones, with Glimmer's reasoning kept in `reasoning_content`. Cap $10.
2b. Spark hints (user idea + yes, 2026-10-31): for each factory job whose Glimmer answer FAILED in step 3, send Spark Open
   (Baseten) the job text + Glimmer's attempt + the referee's failed checks; Spark returns a SHORT HINT only (≤ 60 words,
   no code; reject replies with code fences or `cq.`). Glimmer retries once with the hint appended to the user message.
   If the referee passes it, keep that answer, but train it WITHOUT the hint (prompt = the plain job prompt + card), so
   Glimmer learns to solve it alone. Spark never appears in the product. Log hint, retry verdict, $ per hint.
   Cap: Baseten $10 (≈ 300 hints × ≈ $0.03), Glimmer retries inside the step-3 Modal cap + $5.
4. Mix: all valid CoT rows + factory own-words rows (with reasoning) + valid high rows (code only). Same system prompt
   for every row = short prompt + rule card. Logged: rows per source, tokens, and the rendered first example of each source.

## Training
LoRA r 16, alpha 32, lr 1e-4, 2 epochs, max 8,192 tokens, loss on thinking + code; H200. Log loss per step, the first
loss tokens per source (to check that the thinking turn is kept), and Modal billing before/after. Cap $30.

## Dev check (pre-registered; the gate before the exam)
New 100 factory dev jobs (fresh seed, never seen), k = 1, arms A + card and FT + card, same runner/referee/16,000 tokens.
- FT+card − A+card ≥ +6 points → GO to the exam.
- < +6 → STOP, report honestly; the exam is still run once on the best arm (user rule: no method 5). Cap $8.
- Also report: share of FT answers with a non-empty thinking turn (must be ≥ 90%, else flag "thinking suppressed").

## Final exam (frozen rules: experiments/final/PLAN.md step 6, unchanged). Cap $4.

## Money
Modal caps: 3 + 10 + 5 (hint retries) + 30 + 8 + 4 = $60 worst case (≈ $80 of the $90 Modal budget). Baseten
(Spark hints): cap $10, outside the Modal budget (user yes, 2026-10-31). Muse Code (writes the scripts, user
rule) is billed by Meta, not Modal: estimate ≈ $3-5, to be confirmed by the user.

## Risks (stated up front)
- Style shift: CAD-Coder texts are normalised sketch-and-extrude steps, not mm parts with coordinates.
- Code-only rows may suppress thinking (R1 lesson): mitigated by the CoT + own-words rows and the thinking check.
- Licence lineage: CAD-Coder is Apache-2.0 but built from Text2CAD (CC-BY-NC-SA): disclose in the README.
