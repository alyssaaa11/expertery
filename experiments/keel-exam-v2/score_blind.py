"""Score the blind-rebuild programs (blind/<KEY>.py) against the references with the Keel-exam referee."""
import json, os, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, os.path.join(ROOT, "company"), os.path.join(ROOT, "experiments", "keel-exam")]
from jobs import JOBS, build
from referee import score
exp = json.load(open(os.path.join(HERE, "expected.json"))); ok = 0
for jid in JOBS:
    ref = build(jid, JOBS[jid]["ref"])
    try:
        ans = runpy.run_path(os.path.join(HERE, "blind", f"{jid}.py"))["solid"]
        passed, fails, m = score(ans, ref, exp[jid])
    except Exception as e:
        passed, fails = False, [repr(e)[:100]]
    ok += passed
    if not passed: print(jid, fails)
print(f"BLIND REBUILD {ok}/{len(JOBS)} match")
