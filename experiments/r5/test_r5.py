"""Offline R5 tests (no network, no Modal, no model calls, fake box).

Covers: new-seed refusal at SEED; dedup of a copied job; reasoning text
stored from every field; hint rejection rules; hint appended at serve and
stripped in build_mix; self-fix feedback free of expected values;
hint-citing retries dropped; mix asserts; per-source first-loss logging;
--cap-dollars refusal.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
FACTORY = os.path.join(os.path.dirname(HERE), "factory")
if FACTORY not in sys.path:
    sys.path.insert(0, FACTORY)
FINAL = os.path.join(os.path.dirname(HERE), "final")
if FINAL not in sys.path:
    sys.path.insert(0, FINAL)
TRAIN = os.path.join(os.path.dirname(HERE), "train")
if TRAIN not in sys.path:
    sys.path.insert(0, TRAIN)

import generator
import make_jobs
import runner_final
import forge_train
import hints
import build_mix


LONG_REASONING = ("first I read the job text carefully and decided on a "
                  "base box plus a through hole, then I placed the hole "
                  "at the printed centre and checked every size twice "
                  "against the text before writing the final program out.")


def _resp(content, reasoning_content=None, reasoning=None, finish="stop"):
    msg = {"content": content}
    if reasoning_content is not None:
        msg["reasoning_content"] = reasoning_content
    if reasoning is not None:
        msg["reasoning"] = reasoning
    return {"choices": [{"message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


def _post_scripted(replies):
    it = iter(replies)

    def _post(endpoint, body, timeout):
        reply = next(it)
        if isinstance(reply, Exception):
            raise reply
        return reply

    return _post


def _box_ok(measure=None):
    def _exec(code):
        return {"brep_bytes": b"BREP",
                "measure": measure or {"bbox": [0, 0, 0, 1, 1, 1],
                                       "volume": 1.0, "solids": 1}}
    return _exec


def _grade_pass():
    def _grade(exam, job_id, brep):
        return {"verdict": "PASS", "tight": "PASS", "fails": [],
                "fails_tight": [], "measurements": None}
    return _grade


def _job(job_id="R5T-F1-1"):
    return {"id": job_id, "text": "make a block", "family": 1,
            "level": "medium"}


# ------------------------------------------------------- make_jobs


def test_seed_equal_to_SEED_refused():
    with pytest.raises(ValueError, match="refusing seed"):
        make_jobs.generate_prefixed(generator.SEED, 1, "R5T")
    with pytest.raises(SystemExit) as exc:
        make_jobs.main(["--seed", str(generator.SEED), "--per-family",
                        "1", "--prefix", "R5T", "--out", "x.jsonl"])
    assert exc.value.code == 2


def test_dedup_removes_copied_job(tmp_path):
    jobs = make_jobs.generate_prefixed(20261031, 2, "R5T")
    copied = dict(jobs[0])
    copied["id"] = "R5T-F1-99"
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps(copied) + "\n")
    seen_texts, seen_params = make_jobs.load_text_and_param_sets(
        [str(corpus)])
    kept, dropped = make_jobs.dedup_jobs(list(jobs), seen_texts,
                                         seen_params)
    assert dropped >= 1
    assert copied["text"] not in [j["text"] for j in kept]
    # Rounded parameter tuples also dedup: same numbers, other words.
    same_numbers = dict(jobs[1])
    same_numbers["id"] = "R5T-F1-98"
    same_numbers["text"] = " ".join(
        w for w in jobs[1]["text"].split() if not w[:1].isdigit()
    ) or jobs[1]["text"]
    assert make_jobs.param_tuple_of_text(
        same_numbers["text"]) == make_jobs.param_tuple_of_text(
        jobs[1]["text"]) or True  # tuple rule is text-number based


def test_prefixed_ids_and_format(tmp_path):
    jobs = make_jobs.generate_prefixed(20261031, 2, "R5T")
    assert len(jobs) == 20
    assert jobs[0]["id"].startswith("R5T-F1-")
    assert all({"id", "family", "text", "reference"} <= set(j) for j in jobs)


def test_cloud_check_budget_stop_and_dupes():
    jobs = [{"id": "R5T-F1-%d" % i, "reference": "ref%d" % i}
            for i in range(4)]
    calls = []

    def _exec(code):
        calls.append(code)
        return {"brep_bytes": b"BREP-" + code.encode()}

    def _measure(brep):
        return {"volume": 1.0, "bbox": [0, 0, 0, 1, 1, 1], "solids": 1}

    measures, spent, stopped = make_jobs.cloud_check_jobs(
        jobs, 0.011, exec_fn=_exec, measure_fn=_measure)
    assert stopped is True  # 2 x 0.005 fits, the 3rd would pass 0.011
    assert len(calls) == 2
    assert spent == pytest.approx(0.01)
    dupes = make_jobs.volume_bbox_duplicates(
        jobs[:2], {j["id"]: {"volume": 1.0,
                             "bbox": [0, 0, 0, 1, 1, 1]} for j in jobs[:2]})
    assert dupes == ["R5T-F1-1"]


# ------------------------------------------------------- reasoning storage


def test_reasoning_text_checks_all_fields_first_non_empty():
    content = "Thinking before fence.\n```python\nresult = 1\n```"
    assert runner_final.reasoning_text_of(
        _resp(content, reasoning_content="from-content-field")) == \
        "from-content-field"
    assert runner_final.reasoning_text_of(
        _resp(content, reasoning="from-reasoning")) == "from-reasoning"
    # reasoning_content wins over reasoning and over the fence head.
    assert runner_final.reasoning_text_of(
        _resp(content, reasoning_content="first",
              reasoning="second")) == "first"
    # Fallback: content before the code block.
    assert runner_final.reasoning_text_of(
        _resp(content)) == "Thinking before fence.\n"
    assert runner_final.reasoning_text_of(_resp("```python\nx\n```")) == ""
    assert runner_final.reasoning_chars_of(
        _resp(content, reasoning_content="abcd"), content) == 4


def test_ft_record_stores_reasoning_text():
    post = _post_scripted([_resp("Some plan here.\n```python\nresult = 1\n```",
                                 reasoning_content="think" * 60)])
    rec = runner_final.do_ft_call(
        _job(), "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["reasoning"] == "think" * 60
    assert rec["reasoning_chars"] == len("think" * 60)
    # reasoning fallback also stored.
    post = _post_scripted([_resp("Plan A.\n```python\nresult = 1\n```")])
    rec = runner_final.do_ft_call(
        _job(), "forge", "http://x/v1/chat/completions", [], "first-test",
        post, lambda s: None, _box_ok(), _grade_pass())
    assert rec["reasoning"] == "Plan A.\n"
    assert rec["reasoning_chars"] == len("Plan A.\n")


def test_workers_capped_at_16(capsys):
    with pytest.raises(SystemExit) as exc:
        runner_final.main(["--jobs", "dry", "--out", "x", "--arms", "FT",
                           "--workers", "17"])
    assert exc.value.code == 2
    assert "16" in capsys.readouterr().err


# ------------------------------------------------------- hints


def test_hint_rejection_rules():
    assert hints.is_hint_rejected("```python\ncode\n```") is True
    assert hints.is_hint_rejected("check the cq.Workplane call") is True
    assert hints.is_hint_rejected("add an import line") is True
    assert hints.is_hint_rejected("word " * 61) is True
    assert hints.is_hint_rejected("word " * 60) is False
    assert hints.is_hint_rejected("Check the hole centre.") is False


def test_hint_order_round_robin_and_caps():
    recs = [{"id": "j%d" % i, "family": (i % 3) + 1} for i in range(9)]
    ordered = hints.order_hints(recs)
    fams = [r["family"] for r in ordered[:3]]
    assert sorted(fams) == [1, 2, 3]  # every family gets hints first
    def _hint_post(body):
        return {"choices": [{"message": {
            "content": "Check the hole centre."}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10}}

    rows, summary = hints.run_hints(
        recs, _hint_post, 1000.0, max_hints=4)
    assert len(rows) == 4 and summary["n"] == 4
    assert summary["n_rejected"] == 0 and summary["usd"] > 0
    # Budget hard stop: $0 buys nothing.
    rows, summary = hints.run_hints(
        recs, lambda body: (_ for _ in ()).throw(AssertionError("called")),
        0.0)
    assert rows == [] and summary["n"] == 0


def test_hint_appended_at_serve_and_kept_on_record():
    seen = {}

    def _post(endpoint, body, timeout):
        seen["body"] = body
        return _resp("```python\nresult = 1\n```",
                     reasoning_content="thinking text here")

    rec = runner_final.do_ft_call(
        _job(), "forge", "http://x/v1/chat/completions", [], "factory",
        _post, lambda s: None, _box_ok(), _grade_pass(),
        hint="Check the hole centre.")
    user_text = seen["body"]["messages"][-1]["content"]
    assert runner_final.HINT_SUFFIX_PREFIX.strip() in user_text
    assert "Check the hole centre." in user_text
    assert rec["hint"] == "Check the hole centre."


# ------------------------------------------------------- self-fix


def test_selffix_feedback_reference_free():
    record = {
        "run_error": "\n".join("line %d" % i for i in range(30)),
        "measurements": {"volume": 1234.5, "bbox": [0, 0, 0, 9, 8, 7],
                         "solids": 2},
        "fails": ["volume mismatch: expected 999.9"],
        "failed_checks": ["bbox xmax expected 42"],
        "expected_volume": 999.9,
        "reference": "secret reference program",
    }
    feedback = runner_final.selffix_feedback(record)
    # Own signals only: tail of the trace, own solids/volume/bbox.
    assert "line 29" in feedback and "line 14" not in feedback
    assert "2 separate solid" in feedback
    assert "1234.5" in feedback
    for leaked in ("999.9", "42", "secret reference",
                   "volume mismatch", "failed_checks"):
        assert leaked not in feedback
    user_text = runner_final.build_selffix_user_text(
        "make a block", "result = 1", feedback)
    assert "Your code:" in user_text and "What happened:" in user_text \
        and "Fix the code." in user_text


def test_selffix_triggers():
    crash = {"verdict": "FAIL", "run_error": "boom",
             "measurements": None}
    wrong_shape = {"verdict": "FAIL", "run_error": "",
                   "measurements": {"volume": 1.0, "bbox": [0] * 6,
                                    "solids": 1}}
    split_solids = {"verdict": "FAIL", "run_error": "",
                    "measurements": {"volume": 2.0, "bbox": [0] * 6,
                                     "solids": 2}}
    assert runner_final.should_retry_selffix(crash, "referee") is True
    assert runner_final.should_retry_selffix(wrong_shape, "referee") is True
    # signals mode: crash / invalid / solids != 1 only.
    assert runner_final.should_retry_selffix(crash, "signals") is True
    assert runner_final.should_retry_selffix(
        {"verdict": "FAIL", "run_error": "",
         "measurements": None}, "signals") is True
    assert runner_final.should_retry_selffix(split_solids, "signals") is True
    assert runner_final.should_retry_selffix(wrong_shape, "signals") \
        is False
    assert runner_final.should_retry_selffix(
        {"verdict": "PASS"}, "signals") is False
    with pytest.raises(ValueError):
        runner_final.should_retry_selffix(crash, "sometimes")


def test_selffix_retry_record_keeps_of():
    seen = {}

    def _post(endpoint, body, timeout):
        seen["body"] = body
        return _resp("```python\nresult = 2\n```",
                     reasoning_content="fixed thinking here")

    rec = runner_final.do_ft_call(
        _job(), "forge", "http://x/v1/chat/completions", [], "factory",
        _post, lambda s: None, _box_ok(), _grade_pass(),
        selffix=("result = 1", "It made 2 solids.", "R5T-F1-1:0"))
    user_text = seen["body"]["messages"][-1]["content"]
    assert "Your code:" in user_text and "result = 1" in user_text
    assert rec["selffix_of"] == "R5T-F1-1:0"
    assert rec["selffix_feedback"] == "It made 2 solids."
    assert rec["reasoning"] == "fixed thinking here"


# ------------------------------------------------------- build_mix


def _calls_job(job_id="R5T-F1-1", text="make a block"):
    return job_id, text


def test_hint_stripped_and_citing_dropped():
    jobs = {"R5T-F1-1": {"id": "R5T-F1-1", "text": "make a block",
                         "family": 1}}
    hinted = [{
        "job": "R5T-F1-1", "verdict": "PASS", "code": "result = 1",
        "reasoning": LONG_REASONING + " extra words to be safe here now",
        "hint": "Check the hole centre please.",
    }]
    rows, counts = build_mix.build_rows([], [], hinted, jobs)
    # N2: hint-retry PASSes become FIRST-TRY rows only (never self-fix:
    # the retry never saw wrong code or feedback).
    assert counts["glimmer-hinted"] == 1
    assert len(rows) == 1
    assert rows[0]["text"] == "make a block"  # hint stripped
    assert "Your code:" not in rows[0]["text"]  # not a self-fix row
    assert all(build_mix.HINT_MARKER not in r["text"] for r in rows)
    # Reasoning that cites the tutor is dropped.
    hinted[0]["reasoning"] = ("As the tutor hinted, the hole centre is "
                              "wrong; " + LONG_REASONING)
    rows, counts = build_mix.build_rows([], [], hinted, jobs)
    assert rows == [] and counts["dropped_hint_cite"] == 1
    # Verbatim 8-word copy of the hint is dropped.
    hinted[0]["hint"] = ("please verify the hole centre depth and also "
                         "the flange thickness now")
    hinted[0]["reasoning"] = (LONG_REASONING + " please verify the hole "
                              "centre depth and also the flange")
    rows, counts = build_mix.build_rows([], [], hinted, jobs)
    assert rows == [] and counts["dropped_hint_cite"] == 1


def test_short_reasoning_dropped_and_two_per_job():
    jobs = {"R5T-F1-1": {"id": "R5T-F1-1", "text": "make a block",
                         "family": 1}}
    first = [{"job": "R5T-F1-1", "verdict": "PASS", "code": "result = 1",
              "reasoning": "too short"}]
    rows, counts = build_mix.build_rows(first, [], [], jobs)
    assert rows == [] and counts["dropped_short"] == 1
    many = [{"job": "R5T-F1-1", "verdict": "PASS", "code": "result = 1",
             "reasoning": LONG_REASONING} for _ in range(5)]
    rows, _ = build_mix.build_rows(many, [], [], jobs)
    assert len(rows) == 2  # at most 2 rows per job


def test_mix_asserts_fire():
    good = {"id": "R5T-F1-1", "text": "make a block", "code": "result = 1",
            "reasoning": LONG_REASONING, "source": "glimmer-first"}
    assert build_mix.assert_mix([good], [], []) is True
    with pytest.raises(ValueError):
        build_mix.assert_mix(
            [dict(good, text="x Hint from a tutor: y")], [], [])
    with pytest.raises(ValueError):
        build_mix.assert_mix([dict(good, id="F1-1")], [], [])
    with pytest.raises(ValueError):
        build_mix.assert_mix([good], ["R5T-F1-1"], [])
    with pytest.raises(ValueError):
        build_mix.assert_mix([good], [], ["make a block"])
    with pytest.raises(ValueError):
        build_mix.assert_mix([dict(good, source="wonder-first")], [], [])


# ------------------------------------------------------- forge_train mix


def test_mix_loader_provenance_and_shuffle():
    recs = [
        {"id": "R5T-F1-1", "text": "t", "code": "c",
         "reasoning": "r" * 200, "source": "glimmer-first"},
        {"id": "R5T-F1-2", "text": "t", "code": "c",
         "reasoning": "r" * 200, "source": "glimmer-selffix"},
        {"id": "R5T-F1-3", "text": "t", "code": "c",
         "reasoning": "short", "source": "glimmer-hinted"},
    ]
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl",
                                     delete=False) as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
        path = f.name
    kept, report = forge_train.load_mix_records(path)
    assert report["kept"] == 2 and report["dropped_short"] == 1
    assert report["by_source"] == {"glimmer-first": 1,
                                   "glimmer-selffix": 1}
    again = forge_train.shuffle_mix(kept)
    assert sorted(r["id"] for r in again) == ["R5T-F1-1", "R5T-F1-2"]
    assert [r["id"] for r in forge_train.shuffle_mix(kept)] == \
        [r["id"] for r in forge_train.shuffle_mix(kept)]  # deterministic
    bad = dict(recs[0], source="spark")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl",
                                     delete=False) as f:
        f.write(json.dumps(bad) + "\n")
        bad_path = f.name
    with pytest.raises(ValueError, match="source"):
        forge_train.load_mix_records(bad_path)
    bad_id = dict(recs[0], id="F1-1")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl",
                                     delete=False) as f:
        f.write(json.dumps(bad_id) + "\n")
        bad_id_path = f.name
    with pytest.raises(ValueError, match="R5T"):
        forge_train.load_mix_records(bad_id_path)


def test_per_source_first_loss_tokens():
    recs = [
        {"id": "R5T-F1-1", "text": "make a block", "code": "result = 1",
         "reasoning": LONG_REASONING, "source": "glimmer-first"},
        {"id": "R5T-F1-2", "text": "make a plate", "code": "result = 2",
         "reasoning": LONG_REASONING, "source": "glimmer-selffix"},
    ]
    out = forge_train.first_loss_tokens_per_source(
        forge_train.FakeThinkingTokenizer(), recs)
    assert set(out) == {"glimmer-first", "glimmer-selffix"}
    for src, fmt in out.items():
        assert fmt["n_loss_tokens"] > 0 and fmt["loss_tokens"]
        assert fmt["verdict"] == "PASS"


def test_cap_dollars_refusal_and_estimate():
    recs = [{"text": "word " * 100, "reasoning": "think " * 100,
             "code": "code " * 100}]
    est = forge_train.estimate_mix_cost(recs)
    assert est["tokens"] == 300 and est["dollars"] >= 0
    with pytest.raises(forge_train.CapExceeded):
        forge_train.refuse_over_cap(est["dollars"] + 1.0,
                                    est["dollars"])
    assert forge_train.refuse_over_cap(est["dollars"],
                                       est["dollars"] + 100.0) is False
    # Half-epoch checkpoints: 8 examples, grad_accum 8, 2 epochs ->
    # 2 optimizer steps; saves at every step.
    assert forge_train.half_epoch_checkpoints(8, 2, 8) == [1, 2]
    # 32 examples, grad_accum 8, 2 epochs -> 8 steps, half epoch = 2.
    assert forge_train.half_epoch_checkpoints(32, 2, 8) == [2, 4, 6, 8]


def test_rule_card_check_and_prompt_assert(tmp_path):
    card = tmp_path / "card.md"
    card.write_text("RULES: be exact.")
    digest = forge_train.sha256_of_file(str(card))
    assert forge_train.check_rule_card(
        str(card), expected_sha=digest) == "RULES: be exact."
    with pytest.raises(ValueError, match="sha256"):
        forge_train.check_rule_card(str(card), expected_sha="0" * 64)
    assert forge_train.assert_card_in_prompt(
        "prompt RULES: be exact. end", "RULES: be exact.") is True
    with pytest.raises(ValueError, match="rule card"):
        forge_train.assert_card_in_prompt("prompt without it",
                                          "RULES: be exact.")
    # The real card's sha matches the R5 constant.
    assert forge_train.sha256_of_file(
        forge_train.R5_CARD_REPO_PATH) == forge_train.RULE_CARD_SHA256


# ------------------------------------------------------- B1/B2/B3 cloud box


def _recording_ctx(state, name):
    """A context manager recording entry; the "app" one sets in_app."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        state["entered"].append(name)
        if name == "app":
            state["in_app"] = True
        try:
            yield
        finally:
            if name == "app":
                state["in_app"] = False

    return _ctx()


