# Muse Code round 2b: small fixes before the dev check (verifier E2, E3, T4) — verifier READY WITH 2 EDITS (B1, B2 applied, forge-round2b-prebuild-2026-10-30); waits for the user's yes

Read experiments/final/MUSE_ROUND2.md, experiments/final/compare.py, experiments/train/forge_train.py (loader),
experiments/factory/teacher.py and patterns.py. All rules in experiments/final/MUSE_SPEC.md "Rules" apply (no network,
no Modal runs, no model calls, no commit, never print keys, never open blind/ or experiments/option-a/, never print any
expected*.json). Do not edit experiments/final/cloud_cq.py, run_cq_box.py, generator.py, make_jobs.py, jobs*.jsonl,
split.json, or anything under results/. Nothing is running now.

## Build in this round ONLY
1. **E2 test (compare.py):** a test with 79 baseline BX records + 11 step-6a fake BX records: bar (d) is computed over all
   90; a duplicate (job, rep) refuses; an INCOMPLETE 6a refuses. Fix compare.py only if the test shows a bug.
2. **E3 real guard (forge_train loader):** train_records.jsonl holds only {id,text,code}, so the file-name rule is not a
   real check. The loader cross-checks the run's sibling calls.jsonl (same folder; for a merged file, a `sources.json`
   next to it listing the run dirs): keep only ids with a PASS call whose teacher == "spark"; print kept/dropped ids;
   refuse if no calls.jsonl/sources.json is found. **B1:** the trusted smoke examples (the file `run_smoke` loads) are exempt by explicit path, because
   `run_smoke` loads them before the cap check; the free `smoke --cap-dollars 2.0 → CAP REFUSED` check must keep working. Write `results/factory-train-2026-10-30/sources.json`? NO: do not
   write under results/; Claude writes it. Tests with fake folders.
3. **teacher.py (decision, user 2026-10-30, no Wonder output in training data):** `--escalate` exits 2 with a message
   naming the decision; train_records rows carry `"teacher": "spark"`. (factory_version changes: fine, no run is live.)
4. **T4 patterns.py:** wrong_shape signature = (family, first failed check with numbers replaced by N), so e.g. F8's
   "solids=3 / solids=4" FAILs group into one pattern. Test: 3 F8 FAILs with solids=3, solids=4, solids=3 and different
   later checks → ONE pattern. **B2:** a wrong_shape whose first failed check is `solids=N` or `invalid shape` is kind
   `teacher_habit` (the text was fine: Claude's blind rebuilds passed F8-1 and F8-3); pin `teacher_habit` in the test.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common dashboard` passes (286 + 6 plus the new tests).
- `forge_train.py smoke --cap-dollars 2.0` still prints CAP REFUSED and exits 2.
- `patterns.py --runs results/factory-pilot-2026-10-30 results/factory-main-2026-10-30 --out /tmp/p` now shows the F8
  cluster.
Report: files changed, the pytest line, the new patterns table, anything not followed.
