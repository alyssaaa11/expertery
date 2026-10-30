"""Offline tests for the factory learning loop (no network, fake data)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import patterns
import teacher


def _fake_run(path, records):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "calls.jsonl"), "w",
              encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def _rec(run_id, family, verdict, fails=(), err=None):
    return {"id": run_id, "family": family, "teacher": "spark",
            "verdict": verdict, "fails": list(fails), "run_error": err,
            "usage": {}, "cached_tokens": 0, "latency": 1.0,
            "factory_version": teacher.FACTORY_VERSION}


def test_patterns_writes_markdown_from_fake_runs(tmp_path):
    _fake_run(str(tmp_path / "run-a"), [
        _rec("F1-1", 1, "PASS"),
        _rec("F1-2", 1, "FAIL", ["mismatch 5.0%"], "the answer wrote no X"),
        _rec("F2-1", 2, "INVALID", [], "harness: boom"),
    ])
    _fake_run(str(tmp_path / "run-b"), [
        _rec("F1-3", 1, "PASS"),
        _rec("F2-2", 2, "FAIL", ["bbox"], None),
    ])
    out = str(tmp_path / "patterns.md")
    assert patterns.main(["--runs", str(tmp_path), "--out", out]) == 0
    text = open(out, encoding="utf-8").read()
    assert "Records: 5." in text
    assert "run-a" in text and "run-b" in text
    assert "mismatch 5.0%" in text and "bbox" in text
    assert "harness: boom" in text


def test_patterns_accepts_a_single_run_dir_and_an_out_dir(tmp_path):
    run = tmp_path / "run"
    _fake_run(str(run), [_rec("F1-1", 1, "PASS")])
    outdir = tmp_path / "o"
    assert patterns.main(
        ["--runs", str(run), "--out", str(outdir)]) == 0
    assert (outdir / "patterns.md").is_file()


def test_teacher_notes_file_exists_and_is_empty():
    path = os.path.join(HERE, "teacher_notes.md")
    assert os.path.isfile(path)
    assert open(path, encoding="utf-8").read() == ""


def test_every_teacher_call_carries_factory_version():
    assert teacher.FACTORY_VERSION == "1"
    rec = teacher.do_teacher_call(
        {"id": "F1-1", "family": 1, "text": "t", "reference": "r"},
        "spark", teacher.SPARK_MODEL,
        lambda body: (_ for _ in ()).throw(ConnectionError("x")),
        None, None, "MANUAL")
    assert rec["factory_version"] == "1"
