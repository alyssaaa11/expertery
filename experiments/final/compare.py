#!/usr/bin/env python3
"""The pre-registered final decision (PLAN step 6, round-2 E2).

Inputs: FT's run dir, the baseline dirs main-B2BX and main-BR, AND the
step-6a BX-finisher dir. BX is merged over all answers (no (job, rep)
twice; a duplicate is refused); any (job, rep) of BX still missing, or a
6a dir that ended INCOMPLETE, is refused (exit 2). Bar (d) uses BX tokens
over all answers; BX wall-clock for "per correct part" is the baseline
arm wall-clock plus 6a's arm wall-clock without the cold start, with the
79-answer value reported next to it (disclosure).

Paired bootstrap over the jobs (10,000 resamples, seed 20261029) on
per-job pass rates. Bars (PLAN step 6):
(a) as good as B-max: FT-BX >= -5 points AND 95% CI lower >= -15;
(b) clearly beats the one-try arm: 95% CI of FT-B2 entirely above 0;
(c) about the same cost as B2: FT tokens per correct <= 1.5 x B2's;
(d) much cheaper than B-max: FT tokens per correct <= BX/3, or FT
wall-clock per correct <= BX/3 (wall-clock and $ printed first, then
tokens split into prompt and completion).
The full claim holds only if all four hold. Exit 0 CLAIM HOLDS, 1 the
comparison ran but a bar failed, 2 refused.

Offline: reads only calls.jsonl/summary.json files. No network, no Modal.
"""

import argparse
import json
import os
import random
import sys

BOOTSTRAP_N = 10000
BOOTSTRAP_SEED = 20261029
GPU_DOLLARS_PER_HOUR = 2.50  # same A100-80GB rate as every runner


# ------------------------------------------------------- loading


