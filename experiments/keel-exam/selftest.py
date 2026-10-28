"""Exam self-test: every reference builds one valid solid and passes against itself; every wrong version builds and
FAILS. Writes expected.json (the measurements the referee compares against). Run with the project venv."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, os.path.join(ROOT, "company"), os.path.join(ROOT, "experiments", "first-test")]
from jobs import JOBS, apply_wrong, build
from referee import measure, score

expected, ok, total, problems = {}, 0, 0, []
example_ids = {r["id"] for r in json.load(open(os.path.join(ROOT, "company", "examples", "requests.json")))}
for jid, job in JOBS.items():
    if job["id"] in example_ids:
        problems.append(f"{jid}: part number {job['id']} is also a manual example")
    ref = build(jid, job["ref"])
    m = measure(ref)
    expected[jid] = {k: m[k] for k in ("bbox", "volume", "area", "com")}
    total += 1
    passed, fails, _ = score(ref, ref, expected[jid])
    if passed and m["solids"] == 1 and m["valid"]:
        ok += 1
    else:
        problems.append(f"{jid} reference: {fails}")
    for i, subs in enumerate(job["wrong"]):
        total += 1
        try:
            w = build(jid, apply_wrong(job["ref"], subs))
            passed, fails, wm = score(w, ref, expected[jid])
        except Exception as e:
            passed, fails = True, [f"wrong version did not build: {e}"]
        if passed or "did not build" in str(fails):
            problems.append(f"{jid} wrong{i + 1}: {fails or 'PASSED (should fail)'}")
        else:
            ok += 1
json.dump(expected, open(os.path.join(HERE, "expected.json"), "w"), indent=1)
print("\n".join(problems))
print(f"EXAM SELFTEST {ok}/{total} OK ({len(JOBS)} jobs: references pass, wrong versions fail)")
