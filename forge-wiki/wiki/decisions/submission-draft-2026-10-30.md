# Submission draft: story, numbers, 3-minute demo (DRAFT, blanks filled after the final exam)

**Summary**: draft by Claude, night of 2026-10-29 (user asleep; free work). Every number is either verified (source
given) or a blank `[…]` to fill from the final exam. Nothing here is submitted.

**Last updated**: 2026-10-29 night

---

## Must-do for the submission (verified: ~/.hivey/agent/hiveyAgent-wiki/wiki/user/meta-hackathon-2026.md)
- Public repo (ours is PRIVATE today: github.com/alyssaaa11/expertery) → make public, after a secrets scan
  (`git-scan-secrets` skill) — user's call.
- 3-minute demo video; all teammates listed; only new work counts.
- Deadline: that wiki says Nov 4, 9 PM ET (= Nov 5 03:00 CET); our internal deadline stays Nov 4 18:00 CET.
- Rubric: Impact 30 / Meta tooling 25 / Technical depth 20 / Demo 25. Must fit "Push the Frontier".

## One line
Forge turns a company's CAD tool and design rules into a small private model: Meta's big teacher practises, a strict
referee keeps only exactly-correct parts, and Muse Glimmer 30B learns them, so it designs parts on one GPU the company
owns, [N]× cheaper and faster than the best prompt tricks, at the same accuracy.

## Problem (Impact)
- Engineering firms keep CAD drawings and design standards secret; many cannot send them to a cloud AI.
- The only model that is private enough to run in-house is a small one. Spark Open (816B) needs ≥ 700 GB of GPU
  memory (verified, HF model card); Glimmer 30B in 4-bit is < 20 GB (verified, HF model card).
- Untrained Glimmer is already 87-95% correct with a long manual in the prompt, but slow and token-heavy: B-max
  needs 21,314 tokens and 295 s of model time per correct part (verified, bmax-baseline-2026-10-29).
- Fit to "Push the Frontier": a machine gets a new capability (designing real parts for manufacturing, checked
  geometrically), running where the physical work happens.

## What we built (Technical depth)
- A strict geometric referee (CadQuery; volume of the difference between answer and reference ≤ 1e-6 for training
  data; 0.2% for exams), with a cloud safety box: no AI-written code ever runs on the developer's machine.
- Four honest "is there a gap?" tests before training (scoreboard): Keel private tool 97.8%, CadQuery 87%/95%,
  FreeCAD 93%, a 40-rule company standard 89%, so we moved the claim from "more accurate" to "as accurate, much cheaper".
- Pre-registered rules for every test (written before running), paired bootstrap CIs, an exam-copy guard, a dev gate.
- Factory: 200 new practice jobs from 10 part families, teacher answers kept only if exact → [K] training examples.
- LoRA on one H100 ([M] min, $[x]), merged and served with vLLM.

## Meta tooling (25%)
- Muse Spark Open = teacher (Baseten); Muse Wonder = escalation for the hardest jobs ([X]% of data); Muse Glimmer 30B =
  the private student (Modal, then MLX offline).
- **Muse Code wrote all the code** from our specs (runner, cloud box, grader, training pipeline, dashboards), with an
  independent verifier agent checking every step. Count of Muse rounds and their cost: [from results/muse-*.jsonl].

## Result (fill after the final exam; bars pre-registered in experiments/bmax/PLAN.md rule 3)
| Arm | Accuracy (30 jobs, k=3) | Hard jobs | Tokens per correct part | Seconds per correct part | $ per correct part |
|---|---|---|---|---|---|
| Glimmer + hint, 1 try (B2) | 88% | 76% | 10,662 | 171 s | […] |
| Glimmer + every fair fix (B-max) | 95% → […] after finishing 30 jobs | 91% | 21,314 | 295 s | […] |
| **Trained Glimmer (Forge)** | […] | […] | […] | […] | […] |
Bars: (a) […] (b) […] (c) […] (d) […]. If a bar fails, the report says so in the same table.

## 3-minute demo (outline)
1. 0:00-0:20 The problem: a secret CAD standard, a model that can't leave the building.
2. 0:20-0:50 The referee: show a near-miss part (hole 1 mm off) rejected and the exact one accepted (side-by-side render).
3. 0:50-1:30 The factory live: teacher answers streaming in, referee ✓/✗, the dashboard count of kept examples.
4. 1:30-2:20 Before/after race: untrained Glimmer + manual (295 s, 21k tokens) vs trained Glimmer (… s, … tokens) on
   the same new job, both parts rendered and both PASS.
5. 2:20-2:45 The scoreboard: the 4 pre-registered bars, honest PASS/FAIL.
6. 2:45-3:00 "Your tool, your rules, your GPU": what a company would install.
Offline-on-a-Mac shot: only if it runs on the user's 24 GB Mac (the MLX q4 is ~15 GB and its card recommends ≥ 48 GB;
not tested, hypothesis: tight).

## Honesty section (keep in the submission)
- Distillation is a known method; ours is the verified-data factory, the fair baseline, and the private end-to-end tool.
- Spark via API is cheaper and faster per answer than any Glimmer we run (≈ $0.017, 18 s); the claim is about private
  deployment only.
- Medium jobs were already saturated (B2 100%); all the room is on hard jobs.
