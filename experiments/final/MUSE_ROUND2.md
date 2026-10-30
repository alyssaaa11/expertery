# Muse Code round 2: trained arm, BX finisher, serving, comparison (DRAFT: waits for the user's yes + verifier)

You are building the rest of experiments/final/MUSE_SPEC.md. Read it fully, plus experiments/final/PLAN.md and
experiments/final/cloud_cq.py (built in round 1, extended in 1d; use it, do not change its grading). All rules in
MUSE_SPEC.md "Rules" apply (no network, no Modal runs, no model calls, no commit, never print keys, never open blind/ or
experiments/option-a/, never print any expected*.json, do not edit frozen files: experiments/first-test/*,
experiments/b2-hint/*, experiments/bmax/*, deploy/modal_glimmer.py, experiments/thinking/*; import from them).

## Build in this round ONLY
- **§3** `experiments/final/runner_final.py` (arm FT on the same yardstick as the baselines).
- **§3b** the BX finisher (`--arms BX --fill-missing …`), cloud box + cloud grader, exit 3 when incomplete.
- **§6** `deploy/modal_forge.py` + `experiments/final/run_final_session.sh` (deploy, wait ready, cap with reserve,
  trap that always stops the app).
- **§7** `experiments/final/compare.py` (paired bootstrap, bars (a)-(d), refusals).
- **Decision guard (user, 2026-10-30: no Wonder output in training data, Meta API terms §10.1):** teacher.py refuses
  `--escalate` (exit 2, message names the decision) and `build_train_records` drops any record whose `teacher` is not
  `spark`. Tests for both.
- Grading note: the exam (first-test) uses `checks.score` exactly as the baselines; the factory dev jobs use the factory
  grader (precise volumes, round 1d). Do not mix them.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common` passes (259 plus the new tests).
- `runner_final.py --jobs main --out X` with no keys exits 2 with the missing-variable message, no network.
- `forge_train.py smoke --cap-dollars 2.0` still prints CAP REFUSED and exits 2.
- `teacher.py --ids train --escalate …` exits 2.
Report at the end: files changed, the pytest line, and anything you did not follow.
