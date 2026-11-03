"""Offline tests for test/serve/train/init/status (mocked subprocess)."""

import json
import os
import sys

import pytest

from expertery import cli, cloud, config


class Record:
    """Fake subprocess.run: records argv/env, returns scripted results."""

    def __init__(self, results=None):
        self.calls = []
        self.results = list(results or [])

    def __call__(self, argv, env=None, capture_output=False, text=False):
        self.calls.append({"argv": list(argv),
                           "env": dict(env) if env else None})
        if self.results:
            return self.results.pop(0)
        return FakeProc(0, "https://abc-123.modal.run\n")


class FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def parse(*argv):
    return cli.build_parser().parse_args(list(argv))


def test_test_trained_argv_env_and_redeploy(tmp_path, capsys):
    exam = str(tmp_path / "exam.jsonl")
    open(exam, "w").write("{}\n")
    out = str(tmp_path / "run")
    sub = "exam-FT"
    os.makedirs(os.path.join(out, sub))
    with open(os.path.join(out, sub, "summary.json"), "w") as f:
        json.dump({"pass_rate": 0.9, "PASS": 9, "FAIL": 1}, f)
    run = Record([FakeProc(0, ""), FakeProc(0, "deployed app\n")])
    rc = cli.cmd_test(parse("test", "--exam", exam, "--model", "trained",
                            "--name", "final", "--out", out,
                            "--cap-dollars", "5"),
                      run=run, print_fn=print)
    assert rc == 0
    assert run.calls[0]["argv"] == [
        cloud.final_session_script(), os.path.abspath(out), "5.0",
        "--pilot", "",
        "--run", "%s:%s:FT:3" % (os.path.abspath(exam), sub)]
    assert run.calls[0]["env"]["FORGE_MODEL_NAME"] == "final"
    assert "FORGE_RULE_CARD" not in run.calls[0]["env"]
    # The session script stops the app: redeploy with the same name.
    assert run.calls[1]["argv"] == ["modal", "deploy",
                                    cloud.modal_forge_path()]
    assert run.calls[1]["env"]["FORGE_MODEL_NAME"] == "final"
    assert "pass rate: 0.9" in capsys.readouterr().out


def test_test_base_loop_sets_card_and_no_redeploy(tmp_path, monkeypatch):
    exam = str(tmp_path / "exam.jsonl")
    open(exam, "w").write("{}\n")
    out = str(tmp_path / "run")
    run = Record([FakeProc(0, "")])
    monkeypatch.delenv("FORGE_RULE_CARD", raising=False)
    rc = cli.cmd_test(parse("test", "--exam", exam, "--model", "base",
                            "--name", "b", "--out", out,
                            "--cap-dollars", "5", "--loop"),
                      run=run, print_fn=lambda *a, **k: None)
    assert rc == 0
    assert len(run.calls) == 1  # no redeploy after a base run
    assert run.calls[0]["argv"][-1].endswith(":A:3")
    assert run.calls[0]["env"]["RUNNER_EXTRA"] == "--bx-loop"
    assert (run.calls[0]["env"]["FORGE_RULE_CARD"]
            == cloud.rule_card_path())


def test_test_trained_loop_drops_rule_card(tmp_path, monkeypatch):
    exam = str(tmp_path / "exam.jsonl")
    open(exam, "w").write("{}\n")
    out = str(tmp_path / "run")
    monkeypatch.setenv("FORGE_RULE_CARD", "/tmp/stale-card.md")
    run = Record([FakeProc(0, ""), FakeProc(0, "")])
    rc = cli.cmd_test(parse("test", "--exam", exam, "--model", "trained",
                            "--name", "final", "--out", out,
                            "--cap-dollars", "5", "--loop"),
                      run=run, print_fn=lambda *a, **k: None)
    assert rc == 0
    assert run.calls[0]["env"]["RUNNER_EXTRA"] == "--bx-loop"
    assert "FORGE_RULE_CARD" not in run.calls[0]["env"]


def test_serve_prints_url_and_dry_run_spends_nothing():
    run = Record([FakeProc(0, "https://xyz-9.modal.run\nready\n")])
    lines = []
    rc = cli.cmd_serve(parse("serve", "--name", "final"), run=run,
                       print_fn=lines.append)
    assert rc == 0
    assert lines == ["https://xyz-9.modal.run"]
    assert run.calls[0]["env"]["FORGE_MODEL_NAME"] == "final"

    dry = Record()
    rc = cli.cmd_serve(parse("serve", "--name", "final", "--dry-run"),
                       run=dry, print_fn=lambda *a, **k: None)
    assert rc == 0
    assert dry.calls == []


def test_train_uses_guarded_entrypoint_and_dry_run():
    run = Record([FakeProc(0, "")])
    rc = cli.cmd_train(parse("train", "--data", "d.jsonl", "--out", "m",
                             "--cap-dollars", "20"),
                       run=run, print_fn=lambda *a, **k: None)
    assert rc == 0
    # full-r5 is the guarded entrypoint (never `modal run ...::train`).
    assert run.calls[0]["argv"] == [
        sys.executable, cloud.forge_train_path(), "full-r5",
        "--data", os.path.abspath("d.jsonl"), "--out", "m",
        "--cap-dollars", "20.0"]

    dry = Record()
    rc = cli.cmd_train(parse("train", "--data", "d.jsonl", "--out", "m",
                             "--cap-dollars", "20", "--dry-run"),
                       run=dry, print_fn=lambda *a, **k: None)
    assert rc == 0
    assert dry.calls == []


def test_init_checks_deploys_writes_config_no_secrets(
        tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EXPERTERY_READER_KEY", "sekret-key-123")
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    monkeypatch.setattr(config, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(config, "CONFIG_PATH",
                        str(tmp_path / "config.json"))
    run = Record([FakeProc(0, "default\n"),
                  FakeProc(0, "https://grader.modal.run\n")])
    rc = cli.cmd_init(parse("init"), run=run, print_fn=print)
    assert rc == 0
    assert run.calls[0]["argv"] == ["modal", "profile", "current"]
    assert run.calls[1]["argv"] == ["modal", "deploy",
                                    cloud.cloud_cq_path()]
    saved = json.load(open(str(tmp_path / "config.json")))
    assert saved["tool"] == "cadquery"
    out = capsys.readouterr().out
    assert "sekret-key-123" not in out
    assert "present" in out


def test_init_dry_run_changes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(config, "CONFIG_PATH",
                        str(tmp_path / "config.json"))
    run = Record()
    rc = cli.cmd_init(parse("init", "--dry-run"), run=run,
                      print_fn=lambda *a, **k: None)
    assert rc == 0
    assert run.calls == []
    assert not os.path.exists(str(tmp_path / "config.json"))


def test_status_reports_no_secrets(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EXPERTERY_READER_KEY", "sekret-key-123")
    monkeypatch.chdir(tmp_path)
    os.makedirs("old-exam")
    open("old-exam/candidates.jsonl", "w").write("{}\n")
    run = Record([FakeProc(0, "forge-cq-grader\n")])
    rc = cli.cmd_status(parse("status"), run=run, print_fn=print)
    assert rc == 0
    out = capsys.readouterr().out
    assert "sekret-key-123" not in out
    assert "exam dir: old-exam" in out


def test_cap_dollars_rejects_zero():
    with pytest.raises(SystemExit) as exc:
        parse("test", "--exam", "e", "--model", "base", "--name", "n",
              "--out", "o", "--cap-dollars", "0")
    assert exc.value.code == 2
