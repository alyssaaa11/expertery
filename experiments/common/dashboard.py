"""Live run dashboard for a Glimmer evaluation session (generalised).

Same output style as experiments/bmax/glimmer_dashboard.py: one
self-contained HTML page (data embedded, because Chrome blocks fetch() on
file://) that reloads itself every 20 s. Status is colour plus a symbol
(✓ correct, ✗ wrong, ! invalid, · not run yet), never colour alone, with
light/dark CSS.

Usage: dashboard.py --run <results dir> --config <arms.json> --out <page.html> [--loop]
The arms config is a JSON list of {name, label, description, expected, colour}.
--loop rewrites the page every 20 s until the session log says the app stopped.
"""
import argparse
import glob
import html
import json
import os
import sys
import time

RATE = 2.50  # A100-80GB $/h
REFRESH_S = 20


def load_arms(config_path):
    """Arms list: [(name, label, description, expected, colour)]."""
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        (a["name"], a.get("label", a["name"]), a.get("description", ""),
         a["expected"], a.get("colour", "#2a78d6"))
        for a in data
    ]


def default_arms():
    return [
        ("BR", "Plain Glimmer", "manual + request, 1 try", 30, "#2a78d6"),
        ("B2", "Hint, 1 try", "manual + hint sentence, 1 try", 90, "#eb6834"),
        ("BX", "All fair fixes (B-max)", "hint + 3 examples + xhigh + up to 3 tries",
         90, "#1baf7a"),
    ]


def load_calls(run_dir):
    """All calls.jsonl records under the run dir (any depth)."""
    recs = []
    for path in glob.glob(os.path.join(run_dir, "**", "calls.jsonl"), recursive=True):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    recs.append(json.loads(line))
                except ValueError:
                    pass
    return recs


def load_log(run_dir):
    path = os.path.join(run_dir, "session.log")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


def arm_k(recs, arm):
    """Samples per job for this arm (1 unless multi-sample records exist)."""
    samples = [r.get("sample", 0) for r in recs
               if r.get("arm") == arm and r.get("outcome")]
    return max(samples, default=0) + 1


def stats(recs, arms):
    out = {}
    for arm, *_ in arms:
        k = arm_k(recs, arm)
        multi = k > 1
        fin = [r for r in recs if r.get("arm") == arm and r.get("outcome")]
        p = sum(r["outcome"] == "PASS" for r in fin)
        f = sum(r["outcome"] == "FAIL" for r in fin)
        inv = sum(r["outcome"] == "INVALID" for r in fin)
        tok = 0
        for r in fin:
            if multi:
                tok += (r.get("prompt_tokens_total") or 0) + (r.get("completion_tokens_total") or 0)
            else:
                tok += (r.get("usage") or {}).get("total_tokens") or 0
        lat = [r.get("latency_total") if multi else r.get("latency") for r in fin]
        lat = [x for x in lat if x]
        mc = [r.get("model_calls") or 1 for r in fin]
        out[arm] = dict(done=len(fin), pass_=p, fail=f, inv=inv,
                        rate=(100 * p / (p + f)) if p + f else None,
                        tok_per=(tok / len(fin)) if fin else None,
                        tok_per_correct=(tok / p) if p else None,
                        lat=(sum(lat) / len(lat)) if lat else None,
                        calls=(sum(mc) / len(mc)) if mc else None)
    return out


def phase(log):
    if "app stopped" in log or "APP STOP FAILED" in log:
        return "Finished, GPU stopped"
    n = log.count("runner exit")
    if n >= 3:
        return "Main run finished, stopping GPU"
    if n == 2:
        return "Main run in progress"
    if "main start" in log:
        return "Main run started"
    if "PILOT DONE" in log:
        return "Pilot done, waiting for GO"
    if "ready" in log:
        return "Pilot running"
    return "Starting Glimmer on Modal"


def live(run_dir):
    return sum(
        len(os.listdir(d))
        for d in glob.glob(os.path.join(run_dir, "**", "sandbox_*"), recursive=True)
        if os.path.isdir(d)
    )


def fmt(x, d=0, suf=""):
    return "–" if x is None else "%s%s" % (format(x, ",.%df" % d), suf)


def outcome_cell(r, arm, multi):
    """(css class, symbol, tooltip) for one answer cell."""
    if r is None:
        return "wait", "·", "not run yet"
    o = r["outcome"]
    cls, sym = {"PASS": ("ok", "✓"), "FAIL": ("bad", "✗")}.get(o, ("inv", "!"))
    why = "; ".join(map(str, (r.get("fails") or r.get("failed_checks") or [])))[:120]
    why = why or (r.get("run_error") or "")[:120]
    tip = "answer %d: %s" % ((r.get("sample") or 0) + 1, o)
    if multi and r.get("model_calls"):
        tip += " (%s calls)" % r.get("model_calls")
    if o != "PASS" and why:
        tip += " · %s" % why
    return cls, sym, tip


