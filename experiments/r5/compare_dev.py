#!/usr/bin/env python3
"""R5 dev reading (PLAN "Plan change: option B"), pre-registered before the dev runs.

Claude-written analysis script (disclosed in README; reads results only, runs no answer code).
Reuses experiments/final/compare.py: load_calls, per_job_rates (INVALID counts as not PASS),
split_tokens and bootstrap_ci (paired, 10,000 resamples, seed fixed there).

CLI: compare_dev.py --ft <dir> --a <dir> --acard <dir> [--ftcard <dir>]
Each dir holds calls.jsonl for 100 R5D jobs, k = 1.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "final"))
import compare  # noqa: E402


def arm_stats(run_dir):
    recs = compare.load_calls(run_dir)
    rates = compare.per_job_rates(recs)
    n_pass = sum(1 for r in recs if compare.is_pass(r))
    comp = sum(compare.split_tokens(r)[1] for r in recs)
    think = sum(1 for r in recs if (r.get("reasoning_len") or 0) >= 200)
    return {"n": len(recs), "pass": n_pass, "rate": 100.0 * n_pass / max(1, len(recs)),
            "completion_per_correct": comp / n_pass if n_pass else None,
            "thinking_share": think / max(1, len(recs)),
            "crashes": sum(1 for r in recs if r.get("run_error")),
            "invalid": sum(1 for r in recs if r.get("verdict") == "INVALID"),
            "_rates": rates}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ft", required=True)
    ap.add_argument("--a", required=True)
    ap.add_argument("--acard", required=True)
    ap.add_argument("--ftcard")
    args = ap.parse_args(argv)
    arms = {"FT": arm_stats(args.ft), "A": arm_stats(args.a), "A+card": arm_stats(args.acard)}
    if args.ftcard:
        arms["FT+card"] = arm_stats(args.ftcard)
    jobs = sorted(set.intersection(*[set(s["_rates"]) for s in arms.values()]))
    out = {"n_common_jobs": len(jobs), "arms": {k: {kk: vv for kk, vv in v.items() if kk != "_rates"}
                                              for k, v in arms.items()}}
    ft = arms["FT"]["_rates"]
    est1, lo1, hi1 = compare.bootstrap_ci(ft, arms["A+card"]["_rates"], jobs)
    est2, lo2, hi2 = compare.bootstrap_ci(ft, arms["A"]["_rates"], jobs)
    out["FT_minus_Acard"] = [round(est1, 1), round(lo1, 1), round(hi1, 1)]
    out["FT_minus_A"] = [round(est2, 1), round(lo2, 1), round(hi2, 1)]
    cpc_ft = arms["FT"]["completion_per_correct"]
    cpc_ac = arms["A+card"]["completion_per_correct"]
    out["reading"] = {
        "as_good_as_card (est >= -3 and lo >= -10)": est1 >= -3 and lo1 >= -10,
        "beats_plain (est >= +10)": est2 >= 10,
        "cheaper (completion/correct FT <= A+card)": bool(cpc_ft and cpc_ac and cpc_ft <= cpc_ac),
        "thinking_ok (FT share >= 0.90)": arms["FT"]["thinking_share"] >= 0.90,
    }
    if args.ftcard:
        out["FTcard_minus_Acard"] = [round(x, 1) for x in compare.bootstrap_ci(
            arms["FT+card"]["_rates"], arms["A+card"]["_rates"], jobs)]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
