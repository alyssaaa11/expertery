"""Glimmer live dashboard for the step-2 baseline run (Claude, 2026-10-29; a monitoring view, not product code).
Reads results/bmax-baseline-2026-10-29/{main-BR,main-B2BX,pilot}/calls.jsonl + session.log and writes one
self-contained HTML page (data embedded, because Chrome blocks fetch() on file://) that reloads itself every 20 s.
Usage: python glimmer_dashboard.py [--loop]   (--loop rewrites the page every 20 s until the session log says done)"""
import html, json, os, sys, time
RUN = os.path.expanduser("~/projects/forge/results/bmax-baseline-2026-10-29")
OUT = os.path.expanduser("~/projects/forge/forge-wiki/wiki/assets/dashboards/glimmer-baseline-2026-10-29.html")
ARMS = [("BR", "Plain Glimmer", "manual + request, 1 try", 30, "#2a78d6"),
        ("B2", "Hint, 1 try", "manual + hint sentence, 1 try", 90, "#eb6834"),
        ("BX", "All fair fixes (B-max)", "hint + 3 examples + xhigh + up to 3 tries", 90, "#1baf7a")]
GPU_START = "10:45:13"; RATE = 2.50


def load():
    recs = []
    for sub in ("main-BR", "main-B2BX"):
        p = os.path.join(RUN, sub, "calls.jsonl")
        if os.path.exists(p):
            for line in open(p):
                try: recs.append(json.loads(line))
                except ValueError: pass
    log = open(os.path.join(RUN, "session.log")).read() if os.path.exists(os.path.join(RUN, "session.log")) else ""
    return recs, log


def stats(recs):
    out = {}
    for arm, *_ in ARMS:
        fin = [r for r in recs if r.get("arm") == arm and r.get("outcome")]
        calls = [r for r in recs if r.get("arm") == arm and (r.get("event") or (arm != "BX" and r.get("outcome")))]
        p = sum(r["outcome"] == "PASS" for r in fin); f = sum(r["outcome"] == "FAIL" for r in fin)
        inv = sum(r["outcome"] == "INVALID" for r in fin)
        tok = 0
        for r in fin:
            if arm == "BX": tok += (r.get("prompt_tokens_total") or 0) + (r.get("completion_tokens_total") or 0)
            else: tok += (r.get("usage") or {}).get("total_tokens") or 0
        lat = [r.get("latency_total") if arm == "BX" else r.get("latency") for r in fin]
        lat = [x for x in lat if x]
        mc = [r.get("model_calls") or 1 for r in fin]
        out[arm] = dict(done=len(fin), pass_=p, fail=f, inv=inv, rate=(100 * p / (p + f)) if p + f else None,
                        tok_per=(tok / len(fin)) if fin else None, tok_per_correct=(tok / p) if p else None,
                        lat=(sum(lat) / len(lat)) if lat else None, calls=(sum(mc) / len(mc)) if mc else None)
    return out


def phase(log):
    if "app stopped" in log: return "Finished, GPU stopped"
    if log.count("runner exit") >= 3: return "Main run finished, stopping GPU"
    if log.count("runner exit") == 2: return "Running: Hint (1 try) and All fair fixes"
    if "main start" in log: return "Running: Plain Glimmer"
    if "PILOT DONE" in log: return "Pilot done, waiting for GO"
    if "ready" in log: return "Pilot running"
    return "Starting Glimmer on Modal"


def live():
    import glob
    return sum(len(os.listdir(d)) for d in glob.glob(os.path.join(RUN, "main-B2BX", "sandbox_*")) if os.path.isdir(d))


def fmt(x, d=0, suf=""):
    return "–" if x is None else f"{x:,.{d}f}{suf}"


