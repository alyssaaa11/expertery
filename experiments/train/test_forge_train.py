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

    With the 300 s startup allowance the minimum total cap is ~$3.10
    (round 3: train on H200), so $2.0 must refuse. Every remote path
    raises if touched, so a wrong cap check would fail the test instead
    of starting a paid GPU job.
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
    """Round 2 item 2: STARTUP_TIMEOUT_S = 300. Round 3: train runs on
    H200 ($4.54/h), so the minimum cap moves to ~$3.10."""
    assert forge_train.STARTUP_TIMEOUT_S == 300
    assert forge_train.H200_RATE == 4.54
    with pytest.raises(forge_train.CapExceeded):
        forge_train.split_cap(2.0)  # under the ~$3.10 minimum: refuse
    with pytest.raises(forge_train.CapExceeded):
        forge_train.split_cap(3.0)  # H200: no longer 15 min of train
    split = forge_train.split_cap(3.5)  # $3.5 still buys >= 15 min
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


def _write_calls(run_dir, calls):
    """Fake sibling calls.jsonl: [(id, teacher, verdict)]."""
    run_dir.mkdir(exist_ok=True)
    (run_dir / "calls.jsonl").write_text(
        "\n".join(json.dumps({"id": i, "teacher": t, "verdict": v})
                   for i, t, v in calls) + "\n",
        encoding="utf-8")


def test_loader_accepts_jsonl_and_json_array(tmp_path, capsys):
    # E3 (round 2b): records still need the calls.jsonl cross-check: a
    # sibling calls.jsonl with a Spark PASS for each id keeps them.
    run_dir = tmp_path / "run"
    _write_calls(run_dir, [("a", "spark", "PASS"), ("b", "spark", "PASS")])
    recs = [{"id": "a", "text": "make a box", "code": "result = 1",
             "teacher": "spark"},
            {"id": "b", "text": "make a tube", "code": "result = 2",
             "teacher": "spark"}]
    jl = run_dir / "data.jsonl"
    jl.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                  encoding="utf-8")
    assert forge_train.load_training_records(str(jl)) == recs
    ja = run_dir / "data.json"
    ja.write_text(json.dumps(recs), encoding="utf-8")
    assert forge_train.load_training_records(str(ja)) == recs
    out = capsys.readouterr().out
    assert "CALLS_FILTER" in out and "kept=2" in out


def test_smoke_examples_exempt_from_both_rules():
    """B1 (round 2b): the trusted smoke examples (SMOKE_EXAMPLES, the
    file run_smoke loads) are exempt by explicit path from BOTH the
    calls.jsonl rule and the teacher-field rule: they carry no teacher
    tag and sit next to no calls.jsonl, yet they all load."""
    smoke = forge_train.load_training_records(forge_train.SMOKE_EXAMPLES)
    assert len(smoke) > 0  # today a real smoke run keeps 0 records
    assert all(r.get("text") and r.get("code") for r in smoke)


def test_loader_rejects_records_without_text_and_code(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"text": "no code here"}) + "\n",
                   encoding="utf-8")
    with pytest.raises(ValueError):
        forge_train.load_training_records(str(bad))


def test_loader_drops_non_spark_teacher_and_counts(tmp_path, capsys):
    """E3 (user, 2026-10-30): any record whose teacher is not spark is
    dropped and counted in the log."""
    run_dir = tmp_path / "run"
    _write_calls(run_dir, [("s", "spark", "PASS")])
    recs = [
        {"id": "s", "text": "spark box", "code": "result = 1",
         "teacher": "spark"},
        {"id": "w", "text": "wonder box", "code": "result = 2",
         "teacher": "wonder"},
        {"id": "h", "text": "human box", "code": "result = 3",
         "teacher": "human"},
    ]
    path = run_dir / "mixed.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                    encoding="utf-8")
    kept = forge_train.load_training_records(str(path))
    assert [r["text"] for r in kept] == ["spark box"]
    out = capsys.readouterr().out
    assert "TEACHER_FILTER" in out and "kept=1" in out
    assert "dropped_non_spark=2" in out


