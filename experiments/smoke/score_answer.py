"""Score the smoke test's single answer with the STRICT referee (checks.py, TOL_DIFF = 1e-6), inside the sandbox.
Reference = a spacer block 30 x 20 x 10 at the origin with a 6 mm hole along Z at (15, 10) (the job in train_smoke.py)."""
import json, os, sys
FT = os.path.expanduser("~/projects/forge/experiments/first-test"); sys.path.insert(0, FT)
import cadquery as cq, checks, runner
checks.TOL_DIFF = 1e-6
ref = (cq.Workplane("XY").box(30, 20, 10, centered=False)
       .cut(cq.Workplane("XY").center(15, 10).circle(3).extrude(10)))
exp_m = checks.measure(ref)
expected = {k: exp_m[k] for k in ("bbox", "volume", "area", "com")}
serve = json.load(open(os.path.expanduser("~/projects/forge/results/smoke-2026-10-29/serve.json")))
code = runner.extract_code(serve.get("answer") or "")
shape, err = runner.run_code(code, sandbox_profile=os.path.expanduser("~/projects/forge/experiments/b2-hint/sandbox_cq.sb"),
                             sandbox_dir=sys.argv[1])
if shape is None:
    print("FAIL (did not run):", err[:300]); sys.exit()
passed, fails, m = checks.score(shape, ref, expected)
print("PASS" if passed else f"FAIL {fails}")
