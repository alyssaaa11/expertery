"""Offline tests for experiments/final/compare.py (no network, no Modal).

Fake run dirs (calls.jsonl + summary.json) stand in for the real FT,
baseline and 6a sessions. Boundary tests hit each bar exactly at its
threshold; refusal tests cover duplicates, still-missing answers, and an
INCOMPLETE 6a dir.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import compare


# ------------------------------------------------------- builders


def _write_dir(path, records, summary):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "calls.jsonl"), "w",
              encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    with open(os.path.join(path, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f)


def _rec(job, arm, rep, verdict, prompt=1000, completion=500,
         level="medium", bx=False):
    rec = {"job": job, "arm": arm, "sample": rep, "level": level,
           "outcome": verdict, "verdict": verdict,
           "usage": {"prompt_tokens": prompt,
                     "completion_tokens": completion},
           "seconds": 10.0}
    if bx:
        rec["bx_final"] = True
        rec["prompt_tokens_total"] = prompt
        rec["completion_tokens_total"] = completion
        rec["model_calls"] = 1
    return rec


def _world(tmp_path, ft_fail_jobs=()):
    """A tiny complete world: 4 jobs x 2 reps for B2/BX/BR/FT + a
    COMPLETE empty 6a dir. FT passes every job (bar b can hold);
    tokens make bars c/d hold. Jobs in ft_fail_jobs fail all FT reps."""
    jobs = ["M1", "M2", "H1", "H2"]
    levels = {"M1": "medium", "M2": "medium", "H1": "hard", "H2": "hard"}
    b2, bx, br, ft = [], [], [], []
    for job in jobs:
        for rep in (0, 1):
            # B2: one of two reps PASS (rate 0.5); BX/BR: all PASS.
            b2.append(_rec(job, "B2", rep,
                           "PASS" if rep == 0 else "FAIL",
                           prompt=6000, completion=4000,
                           level=levels[job]))
            bx.append(_rec(job, "BX", rep, "PASS", prompt=14000,
                           completion=7000, level=levels[job], bx=True))
            if rep == 0:
                br.append(_rec(job, "BR", rep, "PASS", level=levels[job]))
            ft.append(_rec(job, "FT", rep,
                           "FAIL" if job in ft_fail_jobs else "PASS",
                           prompt=3000, completion=1500,
                           level=levels[job]))
    b2bx = str(tmp_path / "b2bx")
    _write_dir(b2bx, b2 + bx,
               {"arm_timing": {"B2": {"seconds": 100.0},
                               "BX": {"seconds": 200.0}}})
    brd = str(tmp_path / "br")
    _write_dir(brd, br, {"arm_timing": {"BR": {"seconds": 50.0}}})
    ftd = str(tmp_path / "ft")
    _write_dir(ftd, ft, {"arm": "FT", "wall_seconds": 80.0,
                         "cold_start_s": 0.0})
    extra = str(tmp_path / "extra")
    _write_dir(extra, [],
               {"arm": "BX", "status": "COMPLETE", "wall_seconds": 30.0,
                "cold_start_s": 5.0})
    return ftd, b2bx, brd, extra


# ------------------------------------------------------- bar boundaries


def test_bar_a_boundaries():
    assert compare.check_a(-5.0, -15.0) is True  # exactly at both
    assert compare.check_a(-4.9, -15.0) is True
    assert compare.check_a(-5.1, -15.0) is False  # past -5 points
    assert compare.check_a(-5.0, -15.1) is False  # lower bound past -15


def test_bar_b_boundary():
    assert compare.check_b(0.1, 5.0) is True
    assert compare.check_b(0.0, 5.0) is False  # not entirely above 0
    assert compare.check_b(-0.1, 5.0) is False


def test_bar_c_boundary():
    assert compare.check_c(1500.0, 1000.0) is True  # exactly 1.5x
    assert compare.check_c(1501.0, 1000.0) is False


def test_bar_d_boundaries():
    assert compare.check_d(1000.0, 3000.0, 99.0, 100.0) is True  # tokens
    assert compare.check_d(1001.0, 3000.0, 99.0, 100.0) is False
    assert compare.check_d(2000.0, 3000.0, 30.0, 100.0) is True  # wall
    assert compare.check_d(2000.0, 3000.0, 34.0, 100.0) is False


def test_bootstrap_deterministic_and_sane():
    x = {"J%d" % i: 1.0 for i in range(6)}
    y = {"J%d" % i: 0.0 for i in range(6)}
    jobs = sorted(x)
    first = compare.bootstrap_ci(x, y, jobs)
    assert compare.bootstrap_ci(x, y, jobs) == first  # same seed
    est, lo, hi = first
    assert est == pytest.approx(100.0)
    assert lo > 0.0 and hi >= lo  # a clean sweep stays above 0


# ------------------------------------------------------- end to end


def test_all_pass_world_claim_holds(tmp_path, capsys):
    ftd, b2bx, brd, extra = _world(tmp_path)
    lines, result = compare.decide(ftd, b2bx, brd, extra)
    assert result["claim_holds"] is True
    assert all(result["bar_%s" % b]["pass"] for b in "abcd")
    text = "\n".join(lines)
    assert "CLAIM HOLDS" in text
    assert "(a)" in text and "(d)" in text
    assert "79 answers" in text  # the disclosure line
    assert "medium" in text and "hard" in text  # level tables
    # E2 wall math: 200 (baseline) + (30 - 5) (6a without cold start).
    assert result["bar_d"]["bx_wall_s"] == pytest.approx(225.0)
    assert result["bar_d"]["bx_extra_effective_s"] == pytest.approx(25.0)
    assert compare.main(["--ft", ftd, "--b2bx", b2bx, "--br", brd,
                         "--bx-extra", extra]) == 0
    assert "CLAIM HOLDS" in capsys.readouterr().out


def test_failing_world_claim_does_not_hold(tmp_path):
    # FT fails both medium jobs: bar (a) est = -50 points.
    ftd, b2bx, brd, extra = _world(tmp_path, ft_fail_jobs=("M1", "M2"))
    lines, result = compare.decide(ftd, b2bx, brd, extra)
    assert result["claim_holds"] is False
    assert result["bar_a"]["pass"] is False
    assert "CLAIM DOES NOT HOLD" in "\n".join(lines)


# ------------------------------------------------------- refusals (exit 2)


def test_refuses_when_a_bx_answer_still_missing(tmp_path):
    ftd, b2bx, brd, extra = _world(tmp_path)
    # Drop one BX final from the baseline: H2 rep 1 now missing.
    recs = [json.loads(line) for line in
            open(os.path.join(b2bx, "calls.jsonl")) if line.strip()]
    recs = [r for r in recs
            if not (r.get("arm") == "BX" and r.get("job") == "H2"
                    and r.get("sample") == 1)]
    _write_dir(b2bx, recs, {"arm_timing": {"B2": {"seconds": 100.0},
                                           "BX": {"seconds": 200.0}}})
    with pytest.raises(ValueError, match="H2 rep 1"):
        compare.decide(ftd, b2bx, brd, extra)
    with pytest.raises(SystemExit) as exc:
        compare.main(["--ft", ftd, "--b2bx", b2bx, "--br", brd,
                      "--bx-extra", extra])
    assert exc.value.code == 2


def test_refuses_on_duplicate_bx_answer(tmp_path):
    ftd, b2bx, brd, extra = _world(tmp_path)
    dup = _rec("M1", "BX", 0, "PASS", bx=True)
    with open(os.path.join(extra, "calls.jsonl"), "a",
              encoding="utf-8") as f:
        f.write(json.dumps(dup) + "\n")
    with pytest.raises(ValueError, match="duplicate BX answer.*M1 rep 0"):
        compare.decide(ftd, b2bx, brd, extra)


def test_refuses_when_6a_ended_incomplete(tmp_path):
    ftd, b2bx, brd, extra = _world(tmp_path)
    _write_dir(extra, [], {"arm": "BX", "status": "INCOMPLETE",
                           "wall_seconds": 30.0, "cold_start_s": 5.0,
                           "still_missing": ["H2 rep 1"]})
    with pytest.raises(ValueError, match="did not end COMPLETE"):
        compare.decide(ftd, b2bx, brd, extra)
    with pytest.raises(SystemExit) as exc:
        compare.main(["--ft", ftd, "--b2bx", b2bx, "--br", brd,
                      "--bx-extra", extra])
    assert exc.value.code == 2
