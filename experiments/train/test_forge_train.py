"""Offline tests for experiments/train/forge_train.py (no GPU, no network)."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import forge_train

FT = os.path.join(os.path.dirname(HERE), "first-test")
if FT not in sys.path:
    sys.path.insert(0, FT)
import runner


class FakeTok:
    """Minimal tokenizer with a chat template (word tokens)."""

    eos_token = ""

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=False):
        text = "".join(
            "[%s]%s[/%s]" % (m["role"], m["content"], m["role"]) for m in msgs
        )
        if add_generation_prompt:
            text += "[assistant]"
        return text

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


class SkewTok(FakeTok):
    """Template that renders history differently, forcing the fallback."""

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=False):
        if add_generation_prompt:
            return "PROMPT>" + msgs[-1]["content"]
        return "FULL>" + " | ".join(m["content"] for m in msgs)


def test_system_prompt_matches_first_test():
    assert forge_train.SYSTEM_PROMPT == runner.SYSTEM_PROMPT


def test_labels_masked_before_answer():
    tok = FakeTok()
    enc = forge_train.encode_example(tok, "make a box", "result = 1")
    assert not enc["dropped"]
    prompt, full = forge_train.render_full(tok, "make a box", "result = 1")
    n_prompt = len(tok(prompt)["input_ids"])
    assert enc["input_ids"] == tok(full)["input_ids"]
    assert enc["labels"][:n_prompt] == [-100] * n_prompt
    assert enc["labels"][n_prompt:] == enc["input_ids"][n_prompt:]
    assert any(v != -100 for v in enc["labels"])  # answer part really trained


def test_fallback_render_when_template_skews_history():
    tok = SkewTok()
    prompt, full = forge_train.render_full(tok, "make a box", "result = 1")
    assert full.startswith(prompt)  # fallback = prompt + answer
    enc = forge_train.encode_example(tok, "make a box", "result = 1")
    assert not enc["dropped"]
    n_prompt = len(tok(prompt)["input_ids"])
    assert enc["labels"][:n_prompt] == [-100] * n_prompt


def test_long_examples_dropped_and_counted():
    tok = FakeTok()
    short = {"text": "box", "code": "result = 1"}
    long = {"text": "big " * 200, "code": "result = 1"}
    enc = forge_train.encode_example(tok, long["text"], long["code"], max_tokens=50)
    assert enc["dropped"] and enc["tokens"] > 50
    kept, dropped = forge_train.filter_batch(tok, [short, long, short], max_tokens=50)
    assert len(kept) == 2 and dropped == 1


def test_cap_timeout_math():
    assert forge_train.seconds_for_dollars(3.95, 3.95) == pytest.approx(3600.0)
    assert forge_train.dollars_for_seconds(3600.0, 2.50) == pytest.approx(2.50)
    plan = forge_train.plan_timeouts(
        3.0, [("train", 3.95, 600), ("serve", 2.50, 600)]
    )
    assert plan["train"] == 600 and plan["serve"] == 600
    assert plan["_left"] == pytest.approx(
        3.0 - forge_train.dollars_for_seconds(600, 3.95)
        - forge_train.dollars_for_seconds(600, 2.50),
        abs=0.01,  # plan rounds money left to cents
    )


def test_cap_refuses_step_that_does_not_fit():
    with pytest.raises(forge_train.CapExceeded):
        forge_train.plan_timeouts(0.01, [("train", 3.95, 600)])
    # First step fits, second does not: the second is refused.
    with pytest.raises(forge_train.CapExceeded):
        forge_train.plan_timeouts(0.10, [("train", 3.95, 60), ("merge", 3.95, 600)])


def test_smoke_entrypoint_refuses_tiny_cap_offline():
    assert forge_train.main(["smoke", "--cap-dollars", "0.01"]) == 2


def test_smoke_cap_2_refused_without_any_remote_call(monkeypatch, capsys):
    """Round 2 item 1: `smoke --cap-dollars 2.0` is CAP REFUSED before Modal.

    With the 300 s startup allowance the minimum total cap is ~$2.89, so
    $2.0 must refuse. Every remote path raises if touched, so a wrong cap
    check would fail the test instead of starting a paid H100 job.
    """
    import modal

    def _boom(*args, **kwargs):
        raise AssertionError("a remote call was attempted")

    monkeypatch.setattr(modal, "enable_output", _boom)
    monkeypatch.setattr(forge_train.app, "run", _boom)
    for fn in (forge_train.train, forge_train.merge,
               forge_train.serve_merged):
        monkeypatch.setattr(fn, "remote", _boom)
    assert forge_train.main(["smoke", "--cap-dollars", "2.0"]) == 2
    assert "CAP REFUSED" in capsys.readouterr().out


def test_startup_allowance_is_300s():
    """Round 2 item 2: STARTUP_TIMEOUT_S = 300, so a $3 cap still trains."""
    assert forge_train.STARTUP_TIMEOUT_S == 300
    with pytest.raises(forge_train.CapExceeded):
        forge_train.split_cap(2.0)  # under the ~$2.89 minimum: refuse
    split = forge_train.split_cap(3.0)  # $3 still buys >= 15 min of train
    assert split["train"] >= 15 * 60


def test_guard_fails_closed_when_references_unbuildable(monkeypatch):
    """Round 2 item 3: an unbuildable exam reference raises, never passes."""
    def _broken():
        raise RuntimeError("no cadquery here")
    monkeypatch.setattr(forge_train, "build_exam_shapes", _broken)
    with pytest.raises(RuntimeError):
        forge_train.guard_records([{"text": "a widget", "code": "result = 1"}])


def test_serve_wait_and_prompt_fit_inside_timeout():
    """Round 2 item 4: ready wait (<= 3 min) + one prompt fit the timeout."""
    assert forge_train.SERVE_REQUEST_TIMEOUT_S <= 120
    assert (forge_train.SERVE_READY_S + forge_train.SERVE_REQUEST_TIMEOUT_S
            <= forge_train.SERVE_RESERVE_S)
    src = open(os.path.join(HERE, "forge_train.py"), encoding="utf-8").read()
    assert "8 * 60" not in src  # no 8-minute ready wait anymore
    assert "SERVE_REQUEST_TIMEOUT_S" in src


def test_never_modal_run_docstring():
    """Round 2 item 5: the never-modal-run warning is in the docstring."""
    assert "`modal run forge_train.py::train`" in forge_train.__doc__
    assert "bypasses the exam guard" in forge_train.__doc__


def test_schedule_counts_micro_and_optimizer_steps():
    s = forge_train.plan_optimizer_steps(400, 2, 8)
    assert s["optimizer_steps"] == 100  # ceil(800 / 8)
    assert s["micro_steps"] == 800  # every micro-step is used
    assert s["groups"] == [8] * 100
    s = forge_train.plan_optimizer_steps(16, 1, 8)
    assert s["optimizer_steps"] == 2 and s["micro_steps"] == 16
    s = forge_train.plan_optimizer_steps(8, 2, 1, max_steps=10)
    assert s["optimizer_steps"] == 10 and s["micro_steps"] == 10


def test_schedule_leftover_partial_group():
    s = forge_train.plan_optimizer_steps(10, 1, 8)
    assert s["groups"] == [8, 2]  # full groups + one partial group
    assert s["optimizer_steps"] == 2 and s["micro_steps"] == 10
    s = forge_train.plan_optimizer_steps(10, 1, 8, max_steps=1)
    assert s["optimizer_steps"] == 1 and s["micro_steps"] == 8


def test_loader_accepts_jsonl_and_json_array(tmp_path):
    recs = [{"text": "make a box", "code": "result = 1"},
            {"text": "make a tube", "code": "result = 2"}]
    jl = tmp_path / "data.jsonl"
    jl.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                  encoding="utf-8")
    assert forge_train.load_training_records(str(jl)) == recs
    ja = tmp_path / "data.json"
    ja.write_text(json.dumps(recs), encoding="utf-8")
    assert forge_train.load_training_records(str(ja)) == recs
    # The smoke examples file is a JSON array and loads with the same loader.
    smoke = forge_train.load_training_records(forge_train.SMOKE_EXAMPLES)
    assert len(smoke) > 0 and all(r["text"] and r["code"] for r in smoke)


def test_loader_rejects_records_without_text_and_code(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"text": "no code here"}) + "\n",
                   encoding="utf-8")
    with pytest.raises(ValueError):
        forge_train.load_training_records(str(bad))


FAKE_EXAM = [
    "A spacer block. Block: X from 0 to 30, Y from 0 to 20, Z from 0 to 10. "
    "A 6 mm hole goes through it along the Z axis.",
]


def test_guard_refuses_exact_text_warns_on_restructured(tmp_path):
    verdict, _ = forge_train.check_text_record(FAKE_EXAM[0], FAKE_EXAM)
    assert verdict == "refuse"  # exact-number ratio 1.0 >= 0.9
    paraphrase = (
        "A mounting plate. Plate: X from 0 to 300, Y from 0 to 200, "
        "Z from 0 to 100. A 60 mm hole goes through it along the Z axis.")
    verdict, detail = forge_train.check_text_record(paraphrase, FAKE_EXAM)
    assert verdict == "warn"  # collapsed >= 0.8, exact < 0.9
    assert detail["collapsed_ratio"] >= 0.8 and detail["exact_ratio"] < 0.9
    verdict, _ = forge_train.check_text_record(
        "A plus-shaped spacer with crossing bars and a centre hole.",
        FAKE_EXAM)
    assert verdict == "ok"


def test_guard_code_match_prefilter_then_full_score():
    ref = {"bbox": [0, 0, 0, 10, 10, 10], "volume": 1000.0}
    same = {"bbox": [0, 0, 0, 10, 10, 10], "volume": 1000.0}
    assert forge_train.measurements_match(same, ref)  # 1e-6 prefilter hit
    other = {"bbox": [0, 0, 0, 10, 10, 11], "volume": 1100.0}
    assert not forge_train.measurements_match(other, ref)
    matched, idx = forge_train.code_matches_exam(same, [other, ref])
    assert matched and idx == 1
    matched, _ = forge_train.code_matches_exam(other, [ref])
    assert not matched
    # The full score runs only on a prefilter hit: it can still clear.
    calls = []
    def scorer(t, r):
        calls.append((t, r))
        return False
    matched, _ = forge_train.code_matches_exam(same, [ref], scorer)
    assert not matched and len(calls) == 1
    matched, _ = forge_train.code_matches_exam(other, [ref], scorer)
    assert not matched and len(calls) == 1  # no full score without a hit


def test_guard_drops_refused_and_aborts_over_five_percent():
    recs = [{"text": "job %d, a small bracket" % i, "code": "result = %d" % i}
            for i in range(20)]
    kept, refused, report = forge_train.guard_records(
        recs, exam_texts=FAKE_EXAM, ref_meases=[])
    assert report["n_refused"] == 0 and len(kept) == 20
    assert report["aborted"] is False
    # One exact copy out of 21 (< 5%) is dropped without aborting.
    recs2 = list(recs) + [{"text": FAKE_EXAM[0], "code": "result = 0"}]
    kept, refused, report = forge_train.guard_records(
        recs2, exam_texts=FAKE_EXAM, ref_meases=[])
    assert len(kept) == 20 and report["n_refused_text"] == 1
    assert report["aborted"] is False  # 1/21 <= 5%
    # Two copies out of 21 cross 5%: abort.
    recs3 = recs2 + [{"text": FAKE_EXAM[0], "code": "result = 1"}]
    kept, refused, report = forge_train.guard_records(
        recs3, exam_texts=FAKE_EXAM, ref_meases=[])
    assert report["aborted"] is True and report["n_refused"] == 2


def test_guard_code_refusal_with_fake_shapes():
    ref = {"bbox": [0, 0, 0, 10, 10, 10], "volume": 1000.0}
    recs = [{"text": "an unrelated widget", "code": "CODE-A"},
            {"text": "another unrelated widget", "code": "CODE-B"}]
    def fake_meas(code):
        return dict(ref) if code == "CODE-B" else {
            "bbox": [0, 0, 0, 1, 1, 1], "volume": 1.0}
    kept, refused, report = forge_train.guard_records(
        recs, exam_texts=["something entirely different"], ref_meases=[ref],
        train_meas_fn=fake_meas)
    assert refused == [1] and len(kept) == 1
    assert report["n_refused_code"] == 1


def test_guard_report_holds_counts_only(tmp_path):
    recs = [{"text": FAKE_EXAM[0], "code": "result = 0"},
            {"text": "an unrelated widget", "code": "result = 1"}]
    res = tmp_path / "train-x"
    res.mkdir()
    with pytest.raises(forge_train.ExamRefused):
        forge_train.guard_or_abort(recs, str(res), exam_texts=FAKE_EXAM,
                                   ref_meases=[])  # 1/2 refused: abort
    saved = json.loads((res / "exam_guard.json").read_text(encoding="utf-8"))
    assert set(saved) == {"n_records", "n_refused_text", "n_warned_text",
                          "n_refused_code", "n_refused", "n_kept",
                          "refused_frac", "aborted"}
    assert saved["n_refused"] == 1 and saved["aborted"] is True


def test_cap_includes_startup_and_spent():
    plan = forge_train.plan_timeouts(
        1.50, [("train", 3.95, 300), ("serve", 2.50, 60)],
        startup_s=600)
    cost = forge_train.worst_case_cost(
        plan, {"train": 3.95, "serve": 2.50}, startup_s=600)
    assert cost <= 1.50  # (startup + timeout) x rate stays in the cap
    with pytest.raises(forge_train.CapExceeded):
        forge_train.plan_timeouts(1.50, [("train", 3.95, 300)], startup_s=600,
                                  spent_dollars=1.00)


def test_split_cap_reserves_merge_serve_first():
    split = forge_train.split_cap(6.0)
    assert split["merge"] == 12 * 60 and split["serve"] == 6 * 60
    assert split["train"] >= 15 * 60  # the rest goes to train
    cost = (forge_train.dollars_for_seconds(split["startup_s"] + split["train"],
                                            forge_train.H100_RATE)
            + forge_train.dollars_for_seconds(split["startup_s"] + split["merge"],
                                              forge_train.H100_RATE)
            + forge_train.dollars_for_seconds(split["startup_s"] + split["serve"],
                                              forge_train.A100_RATE))
    assert cost <= 6.0
    with pytest.raises(forge_train.CapExceeded):
        forge_train.split_cap(1.50)  # train would get under 15 min: refuse
    with pytest.raises(forge_train.CapExceeded):
        forge_train.split_cap(6.0, spent_dollars=5.0)  # earlier spend counts


def test_deadline_margin_and_stage_threshold():
    assert forge_train.DEADLINE_MARGIN_S == 240  # timeout minus 240 s
    small = [{"text": "t", "code": "c"}]
    assert forge_train.data_needs_volume_stage(small) is False
    assert forge_train.stage_data(small, "x") == small  # inline records
    big = [{"text": "t " * 1000, "code": "c " * 1000}] * 2000
    assert forge_train.data_needs_volume_stage(big) is True


def test_real_exam_texts_count():
    assert len(forge_train.exam_job_texts()) == 33  # first-test jobs


def test_serve_is_a_one_prompt_format_check():
    src = open(os.path.join(HERE, "forge_train.py"), encoding="utf-8").read()
    assert "SERVE_READY_S" in src and "[:1]" in src  # at most one prompt
    assert forge_train.SERVE_READY_S <= 3 * 60


def test_returns_are_plain_json():
    out = forge_train.ensure_plain_json(
        {"params": {1, 2}, "when": (1, 2), "nested": [{"x": frozenset((3,))}]}
    )
    json.dumps(out)  # must serialize without a custom default
    assert isinstance(out, dict)
    for v in out.values():
        assert isinstance(v, (dict, list, str, int, float, bool, type(None)))


def test_train_code_runs_in_box_measured_grader_side():
    """MUSE_SPEC section 4: the training record's code runs in cloud_cq's
    box (fake here), measured grader-side; no BREP means no measurement.
    """
    meas = {"bbox": [0, 0, 0, 10, 10, 10], "volume": 1000.0}
    old = forge_train.set_box_fns(
        exec_fn=lambda code: {"brep_bytes": b"BREP:" + code.encode(),
                              "measure": None, "log": "",
                              "run_error": None},
        measure_fn=lambda brep: dict(meas))
    try:
        brep, err = forge_train.run_train_code("CODE-A")
        assert brep == b"BREP:CODE-A" and err is None
        assert forge_train.default_train_meas("CODE-A") == meas
        old2 = forge_train.set_box_fns(
            exec_fn=lambda code: {"brep_bytes": None, "measure": None,
                                  "log": "",
                                  "run_error": "the answer wrote no BREP"},
            measure_fn=lambda brep: (_ for _ in ()).throw(
                AssertionError("grader must not run without a BREP")))
        try:
            brep, err = forge_train.run_train_code("CODE-B")
            assert brep is None and "no BREP" in err
            assert forge_train.default_train_meas("CODE-B") is None
        finally:
            forge_train.set_box_fns(*old2)
    finally:
        forge_train.set_box_fns(*old)


def test_default_box_measure_runs_inside_cloud_cq_app(monkeypatch):
    """F1: the exam guard's measure call runs inside cloud_cq._app.run()
    (forge_train's own app.run is a different App). A fake app carries
    an "entered" flag; the real-path measure call outside the context
    fails like Modal's "Function has not been hydrated"."""
    import types

    state = {"entered": False, "outputs": 0, "runs": 0,
             "forge_runs": 0}

    class _Ctx:
        def __init__(self, flag):
            self._flag = flag

        def __enter__(self):
            self._flag[0] = True

        def __exit__(self, *args):
            self._flag[0] = False
            return False

    entered = [False]

    class _Modal:
        @staticmethod
        def enable_output():
            state["outputs"] += 1
            return _Ctx([False])

    class _CloudApp:
        def run(self):
            state["runs"] += 1
            return _Ctx(entered)

    class _Measure:
        def remote(self, brep_bytes):
            if not entered[0]:
                raise RuntimeError("Function has not been hydrated")
            return {"volume": 1.0, "brep_len": len(brep_bytes)}

    fake_cq = types.SimpleNamespace(modal=_Modal(), _app=_CloudApp(),
                                    measure_brep=_Measure())
    monkeypatch.setattr(forge_train, "_final_cq", lambda: fake_cq)
    # Outside the context the real path fails, like unhydrated Modal.
    with pytest.raises(RuntimeError, match="has not been hydrated"):
        fake_cq.measure_brep.remote(b"B")
    # The guard's hook enters cloud_cq's app run itself.
    assert forge_train.default_box_measure(b"BREP!") == {
        "volume": 1.0, "brep_len": 5}
    assert state["runs"] == 1 and state["outputs"] == 1
    if getattr(forge_train, "app", None) is not None:
        assert forge_train.app is not fake_cq._app  # a different App


def test_guard_uses_box_measure_for_code_side():
    """The guard's code side refuses a training part whose box-measured
    part matches an exam reference (fake box, fake refs)."""
    ref = {"bbox": [0, 0, 0, 10, 10, 10], "volume": 1000.0}
    old = forge_train.set_box_fns(
        exec_fn=lambda code: {"brep_bytes": b"B", "measure": None,
                              "log": "", "run_error": None},
        measure_fn=lambda brep: dict(ref))
    try:
        recs = [{"text": "an unrelated widget", "code": "CODE-A"}]
        kept, refused, report = forge_train.guard_records(
            recs, exam_texts=["something entirely different"],
            ref_meases=[dict(ref)])
        assert refused == [0] and kept == []
        assert report["n_refused_code"] == 1
    finally:
        forge_train.set_box_fns(*old)


def test_guard_opens_cloud_cq_app_once_for_whole_pass(monkeypatch):
    """The guard holds cloud_cq._app.run() once for the whole pass,
    not once per record (slow). Three records, one app run."""
    import types

    state = {"entered": False, "outputs": 0, "runs": 0}

    class _Ctx:
        def __init__(self, flag):
            self._flag = flag

        def __enter__(self):
            self._flag[0] = True

        def __exit__(self, *args):
            self._flag[0] = False
            return False

    entered = [False]

    class _Modal:
        @staticmethod
        def enable_output():
            state["outputs"] += 1
            return _Ctx([False])

    class _CloudApp:
        def run(self):
            state["runs"] += 1
            return _Ctx(entered)

    class _Measure:
        def remote(self, brep_bytes):
            if not entered[0]:
                raise RuntimeError("Function has not been hydrated")
            return {"bbox": [0, 0, 0, 1, 1, 1], "volume": 1.0}

    fake_cq = types.SimpleNamespace(
        modal=_Modal(), _app=_CloudApp(), measure_brep=_Measure(),
        run_answer_in_box=lambda code: {"brep_bytes": b"B",
                                        "measure": None, "log": "",
                                        "run_error": None})
    monkeypatch.setattr(forge_train, "_final_cq", lambda: fake_cq)
    old_exec, old_measure = (forge_train._box_exec_fn,
                             forge_train._box_measure_fn)
    forge_train._box_exec_fn = None
    forge_train._box_measure_fn = None
    try:
        recs = [{"text": "an unrelated widget %d" % i, "code": "CODE"}
                for i in range(3)]
        kept, refused, _report = forge_train.guard_records(
            recs, exam_texts=["something entirely different"],
            ref_meases=[{"bbox": [0, 0, 0, 10, 10, 10],
                         "volume": 1000.0}])
        assert len(kept) == 3 and refused == []  # no code match
        assert state["runs"] == 1 and state["outputs"] == 1
        assert forge_train._GUARD_CTX_DEPTH == 0  # released
    finally:
        forge_train._box_exec_fn = old_exec
        forge_train._box_measure_fn = old_measure
