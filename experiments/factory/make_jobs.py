#!/usr/bin/env python3
"""Write the factory jobs file + dev split, with the self-checks.

Writes experiments/factory/jobs.jsonl (200 jobs: id, family, text,
reference source), split.json (the 20 seed-chosen dev ids) and
jobs_dev.jsonl (the 20 dev jobs as a jobs file for the final-exam
runner's --jobs-file).

Self-check (SPEC section 1): every reference builds one valid solid
in-process (trusted generator code); two "wrong" variants per family
(a moved feature, a wrong size) FAIL at 1e-6; no job text has difflib
ratio >= 0.9 (exact numbers) to any first-test job text; TEXT=REF: for
every job, the numbers in the text are re-parsed and each number the
reference program uses (its literal numbers, after rounding) must
appear in the text (a family passes only at 20/20). Prints a
10-family table.
"""

import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import generator

JOBS_NAME = "jobs.jsonl"
SPLIT_NAME = "split.json"
DEV_JOBS_NAME = "jobs_dev.jsonl"
OVERLAP_LIMIT = 0.9

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
# Whole-number construction constants (overshoot +-1, the origin, small
# counts) carry no design value and are exempt from the TEXT=REF check.
SMALL_INT = 8


def body_of(reference):
    """The reference program without the shared preamble helpers."""
    if reference.startswith(generator.PREAMBLE):
        return reference[len(generator.PREAMBLE):]
    return reference


def text_ref_ok(text, reference):
    """True when every design number the reference program uses appears
    in the job text (TEXT=REF).

    Each numeric literal in the reference body (after rounding) must
    match a number parsed from the text within 1e-9, except whole-number
    construction constants with abs(v) <= 8. A text that prints 21.2
    while its reference uses 21.3 fails. (--check-refs grades a
    reference against itself and cannot see this.)
    Returns (ok, missing_literal_or_None)."""
    texts = [float(m) for m in NUM_RE.findall(text or "")]
    for m in NUM_RE.findall(body_of(reference or "")):
        v = float(m)
        if v == int(v) and abs(int(v)) <= SMALL_INT:
            continue
        if not any(abs(v - t) <= 1e-9 for t in texts):
            return False, m
    return True, None


def exam_texts():
    """First-test job texts (for the overlap self-check)."""
    import importlib.util as _ilu

    path = os.path.join(os.path.dirname(HERE), "first-test", "jobs.py")
    spec = _ilu.spec_from_file_location("factory_exam_jobs", path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [j["text"] for j in mod.JOBS]


def max_overlap(text, texts):
    """Largest difflib ratio of a job text to any exam text."""
    return max(difflib.SequenceMatcher(None, text, e).ratio()
               for e in texts)


def self_check(jobs, texts):
    """Full self-check. Returns per-family rows:
    (family, name, n_valid, n_jobs, wrong_results, max_ratio, n_text_ref).
    n_text_ref is the TEXT=REF count: jobs whose every reference number
    (after rounding) appears in the text."""
    rows = []
    for family in range(1, generator.N_FAMILIES + 1):
        fam = generator.FAMILIES[family]
        sub = [j for j in jobs if j["family"] == family]
        n_valid = 0
        for job in sub:
            shape = generator.build_source(job["reference"])
            n_solids, valid = generator.shape_info(shape)
            if n_solids == 1 and valid:
                n_valid += 1
            else:
                print("INVALID REF %s: solids=%s valid=%s"
                      % (job["id"], n_solids, valid))
        ref = generator.build_source(sub[0]["reference"])
        wrongs = []
        for override in fam["wrong"](generator.first_params(family)):
            wsrc = fam["src"](override)
            passed, fails = generator.score_at_tight(wsrc, ref)
            wrongs.append((passed, fails))
        ratio = max(max_overlap(j["text"], texts) for j in sub)
        n_text_ref = 0
        for job in sub:
            ok, missing = text_ref_ok(job["text"], job["reference"])
            if ok:
                n_text_ref += 1
            else:
                print("TEXT!=REF %s: reference uses %s, not in the text"
                      % (job["id"], missing))
        rows.append((family, fam["name"], n_valid, len(sub), wrongs,
                     ratio, n_text_ref))
    return rows


def print_table(rows):
    """Print the 10-family self-check table."""
    print("%-28s %8s %8s %8s %8s %8s" % (
        "FAMILY", "VALID", "WRONG-1", "WRONG-2", "OVERLAP", "TEXT=REF"))
    ok = True
    for family, name, n_valid, n_jobs, wrongs, ratio, n_text_ref in rows:
        cells = []
        v_ok = n_valid == n_jobs
        cells.append("%d/%d" % (n_valid, n_jobs))
        for passed, _fails in wrongs:
            cells.append("FAIL" if not passed else "PASS-BAD")
        cells.append("%.3f" % ratio)
        cells.append("%d/%d" % (n_text_ref, n_jobs))
        if not v_ok or any(p for p, _f in wrongs) \
                or ratio >= OVERLAP_LIMIT or n_text_ref != n_jobs:
            ok = False
        print("%-28s %8s %8s %8s %8s %8s" % (
            "%d %s" % (family, name), cells[0], cells[1], cells[2],
            cells[3], cells[4]))
    print("SELF-CHECK %s" % ("OK" if ok else "FAIL"))
    return ok


def main(argv=None):
    import argparse as _ap

    parser = _ap.ArgumentParser(description="Write factory jobs + split.")
    parser.add_argument("--out-dir", default=HERE)
    args = parser.parse_args(argv)
    jobs = generator.generate_all()
    dev_ids = generator.choose_dev_ids(jobs)
    dev_set = set(dev_ids)
    with open(os.path.join(args.out_dir, JOBS_NAME), "w",
              encoding="utf-8") as f:
        for job in jobs:
            f.write(json.dumps(job) + "\n")
    with open(os.path.join(args.out_dir, SPLIT_NAME), "w",
              encoding="utf-8") as f:
        json.dump({"seed": generator.SEED, "dev": dev_ids}, f, indent=1)
    with open(os.path.join(args.out_dir, DEV_JOBS_NAME), "w",
              encoding="utf-8") as f:
        for job in jobs:
            if job["id"] in dev_set:
                f.write(json.dumps(job) + "\n")
    print("wrote %d jobs, %d dev ids" % (len(jobs), len(dev_ids)))
    rows = self_check(jobs, exam_texts())
    ok = print_table(rows)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
