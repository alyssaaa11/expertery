#!/usr/bin/env python3
"""Answer viewer: one static HTML page per run.

For every record in a results dir's calls.jsonl the page shows: the task
text, Glimmer's thinking (collapsed <details>, full text), its code
(<pre>, HTML-escaped), a picture of ITS part next to the CORRECT part
(SVG rendered in the cloud box via render_cloud; --offline = no
pictures), and the referee's verdict (big PASS / FAIL / crash), the
fails list, the answer's own measurements, the crash's last lines, and
tokens + seconds.

Summary at the top: pass rate, crashes, wrong shapes, a per-family
table, median tokens and seconds. Filters are plain HTML anchors (no JS
libraries): all / pass / fail / crash, and by family.

Writes <out>/index.html (one file, inline SVG, no network) and
<out>/svgs.json (cache, so re-runs cost $0: only ids missing from the
cache are rendered).

Never prints reference code or expected values: the reference appears
only as a PICTURE. Reference ``reference`` fields from the jobs file are
used as render input and are never written to the HTML.

CLI: make_viewer.py --run <results dir with calls.jsonl> --jobs <jobs
  file> --out <dir> [--limit N] [--budget 0.30] [--offline]

Tests are offline (fake render_fn, synthetic jobs/records); --offline
renders nothing and reaches nothing.
"""

import argparse
import html
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import render_cloud  # noqa: E402 (Modal only inside its remote function)

CALLS_NAME = "calls.jsonl"
INDEX_NAME = "index.html"
CACHE_NAME = "svgs.json"

CRASH_TAIL_LINES = 15

FORBIDDEN_PARTS = ("blind/", "experiments/option-a/")


def is_forbidden(path):
    """Refuse paths under blind/ or experiments/option-a/."""
    text = os.path.normpath(str(path or ""))
    return any(part in (text + "/") for part in FORBIDDEN_PARTS)


def load_calls(run_dir):
    """All calls.jsonl records in a results dir (in file order)."""
    path = os.path.join(run_dir, CALLS_NAME)
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_jobs(path):
    """Jobs file: jsonl lines with id/text (+ family/level/reference).

    Returns {id: job}. Reference sources are kept for RENDER input
    only; render input never reaches the HTML writer.
    """
    jobs = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            job = json.loads(line)
            if not isinstance(job, dict) or not job.get("id") \
                    or not job.get("text"):
                raise ValueError("jobs file %r has a record without "
                                 "id/text" % (path,))
            jobs[job["id"]] = job
    return jobs


def job_id_of(rec):
    """The record's job id (final `job` or factory `id`)."""
    return rec.get("job", rec.get("id"))


def rep_of(rec):
    """The record's repetition index."""
    return rec.get("rep", rec.get("sample", 0))


def verdict_of(rec):
    """The recorded verdict (final `verdict`/`outcome`)."""
    return rec.get("verdict", rec.get("outcome", "INVALID"))


def is_crash(rec):
    """A crash: not PASS with a non-empty run error (or INVALID)."""
    if verdict_of(rec) == "PASS":
        return False
    return bool(str(rec.get("run_error") or "").strip()) \
        or verdict_of(rec) == "INVALID"


def status_of(rec):
    """pass | crash | fail (crash = run error, fail = wrong shape)."""
    if verdict_of(rec) == "PASS":
        return "pass"
    return "crash" if is_crash(rec) else "fail"


def family_of(rec, jobs):
    """The job's family (or level), for the per-family table/filters."""
    job = jobs.get(job_id_of(rec) or "", {})
    fam = job.get("family", job.get("level"))
    return str(fam) if fam is not None else "-"


def tokens_of(rec):
    """(prompt_tokens, completion_tokens) as ints (same rule as runners)."""
    usage = rec.get("usage") or {}
    try:
        prompt = int(rec.get("prompt_tokens",
                             usage.get("prompt_tokens", 0)) or 0)
    except (TypeError, ValueError):
        prompt = 0
    try:
        completion = int(rec.get("completion_tokens",
                                 usage.get("completion_tokens", 0)) or 0)
    except (TypeError, ValueError):
        completion = 0
    return prompt, completion


