"""Offline tests for the factory gallery (no network, no expected*.json).

The gallery builds trusted generator references in-process (needs
cadquery, like make_jobs) and only reads calls.jsonl for verdicts: no
answer code ever runs.
"""
import builtins
import json
import os
import sys

import pytest

cadquery = pytest.importorskip("cadquery")

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gallery


@pytest.fixture
def no_expected_json(monkeypatch):
    """Fail any open() of an expected*.json file."""
    real_open = builtins.open

    def _guarded(file, *args, **kwargs):
        if "expected" in str(file):
            raise AssertionError(
                "gallery must never open %s" % (file,))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _guarded)


def _dev_ids():
    return gallery.load_dev_ids()


def test_gallery_writes_10_svg_cards_skips_dev(tmp_path, no_expected_json):
    out = str(tmp_path / "gallery")
    assert gallery.main(["--out", out]) == 0
    text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    assert text.count('class="card"') == 10
    assert text.count("<svg") == 10  # inline SVG, no JS libraries
    head = text.split("<svg")[0]
    assert "http" not in head and "<script" not in text.lower()
    for job in gallery.pick_first_jobs(gallery.load_jobs(), _dev_ids()):
        assert job["id"] in text  # first non-dev job per family
    for dev in _dev_ids():
        assert dev not in text
    for name in gallery.family_names().values():
        assert name in text
    assert "teacher verdict" not in text  # no --runs: no verdict column


def test_gallery_with_runs_shows_verdicts_runs_no_code(tmp_path,
                                                       no_expected_json):
    cards = gallery.pick_first_jobs(gallery.load_jobs(), _dev_ids())
    run = tmp_path / "run"
    run.mkdir()
    records = []
    for i, job in enumerate(cards):
        if i % 2:
            records.append({"id": job["id"], "family": job["family"],
                            "teacher": "spark", "verdict": "PASS",
                            "fails": [], "run_error": None,
                            "code": "raise AssertionError('must not run')"})
        else:
            records.append({"id": job["id"], "family": job["family"],
                            "teacher": "spark", "verdict": "FAIL",
                            "fails": ["bbox xmax mismatch"],
                            "run_error": None,
                            "code": "raise AssertionError('must not run')"})
    with open(str(run / "calls.jsonl"), "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    out = str(tmp_path / "gallery")
    assert gallery.main(["--out", out, "--runs", str(run)]) == 0
    text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    assert text.count('class="card"') == 10
    assert "teacher verdict" in text
    assert text.count("bbox xmax mismatch") == 5  # the FAIL cards only
    assert "AssertionError" not in text  # answer code never ran
