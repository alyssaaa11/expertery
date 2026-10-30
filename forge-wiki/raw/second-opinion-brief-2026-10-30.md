# Second opinion request: why did training make Glimmer worse, and what is the best fix now? (2026-10-30 ~17:20)

You are asked by Alyssa (the user) for an independent judgment. Read-only: do not run anything that costs money
(no Modal, Baseten, Meta API, muse calls), do not edit files in ~/projects/forge except your answer file.

## Project (Meta hackathon, submit Nov 4; Alyssa's internal target: trained result by Nov 1 evening)
Forge = a "factory" that makes a small private model good at a company tool:
practice jobs → a teacher (Muse Spark Open 816B, on Baseten) writes CadQuery code → each answer runs in a locked cloud
box and a strict referee (1e-6) keeps only correct parts → the student (Muse Glimmer 30B, open weights; Meta distilled
Glimmer from Spark) is LoRA-trained on the kept answers. Goal: trained Glimmer as correct as "B-max" (base Glimmer +
5.7k-token manual + hint + up to 5 self-checks = 95% on a frozen 30-job exam) but many times cheaper/faster.
Baselines on the exam: base Glimmer plain 87%, + hint 88% (hard jobs 76%), B-max 95%.
CadQuery is the demo tool; the factory method is meant to be tool-agnostic. FreeCAD was tested Oct 29: Glimmer 93% vs
Spark 100% (no gap), and a FreeCAD "thinking" exam was too easy (Glimmer 8/9), so the project stayed on hard CadQuery.

## What happened today
- Factory: 200 jobs, 10 families; Spark answered 177, 167 passed the referee (94%). Training set = 167 records of
  {job text → Spark's extracted code only}. Spark's reasoning TEXT was not stored (only reasoning token counts, ~3k).
- Training: LoRA r16/a32, lr 1e-4, 2 epochs, 42 optimizer steps, loss 0.42 → ~0.2. Short prompt (system + job text,
  no manual). The training target = assistant answers the user directly with the code (no reasoning / "to=self" turn).
- Practice test (20 hidden factory dev jobs × 3 tries): **trained Glimmer 23/60 = 38%** (gate was 80%) → STOP; exam untouched.
  0 reasoning tokens in all 60 answers; ~390 completion tokens each. It copies the teacher's style and even its
  comments ("extended slightly to ensure open ends") but gets geometry wrong (e.g. builds an X-axis tube along Z,
  uses centred boxes when the text says "corner at origin", parts not fused).
  Format check on 3 easy exam-style jobs: trained 0/3; base Glimmer passed D1, D2 earlier with ~1.3k reasoning tokens.
- Base Glimmer on the 20 dev jobs was NOT measured.

## Evidence (read these)
- ~/projects/forge/results/dev-2026-10-30/dev-FT/calls.jsonl, summary.json (the 60 answers); pilot-D/calls.jsonl
- ~/projects/forge/results/train-final/train.json (training config, loss per step, rendered first example)
- ~/projects/forge/results/factory-train-2026-10-30/train_records.jsonl (the 167 examples)
- ~/projects/forge/experiments/final/PLAN.md (pre-registered rules), forge-wiki/wiki/status.md (state, money)
- Verifier's reading: ~/agents/verifier/reports/forge-dev-result-2026-10-30.md

## Options on the table (money left ≈ $18 of $65; ≈ 4 days)
1. Pre-registered retry: same data, 3 epochs. (Verifier and I think it does not fix the cause.)
2. Self-distillation (verifier's pick): base Glimmer answers the 160 training jobs WITH its own reasoning; keep only
   referee-passed ones; train on reasoning + code. ≈ $3-4. Also measures base Glimmer on factory jobs for free.
3. **Teacher-reasoning distillation (Alyssa's idea, my current pick):** keep Spark as the teacher, re-run the factory
   capturing Spark's reasoning text (or, if Baseten does not return it, ask Spark for a short "Plan: steps" before
   the code); train Glimmer on reasoning/plan in its thinking slot + code as the answer, so it learns HOW, not just
   the answer. ≈ $7.5. Risk: Baseten may not return reasoning text; reasoning makes answers longer (cost goal).
4. Manual in the training prompt (does not fix reasoning; gives up the "much cheaper" bar).

## Questions for you
a) Is our diagnosis right (answer-only targets removed the reasoning turn and taught style, not skill)? Anything
   else wrong in the training method (data size 167, LR, epochs, loss masking, chat template, serving)?
b) Which option is best for a correct, honest result by Nov 1 evening, and why? Would you change it (e.g. mix:
   Spark's plan + Glimmer's own reasoning, more data, a short "plan" instead of full reasoning)?
c) What single cheap check should run first to de-risk it?
Write your answer (≤ 1 page, plain words, with a clear recommendation) to
~/projects/forge/forge-wiki/raw/second-opinion-answer-2026-10-30.md and say "DONE" when finished.
