# Muse Code round 1: cloud CadQuery box + factory (user 2026-10-30: "first the factory")

You are building part of experiments/final/MUSE_SPEC.md. Read it fully, plus experiments/factory/SPEC.md and
experiments/factory/PLAN.md. All rules in MUSE_SPEC.md "Rules" apply (no network, no Modal runs, no model calls, no
commit, never print keys, never open blind/ or experiments/option-a/, never print any expected*.json, do not edit
frozen files).

## Build in this round ONLY
- **§1** `experiments/final/cloud_cq.py`: cloud CadQuery box + grader (BREP, pinned cadquery==2.8.0
  cadquery-ocp==7.9.3.1), `--check-refs`, `--regrade` with the measure-equality column.
- **§2** the factory per experiments/factory/SPEC.md, with §2's changes: `generator.py`, `make_jobs.py`, `teacher.py`
  (teacher answers run in cloud_cq's box and are graded by its grader at 1e-6; nested cached_tokens; dev jobs file).
- **§4** the exam guard in experiments/train/forge_train.py uses cloud_cq's box for training-record code.
- **§5** the cached_tokens fix in experiments/freecad/runner_fc.py.

## Do NOT build in this round
§3 (runner_final.py), §3b (BX finisher), §6 (deploy/modal_forge.py, run_final_session.sh), §7 (compare.py). They
come in round 2.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common` passes (the old 150 plus the new tests).
- `~/projects/forge/.venv/bin/python experiments/factory/make_jobs.py` writes experiments/factory/jobs.jsonl
  (200 jobs, 10 families) and split.json (20 dev ids), and prints the 10-family self-check table (every reference
  valid, wrong variants FAIL at 1e-6, no job text with difflib ratio ≥ 0.9 to a first-test job text).
- `teacher.py --ids pilot --out X --budget-dollars 1` with no BASETEN_KEY exits 2 with the missing-variable message,
  no network.
- `forge_train.py smoke --cap-dollars 2.0` still prints CAP REFUSED and exits 2.

Report at the end: files changed, the pytest line, the self-check table, and anything you did not follow.
