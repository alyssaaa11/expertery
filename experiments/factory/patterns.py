#!/usr/bin/env python3
"""Learning loop: aggregate teacher runs into failure patterns.

SPEC section 4 (factory learning loop). Goal: find failures that repeat,
so the cause is fixed in the factory before the next run instead of
paying for the same failure again. The loop suggests; the user approves
every fix; Muse Code applies it.

CLI: patterns.py --runs <teacher run dir> [<dir> ...] --out <dir>
  [--min-count 3].

Reads only calls.jsonl from factory teacher runs. Refuses (exit 2) any
--runs path under blind/, experiments/option-a/ or
experiments/first-test/. Records whose id is not F<n>-<m> are refused
(skipped), and dev ids from split.json are skipped. No network, no model
calls, edits no file; writes patterns.json + patterns.md.

Every FAIL or error gets a signature (category, key). Categories:
  harness: box error, timeout, no BREP, grader exception
    (run_error starting with "harness:", mentioning no BREP, or a
    timeout).
  no_code: the answer had no code.
  run_error: exception type + message with numbers replaced by N.
  wrong_shape: the sorted failed checks.
A signature seen >= min-count times is a pattern. Kind:
  our_bug if harness;
  our_wording if wrong_shape and >= 80% of its hits are in one family;
  teacher_habit if run_error/no_code, or wrong_shape spread over >= 2
  families.

Each calls.jsonl record carries factory_version (see teacher.py), so
patterns from different generator versions stay separable.

Locked (never suggested or changed): checks.py tolerances, the cloud
box and grader, the dev split, the exam files, the overlap check.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT_PATH = os.path.join(HERE, "split.json")
PATTERNS_MD = "patterns.md"
PATTERNS_JSON = "patterns.json"

ID_RE = re.compile(r"F\d+-\d+$")
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

FORBIDDEN = ("blind", "experiments/option-a", "experiments/first-test")


def is_forbidden(path):
    """True when a --runs path points under blind/, experiments/option-a/
    or experiments/first-test/."""
    norm = os.path.abspath(path).replace(os.sep, "/")
    parts = norm.split("/")
    if "blind" in parts:
        return True
    return ("experiments/option-a" in norm
            or "experiments/first-test" in norm)


def load_dev_ids(path=None):
    """The dev ids from split.json (skipped by the loop)."""
    try:
        with open(path or SPLIT_PATH, encoding="utf-8") as f:
            return set(json.load(f).get("dev", []))
    except OSError:
        return set()


def normalize_numbers(text):
    """Replace every number with N (run_error signatures)."""
    return NUM_RE.sub("N", text or "")


def is_valid_id(job_id):
    """Factory ids look like F<n>-<m>; anything else is refused."""
    return bool(ID_RE.match(str(job_id or "")))


def signature_of(rec):
    """The (category, key) of one FAIL/error record, or None for PASS.

    Priority: wrong_shape (a FAIL with failed checks) first, then
    no_code (the answer had no code), then harness (our side: box
    error, timeout, no BREP, grader exception, or a call that never
    returned an answer), then the generic run_error shape (the answer's
    code raised).
    """
    if rec.get("verdict") == "PASS":
        return None
    fails = [f for f in (rec.get("fails") or []) if f]
    if fails and rec.get("verdict") == "FAIL":
        return ("wrong_shape", " | ".join(sorted(set(str(f)
                                                     for f in fails)))[:200])
    err = str(rec.get("run_error") or "")
    code = rec.get("code")
    if rec.get("verdict") == "INVALID" and (
            not (code or "").strip() or err in (
                "empty reply", "cut off by the token limit")
            or "empty reply" in err
            or "no code block" in err.lower()):
        return ("no_code", "no_code")
    low = err.lower()
    if (rec.get("verdict") == "INVALID"
            or err.startswith("harness:") or "wrote no brep" in low
            or "no brep" in low or "timeout" in low
            or "timed out" in low):
        return ("harness", normalize_numbers(err.strip())[:200]
                or "harness")
    if err.strip():
        return ("run_error", normalize_numbers(err.strip())[:200])
    return ("run_error", "(no error text)")


def kind_of(category, families):
    """our_bug / our_wording / teacher_habit per SPEC section 4."""
    if category == "harness":
        return "our_bug"
    if category in ("run_error", "no_code"):
        return "teacher_habit"
    # wrong_shape: one family (>= 80%) means our wording, spread means
    # the teacher keeps missing the same check across families.
    if families and max(families.values()) / sum(families.values()) >= 0.8:
        return "our_wording"
    return "teacher_habit"


def where_to_fix(kind, families):
    """Where the fix goes for a pattern kind."""
    if kind == "our_bug":
        return "factory/box code"
    if kind == "our_wording":
        top = max(families, key=families.get) if families else "?"
        return "generator.py family %s" % top
    return "teacher_notes.md"


def find_calls_files(runs_dirs):
    """Every calls.jsonl under each run dir (or dir of run dirs)."""
    out = []
    for runs_dir in runs_dirs:
        top = os.path.join(runs_dir, "calls.jsonl")
        if os.path.isfile(top):
            out.append(top)
            continue
        if not os.path.isdir(runs_dir):
            continue
        for name in sorted(os.listdir(runs_dir)):
            path = os.path.join(runs_dir, name, "calls.jsonl")
            if os.path.isfile(path):
                out.append(path)
    return out


def load_records(paths, dev_ids=None):
    """[(run_name, record)] for every calls.jsonl record, skipping dev
    ids and non-F<n>-<m> ids. Returns (records, n_skipped_dev,
    n_skipped_bad_id)."""
    dev = dev_ids if dev_ids is not None else load_dev_ids()
    out, n_dev, n_bad = [], 0, 0
    for path in paths:
        run = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if not is_valid_id(rec.get("id")):
                    n_bad += 1
                    continue
                if rec.get("id") in dev:
                    n_dev += 1
                    continue
                out.append((run, rec))
    return out, n_dev, n_bad


def summarize(records, min_count=3):
    """Pass rates per run/family plus the repeated failure patterns."""
    by_run = Counter()
    run_pass = Counter()
    by_family = Counter()
    family_pass = Counter()
    versions = Counter()
    hits = {}  # (category, key) -> [records in input order]
    for run, rec in records:
        by_run[run] += 1
        versions[str(rec.get("factory_version"))] += 1
        fam = str(rec.get("family"))
        by_family[fam] += 1
        if rec.get("verdict") == "PASS":
            run_pass[run] += 1
            family_pass[fam] += 1
            continue
        sig = signature_of(rec)
        if sig is None:
            continue
        hits.setdefault(sig, []).append(rec)
    patterns = []
    for (category, key), recs in hits.items():
        if len(recs) < min_count:
            continue
        fams = Counter(str(r.get("family")) for r in recs)
        kind = kind_of(category, fams)
        patterns.append({
            "kind": kind,
            "category": category,
            "key": key,
            "count": len(recs),
            "families": sorted(fams, key=lambda x: (
                int(x) if x.isdigit() else x)),
            "family_counts": {f: fams[f] for f in sorted(fams)},
            "example_ids": [r.get("id") for r in recs[:2]],
            "where": where_to_fix(kind, fams),
        })
    patterns.sort(key=lambda p: (-p["count"], p["kind"], p["key"]))
    return {
        "n_records": len(records),
        "runs": {r: {"n": by_run[r], "pass": run_pass[r],
                     "rate": round(run_pass[r] / by_run[r], 4)}
                 for r in sorted(by_run)},
        "families": {f: {"n": by_family[f], "pass": family_pass[f],
                         "rate": round(family_pass[f] / by_family[f], 4)}
                     for f in sorted(
                         by_family, key=lambda x: (int(x)
                                                   if x.isdigit() else x))},
        "versions": dict(versions),
        "patterns": patterns,
    }


def render(summary, min_count=3):
    """patterns.md text: pass-rate tables plus one row per pattern."""
    lines = ["# Teacher failure patterns", "",
             "Records: %d." % summary["n_records"],
             "Versions seen: %s."
             % (", ".join(sorted(summary["versions"])) or "none"), "",
             "## Pass rate per run", "",
             "| run | calls | pass | rate |",
             "|---|---|---|---|"]
    for run, s in summary["runs"].items():
        lines.append("| %s | %d | %d | %.3f |"
                     % (run, s["n"], s["pass"], s["rate"]))
    lines += ["", "## Pass rate per family", "",
              "| family | calls | pass | rate |",
              "|---|---|---|---|"]
    for fam, s in summary["families"].items():
        lines.append("| %s | %d | %d | %.3f |"
                     % (fam, s["n"], s["pass"], s["rate"]))
    lines += ["", "## Patterns (seen >= %d times)" % min_count, "",
              "| kind | signature | count | families | examples | "
              "where to fix |",
              "|---|---|---|---|---|---|"]
    if summary["patterns"]:
        for p in summary["patterns"]:
            lines.append("| %s | %s: %s | %d | %s | %s | %s |" % (
                p["kind"], p["category"], p["key"], p["count"],
                ", ".join(p["families"]), ", ".join(p["example_ids"]),
                p["where"]))
    else:
        lines.append("| - | no repeated pattern | - | - | - | - |")
    lines += ["", "## Notes",
              "Human notes on these patterns live in teacher_notes.md.",
              ""]
    return "\n".join(lines)


def main(argv=None):
    """CLI: --runs <dir> [...] --out <dir> [--min-count 3]."""
    parser = argparse.ArgumentParser(
        description="Aggregate teacher runs into failure patterns.")
    parser.add_argument("--runs", nargs="+", required=True,
                        help="teacher run dirs (a run dir or a dir of "
                             "run dirs)")
    parser.add_argument("--out", required=True,
                        help="output dir (patterns.json + patterns.md)")
    parser.add_argument("--min-count", type=int, default=3,
                        help="a signature seen >= this many times is a "
                             "pattern")
    args = parser.parse_args(argv)
    for path in args.runs:
        if is_forbidden(path):
            parser.error("refusing --runs path under blind/, "
                         "experiments/option-a/ or experiments/first-test/: "
                         "%s" % path)
            return 2
    records, n_dev, n_bad = load_records(find_calls_files(args.runs))
    summary = summarize(records, min_count=args.min_count)
    summary["min_count"] = args.min_count
    summary["n_skipped_dev"] = n_dev
    summary["n_skipped_bad_id"] = n_bad
    out = args.out
    if out.endswith(".md"):
        md_path = out
        json_path = out[:-3] + ".json"
    elif out.endswith(".json"):
        json_path = out
        md_path = out[:-5] + ".md"
    else:
        os.makedirs(out, exist_ok=True)
        md_path = os.path.join(out, PATTERNS_MD)
        json_path = os.path.join(out, PATTERNS_JSON)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render(summary, min_count=args.min_count))
    print("wrote %s and %s (%d records, %d patterns, skipped %d dev, "
          "%d bad id)" % (md_path, json_path, len(records),
                           len(summary["patterns"]), n_dev, n_bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
