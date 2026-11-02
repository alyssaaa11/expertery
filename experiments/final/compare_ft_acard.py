#!/usr/bin/env python3
"""Exam reading FT vs A + card (Claude small fix 2026-11-02, disclosed; verifier X3).

Pre-registered before the exam run. Reuses compare.py (load_calls, finals_for, per_job_rates, bootstrap_ci,
tokens_per_correct): paired bootstrap of FT - (A + card) over the 30 exam jobs, each job's pass rate over its k = 3
first-try answers, 10,000 resamples, seed 20261029. Reported: pass (all / medium / hard), estimate and 95% CI,
completion tokens per correct, crashes. Rule: an arm with fewer than 90 answers (budget stop) -> exit 3 (STOP, ask).
Usage: compare_ft_acard.py --ft <exam-FT dir> --acard <exam-Acard dir>
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare  # noqa: E402


def arm(run_dir, name):
    recs = compare.load_calls(run_dir)
    finals = compare.finals_for(recs, name)
    return finals


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--ft", required=True)
    p.add_argument("--acard", required=True)
    a = p.parse_args(argv)
    ft, ac = arm(a.ft, "FT"), arm(a.acard, "A")
    out = {}
    for name, fin in (("FT", ft), ("A+card", ac)):
        if len(fin) < 90:
            print(json.dumps({"STOP": "%s has %d answers < 90" % (name, len(fin))}))
            return 3
        rates = compare.per_job_rates(fin)
        med = [r for r in fin if str(r.get("job", "")).startswith("M")]
        hard = [r for r in fin if str(r.get("job", "")).startswith("H")]
        out[name] = {
            "n": len(fin), "pass": sum(1 for r in fin if compare.is_pass(r)),
            "rate": round(100.0 * sum(rates.values()) / len(rates), 1),
            "medium": "%d/%d" % (sum(1 for r in med if compare.is_pass(r)), len(med)),
            "hard": "%d/%d" % (sum(1 for r in hard if compare.is_pass(r)), len(hard)),
            "tokens_per_correct": compare.tokens_per_correct(fin),
            "crashes": sum(1 for r in fin if r.get("run_error")),
        }
    rf, ra = compare.per_job_rates(ft), compare.per_job_rates(ac)
    jobs = sorted(set(rf) & set(ra))
    est, lo, hi = compare.bootstrap_ci(rf, ra, jobs)
    out["FT_minus_Acard_pts"] = [round(est, 1), round(lo, 1), round(hi, 1)]
    out["n_jobs"] = len(jobs)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