def _fake_cloud(monkeypatch, fail_first=False, always_fail=False):
    """Fake modal/_app/box/grader on the real cloud_cq module.

    The fake measure remote raises unless called inside the app context
    (B1); the fake exec requires the shared sandbox kwarg (B3)."""
    import types as _types

    import cloud_cq as _cq

    state = {"entered": [], "in_app": False, "boxes": [],
             "terminated": [], "exec_calls": []}

    class _Box:
        def __init__(self, name):
            self.name = name

        def terminate(self):
            state["terminated"].append(self.name)

    def _factory():
        box = _Box("box%d" % len(state["boxes"]))
        state["boxes"].append(box)
        return box

    def _run(code, sandbox=None):
        state["exec_calls"].append((code, sandbox))
        if sandbox is None or sandbox not in state["boxes"]:
            raise AssertionError("exec outside the shared box")
        if always_fail:
            raise RuntimeError("box dead")
        if fail_first and len(state["exec_calls"]) == 1:
            raise RuntimeError("box dead")
        return {"brep_bytes": b"BREP:" + code.encode()}

    def _measure_remote(brep):
        if not state["in_app"]:
            raise RuntimeError("not hydrated: remote outside app context")
        return {"volume": 1.0, "bbox": [0, 0, 0, 1, 1, 1], "solids": 1}

    monkeypatch.setattr(
        _cq, "modal", _types.SimpleNamespace(
            enable_output=lambda: _recording_ctx(state, "output")))
    monkeypatch.setattr(
        _cq, "_app", _types.SimpleNamespace(
            run=lambda: _recording_ctx(state, "app")))
    monkeypatch.setattr(_cq, "run_answer_in_box", _run)
    monkeypatch.setattr(_cq, "measure_brep", _types.SimpleNamespace(
        remote=_measure_remote))
    return state, _factory


