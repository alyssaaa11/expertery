#!/usr/bin/env python3
"""Second-look reading: FTX (trained model inside the BX fix loop) vs BX (base Glimmer + manual + fixes).

Claude small fix 2026-11-02, disclosed; written BEFORE the FTX run. Reuses compare.py. 30 exam jobs (M*/H*), k = 3.
BX = baseline main-B2BX finals merged with the 6a finisher (dry D* jobs excluded). Paired bootstrap FTX - BX over
jobs (10,000 resamples, seed 20261029). Reading (same as bar (a)): "about as good as BX" iff est >= -5 points AND
95% CI lower bound >= -15. Also reported: FTX - FT(first look), tokens / wall seconds per correct part, crashes.
Rule: FTX with fewer than 90 finals -> exit 3 (STOP, ask the user).
Usage: compare_ftx.py --ftx <dir> --ft <exam-FT dir> --b2bx <main-B2BX dir> --bx-extra <exam-BX6a dir>
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare  # noqa: E402


def exam_only(recs):
    return [r for r in recs if str(r.get("job", ""))[:1] in ("M", "H")]


def main(argv=None):
    p = argparse.ArgumentParser()
    for a in ("--ftx", "--ft", "--b2bx", "--bx-extra"):
        p.add_argument(a, required=True)
    a = p.parse_args(argv)
    ftx = exam_only(compare.finals_for(compare.load_calls(a.ftx), "FTX"))
    if len(ftx) < 90:
        print(json.dumps({"STOP": "FTX has %d finals < 90" % len(ftx)}))
        return 3
    ft = exam_only(compare.finals_for(compare.load_calls(a.ft), "FT"))
    bx = compare.merge_bx(exam_only(compare.finals_for(compare.load_calls(a.b2bx), "BX")),
                          exam_only(compare.finals_for(compare.load_calls(a.bx_extra), "BX")))
    bx = list(bx.values())
    jobs = sorted({r["job"] for r in ftx})
    compare.require_bx_complete({(r["job"], compare.rep_of(r)): r for r in bx}, jobs, range(3))
    rx, rb, rf = (compare.per_job_rates(x) for x in (ftx, bx, ft))
    est, lo, hi = compare.bootstrap_ci(rx, rb, jobs)
    e2, l2, h2 = compare.bootstrap_ci(rx, rf, jobs)
    out = {"n_jobs": len(jobs)}
    for name, fin in (("FTX", ftx), ("BX", bx), ("FT", ft)):
        out[name] = {"n": len(fin), "pass": sum(1 for r in fin if compare.is_pass(r)),
                     "rate": round(100.0 * sum(1 for r in fin if compare.is_pass(r)) / len(fin), 1),
                     "hard": "%d/%d" % (sum(1 for r in fin if r["job"][0] == "H" and compare.is_pass(r)),
                                        sum(1 for r in fin if r["job"][0] == "H")),
                     "tokens_per_correct": round(compare.tokens_per_correct(fin)[4] or 0),
                     "seconds_per_answer_mean": round(sum(float(r.get("seconds") or r.get("latency") or 0)
                                                          for r in fin) / len(fin), 1)}
    out["FTX_minus_BX"] = [round(est, 1), round(lo, 1), round(hi, 1)]
    out["FTX_minus_FT"] = [round(e2, 1), round(l2, 1), round(h2, 1)]
    out["about_as_good_as_BX"] = bool(est >= -5 and lo >= -15)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
