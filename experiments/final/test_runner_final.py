"""Offline tests for experiments/final/runner_final.py (no Modal, no network).

Fake post/exec/grade/server-info functions stand in for the real ones.
Any test that could reach a real Modal call or the network monkeypatches
it to raise. Never opens blind/ folders or expected*.json contents.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
FIRST_TEST = os.path.join(os.path.dirname(HERE), "first-test")
if FIRST_TEST not in sys.path:
    sys.path.insert(0, FIRST_TEST)

import runner
import runner_final


# ------------------------------------------------------- fakes


def _resp(content, finish="stop", prompt=100, completion=50,
          reasoning=None):
    msg = {"content": content}
    if reasoning is not None:
        msg["reasoning_content"] = reasoning
    return {"choices": [{"message": msg,
                         "finish_reason": finish}],
            "usage": {"prompt_tokens": prompt,
                      "completion_tokens": completion}}


def _post_scripted(replies):
    """post_fn serving scripted replies; records the message lists sent."""
    sent = []
    state = {"i": 0}

    def _post(endpoint, body, timeout):
        sent.append([dict(m) for m in body["messages"]])
        reply = replies[min(state["i"], len(replies) - 1)]
        state["i"] += 1
        if isinstance(reply, Exception):
            raise reply
        return reply

    _post.sent = sent
    return _post


def _box_ok(brep=b"BREP", measure=None):
    m = {"bbox": [0, 0, 0, 10, 10, 5], "volume": 500.0, "area": 1.0,
         "com": [5, 5, 2.5], "solids": 1, "valid": True}
    if measure is not None:
        m = measure
    return lambda code: {"brep_bytes": brep, "measure": dict(m), "log": "",
                         "run_error": None}


def _grade_pass(verdict="PASS", tight="PASS"):
    return lambda exam, job_id, brep: {
        "verdict": verdict, "tight": tight, "fails": [],
        "fails_tight": [], "measurements": {"volume": 1.0}}


def _no_net(monkeypatch):
    import urllib.request

    def _boom(*args, **kwargs):
        raise AssertionError("network reached in a test")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(runner_final.cloud_cq, "modal", None,
                        raising=False)


# ------------------------------------------------------- FT messages / body


def test_ft_messages_and_body_equal_arm_a_except_model():
    job_text = "A widget. Block: X from 0 to 10."
    assert runner_final.ft_messages(job_text) == runner.build_messages(
        "A", job_text, "")
    assert runner_final.ft_messages(job_text) == runner.build_messages(
        "A", job_text, "whatever manual")
    body = runner_final.ft_body(runner_final.ft_messages(job_text))
    expected = runner.build_body("muse-glimmer",
                                 runner.build_messages("A", job_text, ""))
    assert body["max_tokens"] == expected["max_tokens"] == 16000
    assert body["temperature"] == expected["temperature"] == 1.0
    assert body["top_p"] == expected["top_p"] == 0.95
    assert body["top_k"] == expected["top_k"] == 64
    assert body["messages"] == expected["messages"]
    assert body["model"] == "forge"
    assert set(body) == set(expected)  # no extra keys


# ------------------------------------------------------- FT call


def test_ft_pass_fail_invalid_paths():
    job = {"id": "M1", "text": "make a box", "level": "medium"}
    post = _post_scripted([_resp("```python\nresult = 1\n```")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass(), rep=2)
    assert rec["verdict"] == "PASS" and rec["outcome"] == "PASS"
    assert rec["tight"] == "PASS"
    assert rec["grader"] == "first-test"
    assert rec["rep"] == 2 and rec["sample"] == 2
    assert rec["t_call_s"] >= 0 and rec["usage"]["prompt_tokens"] == 100

    post = _post_scripted([_resp("```python\nresult = 1\n```")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass("FAIL", "FAIL"))
    assert rec["verdict"] == "FAIL" and rec["tight"] == "FAIL"

    post = _post_scripted([_resp("```python\nresult = 1\n```")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "factory",
        post, lambda s: None,
        lambda code: {"brep_bytes": None, "measure": None, "log": "",
                      "run_error": "the answer wrote no BREP: boom"},
        _grade_pass())
    assert rec["verdict"] == "FAIL" and rec["grader"] == "factory"
    assert "no BREP" in rec["run_error"]

    post = _post_scripted([_resp("", finish="length")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["verdict"] == "INVALID"

    post = _post_scripted([RuntimeError("down")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["verdict"] == "INVALID" and "down" in rec["run_error"]


def test_ft_suite_writes_grader_records_and_summary(tmp_path):
    jobs = [{"id": "M%d" % i, "text": "make box %d" % i,
             "level": "medium"} for i in range(2)]
    n = {"i": 0}

    def _post(endpoint, body, timeout):
        n["i"] += 1
        return _resp("```python\nresult = %d\n```" % n["i"])

    out = str(tmp_path / "ft")
    recs, summary = runner_final.run_ft_suite(
        jobs, out, "http://x/v1/chat/completions", "forge", "K",
        "first-test", _post, lambda s: None, _box_ok(), _grade_pass(),
        server_info_fn=lambda: {"models": ["forge"],
                                "image_digest": "sha256:abc"},
        k=2, workers=2, budget=5.0, gpu_start=None)
    assert len(recs) == 4
    assert all(r["grader"] == "first-test" for r in recs)
    assert summary["PASS"] == 4 and summary["pass_rate"] == 1.0
    assert summary["pass_rate_tight"] == 1.0
    assert summary["pass_at_k"] == 1.0
    assert summary["tokens_per_correct"] == pytest.approx(150.0)
    assert summary["prompt_tokens"] == 400
    assert summary["server"]["image_digest"] == "sha256:abc"
    assert summary["status"] == "COMPLETE"
    assert "dev_gate" not in summary  # exam runs have no dev gate
    calls = [json.loads(line) for line in
             open(os.path.join(out, "calls.jsonl")) if line.strip()]
    assert len(calls) == 4
    assert json.load(open(os.path.join(out, "summary.json")))["PASS"] == 4
    report = open(os.path.join(out, "report.md")).read()
    assert "1e-6" in report and "sha256:abc" in report


def test_dev_gate_go_and_stop(tmp_path, capsys):
    jobs = [{"id": "F1-1", "text": "make spool", "family": 1}]
    out = str(tmp_path / "dev")
    post = _post_scripted([_resp("```python\nresult = 1\n```")] * 3)
    _recs, summary = runner_final.run_ft_suite(
        jobs, out, "http://x/v1/chat/completions", "forge", "K",
        "factory", post, lambda s: None, _box_ok(), _grade_pass(),
        server_info_fn=lambda: {}, k=3, workers=1, budget=5.0)
    assert summary["dev_gate"] == "GO"  # 100% >= 80%
    assert "GO" in runner_final.dev_gate_line(summary)
    report = open(os.path.join(out, "report.md")).read()
    assert "DEV GATE (PLAN step 5)" in report and "GO" in report

    post = _post_scripted([_resp("```python\nresult = 1\n```")] * 3)
    out2 = str(tmp_path / "dev2")
    _recs, summary = runner_final.run_ft_suite(
        jobs, out2, "http://x/v1/chat/completions", "forge", "K",
        "factory", post, lambda s: None, _box_ok(),
        _grade_pass("FAIL", "FAIL"),
        server_info_fn=lambda: {}, k=3, workers=1, budget=5.0)
    assert summary["dev_gate"] == "STOP"  # 0% < 80%
    assert runner_final.dev_gate_line(summary).endswith("STOP")


def test_no_keys_exits_2_with_variable_name(monkeypatch, tmp_path, capsys):
    import urllib.request

    def _boom(*args, **kwargs):
        raise AssertionError("network reached before the env check")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    for var in ("FORGE_URL", "FORGE_KEY", "GLIMMER_URL", "GLIMMER_KEY",
                "BASETEN_KEY", "META_HERDSHOT_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SystemExit) as exc:
        runner_final.main(["--jobs", "main", "--out", str(tmp_path)])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "FORGE_URL" in err
    assert "FORGE_KEY" in err


# ------------------------------------------------------- BX cloud loop


CODE_A = "```python\nCODE-A\n```"
CODE_B = "```python\nCODE-B\n```"


def _local_shape_exec(outcomes):
    """Fake run_code_sandboxed: scripted (built?, measure) per call."""
    state = {"i": 0}

    def _exec(code, run_tmp, profile, timeout=60.0):
        built, measure = outcomes[min(state["i"], len(outcomes) - 1)]
        state["i"] += 1
        if built:
            return (object(), None, dict(measure))
        return (None, "boom: no result", None)

    return _exec


def _box_exec_from(outcomes):
    """The same script as cloud box dicts (bbox-list measure format)."""
    state = {"i": 0}

    def _exec(code):
        built, measure = outcomes[min(state["i"], len(outcomes) - 1)]
        state["i"] += 1
        if built:
            box = {"bbox": [measure["xmin"], measure["ymin"],
                            measure["zmin"], measure["xmax"],
                            measure["ymax"], measure["zmax"]],
                   "volume": measure["volume"], "area": 1.0,
                   "com": [0, 0, 0], "solids": measure["solids"],
                   "valid": True}
            return {"brep_bytes": b"BREP:" + code.encode(), "measure": box,
                    "log": "", "run_error": None}
        # Same observable failure as the local fake executor (the box's
        # run_error prefix is production-only detail, not loop behavior).
        return {"brep_bytes": None, "measure": None, "log": "",
                "run_error": "boom: no result"}

    return _exec


MEAS = {"xmin": 0, "ymin": 0, "zmin": 0, "xmax": 10, "ymax": 10,
        "zmax": 5, "volume": 500.0, "solids": 1}


def test_bx_cloud_sends_same_messages_as_frozen_loop(monkeypatch):
    """With fake replies and equivalent fake executors, the cloud BX loop
    sends exactly the same message list, round by round, as the frozen
    runner.do_bx_call (build, run error, self-check, no-code-block end).
    """
    cq = pytest.importorskip("cadquery")
    sys.path.insert(0, FIRST_TEST)
    import checks
    ref_shape = cq.Solid.makeBox(10, 10, 5)
    expected = checks.measure(ref_shape)
    job = {"id": "H1", "text": "make a hard part", "level": "hard",
           "build": lambda: cq.Solid.makeBox(10, 10, 5)}
    manual, hint = "MANUAL", "HINT"
    examples = [{"text": "ex job", "code": "result = 1"}]
    # Round 1 builds (self-check follows), round 2 crashes (error
    # follow-up), round 3 builds then the model ends with no code block.
    replies = [_resp(CODE_A), _resp(CODE_B), _resp("DONE, looks right")]
    script = [(True, dict(MEAS)), (False, None), (True, dict(MEAS))]
    frozen_post = _post_scripted(list(replies))

    def _real_shape_exec(code, run_tmp, profile, timeout=60.0):
        built, measure = script[min(_real_shape_exec.i, len(script) - 1)]
        _real_shape_exec.i += 1
        if built:
            return (cq.Solid.makeBox(10, 10, 5), None, dict(measure))
        return (None, "boom: no result", None)

    _real_shape_exec.i = 0
    monkeypatch.setattr(runner, "run_code_sandboxed", _real_shape_exec)
    frozen = runner.do_bx_call(
        job, "muse-glimmer", "http://x/v1/chat/completions", [], manual,
        expected, frozen_post, lambda s: None,
        sandbox_profile="PROFILE", sandbox_dir=None, examples=examples,
        hint_text=hint)
    cloud_post = _post_scripted(list(replies))
    cloud = runner_final.do_bx_cloud_call(
        job, "muse-glimmer", "http://x/v1/chat/completions", [], manual,
        cloud_post, lambda s: None, _box_exec_from(list(script)),
        _grade_pass(), hint_text=hint, examples=examples)
    assert cloud_post.sent == frozen_post.sent
    assert len(cloud_post.sent) == 3  # build, error, self-check ends
    assert [r["event"] for r in cloud["bx_rounds"]] == \
        [r["event"] for r in frozen["bx_rounds"]] == \
        ["built", "crash", "DONE"]
    assert cloud["outcome"] == frozen["outcome"] == "PASS"
    assert cloud["verdict"] == "PASS" and cloud["grader"] == "first-test"


def test_bx_cloud_crash_and_invalid_paths():
    job = {"id": "H2", "text": "make a part", "level": "hard"}
    # Three crashes: FAIL, keeps the last error.
    post = _post_scripted([_resp(CODE_A)] * 3)
    rec = runner_final.do_bx_cloud_call(
        job, "m", "http://x", [], "MAN", post, lambda s: None,
        _box_exec_from([(False, None)] * 3), _grade_pass())
    assert rec["outcome"] == "FAIL" and rec["model_calls"] == 3
    assert [r["event"] for r in rec["bx_rounds"]] == ["crash"] * 3
    # Round-1 cut-off: INVALID.
    post = _post_scripted([_resp("", finish="length")])
    rec = runner_final.do_bx_cloud_call(
        job, "m", "http://x", [], "MAN", post, lambda s: None,
        _box_exec_from([(True, dict(MEAS))]), _grade_pass())
    assert rec["outcome"] == "INVALID" and rec["tight"] == "INVALID"


def test_box_measure_conversion():
    box = {"bbox": [1, 2, 3, 11, 12, 13], "volume": 7.5, "solids": 2,
           "area": 1.0, "com": [0, 0, 0], "valid": True}
    sc = runner_final.box_measure_to_selfcheck(box)
    assert sc == {"xmin": 1, "ymin": 2, "zmin": 3, "xmax": 11,
                  "ymax": 12, "zmax": 13, "volume": 7.5, "solids": 2}
    msg = runner.bx_self_check_message(sc)  # the frozen message accepts it
    assert "volume 7.5" in msg
    assert runner_final.box_measure_to_selfcheck(None) is None
    assert runner_final.box_measure_to_selfcheck({"bbox": [1]}) is None


# ------------------------------------------------------- fill-missing


def _baseline_with_bx_finals(tmp_path, finals):
    base = tmp_path / "base"
    base.mkdir()
    with open(str(base / "calls.jsonl"), "w", encoding="utf-8") as f:
        for rec in finals:
            f.write(json.dumps(rec) + "\n")
    return str(base)


def _bx_final(job, rep, verdict="PASS"):
    return {"job": job, "arm": "BX", "bx_final": True, "round": 1,
            "sample": rep, "outcome": verdict, "verdict": verdict,
            "prompt_tokens_total": 10, "completion_tokens_total": 5,
            "model_calls": 1, "bx_rounds": []}


def test_missing_pairs_and_incomplete_exit_3(tmp_path, capsys):
    jobs = [{"id": "H13", "text": "hard 13", "level": "hard"},
            {"id": "H14", "text": "hard 14", "level": "hard"}]
    base = _baseline_with_bx_finals(
        tmp_path, [_bx_final("H13", 0), {"job": "H13", "arm": "B2",
                                         "outcome": "PASS"}])
    missing, present = runner_final.missing_bx_pairs(base, jobs, k=2)
    assert [(j["id"], r) for j, r in missing] == [
        ("H13", 1), ("H14", 0), ("H14", 1)]
    assert ("H13", 0) in present and len(present) == 1

    post = _post_scripted([_resp("DONE")])  # no code: best None -> FAIL
    out = str(tmp_path / "fill")
    sent, summary, missing_pairs = runner_final.run_bx_fill(
        base, jobs, out, "http://x", "m", "K", "MAN", post,
        lambda s: None,
        lambda code: {"brep_bytes": None, "measure": None, "log": "",
                      "run_error": "boom"},
        _grade_pass(), server_info_fn=lambda: {}, workers=3, k=2,
        budget=5.0)
    assert len(sent) == 3  # one final per missing pair
    # Simulate the stop: drop one final -> fewer finals than missing.
    assert summary["status"] == "COMPLETE"
    assert summary["n_missing"] == 3


def test_fill_incomplete_writes_refused_summary(tmp_path):
    jobs = [{"id": "H13", "text": "hard 13", "level": "hard"}]
    base = _baseline_with_bx_finals(tmp_path, [])
    out = str(tmp_path / "fill")

    def _post(endpoint, body, timeout):
        raise AssertionError("no call may start without money")

    # Zero budget: nothing is sent, so fewer finals than missing pairs.
    sent, summary, missing_pairs = runner_final.run_bx_fill(
        base, jobs, out, "http://x", "m", "K", "MAN", _post,
        lambda s: None, _box_ok(), _grade_pass(),
        server_info_fn=lambda: {}, workers=1, k=2, budget=0.0)
    assert len(missing_pairs) == 2
    assert len([r for r in sent if r.get("bx_final") is True]) == 0
    assert summary["status"] == "INCOMPLETE"
    assert summary["still_missing"] == ["H13 rep 0", "H13 rep 1"]
    saved = json.load(open(os.path.join(out, "summary.json")))
    assert saved["status"] == "INCOMPLETE"  # compare.py refuses this
    assert "INCOMPLETE: ask the user" in open(
        os.path.join(out, "report.md")).read()


def test_fill_workers_default_12_and_budget_guard(tmp_path):
    assert runner_final.money_left(5.0, None) == pytest.approx(5.0)
    assert runner_final.out_of_money(0.1, None) is True
    assert runner_final.out_of_money(5.0, None) is False
    # A zero budget sends nothing new: everything is skipped.
    jobs = [{"id": "M1", "text": "box", "level": "medium"}]
    out = str(tmp_path / "skipped")

    def _post(endpoint, body, timeout):
        raise AssertionError("no call may start without money")

    recs, summary = runner_final.run_ft_suite(
        jobs, out, "http://x", "forge", "K", "first-test", _post,
        lambda s: None, _box_ok(), _grade_pass(),
        server_info_fn=lambda: {}, k=1, workers=1, budget=0.0)
    assert recs == [] and summary["skipped"] == 1
    assert summary["budget_stopped"] is True


def test_modal_forge_matches_glimmer_settings():
    """Section 6: same GPU/image/flags/limits/secret as modal_glimmer,
    except app forge-trained, /vol/<name>/merged, served name forge."""
    src = open(os.path.join(HERE, "..", "..", "deploy", "modal_forge.py"),
               encoding="utf-8").read()
    assert 'modal.App("forge-trained")' in src
    assert '"A100-80GB"' in src and '"32768"' in src
    assert "max_containers=1" in src and "300" in src
    assert 'Secret.from_name("forge-glimmer")' in src
    assert '"forge-lora"' in src and "/vol/" in src
    assert 'FORGE_MODEL_NAME' in src and '"final"' in src
    assert '"forge"' in src
    assert "muse_glimmer" in src  # same vLLM parsers


def test_modal_forge_bakes_name_into_container_env():
    """Round 3c (verifier D1): the deploy-time FORGE_MODEL_NAME reaches
    the container env (Modal re-imports the module inside the container
    where the variable is not set), and serve() logs the served path."""
    src = open(os.path.join(HERE, "..", "..", "deploy", "modal_forge.py"),
               encoding="utf-8").read()
    assert 'image.env({"FORGE_MODEL_NAME"' in src or \
        "image.env({'FORGE_MODEL_NAME'" in src
    assert "MODEL_NAME" in src  # the deploy-time value is what is baked in
    assert "SERVING" in src and "/vol/" in src and "/merged" in src
    # serve() re-reads the name inside the container instead of trusting
    # the deploy-time MODEL_PATH global.
    serve_body = src.split("def serve", 1)[1]
    assert "FORGE_MODEL_NAME" in serve_body
    assert "MODEL_PATH" not in serve_body or "model_path" in serve_body


def test_run_final_session_verifies_served_model():
    """Round 3c (verifier D1): after ready, the session fetches
    $URL/v1/models, prints the served root, and refuses (exit 1, app
    stopped by the trap) unless it equals /vol/$FORGE_MODEL_NAME/merged
    (default final)."""
    src = open(os.path.join(HERE, "run_final_session.sh"),
               encoding="utf-8").read()
    assert "$URL/v1/models" in src
    assert "root" in src
    assert "served model root" in src
    assert "/vol/${FORGE_MODEL_NAME:-final}/merged" in src
    assert "MODEL MISMATCH" in src
    assert "exit 1" in src


def test_run_final_session_refuses_on_root_mismatch(tmp_path):
    """Round 3c (verifier D1): fake curl/models responses — a served root
    that is not /vol/$FORGE_MODEL_NAME/merged exits 1 and the trap stops
    the app. No network, no Modal."""
    import shutil
    import subprocess
    if not shutil.which("zsh"):
        pytest.skip("zsh is not installed")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    modal_stub = bindir / "modal"
    modal_stub.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"deploy\" ]; then\n"
        "  echo \"https://stub.modal.run\"\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8")
    modal_stub.chmod(0o755)
    curl_stub = bindir / "curl"
    curl_stub.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"-w"*) printf "200"; exit 0;;\n'
        "esac\n"
        'printf \'{"data": [{"id": "forge", "root": "/vol/final/merged"}]}\'\n',
        encoding="utf-8")
    curl_stub.chmod(0o755)
    out = tmp_path / "out"
    env = dict(os.environ, MODAL_BIN=str(modal_stub),
               CURL_BIN=str(curl_stub), FORGE_MODEL_NAME="other-model")
    p = subprocess.run(
        ["zsh", os.path.join(HERE, "run_final_session.sh"), str(out)],
        capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == 1, p.stdout + p.stderr
    assert "MODEL MISMATCH" in p.stdout
    assert "served model root: /vol/final/merged" in p.stdout
    assert "app stopped" in p.stdout  # the EXIT trap stopped the app


def test_run_final_session_script():
    """Section 6: deploy, wait ready, cap with reserve, trap stops app.
    Round 3 (verifier D1): run() passes the whole cap (--budget "$CAP");
    budget_left.py stays only as the refuse-to-start check."""
    src = open(os.path.join(HERE, "run_final_session.sh"),
               encoding="utf-8").read()
    assert "deploy/modal_forge.py" in src
    assert "runner_final.py" in src and "FORGE_URL" in src
    assert "budget_left.py" in src  # whole-session cap with reserve
    assert "app stop forge-trained" in src
    assert "trap" in src and "GO" in src and "STOP" in src
    assert '--budget "$CAP"' in src
    assert '--budget "$B"' not in src


def test_run_base_session_script():
    """Round 3 (verifier P5 + D1): the base control session mirrors the
    final session for app forge-glimmer and deploy/modal_glimmer.py,
    with the same whole-cap budget fix."""
    src = open(os.path.join(HERE, "run_base_session.sh"),
               encoding="utf-8").read()
    assert "deploy/modal_glimmer.py" in src
    assert "modal_forge" not in src and "forge-trained" not in src
    assert "runner_final.py" in src and "GLIMMER_URL" in src
    assert "GLIMMER_KEY" in src and "FORGE_URL" not in src
    assert "budget_left.py" in src
    assert "app stop forge-glimmer" in src
    assert "trap" in src and "GO" in src and "STOP" in src
    assert '--budget "$CAP"' in src
    assert '--budget "$B"' not in src
    assert ":A:3" in src  # arm A specs, not FT


def test_arm_a_messages_and_body_equal_ft_except_model():
    """Round 3 (verifier P5): base control arm A sends the SAME short
    prompt and body as FT, except the model name."""
    job_text = "A widget. Block: X from 0 to 10."
    assert runner_final.a_messages(job_text) == runner_final.ft_messages(
        job_text)
    body = runner_final.a_body(runner_final.a_messages(job_text))
    ft_body = runner_final.ft_body(runner_final.ft_messages(job_text))
    assert body["messages"] == ft_body["messages"]
    assert body["max_tokens"] == ft_body["max_tokens"] == 16000
    assert body["temperature"] == ft_body["temperature"] == 1.0
    assert body["top_p"] == ft_body["top_p"] == 0.95
    assert body["top_k"] == ft_body["top_k"] == 64
    assert set(body) == set(ft_body)  # no extra keys
    assert body["model"] == "muse-glimmer" and ft_body["model"] == "forge"
    assert runner_final.A_MODEL == "muse-glimmer"


def test_arm_a_suite_uses_base_model_and_arm_label(tmp_path):
    """Arm A records carry arm A and model muse-glimmer, graded like FT."""
    jobs = [{"id": "M1", "text": "make a box", "level": "medium"}]
    post = _post_scripted([_resp("```python\nresult = 1\n```",
                                 reasoning="think step")])
    out = str(tmp_path / "a")
    recs, summary = runner_final.run_ft_suite(
        jobs, out, "http://x/v1/chat/completions", runner_final.A_MODEL,
        "K", "first-test", post, lambda s: None, _box_ok(),
        _grade_pass(), server_info_fn=lambda: {}, k=1, workers=1,
        budget=5.0, arm=runner_final.A_ARM)
    assert len(recs) == 1
    assert recs[0]["arm"] == "A" and recs[0]["model"] == "muse-glimmer"
    assert recs[0]["verdict"] == "PASS"
    assert recs[0]["reasoning_chars"] == len("think step")
    assert summary["arm"] == "A"
    assert post.sent[0] == runner_final.a_messages("make a box")


def test_ft_records_carry_reasoning_chars():
    """Round 3 serving check: every FT record holds reasoning_chars =
    len(message.reasoning_content); 0 when absent (INVALID included)."""
    job = {"id": "M1", "text": "make a box", "level": "medium"}
    post = _post_scripted([_resp("```python\nresult = 1\n```",
                                 reasoning="abcd")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["reasoning_chars"] == 4
    assert rec["reasoning_len"] == 4 and rec["reasoning_length"] == 4
    post = _post_scripted([_resp("```python\nresult = 1\n```")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["reasoning_chars"] == 0
    post = _post_scripted([RuntimeError("down")])
    rec = runner_final.do_ft_call(
        job, "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["verdict"] == "INVALID" and rec["reasoning_chars"] == 0
    # The FT body is unchanged: no reasoning_strength, max_tokens 16000.
    body = runner_final.ft_body(runner_final.ft_messages("t"))
    assert "chat_template_kwargs" not in body
    assert body["max_tokens"] == 16000


def test_main_arm_a_needs_glimmer_keys_and_routes_there(
        monkeypatch, tmp_path, capsys):
    """--arms A refuses without GLIMMER_URL/GLIMMER_KEY (exit 2, names
    the variable, no network) and runs the A suite on them otherwise."""
    import urllib.request

    def _boom(*args, **kwargs):
        raise AssertionError("network reached before the env check")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    for var in ("FORGE_URL", "FORGE_KEY", "GLIMMER_URL", "GLIMMER_KEY"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SystemExit) as exc:
        runner_final.main(["--jobs", "dry", "--out", str(tmp_path),
                           "--arms", "A"])
    assert exc.value.code == 2
    assert "GLIMMER_URL" in capsys.readouterr().err

    monkeypatch.setenv("GLIMMER_URL", "http://glimmer")
    monkeypatch.setenv("GLIMMER_KEY", "K")
    seen = {}

    def _suite(jobs, out, endpoint, model, key, exam, **kwargs):
        seen.update(endpoint=endpoint, model=model, key=key,
                    arm=kwargs.get("arm"))
        return [], {"n": 0, "pass_rate": None}

    monkeypatch.setattr(runner_final, "run_ft_suite", _suite)
    import types
    fake_cq = types.SimpleNamespace(
        modal=types.SimpleNamespace(enable_output=lambda: _Ctx()),
        _app=types.SimpleNamespace(run=lambda: _Ctx()),
        run_answer_in_box=lambda code: {}, grade=types.SimpleNamespace())
    monkeypatch.setattr(runner_final, "cloud_cq", fake_cq)
    assert runner_final.main(["--jobs", "dry", "--out", str(tmp_path),
                              "--arms", "A"]) == 0
    assert seen["endpoint"] == "http://glimmer/v1/chat/completions"
    assert seen["model"] == "muse-glimmer" and seen["arm"] == "A"


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_server_info_never_raises_and_reads_digest():
    assert runner_final.fetch_server_info("", "") == {
        "models": [], "image_digest": None}

    class _Resp:
        headers = {"x-image-digest": "sha256:img"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    import io
    payload = json.dumps({"data": [{"id": "forge"}],
                          "image_digest": "sha256:body"}).encode()
    info = runner_final.fetch_server_info(
        "http://gpu/v1/chat/completions", "K",
        urlopen=lambda req, timeout: io.BytesIO(payload))
    assert info == {"models": ["forge"], "image_digest": "sha256:body"}

    def _boom(req, timeout):
        raise RuntimeError("net down")

    assert runner_final.fetch_server_info("http://gpu/v1/chat/completions",
                                          "K", urlopen=_boom) == {
        "models": [], "image_digest": None}
