# Muse Code round 2: trained arm, BX finisher, serving, comparison (user yes 2026-10-30; verifier READY WITH 3 EDITS, applied: forge-muse-round2-prebuild-2026-10-30)

You are building the rest of experiments/final/MUSE_SPEC.md. Read it fully, plus experiments/final/PLAN.md and
experiments/final/cloud_cq.py (built in round 1, extended in 1d; use it, do not change its grading). All rules in
MUSE_SPEC.md "Rules" apply (no network, no Modal runs, no model calls, no commit, never print keys, never open blind/ or
experiments/option-a/, never print any expected*.json, do not edit frozen files: experiments/first-test/*,
experiments/b2-hint/*, experiments/bmax/*, deploy/modal_glimmer.py, experiments/thinking/*; import from them).
- **E1 (a factory run is LIVE while you build):** do not edit experiments/final/cloud_cq.py, experiments/final/run_cq_box.py,
  anything in experiments/factory/, or experiments/train/forge_train.py except the one filter in E3. Do not run
  make_jobs.py, teacher.py or patterns.py, and do not write anything under results/.

## Build in this round ONLY
- **§3** `experiments/final/runner_final.py` (arm FT on the same yardstick as the baselines).
- **§3b** the BX finisher (`--arms BX --fill-missing …`), cloud box + cloud grader, exit 3 when incomplete.
- **§6** `deploy/modal_forge.py` + `experiments/final/run_final_session.sh` (deploy, wait ready, cap with reserve,
  trap that always stops the app).
- **§7** `experiments/final/compare.py` (paired bootstrap, bars (a)-(d), refusals).
- **Decision guard, E3 (user, 2026-10-30: no Wonder output in training data, Meta API terms §10.1):** in
  experiments/train/forge_train.py's training-data loader only: drop (and count in the log) any record whose `teacher`
  is not `spark` (records without the field are refused unless they come from the factory's train_records.jsonl, which
  only holds Spark PASS answers), and refuse to start if any loaded file came from a run with `--escalate`. teacher.py is
  NOT edited this round (it would change factory_version). Tests for both.
- **E2, compare.py inputs (PLAN.md step 6, lines 81-92):** inputs are FT's run dir, the baseline dirs main-B2BX and
  main-BR, AND the step-6a BX-finisher dir; BX is merged over all 90 answers (no (job, rep) twice; refuse on a
  duplicate); refuse if any (job, rep) of BX is still missing or 6a ended INCOMPLETE; bar (d) uses BX tokens over all
  90 answers; BX wall-clock for "per correct part" = 3,050 s (baseline arm) + 6a's arm wall-clock without the cold
  start; report the 79-answer value next to it (disclosure).
- **N1:** runner_final writes `grader: first-test|factory` into every calls.jsonl record, and the dev summary prints
  the PLAN step-5 gate (dev ≥ 80% at 0.2% → GO, else STOP).
- Grading note: the exam (first-test) uses `checks.score` exactly as the baselines; the factory dev jobs use the factory
  grader (precise volumes, round 1d). Do not mix them.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common` passes (259 plus the new tests).
- `runner_final.py --jobs main --out X` with no keys exits 2 with the missing-variable message, no network.
- `forge_train.py smoke --cap-dollars 2.0` still prints CAP REFUSED and exits 2.
- the forge_train loader test shows a non-spark record is dropped and an --escalate run is refused.
Report at the end: files changed, the pytest line, and anything you did not follow.