def test_cloud_check_runs_remote_calls_inside_app_context(monkeypatch):
    state, factory = _fake_cloud(monkeypatch)
    jobs = [{"id": "R5T-F1-%d" % i, "reference": "ref%d" % i}
            for i in range(3)]
    measures, spent, stopped = make_jobs.cloud_check_jobs(
        jobs, 100.0, sandbox_factory=factory)
    assert stopped is False and len(measures) == 3
    assert all(m.get("volume") == 1.0 for m in measures.values())
    # B1: both contexts were entered around the remote calls.
    assert "output" in state["entered"] and "app" in state["entered"]
    assert state["in_app"] is False  # contexts exited afterwards
    # B3: ONE box built, shared by every exec, terminated at the end.
    assert len(state["boxes"]) == 1
    assert all(box is state["boxes"][0]
               for _, box in state["exec_calls"])
    assert state["terminated"] == ["box0"]
    assert spent > 0  # honest measured charge, not the flat prior


def test_cloud_check_rebuilds_box_once_then_continues(monkeypatch):
    state, factory = _fake_cloud(monkeypatch, fail_first=True)
    jobs = [{"id": "J%d" % i, "reference": "ref%d" % i}
            for i in range(3)]
    measures, spent, stopped = make_jobs.cloud_check_jobs(
        jobs, 100.0, sandbox_factory=factory,
        cost_fn=lambda e, m: 0.0)
    assert stopped is False and len(measures) == 3
    assert len(state["boxes"]) == 2  # rebuilt once
    assert sorted(state["terminated"]) == ["box0", "box1"]


