# Spec for Muse Code: FreeCAD gap-test runner (arms G and S) — needs verifier check + user yes

Status: written by Claude 2026-10-29 (user: "install FreeCAD, check how it works, plan all for the paid run"). Plan and
free-check evidence: experiments/freecad/PLAN.md. Every item says why it matters.

## Rules
- Work in ~/projects/forge; new files only in experiments/freecad/ (do not edit experiments/first-test/, which is frozen:
  import from it instead). Never open blind/ folders, experiments/option-a/, or the contents of expected*.json.
- No network, no model calls, no Modal runs, no commit, never print keys.
- Tests: `~/projects/forge/.venv/bin/python -m pytest -q experiments/freecad` until all pass. Sandbox tests may skip
  inside your shell; Claude re-runs them outside.

## 1. Cloud safety box: `cloud_exec.py` (decision, user 2026-10-29: nothing Glimmer writes may run on the Mac)
Every answer runs in a **fresh Modal Sandbox** (`modal.Sandbox.create`, https://modal.com/docs/sdk/py/latest/Sandbox):
`block_network=True`, no secrets, no volumes, cpu 1, memory (1024, 4096) MiB, `timeout` 90 s, one sandbox per answer,
terminated after use. Image: FreeCAD **1.1.4** for Linux from the official release asset `FreeCAD_1.1.4-Linux-x86_64-py311.AppImage` (GitHub
release 2026-09-28): download it in the image build, verify its SHA256 against the release's SHA256 file, unpack with
`--appimage-extract` (no FUSE needed), and the build must print `freecadcmd` version 1.1.4 (the Mac manual's version).
No conda route: conda-forge has no 1.1.4 build (verifier, anaconda.org API: 1.1.0, 1.1.3, 2026.09.16). Why: a different
FreeCAD version could make the manual inaccurate and change the result. The image contains ONLY FreeCAD + `run_one_fc.py`: no references, no jobs file, no expected.json, no cadquery.
Steps: write `answer.py` with `sb.filesystem.write_text`, run `freecadcmd /work/run_one_fc.py` with `sb.exec`
(env FC_SCRATCH=/work), read back `/work/answer.step` (bytes) and `/work/measure.json`, then `sb.terminate()`. Run the answer with `sb.exec(..., timeout=60)` inside the 90 s box (the baseline's 60 s
limit, so speed limits stay the same); refuse a STEP larger than 20 MB. The verdict and failure tags come only from the
grader; the box's measure.json is for logs only (why: the box runs untrusted code and must not decide its own score).
Why: the box never holds the answers, has no internet and is new for each answer, so an answer cannot read the
answer key, other jobs' results, or anything on the user's Mac.
`run_one_fc.py` (inside the box): exec answer.py with `ns = {"__name__": "__main__"}`; require `result` to be a
`Part.Shape` with ≥ 1 solid (`ERROR: no variable named 'result'` / `ERROR: result is not a Part solid`); refuse
`import cadquery` / `OCP` with an import hook; write answer.step + measure.json (bbox, volume, solids, isValid).

## 2. Cloud grader: `cloud_grade.py`
A separate Modal Function (CPU, our own trusted code) with CadQuery 2.8 + experiments/first-test/{jobs.py,checks.py,
expected.json} baked into its image. Input: job id + STEP bytes; output: verdict at 0.2% (the verdict) and at 1e-6,
the failed checks, measurements. It never runs model code. Why: the reference parts live only here, never in the box.
**Consistency check before any paid run (CPU only, cents):** (a) run all 7 hand answers of experiments/freecad/hand/
IN the cloud box → 5 PASS + 2 FAIL through the cloud grader, exactly as on the Mac, with bbox and volume within 1e-9
relative of the Mac-made parts; (b) the 30 CadQuery references through the cloud grader → 30/30 PASS. Why: (a) tests
the Linux FreeCAD box itself, (b) tests the grader; together they show the cloud gives the same verdicts as the Mac.

## 2b. Mac side
runner_fc.py imports `modal` to create sandboxes and call the grader, so modal must be installed in the forge venv
(`~/projects/forge/.venv`); this is the user's decision (the same one as the training fix). Muse Code must not install
anything; if modal is missing, tests that need it skip and the CLI exits with a clear message.

## 3. `runner_fc.py` (reuses the frozen first-test runner; do not copy-paste its logic)
Import from experiments/first-test/runner.py: the Glimmer/Baseten request code and retry, code extraction, the budget
guard, k and workers handling. Replace only:
- system prompt: "You write FreeCAD Python code using the Part module (import FreeCAD as App, Part). Units are
  millimetres. Assign the final solid (a Part.Shape) to a variable named result. Reply with exactly one Python code
  block and nothing else." Why: the same instruction as the CadQuery system prompt, tool swapped.
- manual: experiments/freecad/manual.md, refused if its sha256 differs from the value frozen in PLAN.md
  (865ab9af45eb2fb554f97155fa8f3cf44f92d54973437a1f94c78d67cdc89bb6). Why: a changed manual changes the result.
- user message: "Here is the FreeCAD manual. Use it.\n\n" + manual + "\n\n" + job text (same layout as arm B).
- answer execution: `cloud_exec.py` (Modal Sandbox) → STEP bytes → `cloud_grade.py` (Modal Function): **0.2% is the
  verdict** (the baseline's yardstick) and 1e-6 is also recorded. Nothing from the model runs on the Mac; the Mac only
  coordinates and writes logs. Run up to 8 sandboxes in parallel.
- arms: `G` = Glimmer (same body as arm B: max_tokens 16000, temperature 1.0, top_p 0.95, top_k 64); `S` = Spark Open
  on Baseten (meta-models/muse-spark-open-1026, same sampling, header x-session-affinity, log cached_tokens); `W` = Muse
  Wonder (`muse-wonder-1.0`, https://api.meta.ai/v1 chat completions, key from env META_KEY, same messages, max_tokens
  16000; reasoning tokens are billed as output) run only on job ids that FAILED in S's calls.jsonl (`--escalate-from <S
  run dir>`), with its own budget guard (`--budget-w`, $20/M output, $4/M input, $0.20/M cached). k = 1. Summary adds
  T = S ∪ W-rescues per job and evaluates the PLAN rule on T (S alone reported too).
- every FAIL is tagged `api_error` (the answer raised during the run: AttributeError, TypeError, NameError, Part
  errors, timeout, memory limit, PermissionError) or `wrong_geometry` (built but failed the checker, or `result` is not
  a Part solid); a reply cut off by the token limit is INVALID (as in the baseline). Why: API errors are tool knowledge that training
  can fix; wrong geometry is general skill (PLAN).
- outputs: calls.jsonl, summary.json (pass rate per arm and level, api_error vs wrong_geometry counts, jobs passed by S
  but not G, tokens, cost), report.md, and the PLAN decision rule evaluated (FreeCAD target / stay on CadQuery / grey /
  INVALID). CLI: `runner_fc.py --jobs main --out <dir> --arms G,S --k 1 --workers 8 --budget <$> --budget-c <$>`.

## 4. Session script
Use experiments/common/run_session.sh unchanged, through its existing RUN_SESSION_RUNNER_CMD hook (run_session.sh
lines ~20 and ~87) to call runner_fc.py; do not edit run_session.sh (new files only in experiments/freecad/). Add a
small wrapper experiments/freecad/run_fc_session.sh that sets the hook and passes the arms/budget, plus a test. Why: the money cap
and the app stop must be the same as for every other paid run.

## 5. Tests (offline, fake HTTP)
Offline (no Modal): prompt = system + manual + job (manual hash check refuses a changed file); failure tagging from
fake sandbox results (exception → api_error, built-but-FAIL → wrong_geometry, cut off → INVALID); the decision rule on
synthetic summaries gives each outcome; the sandbox config asserts block_network=True, no secrets, no volumes, and that
the box image file list contains no jobs/expected/reference files. Live checks (Claude runs them, CPU only, cents):
hand/M10.py PASSes end to end in the cloud; hand/M1_wrong.py FAILs as wrong_geometry; a typo'd Part call → api_error;
`import cadquery` refused; an answer that tries `urllib.request.urlopen` fails (no network); an answer that lists `/` finds
no jobs/expected files.
Short report at the end: files, pytest line, anything you could not follow.
