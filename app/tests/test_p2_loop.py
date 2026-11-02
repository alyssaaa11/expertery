"""The FTX-style loop with a fake model + fake box (no Modal, no network)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                               "experiments", "final"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                               "experiments", "first-test"))

import runner  # noqa: E402 (frozen)
import runner_final  # noqa: E402 (frozen)

from app.backend import config, loop  # noqa: E402

JOB = "An L-shaped mounting bracket. Overall size 80 x 30 x 45 mm."

CRASH_CODE = "```python\nresult = oops\n```"
GOOD_CODE = "```python\nresult = box\n```"
GOOD_MEASURE = {"bbox": [0, 0, 0, 80, 30, 45], "volume": 1000.0,
                "solids": 1, "area": 10.0,
                "com": [40.0, 15.0, 22.5], "valid": True}


def fake_model(script):
    """A scripted model: list of (content, gpu_seconds) per call."""
    import copy

    calls = []

    def _call(messages, body):
        # Deep copies: the loop keeps appending to the live history.
        calls.append({"messages": copy.deepcopy(messages),
                      "body": copy.deepcopy(body)})
        content, gpu = script[min(len(calls) - 1, len(script) - 1)]
        return content, gpu

    _call.calls = calls
    return _call


def fake_box(results):
    """A scripted box: list of run_answer_in_box-style dicts per code run."""
    seen = []

    def _run(code):
        seen.append(code)
        out = results[min(len(seen) - 1, len(results) - 1)]
        return dict(out)

    _run.seen = seen
    return _run


CRASH = {"brep_bytes": None, "measure": None,
         "run_error": "NameError: name 'result' is not defined"}
BUILT = {"brep_bytes": b"BREP", "measure": dict(GOOD_MEASURE),
         "log": "", "run_error": None}


def test_crash_fix_build_pass_event_order():
    # FTX rule (Claude fix 2026-11-02): after a build the model sees its own
    # measurements and may fix or say DONE; here it says DONE.
    model = fake_model([(CRASH_CODE, 5.0), (GOOD_CODE, 6.0), ("DONE", 1.0)])
    box = fake_box([CRASH, BUILT])
    events = list(loop.run_job(JOB, model, box))
    assert [(e["step"], e["round"]) for e in events] == [
        ("write", 1), ("build", 1), ("fix", 1),
        ("write", 2), ("build", 2), ("measure", 2), ("fix", 2),
        ("write", 3), ("done", 3),
    ]
    done = events[-1]
    assert done["verdict"] == "PASS"
    assert done["code"] == "result = box"
    assert len(model.calls) == 3
    assert model.calls[2]["messages"][-1]["content"] == runner.bx_self_check_message(
        runner_final.box_measure_to_selfcheck(GOOD_MEASURE))
    assert done["gpu_seconds"] == pytest.approx(12.0)


def test_measure_driven_fix_last_built_counts():
    two = dict(GOOD_MEASURE, solids=2)
    bad = {"brep_bytes": b"BREP", "measure": two, "log": "", "run_error": None}
    model = fake_model([(CRASH_CODE.replace("oops", "two"), 1.0), (GOOD_CODE, 1.0), ("DONE", 1.0)])
    box = fake_box([bad, BUILT])
    events = list(loop.run_job(JOB, model, box))
    assert len(model.calls) == 3
    assert events[-1]["verdict"] == "PASS"
    assert events[-1]["code"] == "result = box"
    assert events[-1]["measurements"]["solids"] == 1


def test_messages_match_ftx_rules_exactly():
    model = fake_model([(CRASH_CODE, 1.0), ("DONE", 1.0)])
    box = fake_box([CRASH])
    list(loop.run_job(JOB, model, box))
    first, second = model.calls[0], model.calls[1]
    assert first["messages"] == runner_final.ft_messages(JOB)
    err = CRASH["run_error"]
    assert second["messages"] == (
        first["messages"]
        + [{"role": "assistant", "content": CRASH_CODE},
           {"role": "user", "content": runner.bx_error_message(err)}])


def test_body_matches_ftx_arm_with_default_strength():
    assert config.reasoning_strength() == "xhigh"
    model = fake_model([("DONE", 0.0)])
    box = fake_box([BUILT])
    list(loop.run_job(JOB, model, box))
    sent = model.calls[0]["body"]
    assert sent == runner.build_bx_body("forge", model.calls[0]["messages"])
    assert sent["chat_template_kwargs"] == {"reasoning_strength": "xhigh"}
    assert sent["max_tokens"] == 16000


def test_body_carries_configured_strength(monkeypatch):
    monkeypatch.setenv("REASONING_STRENGTH", "high")
    assert config.reasoning_strength() == "high"
    model = fake_model([("DONE", 0.0)])
    box = fake_box([BUILT])
    list(loop.run_job(JOB, model, box))
    assert model.calls[0]["body"]["chat_template_kwargs"] == \
        {"reasoning_strength": "high"}


def test_bad_strength_rejected(monkeypatch):
    monkeypatch.setenv("REASONING_STRENGTH", "low")
    with pytest.raises(ValueError):
        config.reasoning_strength()


def test_max_three_model_calls():
    model = fake_model([(CRASH_CODE, 1.0)] * 10)
    box = fake_box([CRASH] * 10)
    events = list(loop.run_job(JOB, model, box))
    assert len(model.calls) == 3
    assert events[-1]["step"] == "done"
    assert events[-1]["verdict"] == "CHECK FAILED"


def test_first_event_before_first_model_call():
    order = []

    def _model(messages, body):
        order.append("model")
        return "DONE", 0.0

    gen = loop.run_job(JOB, _model, fake_box([BUILT]))
    first = next(gen)
    assert first["step"] == "write"
    assert order == []


def test_no_code_reply_ends_loop_without_build():
    model = fake_model([("Looks good to me", 1.0)])
    box = fake_box([BUILT])
    events = list(loop.run_job(JOB, model, box))
    assert [e["step"] for e in events] == ["write", "done"]
    assert box.seen == []
    assert events[-1]["verdict"] == "CHECK FAILED"


def test_build_is_followed_by_measure_then_done():
    model = fake_model([(GOOD_CODE, 2.0), ("DONE", 1.0)])
    box = fake_box([BUILT])
    events = list(loop.run_job(JOB, model, box))
    assert [(e["step"], e["round"]) for e in events] == [
        ("write", 1), ("build", 1), ("measure", 1), ("fix", 1),
        ("write", 2), ("done", 2)]
    assert len(model.calls) == 2
    assert events[-1]["verdict"] == "PASS"
    assert events[-1]["measurements"]["solids"] == 1
    assert events[2]["measurements"] == GOOD_MEASURE