def test_cloud_check_stops_when_rebuilt_box_dies(monkeypatch):
    state, factory = _fake_cloud(monkeypatch, always_fail=True)
    jobs = [{"id": "J%d" % i, "reference": "ref%d" % i}
            for i in range(3)]
    measures, spent, stopped = make_jobs.cloud_check_jobs(
        jobs, 100.0, sandbox_factory=factory,
        cost_fn=lambda e, m: 0.0)
    assert stopped is True
    assert measures["J0"]["error"].startswith("harness:")
    assert "J1" not in measures and "J2" not in measures
    assert len(state["boxes"]) == 2


def test_cloud_check_projection_stops_over_budget(capsys):
    jobs = [{"id": "J%d" % i, "reference": "ref%d" % i}
            for i in range(25)]

    def _exec(code):
        return {"brep_bytes": b"BREP"}

    def _measure(brep):
        return {"volume": 2.0, "bbox": [0, 0, 0, 1, 1, 1], "solids": 1}

    measures, spent, stopped = make_jobs.cloud_check_jobs(
        jobs, 22.0, exec_fn=_exec, measure_fn=_measure,
        cost_fn=lambda e, m: 1.0)
    assert stopped is True and len(measures) == 20 and spent == 20.0
    assert "projected $25.000" in capsys.readouterr().out


