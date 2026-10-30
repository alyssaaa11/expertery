"""Offline tests for the factory learning loop (no network, fake data).

SPEC section 4: signatures, min-count, kinds, dev/bad-id skipping,
forbidden paths, factory_version. Never opens blind/ folders or
expected*.json.
"""
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import patterns
import teacher

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fake_run(path, records):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "calls.jsonl"), "w",
              encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def _rec(run_id, family, verdict, fails=(), err=None, code="result = 1"):
    return {"id": run_id, "family": family, "teacher": "spark",
            "verdict": verdict, "fails": list(fails), "run_error": err,
            "code": code, "usage": {}, "cached_tokens": 0, "latency": 1.0,
            "factory_version": teacher.FACTORY_VERSION}


def _run_patterns(tmp_path, runs, **kwargs):
    out = str(tmp_path / "out")
    argv = ["--runs"] + runs + ["--out", out]
    for key, val in kwargs.items():
        argv += ["--" + key.replace("_", "-"), str(val)]
    assert patterns.main(argv) == 0
    with open(os.path.join(out, "patterns.json"),
              encoding="utf-8") as f:
        data = json.load(f)
    text = open(os.path.join(out, "patterns.md"), encoding="utf-8").read()
    return data, text


def test_run_errors_spread_over_families_are_teacher_habit(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "FAIL", err="ValueError: bad edge 12"),
        _rec("F1-2", 1, "FAIL", err="ValueError: bad edge 34"),
        _rec("F2-1", 2, "FAIL", err="ValueError: bad edge 56"),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert pat["kind"] == "teacher_habit"
    assert pat["category"] == "run_error"
    assert pat["key"] == "ValueError: bad edge N"  # numbers -> N
    assert pat["count"] == 3
    assert sorted(pat["families"]) == ["1", "2"]
    assert len(pat["example_ids"]) == 2
    assert pat["where"] == "teacher_notes.md"
    assert "teacher_habit" in text and "teacher_notes.md" in text


def test_harness_is_our_bug(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "INVALID", err="harness: RuntimeError: box down"),
        _rec("F1-2", 1, "INVALID", err="harness: RuntimeError: box down"),
        _rec("F2-1", 2, "INVALID", err="harness: RuntimeError: box down"),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert pat["kind"] == "our_bug"
    assert pat["category"] == "harness"
    assert pat["where"] == "factory/box code"
    assert "our_bug" in text


def test_teacher_api_error_is_our_bug_not_teacher_habit(tmp_path):
    """An API/HTTP error from the teacher model (no answer produced
    because the call failed) is kind our_bug (category harness), not
    teacher_habit. Records come from real do_teacher_call failures."""
    job = {"id": "F1-1", "family": 1, "text": "t", "reference": "r"}
    recs = []
    for boom in (ConnectionError("connection refused"),
                 Exception("HTTP Error 503: Service Unavailable")):
        def _post(body, _boom=boom):
            raise _boom
        rec = teacher.do_teacher_call(
            dict(job), "spark", teacher.SPARK_MODEL, _post,
            None, None, "MANUAL")
        assert rec["verdict"] == "INVALID"
        assert not (rec["code"] or "").strip()  # no answer produced
        assert patterns.signature_of(rec)[0] == "harness"
        assert patterns.kind_of("harness", {}) == "our_bug"
        recs.append(rec)
    _fake_run(str(tmp_path / "run-a"), [
        {**recs[0], "id": "F1-1"},
        {**recs[0], "id": "F1-2"},
        {**recs[0], "id": "F2-1"},
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert (pat["kind"], pat["category"]) == ("our_bug", "harness")


def test_wrong_shape_in_one_family_is_our_wording(tmp_path):
    fails = ["bbox xmax mismatch", "mismatch 5.0%"]
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "FAIL", fails),
        _rec("F1-2", 1, "FAIL", fails),
        _rec("F1-3", 1, "FAIL", fails),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert pat["kind"] == "our_wording"
    assert pat["category"] == "wrong_shape"
    assert pat["key"] == "1: bbox xmax mismatch"  # family + first check
    assert pat["families"] == ["1"]
    assert pat["where"] == "generator.py family 1"
    assert "our_wording" in text


def test_wrong_shape_same_check_two_families_is_two_patterns(tmp_path):
    """T4: the signature carries the family, so one check failing in
    two families is two per-family patterns, not one spread pattern."""
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "FAIL", ["bbox mismatch"]),
        _rec("F1-2", 1, "FAIL", ["bbox mismatch"]),
        _rec("F1-3", 1, "FAIL", ["bbox mismatch"]),
        _rec("F2-1", 2, "FAIL", ["bbox mismatch"]),
        _rec("F2-3", 2, "FAIL", ["bbox mismatch"]),
        _rec("F2-4", 2, "FAIL", ["bbox mismatch"]),
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 2
    by_key = {p["key"]: p for p in data["patterns"]}
    assert by_key["1: bbox mismatch"]["kind"] == "our_wording"
    assert by_key["2: bbox mismatch"]["kind"] == "our_wording"


