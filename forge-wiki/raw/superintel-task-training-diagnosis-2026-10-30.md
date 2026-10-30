# Task for superintel: why does our fine-tuning not make Glimmer better? (from Alyssa via the Forge coordinator, 2026-10-30)

Goal: find the MAIN reason our LoRA training of Muse Glimmer 30B does not beat the untrained model, using our real data
and the research literature (distillation, rejection-sampling fine-tuning, reasoning distillation, LoRA data size,
small-data SFT, on-policy vs off-policy, chat-template / reasoning-channel effects). Then recommend the single best
next training recipe we can afford: ≈ $20-25 left (Baseten Spark ≈ $0.03 per long worked solution; H200 $4.54/h;
A100 $2.50/h), result needed by Nov 1 evening (hackathon deadline Nov 4).
Read-only on ~/projects/forge (do not edit files there, do not run anything paid: no Modal, Baseten, Meta API, muse).
You may run local Python on the result files for analysis. Write your answer to
~/projects/forge/forge-wiki/raw/superintel-answer-training-diagnosis-2026-10-30.md (≤ 2 pages, plain words, cited
papers with arXiv ids, a ranked list of causes with the evidence for each, and ONE recommended recipe with numbers).
Also file the lesson in your own wiki as you normally do.

## The project in 6 lines
Forge = a factory that makes a small private model good at a CAD tool (CadQuery): practice jobs → a teacher (Muse Spark
Open 816B on Baseten, reads a 5.7k-token CadQuery manual) writes code → each answer runs in a locked cloud box → a
strict referee keeps only correct parts → the student (Muse Glimmer 30B, open weights; Meta distilled Glimmer from
Spark) is LoRA-trained on the kept answers. Goal: trained Glimmer with a SHORT prompt (no manual) as correct as
"B-max" (Glimmer + manual + hint + up to 5 self-checks = 95% on a frozen 30-job exam), but cheaper.

## Results (all on the same 20 hidden factory "dev" jobs × 3 tries, strict referee, short prompt, no manual)
| Model | Pass | pass@3 | tokens/correct | crashes (invented API) |
|---|---|---|---|---|
| Untrained Glimmer (arm A) | **51.7%** | 85% | 9.2k | 7 |
| R1: trained on 167 × {job → Spark code only} | 38.3% | 75% | 1.7k | many |
| R3: trained on 154 × {job → Spark thinking (~5k tok, in Glimmer's to=self turn) → code} | 48.3% | 85% | 14.8k | 15 |
Exam context: untrained Glimmer short prompt 53% (16/30); + manual 67-87%; B-max 95%; Spark 100%.

## Training details (identical for R1 and R3 except data/format/GPU)
LoRA r 16, alpha 32, all attention + MLP projections of the language model (104.8M trainable of ~30B), lr 1e-4,
grad accumulation 8, 2 epochs, loss on assistant tokens only (prompt masked). R1: H100, max 4,096 tokens, 42 steps,
loss 0.42 → ~0.2. R3: H200, max 12,288 (5 of 159 dropped), 39 steps, loss 0.95 → ~0.69. Training prompt = serve prompt
(system line + 'Reasoning strength: high.' template default + job text). Format check verified for R3: first loss
tokens ' to', '=self' (thinking turn first). Teacher prompt = system + "Here is the CadQuery manual. Use it." + manual
+ job; the student never sees the manual. 101/154 of Spark's reasonings mention "manual"; reasoning names real API
args (yDir in 61/159, inPlane in 62/159 records) that the trained student then attaches to the wrong calls.

## Data (all under ~/projects/forge)
- Training sets: results/factory-train-2026-10-30/train_records.jsonl (R1, code only),
  results/factory-r3-train-2026-10-30/train_records.jsonl (R3, with "reasoning"). Raw teacher calls with usage:
  results/factory-*-2026-10-30/calls.jsonl, summary.json.
- Training logs: results/train-final/train.json (R1), results/train-r3/train.json (R3): loss per step, rendered first
  example, first loss tokens.
- Dev answers: results/dev-2026-10-30/dev-FT/ (R1), results/dev-r3-2026-10-30/dev-FT/ (R3),
  results/dev-base-2026-10-30/dev-A/ (untrained): calls.jsonl (code, verdict, fails, run_error, usage, reasoning_len),
  summary.json. Pilot on 3 easy exam jobs: */pilot-D/.
- Jobs: experiments/factory/jobs.jsonl (200 jobs, 10 families), split.json (20 dev ids); generator.py can make more.
- Code: experiments/train/forge_train.py (training), experiments/factory/teacher.py, experiments/final/runner_final.py.
- Plans/decisions: experiments/final/PLAN.md (incl. "Retry R3"), forge-wiki/wiki/status.md.
- Verifier reports: ~/agents/verifier/reports/forge-dev-result-2026-10-30.md, forge-r3-dev-result-2026-10-30.md.
- Second opinion: forge-wiki/raw/second-opinion-answer-2026-10-30.md. Rule-card idea: experiments/final/RULE_CARD.md.

## Candidate plans already on the table (judge them)
1. R4 "many short worked solutions": Spark with 'Reasoning strength: low' (shorter thinking), ~900 new jobs from the
   generator, the ~400-token rule card in BOTH teacher and student prompts, 3 epochs. ≈ $20-25.
2. Self-distillation / rejection sampling from base Glimmer + manual (generate with manual, train without).
3. Teacher corrects the student's failures (on-policy: Spark solves the jobs trained Glimmer fails).
4. No training: Glimmer + rule card in the prompt.

## Questions
a) What is the main problem (rank the causes): data size (154), off-policy teacher style, the manual gap (teacher
   sees the manual, student does not), long reasoning targets, LoRA settings (r, lr, epochs, which layers), template /
   sampling, evaluation noise (60 answers), something else? Use the files to support each claim.
b) Which recipe gives the best chance to beat untrained Glimmer clearly (≥ +10 points on dev) within ≈ $20-25 and one
   day? Exact numbers (examples, reasoning length, epochs, lr, r).
c) What quick, cheap check proves the diagnosis before spending?
