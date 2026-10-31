# Muse Code round R5c: train WITHOUT the rule card (user decision 2026-10-31, option B; PLAN "Plan change: option B")

Rules: all of experiments/final/MUSE_SPEC.md "Rules" (no network, no Modal runs, no model calls, no commit, never print
keys, never open blind/ or experiments/option-a/, never print any expected*.json). **Do not edit
experiments/final/run_base_session.sh, runner_final.py, cloud_cq.py or RULE_CARD.md: a paid run is using them now.**

Read first: experiments/r5/PLAN.md (section "Plan change: option B"), experiments/train/forge_train.py (run_full_r5,
require_rule_card, _r5_messages, count_r5_row_tokens, apply_budget_headroom, check_format, the R5 card checks),
experiments/r5/build_mix.py, experiments/r5/test_r5.py.

## Build
1. forge_train.py `full-r5 --no-card`: R5 rows render with the FT system prompt WITHOUT the card (exactly what
   runner_final.ft_messages sends when FORGE_RULE_CARD is unset). With --no-card: no card file is required in the image
   or checked, the token estimate and the 75% rule count the system prompt without the card, check_format's
   prompt_matches_ft compares against the no-card FT prompt (must be True), and an assert fails if the card text
   appears in the first rendered training prompt. The reference FT prompt for the format check must be built with
   FORGE_RULE_CARD UNSET (pop it from the environment for that call), even if it is exported in the shell [S2]. Without --no-card everything stays exactly as today (tests).
2. build_mix.py:
   - `--drop-card-mentions`: drop rows whose reasoning NAMES the card ("rule card", "card says", "per the card",
     "cheat sheet", "the card", case-insensitive). Do NOT drop rows that only quote or follow true rules (that is the
     point of option B; verifier S3: 170/188 pilot-v2 passes quote rules). Print the drop share per source and STOP
     (non-zero exit) if more than 20% of rows are dropped.
   - `--first` is repeatable (pilot v2 calls.jsonl + rest-run calls.jsonl) [S1]. Refuse records from the v1 pilot
     (results/r5-pilot-2026-10-31/: prompt_tokens < 900 means card v1 or no card) with a clear error.
3. Tests (offline, fake tokenizer): the no-card render has no card text and equals the no-card FT prompt; the default
   path is unchanged; the card-name drops (and that rule-quoting rows are kept); the >20% stop; repeatable --first; v1 refusal; the estimate without the card is smaller than with it.

## Report back
Files changed, pytest count (today 384 across final, factory, freecad, train, r5, common, viewer), and the exact
command for training with --no-card. Do not run anything paid.
