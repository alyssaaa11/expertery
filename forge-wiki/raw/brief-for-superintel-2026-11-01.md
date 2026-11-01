# Brief for superintel: validate the R5 training before we spend (2026-11-01)

Question from the user: "before training, tell superintel how the project is going so he can validate if the training
will go well / get good results". Please give a go / change / no-go view on the training recipe below, and predict the
dev result with reasons.

## Where we are (verified; sources in repo)
- Your 10-30 recipe (card-conditioned self-distillation, raw/superintel-answer-training-diagnosis-2026-10-30.md) was
  adopted with changes. Plan: experiments/r5/PLAN.md ("Plan change: option B"). Verifier reports:
  ~/agents/verifier/reports/forge-r5-*.md.
- New factory sets: R5T 2,000 training jobs + R5D 100 held-out dev jobs (10 families, new seeds, deduped vs exam).
- Rule card v2 (experiments/final/RULE_CARD.md, ~420 tokens; 2 lines added after pilot crashes: Workplane vs Solid,
  makeCylinder positional). Base Glimmer + card on R5T: v1 pilot 149/200 = 74.5% (47 crashes) → v2 pilot 188/200 = 94%
  (3 crashes, in-sample) → rest run **1694/1800 = 94.1%** (35 crashes). Weakest families F4 82%, F1 88%, F8 90%.
- Data: 1,882 PASS answers with full reasoning (Glimmer's own, generated WITH card v2, k=1, temp 1.0). After dropping
  rows whose reasoning names the card: 1,678 first-try rows, 6.01M tokens (verifier dry mix).
- Earlier trainings (for contrast): R1 Spark code-only 167 rows → 38.3%; R3 Spark reasoning 154 rows → 48.3%; base A
  (no card) 51.7% on the old 20-job dev set.

## The training we are about to run (user said yes)
1. Self-fix: 118 first-try FAILs retried once by base Glimmer + card with reference-free feedback (crash tail, solid
   count, own volume/bbox) → PASS retries become self-fix rows (prompt = job + wrong code + feedback).
2. LoRA SFT on Glimmer 30B: r 16, alpha 32, all attn+MLP proj, lr 1e-4, 2 epochs, max 8,192 tokens, H200, loss on
   thinking + code, prompt = short system prompt WITHOUT the card (context distillation). ≈ $9-11.
3. Dev on 100 R5D, k=1: arms A (no card), A + card v2, FT (no card). Pre-registered: FT − (A + card) ≥ −3 (CI lb ≥ −10)
   = "as good as the card"; FT − A ≥ +10 = "beats plain"; completion tokens per correct FT ≤ A + card = "cheaper";
   FT thinking ≥ 200 chars in ≥ 90% else STOP.
4. Exam once (30 hand-made jobs; Glimmer + 5.7k manual = 88%, + all fixes = 95%).

## Questions for you
1. Will context distillation of ~1.7k self-generated rows (2 epochs, LoRA r16) likely make FT (no card) ≈ A + card on
   held-out R5D? Risks (overfit to 10 families? the 6% of jobs it never solved are absent from training = bias toward
   easy jobs? temp-1 samples as targets?).
2. Hyperparameters: keep 2 epochs / lr 1e-4 / r16, or change (e.g. 1 epoch, lr 5e-5) given 6M tokens?
3. Should we filter/limit rows per family (F2/F7 are ~100% easy) or upweight hard families?
4. Does dropping the 11% card-naming rows bias the data?
5. Transfer to the exam (hand-made, different families): realistic expectation?
6. Anything that should STOP us before spending ~$11.
Please answer in forge-wiki/raw/superintel-answer-r5-validation-2026-11-01.md and reply to hivey/master with a 5-line summary.