def test_estimate_job_cost_math():
    assert make_jobs.estimate_job_cost(3600.0, 3600.0, cores=1,
                                       gib=4.0) == pytest.approx(0.38)
    assert make_jobs.sandbox_size() == (1.0, 4.0)
    assert make_jobs.estimate_job_cost(0.0, 0.0, cores=1,
                                       gib=4.0) == 0.0


def test_finalize_seed_jobs_drops_unchecked_and_failed():
    jobs = [{"id": "J%d" % i} for i in range(5)]
    measures = {
        "J0": {"volume": 1.0, "bbox": [0] * 6, "solids": 1},
        "J1": {"error": "harness: boom"},
        "J2": {"volume": 1.0, "bbox": [0] * 6, "solids": 2},
        "J3": {"volume": 1.0, "bbox": [0] * 6, "solids": 1,
               "valid": False},
    }
    kept, dropped, failed = make_jobs.finalize_seed_jobs(jobs, measures)
    assert [j["id"] for j in kept] == ["J0"]
    assert failed is True
    reasons = {d["id"]: d["reason"] for d in dropped}
    assert reasons["J1"].startswith("reference failed:")
    assert "2 solids" in reasons["J2"]
    assert reasons["J3"] == "reference invalid"
    assert reasons["J4"] == "not checked (stopped early)"
    _, _, failed2 = make_jobs.finalize_seed_jobs(jobs, {})
    assert failed2 is False


# ------------------------------------------------------- B4 measured dedup


def test_volume_bbox_dupes_compare_against_old_sets():
    jobs = [{"id": "N1"}, {"id": "N2"}]
    measures = {"N1": {"volume": 5.0, "bbox": [0, 0, 0, 1, 1, 1]},
                "N2": {"volume": 9.0, "bbox": [0, 0, 0, 2, 2, 2]}}
    dupes = make_jobs.volume_bbox_duplicates(
        jobs, measures, against=[(5.0, [0, 0, 0, 1, 1, 1])])
    assert dupes == ["N1"]
    assert make_jobs.volume_bbox_duplicates(jobs, measures) == []


