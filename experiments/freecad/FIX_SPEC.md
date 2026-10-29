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

## Round 2 (Claude's free cloud probe 2026-10-29, after 65e86ad) — binding
Evidence: `cloud_exec.py --check-image` failed at the extract step (`Permission denied`, exit 126; image
im-QIoVZxT6A4M6dizIy9fVWe logs). A throwaway probe by Claude (trusted code only, not project code) then showed:
FreeCAD 1.1.4 runs in the box after `chmod +x`; `freecadcmd /work/run_one_fc.py` IMPORTS the file (a __pycache__
appears, nothing runs, no STEP); run through `freecadcmd -c` with exec + `__name__ = "__main__"` it runs; hand/M10.py
(PASS on the Mac) then fails with "result is not a Part solid" because `Shape.Solids` is a LIST attribute, not a
method (Mac freecadcmd: `type(s.Solids)` → list); network is blocked (URLError) and `import cadquery` is refused.
1. **Image:** `chmod +x` the AppImage before `--appimage-extract`, and delete the AppImage after extracting (smaller
   image). Why: the build stopped there.
2. **Start the box script as a program:** run it with
   `sb.exec("freecadcmd", "-c", BOOTSTRAP, env={"FC_SCRATCH": "/work"}, timeout=60)` where BOOTSTRAP is
   `import sys; sys.argv=['run_one_fc.py']; exec(open('/work/run_one_fc.py').read(), {'__name__': '__main__', '__file__': '/work/run_one_fc.py'})`
   (verified in the probe). Why: freecadcmd imports a file argument, so main() never ran.
3. **`Solids` is a list:** use `len(shape.Solids)` everywhere (solid check and measure.json). Make the fake Part in
   the tests expose `Solids` as a list attribute, like real FreeCAD, and add a test that a fake whose `Solids` is a
   list passes. Why: the fake had a method, so the tests passed while the real box failed every answer.
4. **Decision rates = PASS ÷ (PASS + FAIL)** per arm in `evaluate_fc_decision` too (now it divides by all jobs),
   matching summary.json and PLAN; T's rate = T passes ÷ (S's PASS + FAIL jobs). Test with one INVALID job.
5. **Hand check vs the Mac:** `--check-hand` reads `experiments/freecad/hand/mac_measure.json` (Claude's Mac
   measurements: bbox, volume, solids per hand answer) and prints, per answer, the grader verdict and the largest
   relative bbox/volume difference; it prints `HAND OK` only if M1, M6, M10, H6, H13 PASS, M1_wrong and H13_wrong
   FAIL, and every difference ≤ 1e-9. Map each hand file to its job id by the file name prefix (M1_wrong → M1).
6. **Safety check CLI:** `cloud_exec.py --check-safety` runs four tiny answers through the real box + grader path and
   prints one line each: an answer calling a misspelled Part function → api_error; `import cadquery` → refused
   (api_error, error text kept); an answer that tries `urllib.request.urlopen("https://example.com")` → fails, no
   network; an answer that lists `/` and `/work` and searches for files named like jobs/expected/reference → none
   found (it writes what it found into an error so it shows in `run_error`). Prints `SAFETY OK` only if all four hold.
Run the same pytest line until all pass. Short report: files changed, pytest line, anything not followed.

## Round 3 (Claude's free cloud checks after fd43235; results/freecad-checks-2026-10-29/probe-results.md) — binding
Image check passed (FreeCAD 1.1.4). With the bugs below patched around in a throwaway probe, the cloud gives the Mac's
verdicts: hand 5 PASS / 2 FAIL, SAFETY OK, REFS 30/30 PASS. Fix exactly these:
1. **write_text argument order:** Modal 1.6.3 is `filesystem.write_text(data, remote_path)`; call it with keywords
   `write_text(data=..., remote_path=...)`. Add a test that reads `inspect.signature` of
   `modal.sandbox._filesystem._SandboxFilesystem.write_text` / `read_bytes` / `read_text` (skip if modal is missing)
   and asserts the parameter names the code uses exist. Make the fake filesystem use the same parameter names. Why:
   the fake accepted the reversed order, so tests passed and the real box crashed.
2. **Missing file:** reading a missing STEP/measure raises `modal.exception.SandboxFilesystemNotFoundError`; treat it
   (and FileNotFoundError) as "the answer wrote no STEP" (a FAIL with the ERROR line), not as a harness error.
3. **Grader app:** run grader calls inside the App that defines `grade` (`cloud_grade._app.run()`), in
   cloud_grade.py main and runner_fc.py main; `App.lookup(...).run()` fails with "App is already running". Keep
   App.lookup only for the sandbox app.
4. **Grader image:** add `.apt_install("libgl1", "libglib2.0-0", "libxrender1", "libx11-6", "libxext6")` before
   pip (CadQuery's OCP needs libGL.so.1).
5. **Hand tolerance = 1e-6** (decision, Claude 2026-10-29, disclosed): the Mac (arm64) and the cloud box (x86) give the
   same verdicts but bbox/volume differ by up to 6.4e-8 relative (float differences between builds). The gate is the
   strict referee's 1e-6, so "same part" means the same as in the factory data check. `HAND OK` needs the 5/2
   verdicts AND every difference ≤ 1e-6.
Same pytest line until all pass. Short report: files changed, pytest line, anything not followed.

## Round 4 (verifier GO WITH 4 FIXES, forge-freecad-prerun-2026-10-29) — binding, small
1. **`runner_fc.py --summarize <GS run dir> <W run dir> --out <dir>`:** read both calls.jsonl files, run
   `evaluate_fc_decision` on the union of records, and write summary.json + report.md there (G, S, T rates, Wonder's
   share of T's passes, rules 1-4 on T and on S, rule 6, both decision lines: the runner's label and "PLAN rule 5:
   disagreement → stay on CadQuery"). No model, Modal or network calls. Test with two small fake calls.jsonl files
   (one disagreement case, one rule-6 case). Why: each run's summary sees only its own records, so the pre-registered
   T rule was never computed by code.
2. **`cloud_exec.py --check-hand`:** run inside `with modal.enable_output(): with cloud_grade._app.run():` (it failed
   with "Function has not been hydrated"). Test with a patched app.
3. **run_fc_session.sh keys:** `envsave get` takes the OPAQUE id, not the name. Use
   `envsave get es_LMDrY_C1YRDJYOAGLb2hB1y5WpczSEujtnquV4V5DTzZSMhp` for BASETEN_KEY (the id the baseten-muse-spark
   skill and experiments/first-test/run_live.sh use) and the HerdShot id from `~/.local/bin/muse-wonder` (first
   `es_…` token, read at run time with grep, never printed) for META_HERDSHOT_API_KEY. Keep the empty-key refusal.
Same pytest line until all pass. Short report: files changed, pytest line, anything not followed.
