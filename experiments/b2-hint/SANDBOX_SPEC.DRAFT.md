# Spec for Muse Code: run B2 answers in the Keel v2 sandbox (DRAFT, not approved)

Status: DRAFT by Claude, 2026-10-28 night. Not sent to Muse Code. Needs the user's yes for option (b) in
`forge-wiki/wiki/decisions/option-a-plan-2026-10-29.md` section 6, then verifier review, then one Muse Code session
(est. ~$0.3-0.5, step cap 60).

## Why
The first-test runner (`experiments/first-test/runner.py`, `run_code`, lines ~282-320) runs each model answer as
`python -I -c <answer + exporter>` with cwd `/tmp`, the runner's **full environment** (API keys can be in it) and
**no file or network limits**. The user asked for a sandbox on Keel v2 for exactly this reason; B2 runs 60 more
untrusted Glimmer answers, so it gets the same protection. The scoring must not change: same jobs.py, checks.py,
expected.json, STEP hand-off, verdicts.

## Rules for Muse Code
- Work in `~/projects/forge`. Never open `experiments/first-test/blind/`, `experiments/keel-exam*/blind/`,
  `experiments/option-a/` or any `expected*.json` except to pass its path through.
- Do NOT edit anything in `experiments/first-test/` except `runner.py` and `test_runner.py`, and do NOT edit
  `experiments/keel-exam-v2/` at all (it is frozen by hash). New files go in `experiments/b2-hint/`.
- Default behaviour of `runner.py` must stay byte-for-byte the same in output when the new flag is not used; all
  existing tests must still pass.

## Changes
1. `experiments/b2-hint/sandbox_cq.sb`: a copy of `experiments/keel-exam-v2/sandbox.sb` with the `COMPANY` read
   allow removed (plain CadQuery answers do not need Keel) and the `RUNONE` literal pointing at
   `run_one_cq.py`. Keep: `(allow default)`, `(deny network*)`, deny reads under `/Users/alyssa` and the four temp
   roots, allow reads of VENV, PYHOME, SCRATCH and RUNONE, `(allow file-read-metadata)`, deny writes except SCRATCH and
   `/dev/null`.
2. `experiments/b2-hint/run_one_cq.py` (runs inside the sandbox): reads `answer.py` from its scratch dir (passed as
   argv[1]), executes it in a fresh namespace, requires a variable `result` (same error text as today's
   EXPORTER_SNIPPET: `ERROR: no variable named 'result'`, exit 2), exports `result` to `<scratch>/answer.step` with
   `cadquery.exporters.export`, prints that path. No other output channel.
3. `runner.py`: new flag `--sandbox PROFILE` (path to an .sb file). When set, `run_code` instead:
   - makes a fresh scratch dir per answer under a run temp dir inside `--out` (realpath'ed, no symlinks), writes
     `answer.py`;
   - runs `env -i HOME=<scratch> PATH=/usr/bin:/bin sandbox-exec -f <PROFILE> -D VENV=... -D PYHOME=... -D
     SCRATCH=... -D RUNONE=... /bin/sh -c 'ulimit -t 60; <venv python> -I <run_one_cq.py> <scratch>'`, with a 60 s
     wall clock (same as the frozen first-test RUN_TIMEOUT, so BR stays identical to B; verifier drafts fix 7) (kill the process group) and the 4 GB RSS poll used by the Keel v2 runner;
   - imports `<scratch>/answer.step` in the runner process exactly as today and returns (shape, error) with the same
     error strings; sandbox denials surface as `answer code failed (...)` = FAIL, never INVALID;
   - keeps the scratch dir (answer.py, answer.step, stdout/stderr) for the replay viewer.
   `--sandbox` without a profile file present = refuse to start.
4. `run_live.sh`: no change needed if `"${@:3}"` pass-through already exists (b2-hint/SPEC.md item 2); otherwise add it.
5. Tests (`test_runner.py`, no network, no paid calls, venv python):
   a. a first-test reference program (from jobs.py) PASSes end to end through `--sandbox`, and one wrong version FAILs;
   b. inside the sandbox, reading `experiments/first-test/expected.json`, `~/.zshrc` and a file in `/private/tmp`
      fails; writing to a sibling scratch dir fails; a socket connect fails; `os.environ` has no `*KEY*`/`*TOKEN*`;
   c. an answer with `while True: pass` is killed by the CPU/wall limit and reported as FAIL with "timeout";
   d. without `--sandbox`, `run_code` behaves exactly as before (existing tests).

## After the build (Claude, free)
- Re-run the B2 self-checks: the 30 first-test references through the sandbox must give 30/30 PASS (same verdicts as
  `experiments/first-test/selftest.py`), so the sandbox cannot change the scores.
- Record sha256 of runner.py, sandbox_cq.sb, run_one_cq.py, hint.txt, checks.py, jobs.py, expected.json in
  `b2-hint/PLAN.md` ("Re-frozen" note with date); B2 PLAN rules unchanged.
- Verifier check, then the user's yes, then the run (`run_live.sh main <out> --arms BR,B2 --sandbox
  experiments/b2-hint/sandbox_cq.sb`). After the run: no FAIL reason may contain `harness` or `PermissionError`
  from a legitimate CadQuery import (if any do, the run is INVALID by the harness rule, not a model failure).
