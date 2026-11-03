# Bracket workflow test: is training better because it is cheaper to run? (pre-registered)

Status: written by Claude 2026-11-03 ~11:30 CET, BEFORE any model saw these jobs. Nothing here is run or paid yet.
Each paid step needs the user's yes. Frozen by the sha256 lines at the end (filled in at freeze, before the first call).

## Why (user, 2026-11-03)
The exam proved the technique on CAD. This test links it to a company benefit on one concrete workflow:
**an employee describes a mounting bracket and receives an editable CAD part (CadQuery code + STEP).**
decision (user, 2026-11-03): the claim to test is "training is better because of X", with X chosen before the run.
X = **lower operating cost per usable part, with no loss in quality**: the knowledge sits in the model's weights
instead of a rule card sent with every request. Prior evidence (exam, compare_ft_acard.json): one try, trained
3,352 vs card 4,145 tokens per correct part; prompt tokens 16k vs 80k in total.

## Jobs
20 requests in `jobs_brackets.jsonl` (sha below), written by Claude in an employee's words, each ending with one
placement line so the referee can grade it (10 medium, 10 hard). No bracket family is in the training data
(r5 families 1-10). Self-test: every reference builds as 1 solid, and dropping any single feature changes the part
by more than 0.2% (`python jobs_brackets.py --selftest`, 20/20 OK, 2026-11-03).
Fair note: the exam has 4 bracket-like jobs (M1, M11, H5, H14); the trained model never trained on the exam.

## Arms (identical except training vs card)
| Arm | Model | Prompt | Loop |
|---|---|---|---|
| **FTX** (Homegrown) | trained Glimmer r5f (/vol/r5f/merged), app forge-trained | short prompt, **no card** (FORGE_RULE_CARD unset) | same BX fix loop |
| **AX** (easiest alternative) | untrained Glimmer 30B, app forge-glimmer | short prompt **+ RULE_CARD.md** (sha in FREEZE) | same BX fix loop |
Both: A100-80GB, max_containers 1, same vLLM image, same sampling (temperature 1.0, top_p 0.95, top_k 64), max_tokens
16,000, loop reasoning xhigh, at most 3 rounds, reference-free feedback only, k = 3, 8 workers, cloud box + cloud
grader. Each arm runs once. A rerun is allowed only for an infrastructure failure (no model reply at all), stated.

## Measures
- **Usable part** = the delivered part passes the referee at 0.2% (answer XOR reference ≤ 0.2% of the reference volume).
- **Cost per usable part:** (1) total tokens / usable parts, split into prompt and completion; (2) wall seconds per
  usable part; (3) $ per usable part = Modal billing for the arm's session (before/after) / usable parts.
- Also reported: crashes, rounds per part, medium vs hard.

## Decision rules (paired bootstrap over the 20 jobs, 10,000 resamples, seed 20261103)
- **Quality condition (Q):** FTX − AX usable rate ≥ −10 points (point estimate). The 95% CI is always reported.
- **X holds** iff Q holds AND FTX tokens per usable part < AX's AND the 95% CI upper bound of the ratio
  FTX/AX (tokens per usable part) is < 1.
- Wording: if X holds → "same quality, N× cheaper to run per usable part". If Q holds but the cost CI crosses 1 →
  "same quality, cheaper on average, not significant on 20 jobs". If Q fails → reported as a loss for training on
  this workflow, unchanged. "Within 10 points" is never called "better".
- Never changed after the run. Stop rules: fewer than 60 finals in an arm → STOP, ask the user.

## Human check (optional, decided by the user)
A CAD user looks at one delivered part per job per arm (40), arm labels hidden, and records for each: usable as is
(yes/no) and minutes to fix. Reported next to the referee result, never replacing it.

## Budget
Muse Code (the two small code changes, specs/MUSE_BRACKETS_2026-11-03.md): cap $1.50 Meta credit.
Modal: cap $6 for both arms together (runner `--budget`, plus a billing check after the first arm).

## Freeze (sha256, filled before the first call)
