#!/usr/bin/env python3
"""Position-only analysis for the B2 hint experiment (PLAN.md scoring).

Reads a runner calls.jsonl, rebuilds every FAIL answer with
runner.run_code, shifts it so its bounding-box min corner matches the
reference's, and classifies it as position-only
(checks.mismatch <= 0.002) or wrong shape.

Prints per arm: PASS/FAIL/INVALID, pass rate (whole points),
position-only count, wrong-shape count, crash count, plus a paired
table vs another arm (jobs where only one passed).

CLI: analyze.py <calls.jsonl> [--pair B2,BR]
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIRST_TEST = os.path.join(os.path.dirname(HERE), "first-test")
if FIRST_TEST not in sys.path:
    sys.path.insert(0, FIRST_TEST)

import cadquery as cq  # noqa: E402

import checks  # noqa: E402
import runner  # noqa: E402
from jobs import JOBS  # noqa: E402

JOBS_BY_ID = {j["id"]: j for j in JOBS}


def parse_pair(value, arms_present):
    """Split a --pair value (e.g. "B2,BR" or "B C") into two arm names."""
    if value is None:
        if "B2" in arms_present and "BR" in arms_present:
            return ("B2", "BR")
        arms = sorted(arms_present)
        if len(arms) >= 2:
            return (arms[0], arms[1])
        return None
    parts = []
    for chunk in str(value).replace(",", " ").split():
        parts.append(chunk.strip())
    parts = [p for p in parts if p]
    if len(parts) != 2:
        raise ValueError(
            f"--pair expects two arms (e.g. B2,BR), got {value!r}"
        )
    return (parts[0], parts[1])


def classify_fail(rec):
    """Rebuild one FAIL answer and classify it.

    Returns "position-only", "wrong-shape", or "crash" (rebuild failed).
    """
    job = JOBS_BY_ID.get(rec.get("job"))
    if job is None:
        return "crash"
    code = rec.get("code") or ""
    answer, _err = runner.run_code(code)
    if answer is None:
        return "crash"
    try:
        reference = job["build"]()
        ans = checks.to_shape(answer)
        ref = checks.to_shape(reference)
        abb = ans.BoundingBox()
        rbb = ref.BoundingBox()
        moved = ans.translate(
            cq.Vector(
                rbb.xmin - abb.xmin,
                rbb.ymin - abb.ymin,
                rbb.zmin - abb.zmin,
            )
        )
        m = checks.mismatch(moved, ref)
    except Exception:  # noqa: BLE001 -- unscorable rebuild is a wrong shape
        return "wrong-shape"
    if m is None:
        return "wrong-shape"
    return "position-only" if m <= checks.TOL_DIFF else "wrong-shape"


def whole_points(pass_rate):
    if pass_rate is None:
        return "n/a"
    return f"{round(pass_rate * 100)}%"


def analyze(records):
    arms = []
    for rec in records:
        if rec.get("arm") not in arms:
            arms.append(rec.get("arm"))
    arms = sorted(arms)
    per_arm = {}
    for arm in arms:
        sub = [r for r in records if r.get("arm") == arm]
        n_pass = sum(1 for r in sub if r.get("outcome") == "PASS")
        n_fail = sum(1 for r in sub if r.get("outcome") == "FAIL")
        n_inv = sum(1 for r in sub if r.get("outcome") == "INVALID")
        scored = n_pass + n_fail
        per_arm[arm] = {
            "PASS": n_pass,
            "FAIL": n_fail,
            "INVALID": n_inv,
            "pass_rate": (n_pass / scored) if scored else None,
            "position-only": 0,
            "wrong-shape": 0,
            "crash": 0,
        }
    for rec in records:
        if rec.get("outcome") != "FAIL":
            continue
        per_arm[rec["arm"]][classify_fail(rec)] += 1
    return arms, per_arm


def paired_table(records, arm_x, arm_y):
    """Jobs where only one of the two arms passed."""
    by_job_arm = {}
    for rec in records:
        by_job_arm.setdefault(rec.get("job"), {})[rec.get("arm")] = rec.get(
            "outcome"
        )
    x_only = sorted(
        job
        for job, outcomes in by_job_arm.items()
        if outcomes.get(arm_x) == "PASS" and outcomes.get(arm_y) != "PASS"
    )
    y_only = sorted(
        job
        for job, outcomes in by_job_arm.items()
        if outcomes.get(arm_y) == "PASS" and outcomes.get(arm_x) != "PASS"
    )
    return x_only, y_only


def main(argv=None):
    parser = argparse.ArgumentParser(description="B2 position-only analysis.")
    parser.add_argument("calls", help="calls.jsonl from a runner run")
    parser.add_argument("--pair", default=None,
                        help="two arms to compare, e.g. B2,BR")
    args = parser.parse_args(argv)

    with open(args.calls, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    arms, per_arm = analyze(records)
    for arm in arms:
        s = per_arm[arm]
        print(
            f"Arm {arm}: PASS={s['PASS']} FAIL={s['FAIL']} "
            f"INVALID={s['INVALID']} pass_rate={whole_points(s['pass_rate'])} "
            f"position-only={s['position-only']} "
            f"wrong-shape={s['wrong-shape']} crash={s['crash']}"
        )

    try:
        pair = parse_pair(args.pair, set(arms))
    except ValueError as e:
        parser.error(str(e))
    if pair is not None and pair[0] in per_arm and pair[1] in per_arm:
        x_only, y_only = paired_table(records, pair[0], pair[1])
        print(f"Paired {pair[0]} vs {pair[1]} (jobs where only one passed):")
        print(
            f"  {pair[0]} only ({len(x_only)}): "
            + (", ".join(x_only) if x_only else "-")
        )
        print(
            f"  {pair[1]} only ({len(y_only)}): "
            + (", ".join(y_only) if y_only else "-")
        )
    else:
        print("Paired table skipped (need two arms present in the file).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