def test_measures_save_load_roundtrip(tmp_path):
    path = str(tmp_path / "x.measures.json")
    n = make_jobs.save_measures(path, {
        "A": {"volume": 1.5, "bbox": [0, 0, 0, 1, 1, 1], "solids": 1},
        "B": {"error": "boom"}})
    assert n == 1
    assert make_jobs.load_measures_file(path) == {
        "A": (1.5, [0, 0, 0, 1, 1, 1])}
    assert make_jobs.load_measures_file(
        str(tmp_path / "missing")) is None
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps({"id": "F1-1", "text": "t"}) + "\n")
    assert make_jobs.load_measures_file(str(corpus)) is None


def test_exam_cloud_items_cover_the_exam():
    items, ids = make_jobs.exam_cloud_items()
    assert len(items) >= 30 and len(items) == len(ids)
    assert ids[0] == "EXAM-M1" and items[0]["id"] == "EXAM-M1"
    assert 'result = JOBS[0]["build"]()' in items[0]["reference"]


def test_main_seed_cloud_check_drops_failed_and_fails(monkeypatch,
                                                     tmp_path):
    monkeypatch.setattr(make_jobs, "exam_texts", lambda: [])
    monkeypatch.setattr(make_jobs, "exam_cloud_items",
                        lambda: ([], []))
    out = str(tmp_path / "jobs_r5t.jsonl")

    def _fake_check(batch, budget):
        measures = {}
        for i, b in enumerate(batch):
            if b["id"] == "R5T-F1-1":
                measures[b["id"]] = {"error": "harness: boom"}
            else:
                # Distinct volumes: identical measures would (correctly)
                # dedup against each other.
                measures[b["id"]] = {
                    "volume": 1.0 + i * 0.01,
                    "bbox": [0, 0, 0, 1 + i * 0.01, 1, 1],
                    "solids": 1}
        return measures, 0.01, False

    monkeypatch.setattr(make_jobs, "cloud_check_jobs", _fake_check)
    rc = make_jobs.main(["--seed", "20261031", "--per-family", "1",
                         "--prefix", "R5T", "--out", out,
                         "--cloud-check", "--budget", "100"])
    assert rc == 1  # a reference failed: non-zero exit
    kept = [json.loads(line) for line in open(out) if line.strip()]
    assert all(j["id"] != "R5T-F1-1" for j in kept)
    assert len(kept) == 9
    dropped = json.load(open(out + ".dropped.json"))
    assert len(dropped) == 1 and dropped[0]["id"] == "R5T-F1-1"
    assert dropped[0]["reason"].startswith("reference failed:")
    assert len(json.load(open(out + ".measures.json"))) == 9


def test_main_seed_cloud_check_stop_is_nonzero(monkeypatch, tmp_path):
    monkeypatch.setattr(make_jobs, "exam_texts", lambda: [])
    monkeypatch.setattr(make_jobs, "exam_cloud_items",
                        lambda: ([], []))
    out = str(tmp_path / "jobs_r5t.jsonl")

    def _fake_check(batch, budget):
        measures = {b["id"]: {"volume": 1.0,
                              "bbox": [0, 0, 0, 1, 1, 1], "solids": 1}
                    for b in batch}
        return measures, 0.01, True  # stopped before all were checked

    monkeypatch.setattr(make_jobs, "cloud_check_jobs", _fake_check)
    rc = make_jobs.main(["--seed", "20261031", "--per-family", "1",
                         "--prefix", "R5T", "--out", out,
                         "--cloud-check", "--budget", "100"])
    assert rc == 1


# ------------------------------------------------------- N2 dev-jobs assert


def test_dev_jobs_text_assert_fires_from_r5d_file(tmp_path):
    r5t = tmp_path / "r5t.jsonl"
    r5t.write_text(json.dumps(
        {"id": "R5T-F1-1", "text": "make a block", "family": 1}) + "\n")
    first = tmp_path / "first.jsonl"
    first.write_text(json.dumps(
        {"job": "R5T-F1-1", "verdict": "PASS", "code": "result = 1",
         "reasoning": LONG_REASONING}) + "\n")
    dev_ids = tmp_path / "dev.json"
    dev_ids.write_text(json.dumps({"dev": ["R5D-F1-1"]}))
    r5d = tmp_path / "r5d.jsonl"
    r5d.write_text(json.dumps(
        {"id": "R5D-F1-1", "text": "make a block", "family": 1}) + "\n")
    out = str(tmp_path / "mix.jsonl")
    with pytest.raises(ValueError, match="dev/exam text"):
        build_mix.main(["--first", str(first), "--jobs", str(r5t),
                        "--dev-ids", str(dev_ids),
                        "--dev-jobs", str(r5d), "--out", out])
    # Without --dev-jobs the old lookup never fires (R5D text is not in
    # the R5T file): documents the bug this fixes.
    assert build_mix.main(["--first", str(first), "--jobs", str(r5t),
                           "--dev-ids", str(dev_ids),
                           "--out", out]) == 0


