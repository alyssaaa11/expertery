"""Glimmer smoke test (2026-10-28): 3 questions to the Modal endpoint, run returned CadQuery code locally, measure."""
import json, os, re, subprocess, sys, time, urllib.request

URL = os.environ["GLIMMER_URL"].rstrip("/") + "/v1/chat/completions"
KEY = os.environ["GLIMMER_KEY"]
OUT = os.path.dirname(os.path.abspath(__file__))
PY = os.path.expanduser("~/projects/forge/.venv/bin/python")

JOBS = [
    {"id": "hello", "prompt": "Say hello in one short sentence.", "cad": False},
    {"id": "cube", "cad": True, "expect": {"bbox": [20, 20, 20], "volume": 7607.3},
     "prompt": "Write CadQuery Python code for a 20 x 20 x 20 mm cube with a 5 mm diameter hole going all the way "
               "through it along the Z axis, centred. Assign the final shape to a variable named result. "
               "Reply with only one Python code block."},
    {"id": "bracket", "cad": True, "expect": {"bbox": [40, 20, 20], "volume": 4322.2},
     "prompt": "Write CadQuery Python code for an L-bracket: a base plate 40 mm (X) by 20 mm (Y) by 3 mm thick, and a "
               "vertical wall 40 mm (X) by 3 mm thick, standing on one long edge of the base, total height 20 mm. "
               "Add two 5 mm diameter through holes in the base plate, 30 mm apart along X, centred in X, and "
               "centred in Y on the base plate. Assign the final shape to a "
               "variable named result. Reply with only one Python code block."},
]

MEASURE = """
import cadquery as cq
{code}
s = result.val() if hasattr(result, 'val') else result
bb = s.BoundingBox()
print('MEASURE', round(bb.xlen,2), round(bb.ylen,2), round(bb.zlen,2), round(s.Volume(),1))
"""

def ask(prompt, timeout):
    body = json.dumps({"model": "muse-glimmer", "max_tokens": 6000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    return j, time.time() - t

def main():
    results = []
    for i, job in enumerate(JOBS):
        timeout = 1800 if i == 0 else 600  # first call waits for the cold start (weights download)
        try:
            j, secs = ask(job["prompt"], timeout)
        except Exception as e:
            results.append({"id": job["id"], "error": repr(e)}); print(job["id"], "ERROR", e, flush=True); continue
        msg = j["choices"][0]["message"]; text = msg.get("content") or ""
        rec = {"id": job["id"], "seconds": round(secs, 1), "usage": j.get("usage"),
               "finish": j["choices"][0].get("finish_reason"), "answer": text,
               "reasoning_chars": len(msg.get("reasoning_content") or msg.get("reasoning") or "")}
        if job["cad"]:
            m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
            code = m.group(1) if m else text
            code = "\n".join(l for l in code.splitlines() if not l.strip().startswith("import cadquery"))
            p = subprocess.run([PY, "-I", "-c", MEASURE.format(code=code)], capture_output=True, text=True,
                               timeout=120, cwd="/tmp")
            line = [l for l in p.stdout.splitlines() if l.startswith("MEASURE")]
            if line:
                x, y, z, v = map(float, line[0].split()[1:])
                e = job["expect"]
                ok_bb = sorted([x, y, z]) == sorted(float(a) for a in e["bbox"])
                ok_v = abs(v - e["volume"]) / e["volume"] < 0.01
                rec.update(measured={"bbox": [x, y, z], "volume": v}, expected=e, passed=ok_bb and ok_v)
            else:
                rec.update(passed=False, run_error=(p.stderr or p.stdout)[-800:])
        results.append(rec)
        print(job["id"], rec.get("seconds"), "s", "passed=" + str(rec.get("passed")), flush=True)
    json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=2)

main()
