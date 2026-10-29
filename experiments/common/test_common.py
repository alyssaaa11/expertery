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
    # The default $0.30 reserve is held back: in-flight answers still cost.
    assert budget_left.budget_left(3.0, 1000, now=1000,
                                   rate_per_hour=2.50) == 2.70
    assert budget_left.budget_left(3.0, 1000, now=1000 + 3600,
                                   rate_per_hour=2.50) == 0.20
    assert budget_left.budget_left(3.0, 1000, now=1000, rate_per_hour=2.50,
                                   reserve=0.0) == 3.0
    assert budget_left.budget_left(3.0, 1000, now=1000, rate_per_hour=2.50,
                                   reserve=1.0) == 2.0


def test_budget_left_refuses_at_or_below_five_cents():
    assert budget_left.budget_left(1.0, 0, now=3600, rate_per_hour=2.50) is None
    assert budget_left.budget_left(0.05, 1000, now=1000, rate_per_hour=2.50) is None
    # A cap that only covers the reserve refuses too.
    assert budget_left.budget_left(0.30, 1000, now=1000,
                                   rate_per_hour=2.50) is None


def test_budget_left_cli_fixed_numbers():
    # A gpu-start in the future means no GPU time has accrued: cap minus
    # the default $0.30 reserve is left.
    p = subprocess.run(
        [sys.executable, "-I", os.path.join(HERE, "budget_left.py"),
         "3.0", "9999999999"],
        capture_output=True, text=True, timeout=60,
    )
    assert p.returncode == 0 and p.stdout.strip() == "2.70"
    p = subprocess.run(
        [sys.executable, "-I", os.path.join(HERE, "budget_left.py"),
         "3.0", "9999999999", "--reserve", "0"],
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


def test_run_session_trap_kills_runner_and_stops_app():
    src = open(os.path.join(HERE, "run_session.sh"), encoding="utf-8").read()
    for sig in ("EXIT", "INT", "TERM", "HUP"):
        assert sig in src  # the trap covers EXIT INT TERM HUP
    assert "& RPID=$!" in src and "wait $RPID" in src  # backgrounded runner
    assert "kill -TERM $RPID" in src  # runner killed ...
    assert "pkill -TERM -P $RPID" in src  # ... with its children
    assert "modal app stop" in src and "app stopped" in src


def _alive(pid):
    """True when a process with this pid exists (kill -0 probe)."""
    try:
        os.kill(pid, 0)
    except (OSError, ValueError):
        return False
    return True


def test_run_session_hook_gets_keys_and_session_budget(tmp_path):
    import shutil
    import time
    if not shutil.which("zsh"):
        pytest.skip("zsh is not installed")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "modal"
    stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)
    out = tmp_path / "out"
    record = tmp_path / "hook.env"
    wrap = tmp_path / "dummy_hook.sh"
    # The hook appends --budget/--gpu-start after the command; the dummy
    # records the keys from its env and all its arguments, then stops.
    wrap.write_text(
        "#!/bin/sh\n"
        "echo \"GLIMMER_URL=$GLIMMER_URL\" > %s\n"
        "echo \"GLIMMER_KEY_SET=${GLIMMER_KEY:+yes}\" >> %s\n"
        "printf '%%s\\n' \"$@\" >> %s\n" % (record, record, record),
        encoding="utf-8")
    wrap.chmod(0o755)
    env = dict(os.environ, RUN_SESSION_SKIP_DEPLOY="1",
               RUN_SESSION_RUNNER_CMD="sh %s" % wrap, MODAL_BIN=str(stub))
    p = subprocess.run(
        ["zsh", os.path.join(HERE, "run_session.sh"), str(out),
         "--pilot", "", "--run", "dummy:sub:BR:1"],
        capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    lines = record.read_text(encoding="utf-8").splitlines()
    assert "GLIMMER_URL=skip" in lines  # the session key reaches the hook
    assert "GLIMMER_KEY_SET=yes" in lines
    args = lines[2:]
    assert "--jobs" in args and "dummy" in args  # the spec still flows
    b = args[args.index("--budget") + 1]  # the whole-session cap
    g = args[args.index("--gpu-start") + 1]
    assert float(b) == budget_left.budget_left(
        3.0, int(g), now=time.time(), rate_per_hour=2.50)


def test_run_session_term_kills_dummy_runner(tmp_path):
    import shutil
    import signal
    import time
    if not shutil.which("zsh"):
        pytest.skip("zsh is not installed")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "modal"
    stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stub.chmod(0o755)
    out = tmp_path / "out"
    log = tmp_path / "session.log"
    pidfile = tmp_path / "runner.pid"
    wrap = tmp_path / "dummy_runner.sh"
    # The runner spec args are appended to the command, so the dummy takes
    # no arguments itself: it records its pid, then sleeps (the trap's
    # victim). `exec` keeps the recorded pid as the sleeper.
    wrap.write_text("#!/bin/sh\necho $$ > %s\nexec sleep 60\n" % pidfile,
                    encoding="utf-8")
    wrap.chmod(0o755)
    env = dict(os.environ, RUN_SESSION_SKIP_DEPLOY="1",
               RUN_SESSION_RUNNER_CMD="sh %s" % wrap, MODAL_BIN=str(stub))
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen(
            ["zsh", os.path.join(HERE, "run_session.sh"), str(out),
             "--pilot", "", "--run", "dummy:sub:BR:1"],
            stdout=fh, stderr=subprocess.STDOUT, env=env)
    try:
        for _ in range(100):
            time.sleep(0.2)
            if pidfile.exists() or proc.poll() is not None:
                break
        assert pidfile.exists(), "the dummy runner never started"
        sleeper = int(pidfile.read_text(encoding="utf-8").strip().split()[0])
        assert _alive(sleeper), "the dummy runner is not alive"
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    text = log.read_text(encoding="utf-8", errors="replace")
    assert "app stopped" in text  # the trap stopped the app and said so
    assert not _alive(sleeper), "the dummy runner survived TERM"


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
    assert "Exam:" not in page  # the fc line stays off by default


def _fake_fc_run(tmp_path):
    run = tmp_path / "fcrun"
    run.mkdir()
    recs = [
        {"arm": "G", "job": "T2", "sample": 0, "outcome": "PASS",
         "exam": "thinking", "box_ok": True, "graded": True,
         "usage": {"total_tokens": 100}, "latency": 5.0},
        {"arm": "S", "job": "T2", "sample": 0, "outcome": "FAIL",
         "exam": "thinking", "box_ok": True, "graded": True,
         "fails": ["bbox"], "usage": {"total_tokens": 200},
         "latency": 7.0},
        {"arm": "S", "job": "T5", "sample": 1, "outcome": "FAIL",
         "exam": "thinking", "box_ok": False, "graded": False,
         "usage": {"total_tokens": 200}, "latency": 7.0},
    ]
    with open(run / "calls.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    (run / "session.log").write_text("ready 10:00:00 (try 1)\n",
                                     encoding="utf-8")
    return run


def test_dashboard_fc_mode_shows_exam_boxes_grades_and_gpu(tmp_path):
    import time

    run = _fake_fc_run(tmp_path)
    arms = [("G", "Glimmer", "g", 13, "#2a78d6"),
            ("S", "Spark", "s", 13, "#eb6834")]
    out = str(tmp_path / "fc.html")
    # calls.jsonl is read live on every render (no caching between runs).
    dashboard.write_page(str(run), arms, out, title="FC", fc=True,
                         gpu_start=time.time() - 600)
    page = open(out, encoding="utf-8").read()
    assert "Exam: thinking" in page  # the exam name, from the records
    assert "2 answers through the safety box" in page  # box_ok records
    assert "2 graded" in page  # graded records
    assert "10 min" in page  # GPU minutes from --gpu-start
    # A second render picks up records appended after the first.
    with open(run / "calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(
            {"arm": "S", "job": "T5", "sample": 2, "outcome": "PASS",
             "exam": "thinking", "box_ok": True, "graded": True,
             "usage": {"total_tokens": 200}, "latency": 7.0}) + "\n")
    dashboard.write_page(str(run), arms, out, title="FC", fc=True,
                         gpu_start=time.time() - 600)
    assert "3 answers through the safety box" in open(
        out, encoding="utf-8").read()
    # The --exam flag overrides the records' name; bad --gpu-start is "–".
    info = dashboard.fc_status(dashboard.load_calls(str(run)),
                               gpu_start="soon", exam="first-test")
    assert info["exam"] == "first-test" and info["gpu_min"] is None


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
