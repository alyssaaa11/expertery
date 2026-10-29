"""Build every reference part, save expected values, and prove each job's check passes the reference and fails
both wrong versions (thinking exam; checks from first-test). Writes expected.json. Free: no model calls."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "first-test"))
from checks import measure, score  # noqa: E402
from thinking_jobs import JOBS  # noqa: E402

expected, bad = {}, []
for j in JOBS:
    ref_shape = j["build"]()
    ref = measure(ref_shape)
    expected[j["id"]] = ref
    ok_ref, ref_fails, _ = score(ref_shape, ref_shape, ref)
    ok_ref = ok_ref and ref["solids"] == 1
    wrong = [score(j["build"](**w), ref_shape, ref)[1] for w in j["wrong"]]
    caught = all(len(f) > 0 for f in wrong)
    status = "OK " if ok_ref and caught else "BAD"
    if status == "BAD":
        bad.append(j["id"])
    print(f"{status} {j['id']:4} {j['level']:6} vol={ref['volume']:>10.1f} solids={ref['solids']} "
          f"valid={ref['valid']} wrong-caught-by={[f for f in wrong]}")
json.dump(expected, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected.json"), "w"), indent=1)
print("BAD:", bad or "none", f"({len(JOBS)} jobs)")