def test_f8_solids_counts_group_into_one_pattern(tmp_path):
    """T4: 3 F8 FAILs with solids=3, solids=4, solids=3 and different
    later checks group into ONE pattern (numbers -> N)."""
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F8-1", 8, "FAIL", ["solids=3", "volume", "area"]),
        _rec("F8-2", 8, "FAIL", ["solids=4", "invalid shape", "bbox"]),
        _rec("F8-3", 8, "FAIL", ["solids=3", "mismatch 140.1%"]),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert pat["category"] == "wrong_shape"
    assert pat["key"] == "8: solids=N"
    assert pat["count"] == 3
    assert pat["families"] == ["8"]


def test_solids_or_invalid_shape_first_check_is_teacher_habit(tmp_path):
    """B2: a wrong_shape whose first failed check is `solids=N` or
    `invalid shape` is kind teacher_habit (the text was fine)."""
    assert patterns.is_teacher_habit_shape("solids=N") is True
    assert patterns.is_teacher_habit_shape("invalid shape") is True
    assert patterns.is_teacher_habit_shape("bbox xmax mismatch") is False
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F8-1", 8, "FAIL", ["solids=3", "volume", "area"]),
        _rec("F8-2", 8, "FAIL", ["solids=4", "invalid shape", "bbox"]),
        _rec("F8-3", 8, "FAIL", ["solids=3", "mismatch 140.1%"]),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert pat["key"] == "8: solids=N"
    assert pat["kind"] == "teacher_habit"
    assert pat["where"] == "teacher_notes.md"
    assert "teacher_habit" in text
    # An invalid-shape first check lands in the same kind.
    _fake_run(str(tmp_path / "run-b"), [
        _rec("F8-4", 8, "FAIL", ["invalid shape", "bbox", "volume"]),
        _rec("F8-5", 8, "FAIL", ["invalid shape", "bbox", "area"]),
        _rec("F8-7", 8, "FAIL", ["invalid shape", "volume", "area"]),
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)])
    by_key = {p["key"]: p for p in data["patterns"]}
    assert by_key["8: invalid shape"]["kind"] == "teacher_habit"


def test_no_code_is_teacher_habit(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "INVALID", err="empty reply", code=""),
        _rec("F1-2", 1, "INVALID", err="empty reply", code=""),
        _rec("F2-1", 2, "INVALID", err="empty reply", code="   "),
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)])
    assert len(data["patterns"]) == 1
    pat = data["patterns"][0]
    assert (pat["kind"], pat["category"]) == ("teacher_habit", "no_code")


def test_two_hits_is_no_pattern(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "FAIL", err="ValueError: bad edge 1"),
        _rec("F1-2", 1, "FAIL", err="ValueError: bad edge 2"),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert data["patterns"] == []
    assert "no repeated pattern" in text


def test_min_count_flag(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "FAIL", err="ValueError: bad edge 1"),
        _rec("F1-2", 1, "FAIL", err="ValueError: bad edge 2"),
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)], min_count=2)
    assert len(data["patterns"]) == 1