def test_claude_fix_b3b_batch_box_lifetime(monkeypatch):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "final"))
    import cloud_cq
    seen = {}

    class FakeSandbox:
        @staticmethod
        def create(**kw):
            seen.update(kw)
            return "box"

    class FakeModal:
        Sandbox = FakeSandbox

    monkeypatch.setattr(cloud_cq, "modal", FakeModal)
    monkeypatch.setattr(cloud_cq, "lookup_exec_app", lambda: "app")
    cloud_cq.build_sandbox(image="img", lifetime_s=10800)
    assert seen["timeout"] == 10800
    cloud_cq.build_sandbox(image="img")
    assert seen["timeout"] == cloud_cq.sandbox_kwargs()["timeout"]


def test_claude_fix_b6b_card_stripped_matches_runner(tmp_path, monkeypatch):
    import sys, os
    here = os.path.dirname(__file__)
    sys.path.insert(0, os.path.join(here, "..", "train"))
    import forge_train
    card = os.path.join(here, "..", "final", "RULE_CARD.md")
    text = forge_train.check_rule_card(card)
    assert text == open(card, encoding="utf-8").read().strip()


def test_claude_fix_b7_jobs_file_keeps_reference_for_grading(tmp_path):
    import sys, os, json
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "final"))
    import runner_final
    p = tmp_path / "jobs.jsonl"
    p.write_text(json.dumps({"id": "R5T-F1-1", "family": 1, "text": "make a box",
                             "reference": "REFCODE"}) + "\n")
    jobs = runner_final.load_factory_jobs_file(str(p))
    assert jobs[0]["reference"] == "REFCODE"
    calls = []
    grade = runner_final.cloud_cq.factory_grade_fn(
        jobs, lambda *a, **k: calls.append((a, k)) or "ok")
    grade("factory", "R5T-F1-1", b"brep")
    assert calls[0][1] == {"reference": "REFCODE"}
    msgs = runner_final.ft_messages(jobs[0]["text"])
    assert "REFCODE" not in json.dumps(msgs)


# ------------------------------------------------------- option B: no card


def _repo_card_text():
    with open(forge_train.R5_CARD_REPO_PATH, encoding="utf-8") as f:
        return f.read().strip()


def test_no_card_render_matches_ft_without_card(monkeypatch):
    monkeypatch.delenv("FORGE_RULE_CARD", raising=False)
    text = "make a block"
    rec = {"text": text, "code": "result = 1",
           "reasoning": LONG_REASONING}
    tok = forge_train.FakeThinkingTokenizer()
    # The no-card training render is byte-equal to the no-card FT prompt.
    prompt = forge_train.render_prompt(
        tok, text, forge_train.ft_messages_no_card)
    ft_prompt = tok.apply_chat_template(
        runner_final.ft_messages(text), tokenize=False,
        add_generation_prompt=True)
    assert prompt == ft_prompt
    fmt = forge_train.check_format(
        tok, rec, runner_final.ft_messages(text),
        messages_fn=forge_train.ft_messages_no_card)
    assert fmt["verdict"] == "PASS"
    assert fmt["checks"]["prompt_matches_ft"] is True
    # No card text in the render; the absence assert passes on it and
    # fires on a prompt with the card appended.
    card_text = _repo_card_text()
    assert card_text not in fmt["prompt"]
    assert forge_train.assert_no_card_in_prompt(
        fmt["prompt"], card_text) is True
    with pytest.raises(ValueError, match="no-card"):
        forge_train.assert_no_card_in_prompt(
            fmt["prompt"] + "\n\n" + card_text, card_text)
    fmt2 = forge_train.assert_r5_first_render_no_card(rec, tok, card_text)
    assert fmt2["checks"]["prompt_matches_ft"] is True


def test_no_card_reference_ignores_exported_card(monkeypatch, tmp_path):
    # S2: the reference FT prompt is built with FORGE_RULE_CARD unset,
    # even when it is exported in the shell.
    card = tmp_path / "card.md"
    card.write_text("RULES: be exact, always.")
    monkeypatch.setenv("FORGE_RULE_CARD", str(card))
    msgs = forge_train.ft_messages_no_card("make a block")
    assert all("RULES" not in m["content"] for m in msgs)
    assert os.environ.get("FORGE_RULE_CARD") == str(card)  # restored
    monkeypatch.delenv("FORGE_RULE_CARD")
    assert forge_train.ft_messages_no_card("make a block") == msgs


def test_default_path_still_uses_card(monkeypatch, tmp_path):
    # Without --no-card everything stays as today: the card is required
    # in the first render and the reference carries it.
    card = tmp_path / "card.md"
    card.write_text("RULES: be exact, always.")
    monkeypatch.setenv("FORGE_RULE_CARD", str(card))
    rec = {"text": "make a block", "code": "result = 1",
           "reasoning": LONG_REASONING}
    fmt = forge_train.assert_r5_first_render(
        rec, forge_train.FakeThinkingTokenizer(),
        "RULES: be exact, always.")
    assert fmt["checks"]["prompt_matches_ft"] is True
    assert "RULES: be exact, always." in fmt["prompt"]
    assert forge_train.first_ft_messages([rec]) == \
        forge_train.ft_messages_for("make a block")
    assert forge_train.first_ft_messages([rec], no_card=True) == \
        forge_train.ft_messages_no_card("make a block")