def test_loader_keeps_only_spark_pass_ids(tmp_path, capsys):
    """E3 (round 2b): the calls.jsonl cross-check keeps only ids with
    a PASS call whose teacher == "spark": a Spark FAIL, a Wonder PASS
    and an id with no call at all are dropped, and both id lists print."""
    run_dir = tmp_path / "run"
    _write_calls(run_dir, [("keep", "spark", "PASS"),
                           ("fail", "spark", "FAIL"),
                           ("wonder", "wonder", "PASS")])
    recs = [{"id": i, "text": "job " + i, "code": "result = 1"}
            for i in ("keep", "fail", "wonder", "ghost")]
    path = run_dir / "train_records.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                    encoding="utf-8")
    kept = forge_train.load_training_records(str(path))
    assert [r["id"] for r in kept] == ["keep"]
    out = capsys.readouterr().out
    assert "CALLS_FILTER" in out and "kept=1" in out
    assert "'keep'" in out  # the kept ids print
    for dropped in ("'fail'", "'wonder'", "'ghost'"):
        assert dropped in out  # the dropped ids print


def test_loader_merged_file_uses_sources_json(tmp_path):
    """E3 (round 2b): a merged file sits next to a sources.json listing
    the run dirs; ids PASSing in any listed run are kept."""
    run_a = tmp_path / "run-a"
    run_b = tmp_path / "run-b"
    _write_calls(run_a, [("F1-1", "spark", "PASS")])
    _write_calls(run_b, [("F2-1", "spark", "PASS")])
    merged_dir = tmp_path / "merged"
    merged_dir.mkdir()
    (merged_dir / "sources.json").write_text(
        json.dumps(["../run-a", "../run-b"]), encoding="utf-8")
    recs = [{"id": i, "text": "job " + i, "code": "result = 1"}
            for i in ("F1-1", "F2-1", "F9-9")]
    merged = merged_dir / "train_merged.jsonl"
    merged.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                      encoding="utf-8")
    kept = forge_train.load_training_records(str(merged))
    assert [r["id"] for r in kept] == ["F1-1", "F2-1"]


def test_loader_refuses_without_calls_or_sources(tmp_path):
    """E3 (round 2b): no sibling calls.jsonl and no sources.json next
    to the file refuses (only the smoke examples are exempt)."""
    lonely = tmp_path / "lonely.jsonl"
    lonely.write_text(json.dumps({"id": "a", "text": "a box",
                                  "code": "result = 1",
                                  "teacher": "spark"}) + "\n",
                      encoding="utf-8")
    with pytest.raises(ValueError, match="no sibling calls.jsonl"):
        forge_train.load_training_records(str(lonely))


def test_loader_refuses_escalated_source_via_sources_json(tmp_path):
    """E3 (round 2b): a merged file whose listed run used --escalate
    (that run's summary.json shows Wonder output) is refused."""
    run_a = tmp_path / "run-a"
    _write_calls(run_a, [("F1-1", "wonder", "PASS")])
    (run_a / "summary.json").write_text(json.dumps(
        {"wonder_share": 1.0, "cost_w_dollars": 0.02}), encoding="utf-8")
    merged_dir = tmp_path / "merged"
    merged_dir.mkdir()
    (merged_dir / "sources.json").write_text(
        json.dumps(["../run-a"]), encoding="utf-8")
    merged = merged_dir / "train_merged.jsonl"
    merged.write_text(json.dumps({"id": "F1-1", "text": "job",
                                  "code": "result = 1"}) + "\n",
                      encoding="utf-8")
    with pytest.raises(ValueError, match="--escalate"):
        forge_train.load_training_records(str(merged))


def test_loader_missing_teacher_verified_via_calls(tmp_path):
    """E3 (round 2b): the file-name rule is gone: a record without the
    teacher field is kept when the calls.jsonl shows a Spark PASS for
    its id, and dropped otherwise."""
    run_dir = tmp_path / "run"
    _write_calls(run_dir, [("a", "spark", "PASS")])
    recs = [{"id": "a", "text": "a box", "code": "result = 1"},
            {"id": "b", "text": "a tube", "code": "result = 2"}]
    factory = run_dir / "train_records.jsonl"
    factory.write_text("\n".join(json.dumps(r) for r in recs) + "\n",
                       encoding="utf-8")
    kept = forge_train.load_training_records(str(factory))
    assert [r["id"] for r in kept] == ["a"]