def page(recs, log):
    st = stats(recs); now = time.strftime("%H:%M:%S")
    h, m, s = map(int, GPU_START.split(":")); t0 = time.mktime(time.localtime()[:3] + (h, m, s, 0, 0, -1))
    end_line = [l for l in log.splitlines() if l.startswith("app stopped")]
    t_end = time.mktime(time.localtime()[:3] + tuple(map(int, end_line[0].split()[-1].split(":"))) + (0, 0, -1)) if end_line else time.time()
    gpu_h = max(0, t_end - t0) / 3600
    tiles = ""
    for arm, name, desc, exp, col in ARMS:
        a = st[arm]; pct = 100 * a["done"] / exp
        tiles += f"""<div class="tile"><div class="tname"><span class="sw" style="background:{col}"></span>{name}</div>
<div class="tdesc">{desc}</div><div class="hero">{fmt(a['rate'], 0, '%')}</div><div class="sub">pass rate so far</div>
<div class="prog" title="{a['done']} of {exp} answers"><div style="width:{pct:.1f}%;background:{col}"></div></div>
<div class="sub">{a['done']} / {exp} answers · ✓ {a['pass_']} · ✗ {a['fail']} · ! {a['inv']} invalid</div>
<table class="kv"><tr><td>Model calls per answer</td><td>{fmt(a['calls'], 1)}</td></tr>
<tr><td>Tokens per answer</td><td>{fmt(a['tok_per'])}</td></tr><tr><td>Tokens per correct part</td><td>{fmt(a['tok_per_correct'])}</td></tr>
<tr><td>Model time per answer</td><td>{fmt(a['lat'], 0, ' s')}</td></tr></table></div>"""
    # job grid
    jobs = [f"M{i}" for i in range(1, 16)] + [f"H{i}" for i in range(1, 16)]
    rows = ""
    for j in jobs:
        cells = ""
        for arm, name, _, exp, col in ARMS:
            k = 1 if arm == "BR" else 3
            rs = {r.get("sample", 0): r for r in recs if r.get("arm") == arm and r.get("job") == j and r.get("outcome")}
            for smp in range(k):
                r = rs.get(smp)
                if r is None: cls, sym, tip = "wait", "·", "not run yet"
                else:
                    o = r["outcome"]; cls, sym = {"PASS": ("ok", "✓"), "FAIL": ("bad", "✗")}.get(o, ("inv", "!"))
                    why = "; ".join(map(str, (r.get("fails") or r.get("failed_checks") or [])))[:120] or (r.get("run_error") or "")[:120]
                    tip = f"{name}, answer {smp + 1}: {o}" + (f" ({r.get('model_calls')} calls)" if arm == "BX" else "") + (f" · {why}" if o != "PASS" and why else "")
                cells += f'<td class="c {cls}" title="{html.escape(tip)}">{sym}</td>'
            cells += '<td class="gap"></td>'
        rows += f"<tr><th>{j}</th>{cells}</tr>"
    head = "".join(f'<th colspan="{1 if a == "BR" else 3}">{n}</th><th class="gap"></th>' for a, n, *_ in ARMS)
    # recent
    ev = [r for r in recs if r.get("outcome") or r.get("event")][-12:][::-1]
    recent = "".join(f"<tr><td>{r.get('arm')}</td><td>{r.get('job')}</td><td>{(r.get('sample') or 0) + 1}</td>"
                     f"<td>{r.get('round', '') or ''}</td><td>{r.get('outcome') or r.get('event')}</td>"
                     f"<td>{fmt(r.get('latency') or r.get('latency_total'), 0, ' s')}</td></tr>" for r in ev)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="20">
<title>Glimmer baseline: live</title><style>
:root{{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;--ok:#0ca30c;--bad:#d03b3b;--inv:#fab219}}
@media(prefers-color-scheme:dark){{:root{{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--line:#383835}}}}
body{{background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,system-ui,sans-serif;margin:24px;max-width:1100px}}
h1{{font-size:20px;margin:0}} .muted{{color:var(--ink2)}} .row{{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}}
.tile{{flex:1;min-width:280px;border:1px solid var(--line);border-radius:10px;padding:14px}}
.tname{{font-weight:600}} .sw{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}}
.tdesc,.sub{{color:var(--ink2);font-size:12px}} .hero{{font-size:34px;font-weight:600;margin-top:6px}}
.prog{{height:6px;background:var(--line);border-radius:4px;margin:8px 0 4px;overflow:hidden}} .prog div{{height:100%;border-radius:4px}}
.kv{{width:100%;margin-top:8px;font-size:12px}} .kv td:last-child{{text-align:right;font-variant-numeric:tabular-nums}}
table.grid{{border-collapse:separate;border-spacing:2px;font-size:12px}} .grid th{{color:var(--ink2);font-weight:500;padding:2px 6px}}
.c{{width:22px;height:20px;text-align:center;border-radius:4px;cursor:default}} .ok{{background:var(--ok);color:#fff}}
.bad{{background:var(--bad);color:#fff}} .inv{{background:var(--inv);color:#000}} .wait{{color:var(--ink2);border:1px dashed var(--line)}}
.gap{{width:10px}} table.ev{{border-collapse:collapse;font-size:12px}} .ev td,.ev th{{padding:3px 10px;border-bottom:1px solid var(--line);text-align:left}}
</style></head><body>
<h1>Forge · how Glimmer is doing (step-2 baseline run)</h1>
<div class="muted">{phase(log)} · updated {now} (page reloads every 20 s) · GPU time {gpu_h * 60:.0f} min ≈ ${gpu_h * RATE:.2f} of the $3.00 cap (A100-80GB, $2.50/h)</div>
<div class="muted">Live counter: {live()} answers from Hint + All-fixes have gone through the safety box so far (results appear in the tiles when that part of the run finishes).</div>
<div class="row">{tiles}</div>
<h3>Every answer, job by job</h3><div class="muted">✓ correct · ✗ wrong · ! invalid · · not run yet. Hover a cell for details.
30 held-out CadQuery jobs (M = medium, H = hard). Plain Glimmer gives 1 answer per job; the others give 3.</div>
<table class="grid"><tr><th></th>{head}</tr>{rows}</table>
<h3>Latest events</h3><table class="ev"><tr><th>Arm</th><th>Job</th><th>Answer</th><th>Round</th><th>What</th><th>Model time</th></tr>{recent}</table>
<p class="muted">Pass rates are partial until the run ends; the final numbers and rules are in experiments/bmax/PLAN.md.
Data: results/bmax-baseline-2026-10-29/*/calls.jsonl. Made by experiments/bmax/glimmer_dashboard.py.</p></body></html>"""


def write():
    recs, log = load()
    tmp = OUT + ".tmp"; open(tmp, "w").write(page(recs, log)); os.replace(tmp, OUT)
    return log


if __name__ == "__main__":
    while True:
        log = write()
        if "--loop" not in sys.argv or "app stopped" in log or "APP STOP FAILED" in log: break
        time.sleep(20)
    write()