def seconds_of(rec):
    """Seconds as a float (0.0 when missing)."""
    try:
        return float(rec.get("seconds", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def crash_tail(run_error, n=CRASH_TAIL_LINES):
    """The crash's last lines (empty string when it did not crash)."""
    text = str(run_error or "").strip()
    if not text:
        return ""
    return "\n".join(text.splitlines()[-n:])


def answer_id(rec):
    """SVG-cache id for the answer picture."""
    return "a:%s:%s" % (job_id_of(rec), rep_of(rec))


def ref_id(rec):
    """SVG-cache id for the correct-part picture."""
    return "r:%s" % (job_id_of(rec),)


def code_of(rec):
    """The recorded answer code."""
    code = rec.get("code", rec.get("extracted_code"))
    return code if isinstance(code, str) else ""


def thinking_of(rec):
    """Glimmer's thinking text (full reasoning, never truncated)."""
    for key in ("reasoning", "reasoning_content", "thinking"):
        val = rec.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def fails_of(rec):
    """The referee's fails list."""
    fails = rec.get("fails", rec.get("failed_checks") or [])
    return [str(f) for f in (fails or [])]


def build_render_items(records, jobs):
    """[{id, code}] for every picture the page needs.

    Answers render from the recorded code; references render from the
    jobs file's reference source (trusted generator code, same box, same
    view). Jobs without a reference get no ref item (placeholder text on
    the page instead). Reference sources are render input only.
    """
    items = []
    for rec in records:
        items.append({"id": answer_id(rec), "code": code_of(rec)})
    seen_refs = set()
    for rec in records:
        job = jobs.get(job_id_of(rec) or "", {})
        ref = job.get("reference")
        rid = ref_id(rec)
        if isinstance(ref, str) and ref.strip() \
                and rid not in seen_refs:
            items.append({"id": rid, "code": ref})
            seen_refs.add(rid)
    return items


def load_cache(out_dir):
    """The svgs.json cache ({id: svg_text}), {} when absent."""
    path = os.path.join(out_dir, CACHE_NAME)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _cacheable(text):
    """Cache real pictures and answer errors, never OFFLINE/BUDGET marks
    (those must retry next run)."""
    if not isinstance(text, str) or not text:
        return False
    return not text.startswith(render_cloud.BUDGET_PREFIX) \
        and not text.startswith("OFFLINE")


OFFLINE_TEXT = "OFFLINE: no picture (re-run without --offline)"


def collect_svgs(records, jobs, out_dir, budget, offline, render_fn):
    """{svg id: text} for the page; updates the svgs.json cache.

    Only ids missing from the cache are rendered (re-runs cost $0).
    --offline renders nothing. Returns (svgs, n_rendered).
    """
    os.makedirs(out_dir, exist_ok=True)
    cache = load_cache(out_dir)
    items = build_render_items(records, jobs)
    missing = [it for it in items if it["id"] not in cache]
    rendered = {}
    if missing and not offline:
        rendered = dict(render_fn(missing, budget) or {})
        for key, text in rendered.items():
            if _cacheable(text):
                cache[key] = text
        with open(os.path.join(out_dir, CACHE_NAME), "w",
                  encoding="utf-8") as f:
            json.dump(cache, f)
    elif not os.path.exists(os.path.join(out_dir, CACHE_NAME)):
        with open(os.path.join(out_dir, CACHE_NAME), "w",
                  encoding="utf-8") as f:
            json.dump(cache, f)
    svgs = dict(cache)
    for it in items:
        if it["id"] not in svgs:
            svgs[it["id"]] = rendered.get(it["id"], OFFLINE_TEXT)
    return svgs, len(missing) if not offline else 0


def default_render_fn(items, budget):
    """Render via the Modal app (paid; never used by --offline/tests)."""
    return render_cloud.render_svgs(items, budget)


def summarize(records, jobs):
    """Summary numbers: pass rate, crashes, wrong shapes, per-family
    table, median tokens and seconds."""
    n = len(records)
    statuses = [status_of(r) for r in records]
    n_pass = statuses.count("pass")
    n_crash = statuses.count("crash")
    n_fail = statuses.count("fail")
    by_family = {}
    for rec in records:
        fam = family_of(rec, jobs)
        row = by_family.setdefault(fam, {"n": 0, "pass": 0})
        row["n"] += 1
        if status_of(rec) == "pass":
            row["pass"] += 1
    prompts = [tokens_of(r)[0] for r in records]
    completions = [tokens_of(r)[1] for r in records]
    seconds = [seconds_of(r) for r in records]
    return {
        "n": n,
        "pass": n_pass,
        "crash": n_crash,
        "fail": n_fail,
        "rate": (n_pass / n) if n else 0.0,
        "by_family": {f: {"n": v["n"], "pass": v["pass"],
                           "rate": (v["pass"] / v["n"]) if v["n"]
                           else 0.0}
                      for f, v in sorted(by_family.items())},
        "median_prompt": statistics.median(prompts) if prompts else 0,
        "median_completion": statistics.median(completions)
        if completions else 0,
        "median_seconds": statistics.median(seconds) if seconds else 0,
    }


def svg_html(svg_text):
    """Inline SVG for the page, or escaped placeholder text."""
    if isinstance(svg_text, str) and "<svg" in svg_text:
        i = svg_text.find("<svg")
        return svg_text[i:]
    return "<pre class=\"svg-missing\">%s</pre>" \
        % html.escape(str(svg_text or "no picture"))


STATUS_BADGE = {
    "pass": "<span class=\"badge-pass\">&#10003; PASS</span>",
    "fail": "<span class=\"badge-fail\">&#10007; FAIL</span>",
    "crash": "<span class=\"badge-crash\">&#9888; crash</span>",
}


def card_html(i, rec, jobs, svgs):
    """One answer card: task, verdict, pictures, thinking, code, stats."""
    job = jobs.get(job_id_of(rec) or "", {})
    status = status_of(rec)
    prompt_n, completion_n = tokens_of(rec)
    fails = fails_of(rec)
    meas = rec.get("measurements")
    tail = crash_tail(rec.get("run_error"))
    parts = ["<div class=\"card status-%s\" id=\"rec-%d\">" % (status, i)]
    parts.append("<h3>%s &mdash; rep %s %s</h3>"
                 % (html.escape(str(job_id_of(rec))),
                    html.escape(str(rep_of(rec))),
                    STATUS_BADGE[status]))
    parts.append("<p class=\"task\">%s</p>"
                 % html.escape(str(job.get("text",
                                           "(task text not in jobs "
                                           "file)"))))
    if fails:
        parts.append("<p>referee fails: %s</p>"
                     % html.escape(", ".join(fails)))
    if isinstance(meas, dict) and meas:
        parts.append("<p>answer measurements: %s</p>"
                     % html.escape(json.dumps(meas, sort_keys=True)))
    parts.append("<div class=\"pics\">"
                 "<div><p>Glimmer's part</p>%s</div>"
                 "<div><p>correct part</p>%s</div></div>"
                 % (svg_html(svgs.get(answer_id(rec))),
                    svg_html(svgs.get(ref_id(rec),
                                      "no reference picture"))))
    thinking = thinking_of(rec)
    if thinking:
        parts.append("<details><summary>Glimmer's thinking "
                     "(%d chars)</summary><pre>%s</pre></details>"
                     % (len(thinking), html.escape(thinking)))
    parts.append("<details open><summary>code</summary><pre>%s</pre>"
                 "</details>" % html.escape(code_of(rec) or
                                            "(no code recorded)"))
    if tail:
        parts.append("<details><summary>crash (last %d lines)</summary>"
                     "<pre>%s</pre></details>"
                     % (CRASH_TAIL_LINES, html.escape(tail)))
    parts.append("<p class=\"meta\">prompt %d tokens &middot; "
                 "completion %d tokens &middot; %.1f s</p>"
                 % (prompt_n, completion_n, seconds_of(rec)))
    parts.append("</div>")
    return "\n".join(parts)


def _link_list(title, ids):
    if not ids:
        return "<p>%s: none</p>" % html.escape(title)
    return "<p>%s: %s</p>" % (
        html.escape(title),
        " ".join("<a href=\"#rec-%d\">#%d</a>" % (i, i) for i in ids))


def page_html(records, jobs, svgs, summary, title="Answer viewer"):
    """The whole index.html (one file, inline SVG, no network)."""
    idx = {"pass": [i for i, r in enumerate(records)
                    if status_of(r) == "pass"],
           "fail": [i for i, r in enumerate(records)
                    if status_of(r) == "fail"],
           "crash": [i for i, r in enumerate(records)
                     if status_of(r) == "crash"]}
    fams = sorted({family_of(r, jobs) for r in records})
    fam_ids = {f: [i for i, r in enumerate(records)
                   if family_of(r, jobs) == f] for f in fams}
    parts = ["<!DOCTYPE html>",
             "<html><head><meta charset=\"utf-8\">",
             "<title>%s</title>" % html.escape(title),
             "<style>",
             "body { font-family: sans-serif; margin: 2em; }",
             ".badge-pass { color: green; font-size: 1.4em; }",
             ".badge-fail { color: red; font-size: 1.4em; }",
             ".badge-crash { color: orange; font-size: 1.4em; }",
             ".card { border: 1px solid #999; padding: 1em; "
             "margin-bottom: 1em; }",
             ".card svg { width: 100%; height: auto; }",
             ".pics { display: grid; grid-template-columns: 1fr 1fr; "
             "gap: 1em; }",
             ".task { font-size: 0.9em; }",
             ".meta { font-size: 0.85em; color: #555; }",
             "pre { white-space: pre-wrap; word-break: break-word; "
             "background: #f4f4f4; padding: 0.5em; }",
             "table { border-collapse: collapse; }",
             "th, td { border: 1px solid #999; padding: 0.3em 0.8em; }",
             "</style></head><body>",
             "<h1>%s</h1>" % html.escape(title),
             "<p id=\"summary\">answers <span id=\"count-n\">%d</span> "
             "&middot; pass rate <span id=\"count-rate\">%.1f%%</span> "
             "(<span id=\"count-pass\">%d</span> pass, "
             "<span id=\"count-fail\">%d</span> wrong shape, "
             "<span id=\"count-crash\">%d</span> crash)</p>"
             % (summary["n"], 100.0 * summary["rate"], summary["pass"],
                summary["fail"], summary["crash"]),
             "<p>median prompt <span id=\"med-prompt\">%s</span> tokens "
             "&middot; median completion "
             "<span id=\"med-completion\">%s</span> tokens &middot; "
             "median <span id=\"med-seconds\">%s</span> s</p>"
             % (html.escape(str(summary["median_prompt"])),
                html.escape(str(summary["median_completion"])),
                html.escape(str(summary["median_seconds"]))),
             "<table><tr><th>family</th><th>n</th><th>pass</th>"
             "<th>rate</th></tr>"]
    for fam, row in summary["by_family"].items():
        parts.append("<tr><td>%s</td><td>%d</td><td>%d</td><td>%.1f%%</td>"
                     "</tr>" % (html.escape(str(fam)), row["n"],
                                 row["pass"], 100.0 * row["rate"]))
    parts.append("</table>")
    nav = ["<nav><a href=\"#sec-all\">all (%d)</a>" % len(records),
           "<a href=\"#sec-pass\">pass (%d)</a>" % len(idx["pass"]),
           "<a href=\"#sec-fail\">fail (%d)</a>" % len(idx["fail"]),
           "<a href=\"#sec-crash\">crash (%d)</a>" % len(idx["crash"])]
    nav += ["<a href=\"#fam-%s\">family %s (%d)</a>"
            % (html.escape(f), html.escape(f), len(fam_ids[f]))
            for f in fams]
    parts.append(" | ".join(nav) + "</nav>")
    parts.append("<section id=\"sec-pass\"><h2>pass</h2>%s</section>"
                 % _link_list("answers", idx["pass"]))
    parts.append("<section id=\"sec-fail\"><h2>fail</h2>%s</section>"
                 % _link_list("answers", idx["fail"]))
    parts.append("<section id=\"sec-crash\"><h2>crash</h2>%s</section>"
                 % _link_list("answers", idx["crash"]))
    for f in fams:
        parts.append("<section id=\"fam-%s\"><h2>family %s</h2>%s"
                     "</section>" % (html.escape(f), html.escape(f),
                                     _link_list("answers", fam_ids[f])))
    parts.append("<section id=\"sec-all\"><h2>all answers</h2>")
    for i, rec in enumerate(records):
        parts.append(card_html(i, rec, jobs, svgs))
    parts.append("</section></body></html>")
    return "\n".join(parts) + "\n"


def build(run_dir, jobs_path, out_dir, limit=None, budget=0.30,
          offline=False, render_fn=None):
    """Build index.html + svgs.json. Returns (summary, n_rendered)."""
    records = load_calls(run_dir)
    if limit is not None:
        records = records[:limit]
    jobs = load_jobs(jobs_path)
    svgs, n_rendered = collect_svgs(
        records, jobs, out_dir, budget, offline,
        render_fn or default_render_fn)
    summary = summarize(records, jobs)
    with open(os.path.join(out_dir, INDEX_NAME), "w",
              encoding="utf-8") as f:
        f.write(page_html(records, jobs, svgs, summary))
    return summary, n_rendered


def main(argv=None):
    """CLI: --run --jobs --out [--limit N] [--budget 0.30] [--offline]."""
    parser = argparse.ArgumentParser(
        description="One static HTML page per run: every answer, its "
                    "pictures, and the referee's verdict.")
    parser.add_argument("--run", required=True,
                        help="results dir with calls.jsonl")
    parser.add_argument("--jobs", required=True, help="jobs file")
    parser.add_argument("--out", required=True, help="output dir")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--budget", type=float, default=0.30)
    parser.add_argument("--offline", action="store_true",
                        help="no pictures (for tests)")
    args = parser.parse_args(argv)
    for path in (args.run, args.jobs):
        if is_forbidden(path):
            parser.error("refusing path under blind/ or "
                         "experiments/option-a/: %s" % path)
            return 2
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be >= 1")
        return 2
    summary, n_rendered = build(args.run, args.jobs, args.out,
                                args.limit, args.budget, args.offline)
    print("wrote %s (%d answers, %d rendered, %.1f%% pass)"
          % (os.path.join(args.out, INDEX_NAME), summary["n"],
             n_rendered, 100.0 * summary["rate"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