def test_loader_refuses_escalate_run(tmp_path):
    """E3: a file from a run with --escalate (sibling summary.json with
    Wonder share/cost) is refused entirely, never trained on."""
    run_dir = tmp_path / "factory-escalated"
    run_dir.mkdir()
    train = run_dir / "train_records.jsonl"
    train.write_text(json.dumps({"text": "a box", "code": "result = 1"})
                     + "\n", encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps(
        {"factory_version": "abc", "n_ids": 1, "wonder_share": 0.5,
         "cost_w_dollars": 0.01}), encoding="utf-8")
    with pytest.raises(ValueError, match="--escalate"):
        forge_train.load_training_records(str(train))
    # A Spark-only run's summary is no evidence: it loads (with a
    # sibling calls.jsonl backing the id).
    clean_dir = tmp_path / "factory-clean"
    _write_calls(clean_dir, [("a", "spark", "PASS")])
    clean_train = clean_dir / "train_records.jsonl"
    clean_train.write_text(json.dumps({"id": "a", "text": "a box",
                                       "code": "result = 1"}) + "\n",
                           encoding="utf-8")
    (clean_dir / "summary.json").write_text(json.dumps(
        {"factory_version": "abc", "n_ids": 1, "wonder_share": 0.0,
         "cost_w_dollars": 0.0}), encoding="utf-8")
    kept = forge_train.load_training_records(str(clean_train))
    assert len(kept) == 1


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
    assert split["train"] >= 15 * 60  # the rest goes to train (H200)
    cost = (forge_train.dollars_for_seconds(split["startup_s"] + split["train"],
                                            forge_train.H200_RATE)
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


def test_gpu_stop_and_token_limit_for_h200():
    """Round 3: train on H200 (merge stays H100), stop at 135 GB, and
    keep examples up to 12288 tokens."""
    assert forge_train.GPU_MEM_STOP_GB == 135
    assert forge_train.MAX_TOKENS == 12288
    src = open(os.path.join(HERE, "forge_train.py"), encoding="utf-8").read()
    assert src.count('gpu="H200"') == 1  # train only
    assert src.count('gpu="H100"') == 1  # merge stays as it is


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


# ------------------------------------------------- round 3: thinking + answer

THINK_TOK = forge_train.FakeThinkingTokenizer
REASONING = "try a centred XY box, then cut the hole"
CODE = "result = 1"
TEXT = "make a box"


def test_reasoning_renders_thinking_then_answer_with_loss_on_both():
    tok = THINK_TOK()
    prompt, full = forge_train.render_full(tok, TEXT, CODE, REASONING)
    answer = forge_train.build_answer_text(CODE)
    assert full.startswith(prompt)
    loss_text = full[len(prompt):]
    assert loss_text.index(REASONING) < loss_text.index(answer)
    assert "to=self" in loss_text[:loss_text.index(REASONING)]
    enc = forge_train.encode_example(tok, TEXT, CODE,
                                     reasoning=REASONING)
    assert not enc["dropped"]
    n_prompt = len(tok(prompt)["input_ids"])
    assert enc["labels"][:n_prompt] == [-100] * n_prompt  # prompt masked
    assert enc["labels"][n_prompt:] == enc["input_ids"][n_prompt:]
    assert any(v != -100 for v in enc["labels"])
    # Both turns carry loss: reasoning words and code words are trained.
    loss_words = [tok.decode([i]) for i, lab
                  in zip(enc["input_ids"], enc["labels"]) if lab != -100]
    assert "centred" in loss_words and "result" in loss_words


def test_no_reasoning_renders_byte_equal_to_legacy():
    """A record without reasoning keeps today's exact render."""
    tok = THINK_TOK()
    prompt, full = forge_train.render_full(tok, TEXT, CODE)
    legacy = tok.apply_chat_template(
        forge_train.build_messages(TEXT)
        + [{"role": "assistant",
            "content": forge_train.build_answer_text(CODE)}],
        tokenize=False)
    assert full == legacy
    assert full.startswith(prompt)
    enc = forge_train.encode_example(tok, TEXT, CODE)
    assert not enc["dropped"]


def test_fallback_raises_with_reasoning_never_drops_thinking():
    """H1: a template that renders history differently raises for a
    record with reasoning (the legacy fallback still applies without)."""
    tok = SkewTok()
    with pytest.raises(ValueError):
        forge_train.render_full(tok, TEXT, CODE, "some thinking")
    prompt, full = forge_train.render_full(tok, TEXT, CODE)
    assert full.startswith(prompt)  # legacy fallback unchanged


def test_filter_batch_carries_reasoning():
    tok = THINK_TOK()
    recs = [{"text": TEXT, "code": CODE, "reasoning": REASONING},
            {"text": TEXT, "code": CODE}]
    kept, dropped = forge_train.filter_batch(tok, recs)
    assert dropped == 0 and len(kept) == 2
    assert kept[0]["reasoning"] == REASONING
    assert "reasoning" not in kept[1]


class StripTok(THINK_TOK):
    """A template that strips reasoning from history (the H2 worry):
    the assistant turn renders without the thinking turn."""

    def apply_chat_template(self, msgs, tokenize=False,
                            add_generation_prompt=False):
        plain = [{k: v for k, v in m.items() if k != "reasoning_content"}
                 for m in msgs]
        return super().apply_chat_template(
            plain, tokenize=tokenize,
            add_generation_prompt=add_generation_prompt)


def test_format_check_passes_on_fake_reasoning_record():
    result = forge_train.check_format(THINK_TOK(), {
        "text": TEXT, "code": CODE, "reasoning": REASONING})
    assert result["verdict"] == "PASS"
    assert result["checks"] == {"thinking_first": True,
                                "answer_after_thinking": True,
                                "prompt_matches_ft": True}
    assert result["has_reasoning"] is True
    # (a) the first loss tokens open the thinking turn ...
    assert result["loss_tokens"][0].startswith("to=self")
    assert "to=self" in " ".join(result["loss_tokens"][:5])
    # ... (b) the code turn follows it ...
    joined = " ".join(result["loss_tokens"])
    assert joined.index("centred") < joined.index("result")
    # ... (c) the prompt is byte-equal to what FT sends at serve time,
    # including the template's default reasoning-strength line.
    assert "Reasoning strength: high." in result["prompt"]
    assert result["prompt"] == THINK_TOK().apply_chat_template(
        forge_train.ft_messages_for(TEXT), tokenize=False,
        add_generation_prompt=True)


def test_format_check_fails_when_template_strips_reasoning():
    """H2's case: a template that drops the thinking turn FAILs (a) and
    (b) instead of silently training answer-only."""
    result = forge_train.check_format(StripTok(), {
        "text": TEXT, "code": CODE, "reasoning": REASONING})
    assert result["verdict"] == "FAIL"
    assert result["checks"]["thinking_first"] is False
    assert result["checks"]["prompt_matches_ft"] is True


def test_format_check_fails_on_prompt_mismatch():
    result = forge_train.check_format(
        THINK_TOK(), {"text": TEXT, "code": CODE},
        ft_messages=[{"role": "user", "content": "something else"}])
    assert result["verdict"] == "FAIL"
    assert result["checks"]["prompt_matches_ft"] is False


def test_format_check_cli_fake_prints_text_tokens_and_pass(capsys):
    rc = forge_train.main(["format-check", "--fake"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "FORMAT_FULL " in out and "to=self" in out
    assert "FORMAT_LOSS_TOKENS " in out
    assert "FORMAT_CHECK PASS" in out and "prompt_matches_ft=True" in out


def test_format_check_cli_reads_first_record(tmp_path, capsys):
    path = tmp_path / "recs.jsonl"
    path.write_text(json.dumps({"text": TEXT, "code": CODE}) + "\n",
                    encoding="utf-8")
    rec = forge_train.load_format_record(str(path))
    assert rec == {"text": TEXT, "code": CODE}
    result = forge_train.check_format(THINK_TOK(), rec)
    assert result["verdict"] == "PASS"  # legacy record still passes
    assert result["has_reasoning"] is False


# --------------------------------------- round 3b: the in-train gate aborts

def test_first_format_record_prefers_first_reasoning_record():
    legacy = {"text": TEXT, "code": CODE}
    reasoned = {"text": TEXT, "code": CODE, "reasoning": REASONING}
    assert forge_train.first_format_record([legacy, reasoned]) is reasoned
    assert forge_train.first_format_record([reasoned, legacy]) is reasoned
    assert forge_train.first_format_record([legacy]) is legacy


def test_first_ft_messages_targets_first_reasoning_record():
    legacy = {"text": TEXT, "code": CODE}
    reasoned = {"text": "another job", "code": CODE, "reasoning": REASONING}
    assert (forge_train.first_ft_messages([legacy, reasoned])
            == forge_train.ft_messages_for("another job"))
    assert forge_train.first_ft_messages([]) is None


def _pretraining_gate(tok, examples, ft_messages):
    """Mirror of train()'s pre-training block: check, print, maybe abort."""
    fmt = forge_train.check_format(
        tok, forge_train.first_format_record(examples), ft_messages)
    if forge_train.format_gate_aborts(fmt):
        raise forge_train.FormatRefused(
            "FORMAT_CHECK FAIL %s" % (fmt["checks"],))
    return fmt


def test_failing_render_aborts_before_first_optimizer_step():
    """A fake failing render raises (no optimizer step, no adapter save)."""
    rec = {"text": TEXT, "code": CODE, "reasoning": REASONING}
    with pytest.raises(forge_train.FormatRefused):
        _pretraining_gate(StripTok(), [rec], None)
    fmt = forge_train.check_format(
        StripTok(), forge_train.first_format_record([rec]), None)
    assert fmt["has_reasoning"] is True
    assert forge_train.format_gate_aborts(fmt) is True
    src = open(os.path.join(HERE, "forge_train.py"), encoding="utf-8").read()
    gate_at = src.index("if format_gate_aborts(_fmt):")
    assert gate_at < src.index("opt.step()")  # aborts before any step
    assert gate_at < src.index("save_adapter()")  # no adapter saved
    assert "TRAIN_JSON" in src[gate_at:src.index("raise FormatRefused")] \
        or src.index("TRAIN_JSON", gate_at) < src.index("raise FormatRefused")


def test_passing_render_continues():
    rec = {"text": TEXT, "code": CODE, "reasoning": REASONING}
    fmt = _pretraining_gate(
        THINK_TOK(), [rec], forge_train.ft_messages_for(TEXT))
    assert fmt["verdict"] == "PASS"
    assert forge_train.format_gate_aborts(fmt) is False


def test_legacy_record_without_reasoning_never_aborts():
    """Records without reasoning keep print-and-continue, even on FAIL."""
    fmt = forge_train.check_format(
        THINK_TOK(), {"text": TEXT, "code": CODE},
        ft_messages=[{"role": "user", "content": "something else"}])
    assert fmt["verdict"] == "FAIL"  # prompt mismatch ...
    assert fmt["has_reasoning"] is False
    assert forge_train.format_gate_aborts(fmt) is False  # ... but no abort


# ------------------------------------------------------- R5 B6: card in prompt


def test_r5_render_matches_ft_with_card(tmp_path, monkeypatch):
    card = tmp_path / "card.md"
    card.write_text("RULES: be exact, always.")
    monkeypatch.setenv("FORGE_RULE_CARD", str(card))
    rec = {"text": TEXT, "code": CODE, "reasoning": REASONING}
    tok = THINK_TOK()
    fmt = forge_train.check_format(
        tok, rec, forge_train.ft_messages_for(TEXT),
        forge_train.ft_messages_for)
    assert fmt["verdict"] == "PASS"
    assert fmt["checks"]["prompt_matches_ft"] is True
    assert "RULES: be exact, always." in fmt["prompt"]
    # The legacy short render does NOT match the card-carrying FT arm.
    legacy = forge_train.check_format(tok, rec)
    assert legacy["checks"]["prompt_matches_ft"] is False


def test_assert_r5_first_render_uses_actual_record(tmp_path, monkeypatch):
    card = tmp_path / "card.md"
    card.write_text("RULES: be exact, always.")
    monkeypatch.setenv("FORGE_RULE_CARD", str(card))
    rec = {"text": TEXT, "code": CODE, "reasoning": REASONING}
    fmt = forge_train.assert_r5_first_render(
        rec, THINK_TOK(), "RULES: be exact, always.")
    assert fmt["checks"]["prompt_matches_ft"] is True
    with pytest.raises(ValueError, match="rule card"):
        forge_train.assert_r5_first_render(
            rec, THINK_TOK(), "SOME OTHER CARD")


def test_training_image_bakes_the_card():
    files = forge_train.training_image_local_files()
    assert files == [(forge_train.R5_CARD_REPO_PATH,
                      forge_train.RULE_CARD_BAKED_PATH)]
    assert forge_train.RULE_CARD_BAKED_PATH == "/training/rule_card.md"
    assert forge_train.sha256_of_file(
        forge_train.R5_CARD_REPO_PATH) == forge_train.RULE_CARD_SHA256


# ------------------------------------------------------- R5 N1: token estimate


def test_gpt2_split_basics():
    assert forge_train._gpt2_split("hello world!") == [
        "hello", " world", "!"]
    assert forge_train._gpt2_split("don't") == ["don't"]
    assert forge_train._gpt2_split("abc123") == ["abc", "123"]


def test_bpe_count_uses_merges():
    bpe = forge_train.GlimmerBPE([["h", "e"], ["he", "l"], ["hel", "l"],
                                  ["hell", "o"]])
    assert bpe.count("hello") == 1
    assert bpe.count("") == 0
    assert bpe.count("hello world") == 1 + bpe.count(" world")
    assert bpe.count(" world") > 1  # unmerged tail stays split


def test_real_glimmer_tokenizer_counts():
    path = forge_train.glimmer_tokenizer_file()
    if path is None:
        pytest.skip("no cached Glimmer tokenizer")
    bpe = forge_train.load_bpe_tokenizer(path)
    assert bpe.count("hello") == 1
    code = "result = cq.Workplane('XY').box(30, 20, 10)"
    assert bpe.count(code) > len(code.split())  # whitespace undercounts


def test_count_r5_row_tokens_includes_system_and_card():
    bpe = forge_train.GlimmerBPE([])
    rec = {"text": "make a block", "code": "result = 1",
           "reasoning": "think hard"}
    with_card = forge_train.count_r5_row_tokens(
        [rec], bpe, "SYSTEM CARD TEXT")
    without = forge_train.count_r5_row_tokens([rec], bpe, "")
    assert len(with_card) == 1 and with_card[0] > without[0] > 0


def test_estimate_r5_cost_math():
    est = forge_train.estimate_r5_cost([1650], epochs=2,
                                       throughput=1650.0,
                                       rate_per_hour=3600.0)
    assert est == {"tokens": 1650, "seconds": 2.0, "dollars": 2.0}


def test_apply_budget_headroom_keeps_selffix_and_fits():
    recs = ([{"id": "F%d" % i, "source": "glimmer-first"}
             for i in range(4)]
            + [{"id": "S%d" % i, "source": "glimmer-selffix"}
               for i in range(2)]
            + [{"id": "H0", "source": "glimmer-hinted"}])
    toks = [1000, 1000, 1000, 1000, 100, 100, 1000]
    kept, dropped, est = forge_train.apply_budget_headroom(
        recs, toks, 1.0, epochs=2, throughput=1000.0,
        rate_per_hour=3600.0)
    # $0.002/token: self-fix rows ($0.40) fit in 0.75 x $1 alone.
    assert [r["id"] for r in kept] == ["S0", "S1"]  # order kept
    assert len(dropped) == 5
    assert est["dollars"] <= 0.75
    kept2, dropped2, _ = forge_train.apply_budget_headroom(
        recs, toks, 1.0, epochs=2, throughput=1000.0,
        rate_per_hour=3600.0)
    assert [r["id"] for r in kept2] == ["S0", "S1"]  # seed-deterministic
    assert dropped2 == dropped
    # Everything fits: nothing dropped.
    kept3, dropped3, _ = forge_train.apply_budget_headroom(
        recs, toks, 1000.0, epochs=2, throughput=1000.0,
        rate_per_hour=3600.0)
    assert dropped3 == [] and len(kept3) == 7