def load_calls(run_dir):
    """All records in a run dir's calls.jsonl."""
    with open(os.path.join(run_dir, "calls.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_summary(run_dir):
    """A run dir's summary.json ({} when absent)."""
    path = os.path.join(run_dir, "summary.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def rep_of(rec):
    """The rep index of a record (baselines call it sample)."""
    try:
        return int(rec.get("sample", rec.get("rep", 0)))
    except (TypeError, ValueError):
        return 0


def is_pass(rec):
    return rec.get("verdict", rec.get("outcome")) == "PASS"


def finals_for(records, arm):
    """Final records for one arm: BX needs bx_final True (per-round
    records have it False); other arms' records carry no bx_final key."""
    if arm == "BX":
        return [r for r in records
                if r.get("arm") == arm and r.get("bx_final") is True]
    return [r for r in records if r.get("arm") == arm
            and r.get("bx_final", True) is True]


def split_tokens(rec):
    """(prompt, completion) tokens for one final record."""
    if "prompt_tokens_total" in rec or "completion_tokens_total" in rec:
        try:
            prompt = int(rec.get("prompt_tokens_total", 0) or 0)
        except (TypeError, ValueError):
            prompt = 0
        try:
            completion = int(rec.get("completion_tokens_total", 0) or 0)
        except (TypeError, ValueError):
            completion = 0
        return prompt, completion
    usage = rec.get("usage") or {}
    try:
        prompt = int(usage.get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt = 0
    try:
        completion = int(usage.get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion = 0
    return prompt, completion


def per_job_rates(finals):
    """{job_id: pass fraction over that job's answers}."""
    by_job = {}
    for rec in finals:
        by_job.setdefault(rec.get("job"), []).append(rec)
    return {job: (sum(1 for r in recs if is_pass(r)) / len(recs))
            for job, recs in by_job.items()}


# ------------------------------------------------------- BX merge (E2)


def merge_bx(base_finals, extra_finals):
    """Merge baseline + 6a BX finals keyed (job, rep). A (job, rep) twice
    is refused (ValueError naming it)."""
    merged = {}
    for rec in list(base_finals) + list(extra_finals):
        key = (rec.get("job"), rep_of(rec))
        if key in merged:
            raise ValueError(
                "duplicate BX answer for job %s rep %d "
                "(baseline + 6a hold it twice); refusing" % key)
        merged[key] = rec
    return merged


def require_bx_complete(merged, jobs, reps):
    """Every (job, rep) present, else ValueError naming the jobs."""
    missing = sorted("%s rep %d" % (job, rep)
                     for job in jobs for rep in reps
                     if (job, rep) not in merged)
    if missing:
        raise ValueError(
            "BX still misses %d answers (%s); refusing"
            % (len(missing), ", ".join(missing)))
    return []


def check_extra_status(extra_dir):
    """The 6a dir must hold a COMPLETE summary (an INCOMPLETE session, or
    a missing summary, is refused). Returns its summary dict."""
    summary = load_summary(extra_dir)
    if summary.get("status") != "COMPLETE":
        raise ValueError(
            "6a dir %r did not end COMPLETE (status %r); refusing "
            "(compare.py is not run on an incomplete finisher)" % (
                extra_dir, summary.get("status")))
    return summary


def wall_of_summary(summary, arm=None):
    """Arm wall-clock seconds: runner_final's wall_seconds, else the
    baseline arm_timing entry."""
    if summary.get("wall_seconds") is not None:
        try:
            return float(summary["wall_seconds"])
        except (TypeError, ValueError):
            pass
    timing = (summary.get("arm_timing") or {}).get(arm or "")
    try:
        return float((timing or {}).get("seconds"))
    except (TypeError, ValueError):
        pass
    return None


# ------------------------------------------------------- paired bootstrap


def bootstrap_ci(x_rates, y_rates, jobs, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    """Paired bootstrap of mean(x - y) over jobs, in percentage points.

    Returns (est, lo, hi): the plain mean difference and the 95% CI
    (2.5/97.5 percentiles of n resamples with replacement).
    """
    est = sum(x_rates[j] - y_rates[j] for j in jobs) / len(jobs)
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        s = 0.0
        for _ in jobs:
            j = jobs[rng.randrange(len(jobs))]
            s += x_rates[j] - y_rates[j]
        diffs.append(s / len(jobs))
    diffs.sort()
    return (est * 100.0, diffs[int(0.025 * n)] * 100.0,
            diffs[int(0.975 * n)] * 100.0)


# ------------------------------------------------------- bars


def check_a(est_pts, lo_pts):
    """(a) as good as B-max: est >= -5 points AND CI lower >= -15."""
    return est_pts >= -5.0 and lo_pts >= -15.0


def check_b(lo_pts, _hi_pts):
    """(b) clearly beats the one-try arm: CI entirely above 0."""
    return lo_pts > 0.0


def check_c(ft_tpc, b2_tpc):
    """(c) about the same cost as B2: FT <= 1.5 x B2 tokens/correct."""
    return ft_tpc <= 1.5 * b2_tpc


def check_d(ft_tpc, bx_tpc, ft_wpc, bx_wpc):
    """(d) much cheaper than B-max: tokens <= BX/3 OR wall <= BX/3."""
    return ft_tpc <= bx_tpc / 3.0 or ft_wpc <= bx_wpc / 3.0


def tokens_per_correct(finals):
    """(total, prompt, completion, n_pass, per_correct) over finals."""
    splits = [split_tokens(r) for r in finals]
    total = sum(p + c for p, c in splits)
    prompt = sum(p for p, _ in splits)
    completion = sum(c for _, c in splits)
    n_pass = sum(1 for r in finals if is_pass(r))
    per = (total / n_pass) if n_pass else None
    return total, prompt, completion, n_pass, per


def dollars_per_correct(wall_s, n_pass):
    """$ per correct part = wall-clock h x $2.50 / PASS."""
    if wall_s is None or not n_pass:
        return None
    return wall_s / 3600.0 * GPU_DOLLARS_PER_HOUR / n_pass


# ------------------------------------------------------- decision


def decide(ft_dir, b2bx_dir, br_dir, bx_extra_dir):
    """Run the whole comparison. Returns (lines, result_dict).

    Raises ValueError (refused, exit 2) on a duplicate BX answer, a
    still-missing BX (job, rep), a 6a dir that did not end COMPLETE, or
    an arm with no answers for a job.
    """
    ft_summary = load_summary(ft_dir)
    b2bx_summary = load_summary(b2bx_dir)
    extra_summary = check_extra_status(bx_extra_dir)

    ft_finals = finals_for(load_calls(ft_dir), "FT")
    b2_finals = finals_for(load_calls(b2bx_dir), "B2")
    br_finals = finals_for(load_calls(br_dir), "BR")
    base_bx = finals_for(load_calls(b2bx_dir), "BX")
    extra_bx = finals_for(load_calls(bx_extra_dir), "BX")

    merged_bx = merge_bx(base_bx, extra_bx)
    jobs = sorted({r.get("job") for r in b2_finals})
    if not jobs:
        raise ValueError("no B2 answers in %r; refusing" % (b2bx_dir,))
    reps = sorted({rep_of(r) for r in b2_finals})
    require_bx_complete(merged_bx, jobs, reps)
    bx_finals = [merged_bx[(job, rep)] for job in jobs for rep in reps]

    ft_rates = per_job_rates(ft_finals)
    b2_rates = per_job_rates(b2_finals)
    br_rates = per_job_rates(br_finals)
    bx_rates = per_job_rates(bx_finals)
    for arm_name, rates in (("FT", ft_rates), ("B2", b2_rates),
                            ("BR", br_rates), ("BX", bx_rates)):
        missing = [j for j in jobs if j not in rates]
        if missing:
            raise ValueError(
                "arm %s has no answers for jobs %s; refusing"
                % (arm_name, ", ".join(missing)))

    est_a, lo_a, hi_a = bootstrap_ci(ft_rates, bx_rates, jobs)
    est_b, lo_b, hi_b = bootstrap_ci(ft_rates, b2_rates, jobs)

    _ft_tot, ft_in, ft_out, ft_pass, ft_tpc = tokens_per_correct(ft_finals)
    _b2_tot, _b2_in, _b2_out, b2_pass, b2_tpc = tokens_per_correct(b2_finals)
    _bx_tot, bx_in, bx_out, bx_pass, bx_tpc = tokens_per_correct(bx_finals)
    _base_tot, _bi, _bo, base_pass, base_tpc = tokens_per_correct(base_bx)

    ft_wall = wall_of_summary(ft_summary)
    b2_wall = wall_of_summary(b2bx_summary, "B2")
    base_bx_wall = wall_of_summary(b2bx_summary, "BX")
    extra_wall = wall_of_summary(extra_summary)
    try:
        extra_cold = float(extra_summary.get("cold_start_s", 0) or 0)
    except (TypeError, ValueError):
        extra_cold = 0.0
    # E2: BX wall-clock = baseline arm wall + 6a arm wall without the
    # cold start (the deploy + ready wait before the runner began).
    extra_effective = ((extra_wall - extra_cold)
                       if extra_wall is not None else None)
    bx_wall = ((base_bx_wall + extra_effective)
               if base_bx_wall is not None and extra_effective is not None
               else None)
    ft_wpc = (ft_wall / ft_pass) if ft_wall is not None and ft_pass else None
    b2_wpc = (b2_wall / b2_pass) if b2_wall is not None and b2_pass else None
    bx_wpc = (bx_wall / bx_pass) if bx_wall is not None and bx_pass else None
    base_wpc = ((base_bx_wall / base_pass)
                if base_bx_wall is not None and base_pass else None)

    if ft_tpc is None or b2_tpc is None or bx_tpc is None \
            or ft_wpc is None or bx_wpc is None:
        raise ValueError("a per-correct denominator is empty "
                         "(no PASS in an arm); refusing")
    bar_a = check_a(est_a, lo_a)
    bar_b = check_b(lo_b, hi_b)
    bar_c = check_c(ft_tpc, b2_tpc)
    bar_d = check_d(ft_tpc, bx_tpc, ft_wpc, bx_wpc)

    lines = []
    lines.append("Final comparison: FT (trained, k=%d) vs B2/BR/BX" % len(reps))
    lines.append("Jobs: %d; bootstrap: %d resamples, seed %d" % (
        len(jobs), BOOTSTRAP_N, BOOTSTRAP_SEED))
    lines.append(
        "(a) as good as B-max: FT-BX %+.1f points, 95%% CI [%+.1f, %+.1f] "
        "(need >= -5 and lower >= -15): %s" % (
            est_a, lo_a, hi_a, "PASS" if bar_a else "FAIL"))
    lines.append(
        "(b) beats the one-try arm: FT-B2 %+.1f points, 95%% CI "
        "[%+.1f, %+.1f] (need CI entirely above 0): %s" % (
            est_b, lo_b, hi_b, "PASS" if bar_b else "FAIL"))
    lines.append(
        "(c) about the same cost as B2: FT %.0f tokens/correct "
        "(prompt %d + completion %d) <= 1.5 x B2 %.0f (<= %.0f): %s" % (
            ft_tpc, ft_in // max(ft_pass, 1), ft_out // max(ft_pass, 1),
            b2_tpc, 1.5 * b2_tpc, "PASS" if bar_c else "FAIL"))
    lines.append(
        "(d) much cheaper than B-max (wall-clock and $ first): FT %.1fs "
        "and $%.4f per correct vs BX %.1fs and $%.4f (need <= BX/3: "
        "%.1fs, $%.4f): %s" % (
            ft_wpc, dollars_per_correct(ft_wall, ft_pass),
            bx_wpc, dollars_per_correct(bx_wall, bx_pass),
            bx_wpc / 3.0,
            dollars_per_correct(bx_wall, bx_pass) / 3.0
            if dollars_per_correct(bx_wall, bx_pass) is not None else 0.0,
            "PASS(tokens)" if (ft_tpc <= bx_tpc / 3.0) else
            ("PASS(wall)" if bar_d else "FAIL")))
    lines.append(
        "    tokens split: FT %.0f (prompt %d + completion %d) vs BX %.0f "
        "(prompt %d + completion %d) over all %d answers (need <= "
        "BX/3 = %.0f): %s" % (
            ft_tpc, ft_in // max(ft_pass, 1), ft_out // max(ft_pass, 1),
            bx_tpc, bx_in // max(bx_pass, 1),
            bx_out // max(bx_pass, 1), len(bx_finals), bx_tpc / 3.0,
            "PASS" if ft_tpc <= bx_tpc / 3.0 else "FAIL"))
    lines.append(
        "    disclosure: BX baseline-only (79 answers) was %.0f "
        "tokens/correct, %.1fs wall per correct; the bar above uses all "
        "%d answers." % (base_tpc, base_wpc or 0.0, len(bx_finals)))
    lines.append("")
    lines.append("Pass rates (all / medium / hard):")
    for arm_name, finals in (("FT", ft_finals), ("B2", b2_finals),
                             ("BX", bx_finals), ("BR", br_finals)):
        rates = per_job_rates(finals)
        all_rate = sum(rates.values()) / len(rates)
        parts = ["all %.1f%% (%d answers)" % (
            100.0 * all_rate, len(finals))]
        for level in ("medium", "hard"):
            sub = [r for r in finals if r.get("level") == level]
            if sub:
                sub_rate = (sum(1 for r in sub if is_pass(r)) / len(sub))
                parts.append("%s %.1f%% (%d)" % (level, 100.0 * sub_rate,
                                                 len(sub)))
        lines.append("  %s: %s" % (arm_name, ", ".join(parts)))
    lines.append("")
    holds = bar_a and bar_b and bar_c and bar_d
    lines.append("CLAIM HOLDS" if holds else "CLAIM DOES NOT HOLD")
    result = {
        "jobs": len(jobs),
        "reps": len(reps),
        "bar_a": {"est_pts": est_a, "lo_pts": lo_a, "hi_pts": hi_a,
                  "pass": bar_a},
        "bar_b": {"est_pts": est_b, "lo_pts": lo_b, "hi_pts": hi_b,
                  "pass": bar_b},
        "bar_c": {"ft_tpc": ft_tpc, "b2_tpc": b2_tpc, "pass": bar_c},
        "bar_d": {"ft_tpc": ft_tpc, "bx_tpc": bx_tpc, "ft_wpc": ft_wpc,
                  "bx_wpc": bx_wpc,
                  "bx_wall_s": bx_wall,
                  "bx_baseline_wall_s": base_bx_wall,
                  "bx_extra_effective_s": extra_effective,
                  "bx_79_tpc": base_tpc, "bx_79_wpc": base_wpc,
                  "pass": bar_d},
        "claim_holds": holds,
    }
    return lines, result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pre-registered final "
                                     "decision (PLAN step 6).")
    parser.add_argument("--ft", required=True, help="FT run dir")
    parser.add_argument("--b2bx", required=True, help="baseline main-B2BX")
    parser.add_argument("--br", required=True, help="baseline main-BR")
    parser.add_argument("--bx-extra", required=True,
                        help="step-6a BX-finisher dir")
    parser.add_argument("--out", default=None,
                        help="write comparison.json + report here")
    args = parser.parse_args(argv)
    try:
        lines, result = decide(args.ft, args.b2bx, args.br, args.bx_extra)
    except (ValueError, OSError) as e:
        parser.error(str(e))
    for line in lines:
        print(line)
    if args.out is not None:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "comparison.json"), "w",
                  encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        with open(os.path.join(args.out, "comparison.md"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return 0 if result["claim_holds"] else 1


if __name__ == "__main__":
    sys.exit(main())