def test_dev_ids_ignored(tmp_path):
    dev = json.load(open(os.path.join(HERE, "split.json"),
                         encoding="utf-8"))["dev"]
    assert "F1-4" in dev
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "INVALID", err="harness: boom"),
        _rec("F1-2", 1, "INVALID", err="harness: boom"),
        _rec("F1-4", 1, "INVALID", err="harness: boom"),  # dev
        _rec("F1-7", 1, "INVALID", err="harness: boom"),  # dev
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)])
    assert data["patterns"] == []  # only 2 non-dev hits
    assert data["n_skipped_dev"] == 2


def test_non_factory_ids_refused(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "INVALID", err="harness: boom"),
        _rec("F1-2", 1, "INVALID", err="harness: boom"),
        _rec("F1-3", 1, "INVALID", err="harness: boom"),
        _rec("M1-1", 1, "INVALID", err="harness: boom"),
        _rec("not-an-id", 1, "INVALID", err="harness: boom"),
    ])
    data, _text = _run_patterns(tmp_path, [str(tmp_path)])
    assert data["n_skipped_bad_id"] == 2
    assert len(data["patterns"]) == 1  # exam ids cannot seed a pattern


def test_forbidden_paths_exit_2(tmp_path):
    out = str(tmp_path / "out")
    for bad in (os.path.join(ROOT, "blind", "run"),
                os.path.join(ROOT, "experiments", "option-a", "run"),
                os.path.join(ROOT, "experiments", "first-test", "run")):
        with pytest.raises(SystemExit) as exc:
            patterns.main(["--runs", bad, "--out", out])
        assert exc.value.code == 2


def test_pass_rate_tables_kept(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "PASS"),
        _rec("F1-2", 1, "FAIL", ["mismatch 5.0%"], "the answer wrote no X"),
        _rec("F2-1", 2, "INVALID", [], "harness: boom"),
    ])
    _fake_run(str(tmp_path / "run-b"), [
        _rec("F1-3", 1, "PASS"),
        _rec("F2-3", 2, "FAIL", ["bbox"], None),
    ])
    data, text = _run_patterns(tmp_path, [str(tmp_path)])
    assert data["n_records"] == 5
    assert "Pass rate per run" in text and "Pass rate per family" in text
    assert "run-a" in text and "run-b" in text


def test_patterns_accepts_a_single_run_dir_and_an_out_dir(tmp_path):
    run = tmp_path / "run"
    _fake_run(str(run), [_rec("F1-1", 1, "PASS")])
    outdir = tmp_path / "o"
    assert patterns.main(
        ["--runs", str(run), "--out", str(outdir)]) == 0
    assert (outdir / "patterns.md").is_file()
    assert (outdir / "patterns.json").is_file()


def test_teacher_notes_file_exists_and_is_empty():
    path = os.path.join(HERE, "teacher_notes.md")
    assert os.path.isfile(path)
    assert open(path, encoding="utf-8").read() == ""


def test_factory_version_is_12_hex_of_sources(tmp_path):
    assert re.fullmatch(r"[0-9a-f]{12}", teacher.FACTORY_VERSION)
    gen = tmp_path / "generator.py"
    tch = tmp_path / "teacher.py"
    notes = tmp_path / "teacher_notes.md"
    gen.write_text("gen", encoding="utf-8")
    tch.write_text("tch", encoding="utf-8")
    notes.write_text("", encoding="utf-8")
    empty = teacher.compute_factory_version(str(gen), str(tch), str(notes))
    assert re.fullmatch(r"[0-9a-f]{12}", empty)
    notes.write_text("watch the slot wording", encoding="utf-8")
    assert teacher.compute_factory_version(
        str(gen), str(tch), str(notes)) != empty
    assert teacher.compute_factory_version() == teacher.FACTORY_VERSION


def test_every_teacher_call_carries_factory_version():
    rec = teacher.do_teacher_call(
        {"id": "F1-1", "family": 1, "text": "t", "reference": "r"},
        "spark", teacher.SPARK_MODEL,
        lambda body: (_ for _ in ()).throw(ConnectionError("x")),
        None, None, "MANUAL")
    assert rec["factory_version"] == teacher.FACTORY_VERSION
