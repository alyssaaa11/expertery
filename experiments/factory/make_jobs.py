#!/usr/bin/env python3
"""Write the factory jobs file + dev split, with the self-checks.

Writes experiments/factory/jobs.jsonl (200 jobs: id, family, text,
reference source), split.json (the 20 seed-chosen dev ids) and
jobs_dev.jsonl (the 20 dev jobs as a jobs file for the final-exam
runner's --jobs-file).

Self-check (SPEC section 1): every reference builds one valid solid
in-process (trusted generator code); two "wrong" variants per family
(a moved feature, a wrong size) FAIL at 1e-6; no job text has difflib
ratio >= 0.9 (exact numbers) to any first-test job text. Prints a
10-family table.
"""

import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import generator

JOBS_NAME = "jobs.jsonl"
SPLIT_NAME = "split.json"
DEV_JOBS_NAME = "jobs_dev.jsonl"
OVERLAP_LIMIT = 0.9


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
    (family, name, n_valid, n_jobs, wrong_results, max_ratio)."""
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
        rows.append((family, fam["name"], n_valid, len(sub), wrongs,
                     ratio))
    return rows


def print_table(rows):
    """Print the 10-family self-check table."""
    print("%-28s %8s %8s %8s %8s" % (
        "FAMILY", "VALID", "WRONG-1", "WRONG-2", "OVERLAP"))
    ok = True
    for family, name, n_valid, n_jobs, wrongs, ratio in rows:
        cells = []
        v_ok = n_valid == n_jobs
        cells.append("%d/%d" % (n_valid, n_jobs))
        for passed, _fails in wrongs:
            cells.append("FAIL" if not passed else "PASS-BAD")
        cells.append("%.3f" % ratio)
        if not v_ok or any(p for p, _f in wrongs) \
                or ratio >= OVERLAP_LIMIT:
            ok = False
        print("%-28s %8s %8s %8s %8s" % (
            "%d %s" % (family, name), cells[0], cells[1], cells[2],
            cells[3]))
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
