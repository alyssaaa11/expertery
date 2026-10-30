#!/usr/bin/env python3
"""Learning loop: aggregate teacher runs into failure patterns.

SPEC section 4 (factory learning loop). Reads every calls.jsonl under
--runs (a run dir, or a dir of run dirs) and writes patterns.md: pass
rate per run and per family, the top checker failures, and the top
run-error shapes. Human notes on the patterns live in teacher_notes.md
(next to this file); this script only counts.

Each calls.jsonl record carries factory_version (see teacher.py), so
patterns from different generator versions stay separable.
"""

import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS_NAME = "patterns.md"


def find_calls_files(runs_dir):
    """Every calls.jsonl under a run dir or a dir of run dirs."""
    out = []
    top = os.path.join(runs_dir, "calls.jsonl")
    if os.path.isfile(top):
        return [top]
    for name in sorted(os.listdir(runs_dir)):
        path = os.path.join(runs_dir, name, "calls.jsonl")
        if os.path.isfile(path):
            out.append(path)
    return out


def load_records(paths):
    """[(run_name, record)] for every calls.jsonl record."""
    out = []
    for path in paths:
        run = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append((run, json.loads(line)))
    return out


def summarize(records):
    """Counts per run, per family (+version), failures, error shapes."""
    by_run = Counter()
    run_pass = Counter()
    by_family = Counter()
    family_pass = Counter()
    versions = Counter()
    fails = Counter()
    errors = Counter()
    for run, rec in records:
        by_run[run] += 1
        versions[str(rec.get("factory_version"))] += 1
        fam = str(rec.get("family"))
        by_family[fam] += 1
        if rec.get("verdict") == "PASS":
            run_pass[run] += 1
            family_pass[fam] += 1
        else:
            for fail in rec.get("fails") or []:
                fails[str(fail)[:80]] += 1
            err = str(rec.get("run_error") or "")
            errors[err[:80] or "(no error text)"] += 1
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
        "fails": fails.most_common(10),
        "errors": errors.most_common(10),
    }


def render(summary):
    """patterns.md text."""
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
    lines += ["", "## Top checker failures (FAIL only)", ""]
    if summary["fails"]:
        for fail, n in summary["fails"]:
            lines.append("- %dx %s" % (n, fail))
    else:
        lines.append("- none")
    lines += ["", "## Top run-error shapes (FAIL/INVALID only)", ""]
    if summary["errors"]:
        for err, n in summary["errors"]:
            lines.append("- %dx %s" % (n, err))
    else:
        lines.append("- none")
    lines += ["", "## Notes",
              "Human notes on these patterns live in teacher_notes.md.",
              ""]
    return "\n".join(lines)


def main(argv=None):
    """CLI: --runs <dir> --out <patterns.md file or dir>."""
    parser = argparse.ArgumentParser(
        description="Aggregate teacher runs into patterns.md.")
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    records = load_records(find_calls_files(args.runs))
    text = render(summarize(records))
    out = args.out
    if os.path.isdir(out) or not out.endswith(".md"):
        os.makedirs(out, exist_ok=True)
        out = os.path.join(out, PATTERNS_NAME)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s (%d records)" % (out, len(records)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
