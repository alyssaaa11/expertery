# Fix spec for Muse Code: FreeCAD cloud build (verifier FAIL, report forge-freecad-build-2026-10-29)

Status: written by Claude 2026-10-29, continuing the user's "fix freecad". Same rules as SPEC.md: edit only files in
experiments/freecad/ plus experiments/common/run_session.sh (item 5 only); never open blind/, experiments/option-a/ or
print expected*.json; no network, no model calls, no Modal runs, no installs, no commit, never print keys. Tests
offline with fakes; anything that could reach real Modal is monkeypatched to raise. Run
`~/projects/forge/.venv/bin/python -m pytest -q experiments/freecad experiments/train experiments/common` until all pass.

1. **Image (B1).** SHA URL = `https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage-SHA256.txt`
   (the old `SHA256.txt` is 404); download both files with `curl -fL` so an HTTP error fails the build. apt line:
   `apt-get install -y --no-install-recommends ca-certificates curl libgl1 libglib2.0-0 libx11-6 libxext6 libxrender1 libsm6 libice6`
   with no `|| true`, no libfuse (not needed with `--appimage-extract`). Add
   `ln -s /opt/squashfs-root/usr/bin/freecadcmd /usr/local/bin/freecadcmd`. Why: the build failed at two steps and the
   binary was not on PATH.
2. **Wiring (B2).** `app = modal.App.lookup("forge-freecad", create_if_missing=True)` and `modal.Sandbox.create(app=app,
   image=..., **sandbox_kwargs())` (Modal: app is required). `sb.exec("freecadcmd", "/work/run_one_fc.py",
   env={"FC_SCRATCH": "/work"}, timeout=60)` with separate string arguments. The runner's remote work (grader calls)
   runs inside `with modal.enable_output(): with grader_app.run():` in main(), so `cloud_grade.grade.remote()` has an
   app context. Add a CLI `cloud_exec.py --check-image` that builds the image in a sandbox and prints
   `freecadcmd --version`, and `cloud_grade.py --check-refs` that sends the 30 CadQuery references through the grader and
   prints `REFS n/30 PASS`, and `cloud_exec.py --check-hand` that runs the 7 hand/ answers in the box and grades them
   (prints per answer PASS/FAIL and bbox/volume relative difference vs the Mac-made parts if given). Claude runs these.
3. **Harness errors (B3).** Any exception from Sandbox create / exec / filesystem (other than "the answer wrote no
   STEP") or from the grader → outcome **INVALID**, tag `harness`, error text kept. summary.json counts harness and
   INVALID per arm and applies PLAN rule 6: harness or INVALID > 5% of an arm's answers → decision "RUN INVALID".
   Test with a fake box that raises and a fake grader that raises.
4. **Tags (B4).** When no STEP is written, `run_answer_in_box` returns run_one_fc's stdout/stderr (its ERROR line), and
   runner_fc puts it in `run_error`. "no variable named 'result'" → api_error; "result is not a Part solid" →
   wrong_geometry; any other exception from the answer, timeout, memory limit, PermissionError → api_error (PLAN).
5. **Session cap and keys (B7, B8).** In experiments/common/run_session.sh's hook branch, start the hook command the
   same way as the default branch: with `GLIMMER_URL="$URL" GLIMMER_KEY="$K"` in its env and `--budget "$B"
   --gpu-start "$GPU_START"` appended, so the whole-session cap (money LEFT) applies (lesson: a per-call budget is not a
   session budget). runner_fc accepts `--gpu-start`. In run_fc_session.sh remove the hard-coded `--budget 3.50`; the
   session cap argument (default 3.50) sets it. The wrapper loads the keys without printing them:
   `export BASETEN_KEY=$(envsave get BASETEN_API_KEY)` and `export META_HERDSHOT_API_KEY=$(envsave get META_HERDSHOT_API_KEY)`,
   and fails with a clear message if either is empty. Test: a dummy hook runner sees GLIMMER_URL and the budget left.
6. **Key name (B5).** runner_fc reads `META_HERDSHOT_API_KEY` (never META_KEY) for arm W and `--w-smoke`.
7. **Rates (B9).** Pass rate = PASS ÷ (PASS + FAIL) per arm, as in the baseline; INVALID/harness counted separately.
The rule-5 disagreement label may stay as is (user, 2026-10-29: PLAN rule 5 decides "stay on CadQuery").
Short report at the end: files changed, the pytest line, anything not followed.
