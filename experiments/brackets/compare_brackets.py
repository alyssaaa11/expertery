#!/usr/bin/env python3
"""Bracket workflow decision: trained FTX vs card arm AX (PLAN 2026-11-03).

Reads the two --bx-loop run dirs and applies experiments/brackets/PLAN.md
"Decision rules" exactly. Reuses experiments/final/compare.py (load_calls,
finals_for, per_job_rates, bootstrap_ci) instead of copying that code.

Usage: compare_brackets.py --ftx <dir> --ax <dir>
         --jobs experiments/brackets/jobs_brackets.jsonl
         [--ftx-dollars D --ax-dollars D] [--out <file-or-dir>]

Finals = records with bx_final True of arm FTX / AX for job ids in the
jobs file. Either arm with fewer than 60 finals prints {"STOP": ...} and
exits 3 (PLAN stop rule: fewer than 60 finals in an arm -> STOP, ask the
user).

Per arm: n, usable (PASS at 0.2%: the record's existing verdict field, as
compare.is_pass reads it), rate, medium/hard split, crashes (round records
with event "crash" summed over all finals), mean rounds per part, prompt /
completion / total tokens summed over ALL rounds of every final (the
final's prompt_tokens_total/completion_tokens_total when present, else the
final's bx_rounds entries, else the matching round records: exactly one
source per final, so every model call counts once), tokens per usable part
(total, prompt, completion), wall seconds per usable part (sum of each
final's elapsed seconds / usable), $ per usable part when --*-dollars is
given (Modal billing before/after per arm, typed in by hand).

Statistics: paired bootstrap over the jobs file's job ids, 10,000
resamples, seed 20261103:
(a) usable-rate difference FTX - AX in points: estimate + 95% CI via
    compare.bootstrap_ci;
(b) ratio FTX/AX of tokens per usable part: on each resample, sum tokens
    and usable counts over the resampled jobs per arm; ratio =
    (tokens_ftx / usable_ftx) / (tokens_ax / usable_ax); resamples where an
    arm has 0 usable are skipped (the count is reported); estimate on the
    full sample + 2.5/97.5 percentiles of the kept resamples.

Verdict: Q = (a) estimate >= -10 points; X = Q and ratio estimate < 1 and
ratio CI upper < 1; wording is the matching PLAN.md sentence.

Offline: reads only calls.jsonl files and the jobs file. No network, no
Modal, no model call.
"""

import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_DIR = os.path.join(os.path.dirname(HERE), "final")
if FINAL_DIR not in sys.path:
    sys.path.insert(0, FINAL_DIR)

import compare  # noqa: E402 (sibling experiment dir, reused not copied)

SEED = 20261103
BOOTSTRAP_N = 10000
REQUIRED_FINALS = 60


class StopComparison(Exception):
    """Fewer than 60 finals in an arm: main prints the payload, exit 3."""

    def __init__(self, payload):
        super().__init__(payload.get("STOP", "STOP"))
        self.payload = payload


def load_jobs(path):
    """Jobs file -> (job ids in file order, {id: level})."""
    ids = []
    levels = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if not rec.get("id"):
                raise ValueError("jobs file %r has a record without id"
                                 % (path,))
            ids.append(rec["id"])
            levels[rec["id"]] = rec.get("level")
    if not ids:
        raise ValueError("jobs file %r has no jobs" % (path,))
    return ids, levels


def finals_for_arm(records, arm, job_ids):
    """Final records of one arm for the jobs file's ids."""
    wanted = set(job_ids)
    return [r for r in compare.finals_for(records, arm)
            if r.get("job") in wanted]


def round_records_by_key(records, arm, job_ids):
    """{(job, rep): [round records]} for one arm (bx_final False)."""
    wanted = set(job_ids)
    out = {}
    for rec in records:
        if rec.get("arm") != arm or rec.get("bx_final") is not False:
            continue
        if rec.get("job") not in wanted:
            continue
        out.setdefault((rec.get("job"), compare.rep_of(rec)),
                       []).append(rec)
    return out


def _int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def final_token_totals(final, rounds_by_key):
    """(prompt, completion) tokens over ALL rounds of one final.

    Exactly one source per final, so every model call counts once: the
    final's prompt_tokens_total/completion_tokens_total when present,
    else the final's bx_rounds entries, else the matching round records.
    """
    if ("prompt_tokens_total" in final
            or "completion_tokens_total" in final):
        return (_int(final.get("prompt_tokens_total")),
                _int(final.get("completion_tokens_total")))
    rounds = final.get("bx_rounds") or []
    if any(isinstance(r, dict) and ("prompt_tokens" in r
                                   or "completion_tokens" in r)
           for r in rounds):
        return (sum(_int(r.get("prompt_tokens")) for r in rounds
                if isinstance(r, dict)),
                sum(_int(r.get("completion_tokens")) for r in rounds
                if isinstance(r, dict)))
    key = (final.get("job"), compare.rep_of(final))
    recs = rounds_by_key.get(key, [])
    return (sum(_int(r.get("prompt_tokens")) for r in recs),
            sum(_int(r.get("completion_tokens")) for r in recs))


