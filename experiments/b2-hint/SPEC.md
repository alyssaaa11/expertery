# Spec for Muse Code: B2 run support

Work in ~/projects/forge. Do NOT change any file in experiments/first-test/ except runner.py and test_runner.py, and
keep their current behaviour unchanged when the new options are not used (all 30 existing tests must still pass).

1. runner.py: add `--arms` (comma list, default `A,B,C`). Valid arms: A, B, C (unchanged) and two new ones:
   - `BR` (B-repeat): identical to B (Glimmer, manual, same messages).
   - `B2`: identical to B, but the system message is the current SYSTEM text + one space + the hint text read from
     `experiments/b2-hint/hint.txt` (UTF-8, stripped). Load it only if B2 is requested.
   Arm C must not be called unless requested. Reports/summary list only the requested arms. compute_decision is only
   computed when both B and C are present; otherwise write "decision: see experiments/b2-hint/PLAN.md".
   Add `--jobs-dir`-free behaviour: still use jobs.py from experiments/first-test.
2. experiments/first-test/run_live.sh: pass extra arguments through to runner.py (`"${@:3}"`), so
   `run_live.sh main <out> --arms BR,B2 --budget 3` works. Keep everything else.
3. New script experiments/b2-hint/analyze.py: reads a calls.jsonl, rebuilds every FAIL answer with runner.run_code,
   shifts it so its bounding-box min corner matches the reference's, and classifies it as position-only
   (checks.mismatch ≤ 0.002) or wrong shape; prints per arm: PASS/FAIL/INVALID, pass rate (whole points),
   position-only count, wrong-shape count, crash count, and the paired table vs another arm (jobs where only one passed).
   CLI: `analyze.py <calls.jsonl> [--pair B2,BR]`.
4. Tests (test_runner.py): --arms parsing, BR == B messages, B2 system message ends with the hint, C not called when
   not requested. No network. Use ~/projects/forge/.venv/bin/python.
