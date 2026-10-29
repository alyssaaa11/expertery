# Spec for Muse Code: FreeCAD gap-test runner (arms G and S) — needs verifier check + user yes

Status: written by Claude 2026-10-29 (user: "install FreeCAD, check how it works, plan all for the paid run"). Plan and
free-check evidence: experiments/freecad/PLAN.md. Every item says why it matters.

## Rules
- Work in ~/projects/forge; new files only in experiments/freecad/ (do not edit experiments/first-test/, which is frozen:
  import from it instead). Never open blind/ folders, experiments/option-a/, or the contents of expected*.json.
- No network, no model calls, no Modal runs, no commit, never print keys.
- Tests: `~/projects/forge/.venv/bin/python -m pytest -q experiments/freecad` until all pass. Sandbox tests may skip
  inside your shell; Claude re-runs them outside.

## 1. `run_one_fc.py` (runs inside the sandbox, under FreeCAD's own `freecadcmd`)
Reads `<scratch>/answer.py`, executes it with `ns = {"__name__": "__main__"}`, requires `result` to be a FreeCAD
`Part.Shape` with at least one solid (error text: `ERROR: no variable named 'result'` / `ERROR: result is not a Part
solid`), writes `<scratch>/answer.step` (`result.exportStep`) and `<scratch>/measure.json` (bbox, volume, number of
solids, isValid). Before running the answer, install an import hook that refuses `cadquery` and `OCP` (ImportError
"not allowed in FreeCAD answers"). Why: FreeCAD could run CadQuery code if it were installed; this keeps the test about
FreeCAD (the sandbox already denies the forge venv; this is the second lock).
Invocation: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd <run_one_fc.py> <scratch>` — check how
freecadcmd passes script arguments (if it doesn't, pass the scratch path via an env var set by `env -i`, e.g. FC_SCRATCH).

## 2. `sandbox_fc.sb`
Start from experiments/freecad/sandbox_fc.reference.sb (tested by Claude: freecadcmd runs, cadquery import fails, the
answer key is unreadable). Add a literal read allow for run_one_fc.py (param RUNONE). Why: the same safety as Keel v2
(no network, no home or temp reads, writes only to scratch, `env -i HOME=<scratch>`), so a malicious answer cannot read
the answer key or the user's files.

## 3. `runner_fc.py` (reuses the frozen first-test runner; do not copy-paste its logic)
Import from experiments/first-test/runner.py: the Glimmer/Baseten request code and retry, code extraction, the budget
guard, k and workers handling, and the sandboxed-run plumbing pattern (scratch dirs under --out, realpath inside
scratch, 60 s CPU + wall limit, 4 GB RSS kill, process-group kill). Replace only:
- system prompt: "You write FreeCAD Python code using the Part module (import FreeCAD as App, Part). Units are
  millimetres. Assign the final solid (a Part.Shape) to a variable named result. Reply with exactly one Python code
  block and nothing else." Why: the same instruction as the CadQuery system prompt, tool swapped.
- manual: experiments/freecad/manual.md, refused if its sha256 differs from the value frozen in PLAN.md
  (865ab9af45eb2fb554f97155fa8f3cf44f92d54973437a1f94c78d67cdc89bb6). Why: a changed manual changes the result.
- user message: "Here is the FreeCAD manual. Use it.\n\n" + manual + "\n\n" + job text (same layout as arm B).
- answer execution: freecadcmd + run_one_fc.py in the sandbox; the runner imports <scratch>/answer.step with CadQuery
  and scores it with experiments/first-test/checks.py against jobs.py's reference: **0.2% is the verdict** (the
  baseline's yardstick) and 1e-6 is also recorded.
- arms: `G` = Glimmer (same body as arm B: max_tokens 16000, temperature 1.0, top_p 0.95, top_k 64); `S` = Spark Open
  on Baseten (meta-models/muse-spark-open-1026, same sampling, header x-session-affinity, log cached_tokens). k = 1.
- every FAIL is tagged `api_error` (the answer raised during the run: AttributeError, TypeError, NameError, Part
  errors, no result) or `wrong_geometry` (built but failed the checker). Why: API errors are tool knowledge that training
  can fix; wrong geometry is general skill (PLAN).
- outputs: calls.jsonl, summary.json (pass rate per arm and level, api_error vs wrong_geometry counts, jobs passed by S
  but not G, tokens, cost), report.md, and the PLAN decision rule evaluated (FreeCAD target / stay on CadQuery / grey /
  INVALID). CLI: `runner_fc.py --jobs main --out <dir> --arms G,S --k 1 --workers 8 --budget <$> --budget-c <$>`.

## 4. Session script
Use experiments/common/run_session.sh (session cap, always stops the app). If it cannot run runner_fc.py, add a
`--runner <path>` option there in a backward-compatible way (default = today's runner) and test it. Why: the money cap
and the app stop must be the same as for every other paid run.

## 5. Tests (offline, fake HTTP)
Prompt = system + manual + job (manual hash check refuses a changed file); a fake G reply with the hand-written answer
experiments/freecad/hand/M10.py PASSes end to end through the sandbox and STEP hand-off; hand/M1_wrong.py FAILs as
wrong_geometry; an answer with a typo'd Part call FAILs as api_error; an answer that imports cadquery is refused; reading
expected.json from inside the sandbox fails; the decision rule on synthetic summaries gives each of the 4 outcomes.
Short report at the end: files, pytest line, anything you could not follow.