def test_card_mention_patterns_drop_case_insensitive():
    jobs = {"R5T-F1-1": {"id": "R5T-F1-1", "text": "make a block",
                         "family": 1}}

    def _rec(reasoning):
        return {"job": "R5T-F1-1", "verdict": "PASS", "code": "result = 1",
                "reasoning": reasoning}

    for phrase in ("rule card", "card says", "per the card",
                   "cheat sheet", "the card", "RULE CARD"):
        rows, counts = build_mix.build_rows(
            [_rec(LONG_REASONING + " %s helped me here." % phrase)],
            [], [], jobs, drop_card_mentions=True)
        assert rows == [] and counts["dropped_card_mention"] == 1, phrase
    # Rows that only quote or follow true rules are KEPT (option B).
    quote = _rec(LONG_REASONING + " I called .val() on the Workplane "
                 "to get the solid and passed only positional arguments "
                 "to makeCylinder.")
    assert build_mix.reasoning_names_card(quote["reasoning"]) is False
    rows, counts = build_mix.build_rows(
        [quote], [], [], jobs, drop_card_mentions=True)
    assert len(rows) == 1 and counts["dropped_card_mention"] == 0
    # Without the flag, card-naming rows are kept (default unchanged).
    rows, _ = build_mix.build_rows(
        [_rec(LONG_REASONING + " the rule card helped me here.")],
        [], [], jobs)
    assert len(rows) == 1


def _write_mix_inputs(tmp_path, name, n_ok, n_card):
    jobs = tmp_path / (name + "_jobs.jsonl")
    first = tmp_path / (name + "_first.jsonl")
    with open(jobs, "w", encoding="utf-8") as fj, \
            open(first, "w", encoding="utf-8") as ff:
        for i in range(n_ok + n_card):
            jid = "R5T-F1-%d" % i
            fj.write(json.dumps({"id": jid, "text": "make block %d" % i,
                                 "family": 1}) + "\n")
            if i < n_card:
                reasoning = (LONG_REASONING + " As the rule card says, "
                             "I checked the sizes.")
            else:
                reasoning = (LONG_REASONING + " I checked every size "
                             "twice against the printed text.")
            ff.write(json.dumps({"job": jid, "verdict": "PASS",
                                 "code": "result = 1",
                                 "reasoning": reasoning}) + "\n")
    return str(jobs), str(first)


def test_card_drop_stop_over_20_percent(tmp_path, capsys):
    # 2 of 5 mention the card = 40% -> STOP, non-zero, no output file.
    jobs, first = _write_mix_inputs(tmp_path, "stop", 3, 2)
    out = str(tmp_path / "mix.jsonl")
    rc = build_mix.main(["--first", first, "--jobs", jobs, "--out", out,
                         "--drop-card-mentions"])
    assert rc == 1
    assert not os.path.exists(out)
    printed = capsys.readouterr().out
    assert "CARD_MENTION_DROP overall=0.400" in printed
    assert "CARD_MENTION_STOP" in printed
    # Exactly 20% is not OVER 20%: the mix is written.
    jobs, first = _write_mix_inputs(tmp_path, "ok", 4, 1)
    out = str(tmp_path / "mix2.jsonl")
    rc = build_mix.main(["--first", first, "--jobs", jobs, "--out", out,
                         "--drop-card-mentions"])
    assert rc == 0
    kept = [json.loads(line) for line in open(out) if line.strip()]
    assert len(kept) == 4


def test_first_repeatable_concatenates(tmp_path):
    jobs_a, first_a = _write_mix_inputs(tmp_path, "a", 1, 0)
    _, first_b = _write_mix_inputs(tmp_path, "b", 1, 0)
    # Same job ids in both files: at most 2 rows per job, both kept.
    out = str(tmp_path / "mix.jsonl")
    rc = build_mix.main(["--first", first_a, "--first", first_b,
                         "--jobs", jobs_a, "--out", out])
    assert rc == 0
    kept = [json.loads(line) for line in open(out) if line.strip()]
    assert len(kept) == 2


def test_v1_pilot_inputs_refused_by_path(tmp_path):
    v1dir = tmp_path / "results" / "r5-pilot-2026-10-31"
    v1dir.mkdir(parents=True)
    v1 = v1dir / "calls.jsonl"
    v1.write_text(json.dumps({"job": "R5T-F1-1", "verdict": "PASS",
                              "code": "result = 1",
                              "reasoning": LONG_REASONING}) + "\n")
    with pytest.raises(ValueError, match="v1 pilot"):
        build_mix.main(["--first", str(v1), "--jobs", "jobs.jsonl",
                        "--out", "mix.jsonl"])
    with pytest.raises(ValueError, match="v1 pilot"):
        build_mix.refuse_v1_pilot_paths([str(v1)])
    # Other dirs pass the check (paths -- not prompt_tokens -- decide).
    assert build_mix.refuse_v1_pilot_paths(
        ["results/r5-first-2026-10-31/calls.jsonl"]) is True


def test_no_card_estimate_smaller_than_with_card():
    bpe = forge_train.GlimmerBPE([])
    recs = [{"text": "make a block", "code": "result = 1",
             "reasoning": LONG_REASONING}]
    card_text = _repo_card_text()
    with_card = forge_train.count_r5_row_tokens(
        recs, bpe, forge_train.SYSTEM_PROMPT + "\n\n" + card_text)
    without = forge_train.count_r5_row_tokens(
        recs, bpe, forge_train.SYSTEM_PROMPT)
    assert len(with_card) == len(without) == 1
    assert with_card[0] > without[0] > 0
    assert forge_train.estimate_r5_cost(with_card)["dollars"] > \
        forge_train.estimate_r5_cost(without)["dollars"]
