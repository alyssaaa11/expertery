"""Offline tests for experiments/brackets/compare_brackets.py.

Synthetic calls.jsonl files in tmp dirs stand in for the real FTX/AX
sessions (no network, no Modal, no model call). Small worlds call
decide() directly; only the STOP/main/exit-path tests go through main().
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import compare_brackets


# ------------------------------------------------------- builders


def _rounds(n, prompt=100, completion=10, event="built"):
    return [{"prompt_tokens": prompt, "completion_tokens": completion,
             "event": event} for _ in range(n)]


def _final(job, arm, rep, verdict, prompt_total, completion_total,
           level="medium", seconds=10.0, n_rounds=1, with_totals=True,
           with_rounds=True):
    rec = {"job": job, "arm": arm, "bx_final": True, "rep": rep,
           "sample": rep, "level": level, "outcome": verdict,
           "verdict": verdict, "seconds": seconds,
           "model_calls": n_rounds}
    if with_totals:
        rec["prompt_tokens_total"] = prompt_total
        rec["completion_tokens_total"] = completion_total
    if with_rounds:
        per_p = prompt_total // n_rounds
        per_c = completion_total // n_rounds
        rec["bx_rounds"] = _rounds(n_rounds, per_p, per_c)
    return rec


def _round_rec(job, arm, rep, rnd, prompt=100, completion=10,
               event="built"):
    return {"job": job, "arm": arm, "bx_final": False, "round": rnd,
            "rep": rep, "sample": rep, "prompt_tokens": prompt,
            "completion_tokens": completion, "event": event}


def _write_calls(path, records):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "calls.jsonl"), "w",
              encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def _write_jobs(path, jobs):
    with open(path, "w", encoding="utf-8") as f:
        for job_id, level in jobs:
            f.write(json.dumps({"id": job_id, "level": level,
                                "text": "make %s" % job_id}) + "\n")


def _hand_world():
    """2 jobs x 2 reps; FTX 3/4 usable at 900 tokens each, AX 3/4 at 1800."""
    jobs = ["J1", "J2"]
    levels = {"J1": "medium", "J2": "hard"}
    ftx = [_final("J1", "FTX", 0, "PASS", 300, 150, "medium", 10.0),
           _final("J1", "FTX", 1, "FAIL", 300, 150, "medium", 10.0),
           _final("J2", "FTX", 0, "PASS", 600, 300, "hard", 20.0),
           _final("J2", "FTX", 1, "PASS", 600, 300, "hard", 20.0)]
    ax = [_final("J1", "AX", 0, "PASS", 900, 450, "medium", 30.0),
          _final("J1", "AX", 1, "PASS", 900, 450, "medium", 30.0),
          _final("J2", "AX", 0, "PASS", 900, 450, "hard", 30.0),
          _final("J2", "AX", 1, "FAIL", 900, 450, "hard", 30.0)]
    return jobs, levels, ftx, ax


# ------------------------------------------------------- hand-computed values


def test_hand_computed_rates_tokens_and_ratio():
    jobs, levels, ftx, ax = _hand_world()
    result = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    assert result["ftx"]["n"] == 4
    assert result["ftx"]["usable"] == 3
    assert result["ftx"]["rate"] == 0.75
    assert result["ax"]["usable"] == 3
    assert result["ax"]["rate"] == 0.75
    assert result["ftx"]["total_tokens"] == 2700
    assert result["ftx"]["tokens_per_usable"]["total"] == 900.0
    assert result["ftx"]["tokens_per_usable"]["prompt"] == 600.0
    assert result["ftx"]["tokens_per_usable"]["completion"] == 300.0
    assert result["ax"]["tokens_per_usable"]["total"] == 1800.0
    assert result["tokens_per_usable_ratio_ftx_ax"]["est"] == 0.5
    # Per-job rates: FTX J1 0.5 / J2 1.0, AX J1 1.0 / J2 0.5 -> diff 0.
    assert result["rate_diff_ftx_minus_ax_pts"]["est"] == 0.0
    assert result["Q"] is True
    assert result["X"] is True
    assert "2× cheaper to run per usable part" in result["wording"]
    # Wall: FTX 60s / 3 usable, AX 120s / 3 usable.
    assert result["ftx"]["wall_seconds_per_usable"] == 20.0
    assert result["ax"]["wall_seconds_per_usable"] == 40.0
    # Level split follows the jobs file.
    assert result["ftx"]["by_level"]["medium"]["rate"] == 0.5
    assert result["ftx"]["by_level"]["hard"]["rate"] == 1.0


def test_tokens_count_every_round_once():
    """A 3-round final counts 3 calls even when totals, bx_rounds AND
    separate round records are all present (no double counting)."""
    final = _final("J1", "FTX", 0, "PASS", 300, 30, "medium", 10.0,
                   n_rounds=3)
    rounds = {(u"J1", 0): [_round_rec("J1", "FTX", 0, i + 1)
                           for i in range(3)]}
    prompt, completion = compare_brackets.final_token_totals(
        final, rounds)
    assert (prompt, completion) == (300, 30)
    # Without totals the bx_rounds entries are summed instead.
    bare = _final("J1", "FTX", 0, "PASS", 300, 30, "medium", 10.0,
                  n_rounds=3, with_totals=False)
    assert compare_brackets.final_token_totals(bare, {}) == (300, 30)
    # Without either, the separate round records are summed.
    barer = _final("J1", "FTX", 0, "PASS", 300, 30, "medium", 10.0,
                   n_rounds=3, with_totals=False, with_rounds=False)
    assert compare_brackets.final_token_totals(barer, rounds) == (300, 30)


def test_crashes_and_mean_rounds():
    jobs = ["J1"]
    levels = {"J1": "medium"}
    crash_rounds = ([{"prompt_tokens": 50, "completion_tokens": 5,
                      "event": "crash"}] * 2
                    + [{"prompt_tokens": 100, "completion_tokens": 10,
                        "event": "built"}])
    rec = {"job": "J1", "arm": "FTX", "bx_final": True, "rep": 0,
           "sample": 0, "level": "medium", "outcome": "PASS",
           "verdict": "PASS", "seconds": 5.0, "model_calls": 3,
           "prompt_tokens_total": 200, "completion_tokens_total": 20,
           "bx_rounds": crash_rounds}
    out = compare_brackets.summarize_arm([rec], {}, levels)
    assert out["crashes"] == 2
    assert out["mean_rounds"] == 3.0


# ------------------------------------------------------- STOP / main paths


def test_below_60_finals_exits_3(tmp_path, capsys):
    ftx = str(tmp_path / "ftx")
    ax = str(tmp_path / "ax")
    _write_calls(ftx, [_final("J1", "FTX", 0, "PASS", 100, 10)])
    _write_calls(ax, [_final("J1", "AX", 0, "PASS", 100, 10)])
    jobs_path = str(tmp_path / "jobs.jsonl")
    _write_jobs(jobs_path, [("J1", "medium")])
    assert compare_brackets.main(
        ["--ftx", ftx, "--ax", ax, "--jobs", jobs_path]) == 3
    printed = capsys.readouterr().out
    assert "STOP" in json.loads(printed)["STOP"]


def test_main_writes_json_next_to_ftx_dir(tmp_path, capsys):
    jobs = [("J%d" % i, "medium" if i < 10 else "hard")
            for i in range(20)]
    ftx_recs, ax_recs = [], []
    for job_id, level in jobs:
        for rep in range(3):
            ftx_recs.append(_final(job_id, "FTX", rep, "PASS", 300, 150,
                                   level, 10.0))
            ax_recs.append(_final(job_id, "AX", rep, "PASS", 900, 450,
                                  level, 30.0))
    ftx = str(tmp_path / "runs" / "ftx")
    ax = str(tmp_path / "runs" / "ax")
    _write_calls(ftx, ftx_recs)
    _write_calls(ax, ax_recs)
    jobs_path = str(tmp_path / "jobs.jsonl")
    _write_jobs(jobs_path, jobs)
    assert compare_brackets.main(
        ["--ftx", ftx, "--ax", ax, "--jobs", jobs_path,
         "--ftx-dollars", "6.0", "--ax-dollars", "3.0"]) == 0
    out_path = os.path.join(str(tmp_path / "runs"),
                            "compare_brackets.json")
    assert os.path.isfile(out_path)
    saved = json.load(open(out_path, encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert saved == printed
    assert saved["ftx"]["n"] == 60 and saved["ax"]["n"] == 60
    assert saved["ftx"]["dollars_per_usable"] == 6.0 / 60
    assert saved["ax"]["dollars_per_usable"] == 3.0 / 60
    assert saved["X"] is True


def test_seed_fixed_same_ci_twice():
    jobs, levels, ftx, ax = _hand_world()
    first = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    second = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    assert (first["rate_diff_ftx_minus_ax_pts"]
            == second["rate_diff_ftx_minus_ax_pts"])
    assert (first["tokens_per_usable_ratio_ftx_ax"]
            == second["tokens_per_usable_ratio_ftx_ax"])


def test_zero_usable_resamples_are_skipped_and_counted():
    jobs = ["J1", "J2"]
    levels = {"J1": "medium", "J2": "hard"}
    ftx = [_final("J1", "FTX", 0, "PASS", 300, 150, "medium", 10.0),
           _final("J2", "FTX", 0, "PASS", 300, 150, "hard", 10.0)]
    ax = [_final("J1", "AX", 0, "PASS", 300, 150, "medium", 10.0),
          _final("J2", "AX", 0, "FAIL", 300, 150, "hard", 10.0)]
    result = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    ratio = result["tokens_per_usable_ratio_ftx_ax"]
    # Resamples drawing only J2 leave AX with 0 usable and are skipped.
    assert 0 < ratio["skipped_resamples"] < 10000
    assert ratio["est"] is not None
    assert ratio["lo"] is not None and ratio["hi"] is not None


# ------------------------------------------------------- wording branches


def test_wording_x_holds():
    jobs, levels, ftx, ax = _hand_world()
    result = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    assert result["Q"] is True and result["X"] is True
    assert "cheaper to run per usable part" in result["wording"]


def test_wording_same_quality_not_significant():
    """Q holds but the cost CI is exactly [1, 1]: same tokens both arms."""
    jobs = ["J1", "J2"]
    levels = {"J1": "medium", "J2": "hard"}
    ftx = [_final("J1", "FTX", 0, "PASS", 300, 150, "medium", 10.0),
           _final("J2", "FTX", 0, "PASS", 300, 150, "hard", 10.0)]
    ax = [_final("J1", "AX", 0, "PASS", 300, 150, "medium", 10.0),
          _final("J2", "AX", 0, "PASS", 300, 150, "hard", 10.0)]
    result = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    assert result["Q"] is True and result["X"] is False
    assert "not significant on 20 jobs" in result["wording"]


def test_wording_loss_for_training():
    """FTX 0% usable vs AX 100%: Q fails, reported as a training loss."""
    jobs = ["J1", "J2"]
    levels = {"J1": "medium", "J2": "hard"}
    ftx = [_final("J1", "FTX", 0, "FAIL", 300, 150, "medium", 10.0),
           _final("J2", "FTX", 0, "FAIL", 300, 150, "hard", 10.0)]
    ax = [_final("J1", "AX", 0, "PASS", 300, 150, "medium", 10.0),
          _final("J2", "AX", 0, "PASS", 300, 150, "hard", 10.0)]
    result = compare_brackets.decide(ftx, ax, {}, {}, jobs, levels)
    assert result["Q"] is False and result["X"] is False
    assert "loss for training on this workflow" in result["wording"]
