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
   appears in the first rendered training prompt. Without --no-card everything stays exactly as today (tests).
2. build_mix.py `--drop-card-mentions`: drop rows whose reasoning mentions the card ("rule card", "card says",
   "per the card", "cheat sheet", case-insensitive) or copies ≥ 8 consecutive words of experiments/final/RULE_CARD.md;
   count the drops per source and print them.
3. Tests (offline, fake tokenizer): the no-card render has no card text and equals the no-card FT prompt; the default
   path is unchanged; the card-mention drops; the estimate without the card is smaller than with it.

## Report back
Files changed, pytest count (today 384 across final, factory, freecad, train, r5, common, viewer), and the exact
command for training with --no-card. Do not run anything paid.
