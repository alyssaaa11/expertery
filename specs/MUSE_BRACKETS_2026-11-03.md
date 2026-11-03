# Muse Code task: bracket workflow test (arm AX + compare script), 2026-11-03

Repo: ~/projects/forge. Plan (pre-registered, read it first): experiments/brackets/PLAN.md.
Files to change: experiments/final/runner_final.py and experiments/final/test_runner_final.py. New files:
experiments/brackets/compare_brackets.py and experiments/brackets/test_compare_brackets.py. Change NOTHING else
(in particular not jobs_brackets.py / jobs_brackets.jsonl / PLAN.md / RULE_CARD.md). Do not run any Modal, network or
model call. Run the tests with `.venv/bin/python -m pytest experiments/final experiments/brackets -q`.

## 1. Arm AX in runner_final.py
Goal: the untrained Glimmer (arm A endpoint GLIMMER_URL/GLIMMER_KEY, model A_MODEL) with the rule card gets EXACTLY
the same fix loop as arm FTX. Today `--bx-loop` is allowed only with `--arms FT`.
- New constant `AX_ARM = "AX"`.
- `run_ftx_suite(...)`: add keyword arg `arm_label=FTX_ARM` (default keeps today's behaviour byte-identical) and pass
  it to `do_bx_cloud_call(..., arm_label=arm_label)` and to `run_pairs(..., arm_label, ...)` in place of FTX_ARM.
- CLI: `--bx-loop` is now allowed with exactly `--arms FT` (arm FTX, as today) OR exactly `--arms A` (arm AX). Same
  exclusions as today (--fill-missing, --hints, --selffix). With `--arms A --bx-loop`: endpoint from GLIMMER_URL,
  key GLIMMER_KEY, model A_MODEL, `run_ftx_suite(..., arm_label=AX_ARM)`.
- Card guard (fairness): with `--arms A --bx-loop`, env FORGE_RULE_CARD must name an existing file, else
  parser.error("arm AX needs FORGE_RULE_CARD"). With `--arms FT --bx-loop`, FORGE_RULE_CARD must be unset or empty,
  else parser.error("arm FTX must run without the card"). Print the card's sha256 at start when it is used.
- Starting messages stay `ft_messages(job["text"])` for both arms (it appends the card when FORGE_RULE_CARD is set).

Tests (add; all existing tests stay green):
- `--arms A --bx-loop` with FORGE_RULE_CARD set calls run_ftx_suite with model A_MODEL, the GLIMMER endpoint and
  arm_label "AX" (mock run_ftx_suite / modal; no network).
- `--arms A --bx-loop` without FORGE_RULE_CARD → parser error; `--arms FT --bx-loop` with it set → parser error.
- run_ftx_suite with arm_label="AX": every final and round record has arm "AX"; round 1 messages equal
  ft_messages(text) and include the card text when FORGE_RULE_CARD is set (fake post/exec/grade fns).
- Default run_ftx_suite call still labels FTX (existing test).

## 2. experiments/brackets/compare_brackets.py
Reads the two run dirs and applies PLAN.md's decision rules exactly. Reuse experiments/final/compare.py
(load_calls, finals_for, per_job_rates, bootstrap_ci) instead of copying code.
Usage: `compare_brackets.py --ftx <dir> --ax <dir> --jobs experiments/brackets/jobs_brackets.jsonl
[--ftx-dollars D --ax-dollars D]` (dollars = Modal billing before/after per arm, typed in by hand; optional).
- Finals = records with bx_final True of arm FTX / AX for job ids in the jobs file. Either arm < 60 finals →
  print {"STOP": ...} and exit 3.
- Per arm: n, usable (pass at 0.2%, the record's existing verdict field used by compare.py), rate, medium/hard
  split, crashes, mean rounds per part, prompt / completion / total tokens summed over ALL rounds of every final
  (finals' bx_rounds or the round records: count every model call once), tokens per usable part (total, prompt,
  completion), wall seconds per usable part (sum of each final's elapsed seconds / usable), $ per usable part if
  dollars given.
- Paired bootstrap over the 20 jobs, 10,000 resamples, seed 20261103:
  (a) usable-rate difference FTX − AX (points): estimate + 95% CI (use compare.bootstrap_ci with that seed);
  (b) ratio FTX/AX of tokens per usable part: on each resample, sum tokens and usable counts over the resampled jobs
      per arm, ratio = (tokens_ftx / usable_ftx) / (tokens_ax / usable_ax); skip resamples where an arm has 0 usable
      (report how many were skipped); estimate on the full sample + 2.5/97.5 percentiles.
- Verdict fields: `Q` = (a) estimate ≥ −10; `X` = Q and ratio estimate < 1 and ratio CI upper < 1; `wording` =
  one of the three sentences in PLAN.md "Decision rules" chosen by those booleans.
- Writes compare_brackets.json next to the FTX dir's parent (or --out) and prints it.

Tests (experiments/brackets/test_compare_brackets.py, synthetic calls.jsonl in tmp dirs):
- Known toy data gives the hand-computed rates, tokens per usable part and ratio estimate.
- Tokens count every round once (a 3-round final counts 3 calls).
- < 60 finals → exit 3. Seed fixed → same CI twice. Zero-usable resamples are skipped and counted.
- Each of the three wording branches is reachable.

## Report back
Files changed, pytest summary line, and anything in the plan you could not do exactly (do not improvise silently).
