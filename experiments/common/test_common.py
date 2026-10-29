"""Offline tests for experiments/common/ (no GPU, no network)."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import budget_left
import dashboard

FORGE = os.path.dirname(os.path.dirname(HERE))

GOOD_CODE = 'import cadquery as cq\nresult = cq.Workplane("XY").box(10, 10, 10)\n'
WRONG_CODE = 'import cadquery as cq\nresult = cq.Workplane("XY").box(10, 10, 11)\n'


# ------------------------------------------------------- budget-left helper


def test_budget_left_fixed_numbers():
    assert budget_left.budget_left(3.0, 1000, now=1000, rate_per_hour=2.50) == 3.0
    assert budget_left.budget_left(3.0, 1000, now=1000 + 3600, rate_per_hour=2.50) == 0.5


def test_budget_left_refuses_at_or_below_five_cents():
    assert budget_left.budget_left(1.0, 0, now=3600, rate_per_hour=2.50) is None
    assert budget_left.budget_left(0.05, 1000, now=1000, rate_per_hour=2.50) is None


def test_budget_left_cli_fixed_numbers():
    # A gpu-start in the future means no GPU time has accrued: full cap left.
    p = subprocess.run(
        [sys.executable, "-I", os.path.join(HERE, "budget_left.py"),
         "3.0", "9999999999"],
        capture_output=True, text=True, timeout=60,
    )
    assert p.returncode == 0 and p.stdout.strip() == "3.00"
    # A spent cap refuses with exit 2.
    p = subprocess.run(
        [sys.executable, "-I", os.path.join(HERE, "budget_left.py"),
         "0.01", "0"],
        capture_output=True, text=True, timeout=60,
    )
    assert p.returncode == 2 and "CAP REACHED" in p.stdout


def test_run_session_uses_budget_left_and_refuses():
    src = open(os.path.join(HERE, "run_session.sh"), encoding="utf-8").read()
    assert "budget_left.py" in src  # the helper, not an inline formula
    assert "CAP REACHED" in src
    assert "0.05" in open(os.path.join(HERE, "budget_left.py"),
                          encoding="utf-8").read()


def test_run_session_arms_jobs_k_are_parameters():
    src = open(os.path.join(HERE, "run_session.sh"), encoding="utf-8").read()
    assert "--pilot" in src and "--run" in src
    assert "--arms" in src and "--jobs" in src and "--k" in src
    # No hard-coded runner call: specs flow through the runspec helper.
    assert "runspec" in src
    assert "run --jobs dry" not in src and "run --jobs main" not in src


# --------------------------------------------------------------- dashboard


def _fake_run(tmp_path):
    run = tmp_path / "run"
    (run / "main-BR").mkdir(parents=True)
    recs = [
        {"arm": "BR", "job": "M1", "sample": 0, "outcome": "PASS",
         "usage": {"total_tokens": 1000}, "latency": 5.0},
        {"arm": "BR", "job": "M2", "sample": 0, "outcome": "FAIL",
         "fails": ["bbox"], "usage": {"total_tokens": 2000}, "latency": 7.0},
    ]
    with open(run / "main-BR" / "calls.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    (run / "session.log").write_text("ready 10:00:00 (try 1)\n", encoding="utf-8")
    arms = [{"name": "BR", "label": "Plain Glimmer", "description": "manual, 1 try",
             "expected": 2, "colour": "#2a78d6"}]
    cfg = tmp_path / "arms.json"
    cfg.write_text(json.dumps(arms), encoding="utf-8")
    return run, cfg


def test_dashboard_renders_from_fake_calls(tmp_path):
    run, cfg = _fake_run(tmp_path)
    arms = dashboard.load_arms(str(cfg))
    out = str(tmp_path / "dash.html")
    log = dashboard.write_page(str(run), arms, out, cap=3.0, title="T")
    assert "ready" in log
    page = open(out, encoding="utf-8").read()
    assert 'http-equiv="refresh" content="20"' in page  # reloads every 20 s
    assert "✓" in page and "✗" in page  # symbols, not colour alone
    assert "#2a78d6" in page and "Plain Glimmer" in page
    assert "M1" in page and "M2" in page  # data embedded in the HTML
    assert "prefers-color-scheme" in page  # light/dark CSS
    assert dashboard.stopped("app stopped 10:00:00")
    assert not dashboard.stopped("ready 10:00:00")


# ---------------------------------------------------------------- score_one


def _sandbox_available():
    try:
        p = subprocess.run(
            ["sandbox-exec", "-n", "no-network", "/bin/echo", "hi"],
            capture_output=True, timeout=30,
        )
        return p.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


needs_sandbox = pytest.mark.skipif(
    not _sandbox_available(),
    reason="sandbox-exec cannot apply a profile in this environment")


@needs_sandbox
def test_score_one_pass_and_fail(tmp_path):
    import score_one

    ref = tmp_path / "ref.py"
    ref.write_text(GOOD_CODE, encoding="utf-8")
    sbx = tmp_path / "sbx"
    sbx.mkdir()
    ok, reasons, _ = score_one.score_reply(
        "```python\n%s\n```" % GOOD_CODE, str(ref), sandbox_dir=str(sbx))
    assert ok, reasons
    bad, reasons, _ = score_one.score_reply(
        "```python\n%s\n```" % WRONG_CODE, str(ref), sandbox_dir=str(sbx))
    assert not bad and reasons


@needs_sandbox
def test_score_one_cli_pass_fail(tmp_path, capsys):
    import score_one

    ref = tmp_path / "ref.py"
    ref.write_text(GOOD_CODE, encoding="utf-8")
    reply = tmp_path / "reply.txt"
    reply.write_text("```python\n%s\n```" % GOOD_CODE, encoding="utf-8")
    rc = score_one.main(["--reply-file", str(reply), "--reference", str(ref),
                         "--sandbox-dir", str(tmp_path)])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out
    reply.write_text("```python\n%s\n```" % WRONG_CODE, encoding="utf-8")
    rc = score_one.main([str(reply), str(ref), "--sandbox-dir", str(tmp_path)])
    assert rc == 1
    assert "FAIL" in capsys.readouterr().out