def final_rounds(final, rounds_by_key):
    """Round entries of one final (bx_rounds, else round records)."""
    rounds = final.get("bx_rounds") or []
    if rounds:
        return rounds
    return rounds_by_key.get((final.get("job"),
                              compare.rep_of(final)), [])


def rounds_of_final(final):
    """model_calls of one final (falls back to its round count)."""
    try:
        return int(final.get("model_calls"))
    except (TypeError, ValueError):
        pass
    rounds = final.get("bx_rounds") or []
    if rounds:
        return len(rounds)
    return 0


def _seconds(final):
    try:
        return float(final.get("seconds", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def summarize_arm(finals, rounds_by_key, levels, dollars=None):
    """Per-arm stats dict (see module docstring)."""
    n = len(finals)
    usable = sum(1 for r in finals if compare.is_pass(r))
    toks = [final_token_totals(r, rounds_by_key) for r in finals]
    prompt = sum(p for p, _ in toks)
    completion = sum(c for _, c in toks)
    by_level = {}
    for level in sorted({levels.get(r.get("job"), r.get("level"))
                         for r in finals}):
        sub = [r for r in finals
               if levels.get(r.get("job"), r.get("level")) == level]
        sub_usable = sum(1 for r in sub if compare.is_pass(r))
        by_level[str(level)] = {
            "n": len(sub),
            "usable": sub_usable,
            "rate": (sub_usable / len(sub)) if sub else None,
        }
    crashes = sum(
        1 for r in finals for rnd in final_rounds(r, rounds_by_key)
        if isinstance(rnd, dict) and rnd.get("event") == "crash")
    calls = [rounds_of_final(r) for r in finals]
    wall = sum(_seconds(r) for r in finals)
    return {
        "n": n,
        "usable": usable,
        "rate": (usable / n) if n else None,
        "by_level": by_level,
        "crashes": crashes,
        "mean_rounds": (sum(calls) / len(calls)) if calls else None,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "tokens_per_usable": {
            "total": ((prompt + completion) / usable) if usable else None,
            "prompt": (prompt / usable) if usable else None,
            "completion": (completion / usable) if usable else None,
        },
        "wall_seconds": wall,
        "wall_seconds_per_usable": (wall / usable) if usable else None,
        "dollars_per_usable": ((dollars / usable)
                               if dollars is not None and usable
                               else None),
    }


def per_job_tokens_and_usable(finals, rounds_by_key, jobs):
    """{job: (tokens, usable)} over the jobs file's ids (0 when absent)."""
    toks = {job: 0 for job in jobs}
    usable = {job: 0 for job in jobs}
    for rec in finals:
        job = rec.get("job")
        if job not in toks:
            continue
        prompt, completion = final_token_totals(rec, rounds_by_key)
        toks[job] += prompt + completion
        if compare.is_pass(rec):
            usable[job] += 1
    return toks, usable


def ratio_bootstrap(ftx_toks, ftx_usable, ax_toks, ax_usable, jobs,
                    n=BOOTSTRAP_N, seed=SEED):
    """Bootstrap of FTX/AX tokens per usable part (see module docstring).

    Returns (estimate, lo, hi, skipped): the full-sample ratio, the
    2.5/97.5 percentiles of the kept resamples, and how many resamples
    were skipped for a 0-usable arm. Estimate/lo/hi are None when the
    full sample has a 0-usable arm (kept empty included).
    """
    def _ratio(jobs_sample):
        t_f = sum(ftx_toks[j] for j in jobs_sample)
        u_f = sum(ftx_usable[j] for j in jobs_sample)
        t_a = sum(ax_toks[j] for j in jobs_sample)
        u_a = sum(ax_usable[j] for j in jobs_sample)
        if not u_f or not u_a:
            return None
        return (t_f / u_f) / (t_a / u_a)

    est = _ratio(jobs)
    rng = random.Random(seed)
    ratios = []
    skipped = 0
    for _ in range(n):
        sample = [jobs[rng.randrange(len(jobs))] for _ in jobs]
        ratio = _ratio(sample)
        if ratio is None:
            skipped += 1
        else:
            ratios.append(ratio)
    if est is None or not ratios:
        return est, None, None, skipped
    ratios.sort()
    lo = ratios[int(0.025 * len(ratios))]
    hi = ratios[int(0.975 * len(ratios))]
    return est, lo, hi, skipped


def decide(ftx_finals, ax_finals, ftx_rounds, ax_rounds, jobs, levels,
           ftx_dollars=None, ax_dollars=None):
    """Full comparison over loaded finals. Returns the result dict."""
    ftx = summarize_arm(ftx_finals, ftx_rounds, levels,
                        dollars=ftx_dollars)
    ax = summarize_arm(ax_finals, ax_rounds, levels, dollars=ax_dollars)
    ftx_rates = compare.per_job_rates(ftx_finals)
    ax_rates = compare.per_job_rates(ax_finals)
    x_rates = {job: ftx_rates.get(job, 0.0) for job in jobs}
    y_rates = {job: ax_rates.get(job, 0.0) for job in jobs}
    est_a, lo_a, hi_a = compare.bootstrap_ci(x_rates, y_rates, jobs,
                                             n=BOOTSTRAP_N, seed=SEED)
    ftx_toks, ftx_usable = per_job_tokens_and_usable(
        ftx_finals, ftx_rounds, jobs)
    ax_toks, ax_usable = per_job_tokens_and_usable(
        ax_finals, ax_rounds, jobs)
    est_r, lo_r, hi_r, skipped = ratio_bootstrap(
        ftx_toks, ftx_usable, ax_toks, ax_usable, jobs)
    q_hold = est_a >= -10.0
    x_hold = bool(q_hold and est_r is not None and est_r < 1
                  and hi_r is not None and hi_r < 1)
    if not q_hold:
        wording = ("reported as a loss for training on this workflow, "
                   "unchanged")
    elif x_hold:
        wording = ("same quality, %g× cheaper to run per usable part"
                   % (1.0 / est_r))
    else:
        wording = ("same quality, cheaper on average, not significant "
                   "on 20 jobs")
    return {
        "jobs": len(jobs),
        "seed": SEED,
        "resamples": BOOTSTRAP_N,
        "ftx": ftx,
        "ax": ax,
        "rate_diff_ftx_minus_ax_pts": {
            "est": est_a, "lo": lo_a, "hi": hi_a},
        "tokens_per_usable_ratio_ftx_ax": {
            "est": est_r, "lo": lo_r, "hi": hi_r,
            "skipped_resamples": skipped},
        "Q": q_hold,
        "X": x_hold,
        "wording": wording,
    }


def analyze(ftx_dir, ax_dir, jobs_path, ftx_dollars=None, ax_dollars=None):
    """Load dirs + jobs file and decide. Raises StopComparison (< 60)."""
    jobs, levels = load_jobs(jobs_path)
    ftx_records = compare.load_calls(ftx_dir)
    ax_records = compare.load_calls(ax_dir)
    ftx_finals = finals_for_arm(ftx_records, "FTX", jobs)
    ax_finals = finals_for_arm(ax_records, "AX", jobs)
    if len(ftx_finals) < REQUIRED_FINALS or len(ax_finals) < REQUIRED_FINALS:
        raise StopComparison({
            "STOP": ("fewer than 60 finals in an arm (FTX=%d, AX=%d); "
                     "STOP, ask the user"
                     % (len(ftx_finals), len(ax_finals))),
            "ftx_finals": len(ftx_finals),
            "ax_finals": len(ax_finals),
        })
    return decide(ftx_finals, ax_finals,
                  round_records_by_key(ftx_records, "FTX", jobs),
                  round_records_by_key(ax_records, "AX", jobs),
                  jobs, levels,
                  ftx_dollars=ftx_dollars, ax_dollars=ax_dollars)


def default_out_path(ftx_dir):
    """compare_brackets.json next to the FTX dir (in its parent)."""
    return os.path.join(os.path.dirname(os.path.abspath(ftx_dir)),
                        "compare_brackets.json")


def resolve_out_path(out, ftx_dir):
    """--out: a .json file path, or a directory holding the report."""
    if out is None:
        return default_out_path(ftx_dir)
    if out.endswith(".json"):
        return out
    return os.path.join(out, "compare_brackets.json")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bracket workflow "
                                     "decision: trained FTX vs card AX.")
    parser.add_argument("--ftx", required=True, help="FTX run dir")
    parser.add_argument("--ax", required=True, help="AX run dir")
    parser.add_argument("--jobs", required=True, help="bracket jobs file")
    parser.add_argument("--ftx-dollars", type=float, default=None,
                        help="Modal billing for the FTX arm session")
    parser.add_argument("--ax-dollars", type=float, default=None,
                        help="Modal billing for the AX arm session")
    parser.add_argument("--out", default=None,
                        help=".json file path or directory (default: "
                             "compare_brackets.json next to the FTX dir)")
    args = parser.parse_args(argv)
    try:
        result = analyze(args.ftx, args.ax, args.jobs,
                         ftx_dollars=args.ftx_dollars,
                         ax_dollars=args.ax_dollars)
    except StopComparison as stop:
        print(json.dumps(stop.payload))
        return 3
    except (ValueError, OSError) as e:
        parser.error(str(e))
    text = json.dumps(result, indent=1)
    print(text)
    out_path = resolve_out_path(args.out, args.ftx)
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