def fc_status(recs, gpu_start=None, exam=None):
    """One-line status for runner_fc runs: the exam name, answers with
    a box result, answers with a grade, and GPU minutes since
    --gpu-start. Records without the runner_fc fields count as zero."""
    n_box = sum(1 for r in recs if r.get("box_ok"))
    n_grade = sum(1 for r in recs if r.get("graded"))
    name = exam or next(
        (r.get("exam") for r in recs if r.get("exam")), None) or "–"
    mins = None
    if gpu_start is not None:
        try:
            mins = (time.time() - float(gpu_start)) / 60.0
        except (TypeError, ValueError):
            mins = None
    return {"exam": name, "box": n_box, "graded": n_grade, "gpu_min": mins}


def page(recs, log, arms, run_dir="results", cap=3.0, title=None, fc=None):
    st = stats(recs, arms)
    if fc is not None:
        fc_line = (
            '<div class="muted">Exam: %s · %d answers through the safety '
            "box, %d graded · GPU time %s.</div>\n"
            % (html.escape(str(fc["exam"])), fc["box"], fc["graded"],
               "–" if fc["gpu_min"] is None else "%.0f min" % fc["gpu_min"])
        )
    else:
        fc_line = ""
    now = time.strftime("%H:%M:%S")
    gpu_h = 0.0
    tiles = ""
    for arm, name, desc, exp, col in arms:
        a = st[arm]
        pct = 100 * a["done"] / exp if exp else 0
        tiles += (
            '<div class="tile"><div class="tname">'
            '<span class="sw" style="background:%s"></span>%s</div>\n'
            '<div class="tdesc">%s</div><div class="hero">%s</div>'
            '<div class="sub">pass rate so far</div>\n'
            '<div class="prog" title="%d of %d answers">'
            '<div style="width:%.1f%%;background:%s"></div></div>\n'
            '<div class="sub">%d / %d answers · ✓ %d · ✗ %d · ! %d invalid</div>\n'
            '<table class="kv"><tr><td>Model calls per answer</td><td>%s</td></tr>\n'
            '<tr><td>Tokens per answer</td><td>%s</td></tr>'
            "<tr><td>Tokens per correct part</td><td>%s</td></tr>\n"
            '<tr><td>Model time per answer</td><td>%s</td></tr></table></div>'
            % (col, html.escape(name), html.escape(desc), fmt(a["rate"], 0, "%"),
               a["done"], exp, pct, col, a["done"], exp,
               a["pass_"], a["fail"], a["inv"], fmt(a["calls"], 1),
               fmt(a["tok_per"]), fmt(a["tok_per_correct"]), fmt(a["lat"], 0, " s"))
        )
    jobs = sorted({r.get("job") for r in recs if r.get("job")})
    rows = ""
    for j in jobs:
        cells = ""
        for arm, name, _, _, _ in arms:
            k = arm_k(recs, arm)
            multi = k > 1
            rs = {r.get("sample", 0): r for r in recs
                  if r.get("arm") == arm and r.get("job") == j and r.get("outcome")}
            for smp in range(k):
                cls, sym, tip = outcome_cell(rs.get(smp), arm, multi)
                cells += '<td class="c %s" title="%s">%s</td>' % (
                    cls, html.escape("%s, %s" % (name, tip)), sym)
            cells += '<td class="gap"></td>'
        rows += "<tr><th>%s</th>%s</tr>" % (html.escape(str(j)), cells)
    head = "".join(
        '<th colspan="%d">%s</th><th class="gap"></th>' % (arm_k(recs, a), n)
        for a, n, *_ in arms
    )
    ev = [r for r in recs if r.get("outcome") or r.get("event")][-12:][::-1]
    recent = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (r.get("arm"), r.get("job"), (r.get("sample") or 0) + 1,
           r.get("round", "") or "", r.get("outcome") or r.get("event"),
           fmt(r.get("latency") or r.get("latency_total"), 0, " s"))
        for r in ev
    )
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="%d">\n'
        "<title>%s</title><style>\n"
        ":root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;"
        "--ok:#0ca30c;--bad:#d03b3b;--inv:#fab219}\n"
        "@media(prefers-color-scheme:dark)"
        "{:root{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--line:#383835}}\n"
        "body{background:var(--bg);color:var(--ink);"
        "font:14px/1.45 -apple-system,system-ui,sans-serif;margin:24px;max-width:1100px}\n"
        "h1{font-size:20px;margin:0} .muted{color:var(--ink2)} "
        ".row{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}\n"
        ".tile{flex:1;min-width:280px;border:1px solid var(--line);"
        "border-radius:10px;padding:14px}\n"
        ".tname{font-weight:600} "
        ".sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}\n"
        ".tdesc,.sub{color:var(--ink2);font-size:12px} "
        ".hero{font-size:34px;font-weight:600;margin-top:6px}\n"
        ".prog{height:6px;background:var(--line);border-radius:4px;margin:8px 0 4px;"
        "overflow:hidden} .prog div{height:100%%;border-radius:4px}\n"
        ".kv{width:100%%;margin-top:8px;font-size:12px} "
        ".kv td:last-child{text-align:right;font-variant-numeric:tabular-nums}\n"
        "table.grid{border-collapse:separate;border-spacing:2px;font-size:12px} "
        ".grid th{color:var(--ink2);font-weight:500;padding:2px 6px}\n"
        ".c{width:22px;height:20px;text-align:center;border-radius:4px;cursor:default} "
        ".ok{background:var(--ok);color:#fff}\n"
        ".bad{background:var(--bad);color:#fff} .inv{background:var(--inv);color:#000} "
        ".wait{color:var(--ink2);border:1px dashed var(--line)}\n"
        ".gap{width:10px} table.ev{border-collapse:collapse;font-size:12px} "
        ".ev td,.ev th{padding:3px 10px;border-bottom:1px solid var(--line);text-align:left}\n"
        "</style></head><body>\n"
        "<h1>%s</h1>\n"
        '<div class="muted">%s · updated %s (page reloads every %d s) · '
        "GPU time %.0f min ≈ $%.2f of the $%.2f cap (A100-80GB, $%.2f/h)</div>\n"
        '<div class="muted">Live counter: %d answers have gone through the '
        "safety box so far (results appear in the tiles when that part of the run "
        "finishes).</div>\n"
        "%s"
        '<div class="row">%s</div>\n'
        "<h3>Every answer, job by job</h3>"
        '<div class="muted">✓ correct · ✗ wrong · ! invalid · · not run yet. '
        "Hover a cell for details.</div>\n"
        '<table class="grid"><tr><th></th>%s</tr>%s</table>\n'
        "<h3>Latest events</h3>"
        '<table class="ev"><tr><th>Arm</th><th>Job</th><th>Answer</th><th>Round</th>'
        "<th>What</th><th>Model time</th></tr>%s</table>\n"
        '<p class="muted">Pass rates are partial until the run ends. '
        "Data: %s.</p></body></html>"
        % (REFRESH_S, html.escape(title or "Forge · live run"),
           html.escape(title or "Forge · live run"), phase(log), now, REFRESH_S,
           gpu_h * 60, gpu_h * RATE, cap, RATE, 0, fc_line, tiles, head,
           rows, recent, html.escape(run_dir))
    )


