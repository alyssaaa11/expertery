#!/usr/bin/env python3
"""Factory gallery: one SVG card per family.

For each family, the first non-dev job: build its reference in-process
(trusted generator code, like make_jobs) and export an SVG with
cq.exporters.export(..., exportType="SVG") (isometric view, hidden lines
off). Writes index.html: a grid of 10 cards (family name, job id, job
text, the SVG). With --runs, each card also shows that job's teacher
verdict (PASS/FAIL/INVALID) and, when the answer failed, its fails text
(from calls.jsonl; no answer code is run).

Plain HTML + inline SVG, no network, no JS libraries. The user wants to
see the factory's parts; this is also the start of the demo viewer.

CLI: gallery.py [--out results/factory-gallery] [--runs <teacher run dir>].
"""

import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

JOBS_PATH = os.path.join(HERE, "jobs.jsonl")
SPLIT_PATH = os.path.join(HERE, "split.json")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                           "results", "factory-gallery")

SVG_OPT = {"projectionDir": (1, 1, 1), "showHidden": False}
ID_RE = re.compile(r"F\d+-\d+$")


def load_jobs(path=None):
    """Read the factory jobs file (id, family, text, reference)."""
    with open(path or JOBS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_dev_ids(path=None):
    """The dev ids from split.json (never shown in the gallery)."""
    try:
        with open(path or SPLIT_PATH, encoding="utf-8") as f:
            return set(json.load(f).get("dev", []))
    except OSError:
        return set()


def job_n(job_id):
    """The numeric suffix of F<family>-<n>."""
    return int(str(job_id).rsplit("-", 1)[1])


def pick_first_jobs(jobs, dev_ids):
    """The first non-dev job per family (10 cards), by job number."""
    by_family = {}
    for job in jobs:
        if not ID_RE.match(str(job.get("id") or "")):
            continue
        if job["id"] in dev_ids:
            continue
        by_family.setdefault(job["family"], []).append(job)
    cards = []
    for family in sorted(by_family):
        cards.append(sorted(by_family[family], key=lambda j: job_n(j["id"]))
                     [0])
    return cards


def build_shape(source):
    """Build a factory reference shape from its program source.

    The source is trusted generator code; it assigns `result` (same rule
    as answers: a Workplane gives its solid). Needs cadquery.
    """
    import cadquery as _cq

    ns = {"__name__": "__main__"}
    exec(compile(source, "<reference>", "exec"), ns)
    result = ns["result"]
    if isinstance(result, _cq.Workplane):
        vals = [v for v in result.vals() if isinstance(v, _cq.Shape)]
        if len(vals) == 1:
            return vals[0]
        return _cq.Compound.makeCompound(vals)
    return result


def export_svg(shape, path):
    """Isometric SVG of a shape, hidden lines off. Needs cadquery.

    The exporter writes a fixed-size viewport with no viewBox, which
    clips wide drawings; fit_viewbox_to_drawing adds a viewBox around
    the drawing (with a margin) so nothing is clipped."""
    import cadquery as _cq

    _cq.exporters.export(shape, path, exportType="SVG", opt=dict(SVG_OPT))
    fit_viewbox_to_drawing(path)
    return path


def _transformed_bbox(svg_text):
    """Bounding box of an exported SVG's path coordinates in output units.

    Applies the exporter's <g> scale/translate to every path point.
    Returns (xmin, ymin, xmax, ymax) or None when there is nothing to
    fit (no paths)."""
    paths = re.findall(r'<path\s+d="([^"]*)"', svg_text)
    if not paths:
        return None
    pts = []
    for d in paths:
        nums = [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", d)]
        pts.extend(zip(nums[::2], nums[1::2]))
    if not pts:
        return None
    m = re.search(
        r"<g\s+transform=\"scale\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)"
        r"\s*translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)",
        svg_text)
    if m:
        sx, sy, tx, ty = (float(m.group(i)) for i in range(1, 5))
        pts = [(sx * (x + tx), sy * (y + ty)) for x, y in pts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def fit_viewbox_to_drawing(path_or_svg, margin=0.05):
    """Fit an SVG viewBox to its drawing, with a margin (not clipped).

    Accepts a file path (rewritten in place) or an SVG string (returns
    the rewritten string). The viewBox is the path bounding box grown
    by `margin` (fraction of each size, at least 1 unit). SVGs without
    paths are returned unchanged."""
    is_path = "\n" not in str(path_or_svg) and \
        os.path.isfile(str(path_or_svg))
    if is_path:
        with open(str(path_or_svg), encoding="utf-8") as f:
            svg_text = f.read()
    else:
        svg_text = str(path_or_svg)
    bbox = _transformed_bbox(svg_text)
    if bbox is None:
        result = svg_text
    else:
        xmin, ymin, xmax, ymax = bbox
        w, h = xmax - xmin, ymax - ymin
        mx = max(w * margin, 1.0)
        my = max(h * margin, 1.0)
        view = "viewBox=\"%s %s %s %s\"" % (
            xmin - mx, ymin - my, w + 2 * mx, h + 2 * my)
        if re.search(r"viewBox=\"[^\"]*\"", svg_text):
            result = re.sub(r"viewBox=\"[^\"]*\"", view, svg_text,
                            count=1)
        else:
            result = re.sub(r"<svg\b", "<svg " + view, svg_text, count=1)
    if is_path:
        with open(str(path_or_svg), "w", encoding="utf-8") as f:
            f.write(result)
        return path_or_svg
    return result


def inline_svg(path):
    """An exported SVG file as inline HTML (the <svg> element only)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    i = text.find("<svg")
    return text[i:] if i >= 0 else text


def load_verdicts(runs_dirs):
    """{(job id): (verdict, fails)} from teacher runs' calls.jsonl.

    Only the calls file is read; no answer code runs. When an id was
    asked more than once, a PASS wins, else the latest record wins.
    """
    import patterns as _patterns

    verdicts = {}
    for path in _patterns.find_calls_files(runs_dirs):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                job_id = rec.get("id")
                if (not ID_RE.match(str(job_id or ""))
                        or rec.get("verdict") not in (
                            "PASS", "FAIL", "INVALID")):
                    continue
                old = verdicts.get(job_id)
                if old is None or old[0] != "PASS":
                    verdicts[job_id] = (
                        rec.get("verdict"),
                        list(rec.get("fails") or []))
    return verdicts


def render(cards, inline_svgs, family_names, verdicts=None):
    """index.html: a grid of 10 cards (plain HTML + inline SVG)."""
    parts = ["<!DOCTYPE html>",
             "<html><head><meta charset=\"utf-8\">",
             "<title>Factory gallery</title>",
             "<style>",
             "body { font-family: sans-serif; margin: 2em; }",
             ".grid { display: grid; grid-template-columns: 1fr 1fr; "
             "gap: 1em; }",
             ".card { border: 1px solid #999; padding: 1em; }",
             ".card svg { width: 100%; height: auto; }",
             ".jobtext { font-size: 0.85em; }",
             ".verdict-PASS { color: green; }",
             ".verdict-FAIL { color: red; }",
             ".verdict-INVALID { color: orange; }",
             "</style></head><body>",
             "<h1>Factory gallery</h1>",
             "<div class=\"grid\">"]
    for job, svg in zip(cards, inline_svgs):
        parts.append("<div class=\"card\">")
        parts.append("<h2>%s</h2>"
                     % html.escape("F%s %s" % (
                         job["family"],
                         family_names.get(job["family"], ""))))
        parts.append("<p>job id: %s</p>" % html.escape(str(job["id"])))
        parts.append("<p class=\"jobtext\">%s</p>"
                     % html.escape(job["text"]))
        parts.append(svg)
        if verdicts is not None and job["id"] in verdicts:
            verdict, fails = verdicts[job["id"]]
            parts.append("<p>teacher verdict: "
                         "<span class=\"verdict-%s\">%s</span></p>"
                         % (html.escape(verdict), html.escape(verdict)))
            if verdict == "FAIL" and fails:
                parts.append("<p>fails: %s</p>"
                             % html.escape(", ".join(fails)))
        parts.append("</div>")
    parts.append("</div></body></html>")
    return "\n".join(parts) + "\n"


def family_names():
    """{family number: name} from the trusted generator."""
    import generator as _gen

    return {n: _gen.FAMILIES[n]["name"] for n in sorted(_gen.FAMILIES)}


def main(argv=None):
    """CLI: [--out results/factory-gallery] [--runs <teacher run dir>]."""
    import patterns as _patterns

    parser = argparse.ArgumentParser(
        description="Render one SVG card per factory family.")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="output dir (index.html + svgs)")
    parser.add_argument("--runs", nargs="*", default=[],
                        help="teacher run dirs for the verdict column")
    args = parser.parse_args(argv)
    for path in args.runs:
        if _patterns.is_forbidden(path):
            parser.error("refusing --runs path under blind/, "
                         "experiments/option-a/ or experiments/first-test/: "
                         "%s" % path)
            return 2
    jobs = load_jobs()
    cards = pick_first_jobs(jobs, load_dev_ids())
    if len(cards) != 10:
        parser.error("expected 10 families, found %d" % len(cards))
        return 2
    verdicts = load_verdicts(args.runs) if args.runs else None
    os.makedirs(args.out, exist_ok=True)
    svg_dir = os.path.join(args.out, "svgs")
    os.makedirs(svg_dir, exist_ok=True)
    inlines = []
    for job in cards:
        svg_path = os.path.join(
            svg_dir, "F%d.svg" % job["family"])
        export_svg(build_shape(job["reference"]), svg_path)
        inlines.append(inline_svg(svg_path))
    with open(os.path.join(args.out, "index.html"), "w",
              encoding="utf-8") as f:
        f.write(render(cards, inlines, family_names(), verdicts))
    print("wrote %s (%d cards)" % (
        os.path.join(args.out, "index.html"), len(cards)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
