# Muse Code round 1b: learning loop to spec (verifier: GO for this fix round, forge-factory-build-2026-10-30; waits for the user's yes)

Round 1 built experiments/factory/patterns.py from the round brief only, because experiments/factory/SPEC.md had no §4
yet (Claude's mistake). §4 is now written. Read experiments/factory/SPEC.md §4 fully, plus patterns.py, teacher.py and
test_patterns.py. All rules in experiments/final/MUSE_SPEC.md "Rules" apply (no network, no Modal runs, no model calls,
no commit, never print keys, never open blind/ or experiments/option-a/, never print any expected*.json).

## Build in this round ONLY
- `patterns.py` to §4: signatures (harness / no_code / run_error with numbers → N / wrong_shape = sorted failed checks),
  `--min-count` (default 3), kinds our_bug / our_wording / teacher_habit by §4's rules, "where to fix" column, 2 example
  ids, patterns.json + patterns.md; dev ids from split.json skipped; refuse (exit 2) any --runs path under blind/,
  experiments/option-a/ or experiments/first-test/. Keep the existing pass-rate tables.
- `teacher.py`: `factory_version` = first 12 hex of sha256(generator.py + teacher.py + teacher_notes.md bytes), and
  teacher_notes.md (when not empty) is added to the teacher prompt after the manual. Glimmer's training records keep
  the short prompt (no notes).
- Tests: every case in §4 "Tests".
- **F1 (verifier blocker)**: teacher.py's `main()` runs `run_suite` inside `with modal.enable_output(), cloud_cq._app.run():`,
  and forge_train's exam guard (`default_box_measure` → `cloud_cq.measure_brep.remote`) runs inside `cloud_cq._app.run()`
  too (forge_train's own app.run is a different App). Why: outside it `.remote` raises "Function has not been hydrated"
  and every paid answer would come back harness INVALID. Test: a fake app with an "entered" flag; any real-path grade or
  measure call outside the context fails the test.
- **F2**: Wonder is charged at Meta's rates $4.00 / $0.20 cached / $20.00 per M (not Spark's), and the Wonder in-flight
  reserve is >= $0.35 per call. Tests for both.
- **F4**: besides the path refusal, patterns.py refuses records whose id is not `F<n>-<m>` and skips dev ids.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common` passes (216 plus the new tests).
- `make_jobs.py` output is unchanged (jobs.jsonl byte-identical).

Report at the end: files changed, the pytest line, and anything you did not follow.
