# RUNNER_SPEC: Keel v2 baseline runner (for Muse Code)

Read `PLAN.md` in this folder first: sections 2, 4, 4b, 4c, 4d, 5, 7 are binding. Base the code on
`../first-test/runner.py` and `../first-test/run_live.sh` (copy what you need; do NOT modify anything in
`../first-test/`). Same endpoints, model names, request body keys, sampling, key handling (keys only from the
environment set by run_live.sh, never printed or logged), retry rule and logging style as the first-test runner.

## Files to create in `experiments/keel-exam-v2/`
1. `runner.py`
   - CLI: `--mode pilot|main` (pilot = jobs M1, M7, H9, arm C, k=1, PLAN 4d), `--arms B,C` (default B,C),
     `--k 3`, `--out <dir>`, `--budget 2.50` (Modal USD), `--budget-c 3.00` (Baseten USD), `--max-minutes 60`
     (Glimmer arm wall clock), `--gpu-start <epoch seconds>` (deploy start, for the Modal estimate), `--parallel 16`.
   - Start: freeze check (PLAN 7). Parse the ```text block under "## 7." in PLAN.md (lines `<sha256>  <path>`,
     paths relative to this folder); recompute; refuse to start (exit 3, clear message) if a file is missing, a hash
     differs or the block is empty. Option `--print-hashes` prints the block for the files listed in PLAN 7 and exits
     (used once at freeze time).
   - Messages exactly as PLAN 4b. Body keys as the first test: model, messages, max_tokens 16000, temperature 1.0,
     top_p 0.95, top_k 64. k samples = k independent requests per job per arm.
   - Extraction as PLAN 4b (first fenced block, else whole reply).
   - Sandbox exactly as PLAN 4c: per answer a fresh scratch dir (inside a run temp dir under `--out`), write
     `answer.py`, run `run_one.py` via `env -i HOME=<scratch> PATH=/usr/bin:/bin sandbox-exec -f sandbox.sb
     /bin/sh -c 'ulimit -t 120; <venv python> <abs run_one.py> <abs scratch>'` in a new process group; 120 s
     wall-clock timeout (configurable `--timeout`, for tests) → kill the group; RSS watchdog every 0.5 s (sum the
     process group, `ps`), kill above 4 GB (configurable `--max-rss-mb`) → FAIL "memory".
   - The referee (`referee.py` in this folder; import it, it sets the tolerance) runs in the runner process on the
     BREP the child wrote, against the reference built from `jobs.py` (`build(job_id, JOBS[job_id]["ref"])`) and
     `expected.json`. Keep the BREP files of PASS and FAIL answers (for the replay viewer).
   - Outcomes: PASS / FAIL (with reason: exception text incl. KeelError, no `solid`, timeout, memory, referee
     checks) / INVALID (PLAN 4: cut off by token limit, empty reply, network/HTTP failure after one retry).
   - Caps (PLAN 5): check before every new call; stop sending new calls when the estimate reaches the cap; in-flight
     calls finish and are logged; the report says which cap stopped the run.
   - Log every call to `<out>/calls.jsonl` (arm, job, sample, prompt hash, reply, extracted code, sandbox stdout/
     stderr tail, outcome, reasons, measurements, tokens, seconds, cost estimate).
   - Report `<out>/report.md` + `<out>/summary.json`: per arm the score (mean pass rate %, PLAN 4), PASS/FAIL/INVALID
     counts, pass@1 per sample, per-job passes/3 table, paired bootstrap 95% CI of C − B (10,000 resamples of jobs,
     seed 0), McNemar on sample 1, the decision by the PLAN 4 rules in order (first match wins, whole points), spend
     per credit, and the cap status.
2. `run_one.py`: runs inside the sandbox. Puts `<repo>/company` on sys.path (absolute path computed from its own
   location), executes `answer.py` from the scratch dir with `runpy.run_path`, takes the variable `solid` (must be a
   CadQuery Shape), writes `solid.brep` (`solid.exportBrep(...)`) and `result.json` (ok / error text) into the
   scratch dir. Nothing else.
3. `sandbox.sb`: as PLAN 4c (allow default; deny network*; deny file-write*; allow file-write* to the scratch
   dir's parent run temp dir, /dev/null, /private/var/folders, /private/tmp). The scratch path may be passed with
   `-D SCRATCH=<path>` and `(param "SCRATCH")`.
4. `run_live.sh`: as `../first-test/run_live.sh` (new key into envsave + Modal secret, deploy, poll /v1/models,
   run runner with "${@:3}", trap → `modal app stop forge-glimmer -y || echo "APP STOP FAILED"`, then
   `modal app list`), but calling this folder's runner. Pilot mode must not deploy Glimmer (arm C only).
5. `test_runner.py` (pytest, no network, no paid calls): extraction; message format equals PLAN 4b; sandbox blocks
   a socket connect and a write outside the scratch dir and has no *KEY*/*TOKEN* env; timeout kills an infinite loop
   (use `--timeout 5`); memory watchdog kills a 6 GB allocation (use a low `--max-rss-mb`); a correct reference
   program (from `jobs.py`) PASSes end to end through the sandbox and BREP hand-off, and a wrong version FAILs;
   freeze check refuses on a changed file and on an empty block; decision rules on synthetic scores (each rule
   branch, ordering, whole-point rounding); bootstrap is deterministic with seed 0; caps stop new calls.
   Note: tests may read `jobs.py` (you need it for the end-to-end test), but never copy exam jobs anywhere else.

## Rules
- Do NOT make any call to Baseten, Modal or any model API, and do NOT run `run_live.sh` or deploy anything. Tests
  must be offline. Never print or log API keys.
- Do not change `jobs.py`, `expected.json`, `referee.py`, `PLAN.md`, anything in `../first-test/` or `company/`.
- Use `~/projects/forge/.venv/bin/python`. Run `pytest test_runner.py` from this folder until it passes.
- Do not commit or push.
Final report (short): files created, the pytest summary line, how to run the pilot and the main run, deviations
from this spec and why, anything you could not do.