def write_page(run_dir, arms, out_path, cap=3.0, title=None, fc=False,
               gpu_start=None, exam=None):
    """Render the dashboard; returns the session log text.

    `fc` enables the runner_fc line (exam name, box/grade counts, GPU
    minutes since `gpu_start`); without it the page is unchanged.
    calls.jsonl is re-read on every call, so --loop follows a live run.
    """
    recs = load_calls(run_dir)
    log = load_log(run_dir)
    info = fc_status(recs, gpu_start=gpu_start, exam=exam) if fc else None
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(page(recs, log, arms, run_dir=run_dir, cap=cap, title=title,
                     fc=info))
    os.replace(tmp, out_path)
    return log


def stopped(log):
    return "app stopped" in log or "APP STOP FAILED" in log


def main(argv=None):
    parser = argparse.ArgumentParser(description="Forge live run dashboard")
    parser.add_argument("--run", required=True, help="results dir to read")
    parser.add_argument("--config", default=None,
                        help="arms JSON config (name, label, description, expected, colour)")
    parser.add_argument("--out", default=None, help="output HTML path")
    parser.add_argument("output", nargs="?",
                        help="output HTML path (positional alternative to --out)")
    parser.add_argument("--loop", action="store_true",
                        help="rewrite every 20 s until the session log says stopped")
    parser.add_argument("--cap", type=float, default=3.0)
    parser.add_argument("--title", default=None)
    parser.add_argument("--fc", action="store_true",
                        help="runner_fc run: show the exam name, box/grade "
                             "counts and GPU minutes since --gpu-start")
    parser.add_argument("--gpu-start", default=None,
                        help="unix seconds of the session's GPU start")
    parser.add_argument("--exam", default=None,
                        help="exam name to show (defaults to the records')")
    args = parser.parse_args(argv)
    out_path = args.out or args.output
    if not out_path:
        parser.error("an output path is required (--out or positional)")
    arms = load_arms(args.config) if args.config else default_arms()
    while True:
        log = write_page(args.run, arms, out_path, cap=args.cap,
                         title=args.title, fc=args.fc,
                         gpu_start=args.gpu_start, exam=args.exam)
        if not args.loop or stopped(log):
            break
        time.sleep(REFRESH_S)
    write_page(args.run, arms, out_path, cap=args.cap, title=args.title,
               fc=args.fc, gpu_start=args.gpu_start, exam=args.exam)
    return 0


if __name__ == "__main__":
    sys.exit(main())
