"""Offline tests for the answer viewer (no Modal, no network).

Fake render functions stand in for the Modal app; any test that could
reach a real Modal call monkeypatches it to raise. Synthetic jobs and
records only: never blind/, experiments/option-a/, or expected*.json.
"""

import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import make_viewer
import render_cloud

REFMARKER = "REFMARKER_SECRET_123"
EXPMARKER = "EXPECTED_SECRET_456"
SVG = ("<svg xmlns=\"http://www.w3.org/2000/svg\">"
       "<path d=\"M0 0 L10 0 L10 10 Z\"/></svg>")


def _jobs():
    return [
        {"id": "F1-1", "family": 1, "text": "Spool task text.",
         "reference": "import cadquery as cq  # %s %s\nresult = None"
         % (REFMARKER, EXPMARKER)},
        {"id": "F1-2", "family": 1, "text": "Second spool task.",
         "reference": "import cadquery as cq\nresult = None"},
        {"id": "F2-1", "family": 2, "text": "Bracket task.",
         "reference": "import cadquery as cq\nresult = None"},
    ]


def _records():
    return [
        {"job": "F1-1", "rep": 0, "verdict": "PASS", "fails": [],
         "measurements": {"volume": 10.0, "solids": 1},
         "run_error": None,
         "code": "import cadquery as cq\nresult = 1",
         "reasoning": "I will make a box.",
         "prompt_tokens": 100, "completion_tokens": 50, "seconds": 4.0},
        {"job": "F1-2", "rep": 0, "verdict": "FAIL",
         "fails": ["mismatch 1.2%"],
         "measurements": {"volume": 9.0, "solids": 1},
         "run_error": None,
         "code": ("import cadquery as cq\n<script>alert(1)</script>\n"
                  "result = 2"),
         "reasoning": "Thinking with <script>evil()</script> inside.",
         "prompt_tokens": 200, "completion_tokens": 60, "seconds": 6.0},
        {"job": "F2-1", "rep": 0, "verdict": "FAIL", "fails": [],
         "measurements": None,
         "run_error": "Traceback (most recent call last):\nline1\nBOOM",
         "code": "import cadquery as cq\nresult = oops",
         "reasoning": "Maybe this works.",
         "prompt_tokens": 150, "completion_tokens": 70, "seconds": 8.0},
        {"job": "F2-1", "rep": 1, "verdict": "PASS", "fails": [],
         "measurements": {"volume": 5.0, "solids": 1},
         "run_error": None,
         "code": "import cadquery as cq\nresult = 3",
         "reasoning": "Fixed it.",
         "prompt_tokens": 120, "completion_tokens": 40, "seconds": 2.0},
    ]


@pytest.fixture
def run_dir(tmp_path):
    d = tmp_path / "run"
    d.mkdir()
    with open(d / "calls.jsonl", "w", encoding="utf-8") as f:
        for rec in _records():
            f.write(json.dumps(rec) + "\n")
    jobs = tmp_path / "jobs.jsonl"
    with open(jobs, "w", encoding="utf-8") as f:
        for job in _jobs():
            f.write(json.dumps(job) + "\n")
    return d, str(jobs)


class FakeRender:
    """Fake render_fn: records requested ids, returns inline SVGs."""

    def __init__(self):
        self.calls = []

    def __call__(self, items, budget):
        self.calls.append([it["id"] for it in items])
        return {it["id"]: SVG for it in items}


def _read_index(out_dir):
    with open(os.path.join(out_dir, "index.html"), encoding="utf-8") as f:
        return f.read()


def _span(page, span_id):
    m = re.search(r'<span id="%s">([^<]*)</span>' % span_id, page)
    assert m, "missing span #%s" % span_id
    return m.group(1)


def test_code_and_thinking_are_html_escaped(run_dir, tmp_path):
    """A script tag in code/thinking appears as text, never as markup."""
    run_d, jobs = run_dir
    out = str(tmp_path / "out")
    make_viewer.build(str(run_d), jobs, out, render_fn=FakeRender())
    page = _read_index(out)
    assert "&lt;script&gt;" in page
    assert "<script>alert" not in page
    assert "<script>evil" not in page


def test_cache_reuse_costs_zero(run_dir, tmp_path):
    """A second build renders nothing new (re-runs cost $0)."""
    run_d, jobs = run_dir
    out = str(tmp_path / "out")
    fake = FakeRender()
    make_viewer.build(str(run_d), jobs, out, render_fn=fake)
    assert fake.calls and fake.calls[0]
    assert os.path.exists(os.path.join(out, "svgs.json"))
    fake2 = FakeRender()
    summary, n_rendered = make_viewer.build(
        str(run_d), jobs, out, render_fn=fake2)
    assert n_rendered == 0
    assert fake2.calls == [[]] or fake2.calls == []
    assert summary["n"] == 4


class _FakeFS:
    def __init__(self, tick):
        self.files = {}
        self._tick = tick

    def write_text(self, data, remote_path):
        self.files[remote_path] = data

    def read_bytes(self, remote_path):
        return self.files[remote_path]

    def read_text(self, remote_path):
        return self.files[remote_path]


class _FakeSandbox:
    def __init__(self, tick):
        self.filesystem = _FakeFS(tick)
        self._tick = tick
        self.terminated = False

    def exec(self, *args, **kwargs):
        self._tick[0] += 30.0
        if "-c" in args:
            self.filesystem.files[render_cloud.SVG_PATH] = SVG
        return object()

    def terminate(self):
        self.terminated = True


def test_budget_stop_leaves_every_id_present():
    """Once the budget is exceeded, the rest come back BUDGET STOP."""
    import cloud_cq

    tick = [0.0]
    made = []

    def _factory():
        sb = _FakeSandbox(tick)
        made.append(sb)
        sb.filesystem.files[cloud_cq.BREP_PATH] = b"brep"
        return sb

    items = [{"id": "a:%d" % i, "code": "result = 1"} for i in range(3)]
    results, _elapsed, _cost = render_cloud.render_items(
        items, _factory, budget_dollars=0.005, clock=lambda: tick[0])
    assert len(made) == 1
    assert set(results) == {"a:0", "a:1", "a:2"}
    stopped = [k for k, v in results.items()
               if v.startswith(render_cloud.BUDGET_PREFIX)]
    assert stopped
    assert results["a:0"].startswith("<svg")


def test_over_budget_math():
    assert not render_cloud.over_budget(0.0, 0.30)
    assert render_cloud.over_budget(10 ** 9, 0.30)
    assert render_cloud.estimate_cost(0.0) == 0.0


def test_page_counts_match_calls_jsonl(run_dir, tmp_path):
    """Summary spans and cards match the calls.jsonl records."""
    run_d, jobs = run_dir
    out = str(tmp_path / "out")
    summary, _ = make_viewer.build(str(run_d), jobs, out,
                                   render_fn=FakeRender())
    assert (summary["pass"], summary["fail"], summary["crash"]) == (2, 1, 1)
    page = _read_index(out)
    assert _span(page, "count-n") == "4"
    assert _span(page, "count-pass") == "2"
    assert _span(page, "count-fail") == "1"
    assert _span(page, "count-crash") == "1"
    assert len(re.findall(r'<div class="card ', page)) == 4
    assert "PASS" in page and "crash" in page


def test_no_reference_code_or_expected_on_page(run_dir, tmp_path):
    """Reference code and expected values never appear as page text."""
    run_d, jobs = run_dir
    out = str(tmp_path / "out")
    make_viewer.build(str(run_d), jobs, out, render_fn=FakeRender())
    page = _read_index(out)
    assert REFMARKER not in page
    assert EXPMARKER not in page
    assert "<svg" in page  # only the reference PICTURE is shown


def test_offline_build_reaches_nothing(run_dir, tmp_path):
    """--offline writes placeholders and never calls render."""
    run_d, jobs = run_dir
    out = str(tmp_path / "out")

    def _boom(items, budget):
        raise AssertionError("no render in offline mode")

    summary, n_rendered = make_viewer.build(
        str(run_d), jobs, out, offline=True, render_fn=_boom)
    assert n_rendered == 0
    assert summary["n"] == 4
    page = _read_index(out)
    assert "OFFLINE" in page
    assert os.path.exists(os.path.join(out, "svgs.json"))


def test_box_config_and_svg_settings():
    """One box, network blocked, lifetime capped; gallery SVG settings."""
    import cloud_cq
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location(
        "gallery_src",
        os.path.join(HERE, "..", "factory", "gallery.py"))
    gallery = _ilu.module_from_spec(spec)
    spec.loader.exec_module(gallery)
    assert render_cloud.SVG_OPT == dict(gallery.SVG_OPT)
    kwargs = render_cloud.box_kwargs()
    assert kwargs["block_network"] is True
    assert "secrets" not in kwargs and "volumes" not in kwargs
    assert kwargs["timeout"] <= 7200
    assert render_cloud.sandbox_lifetime_s(1000) <= 7200
    assert render_cloud.EXEC_TIMEOUT_S == cloud_cq.EXEC_TIMEOUT_S == 60


def test_forbidden_paths_refused(tmp_path):
    """--run/--jobs under blind/ or option-a/ are refused."""
    with pytest.raises(SystemExit):
        make_viewer.main(["--run", "blind/x", "--jobs", str(tmp_path),
                          "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit):
        make_viewer.main(["--run", str(tmp_path), "--jobs",
                          "experiments/option-a/jobs.jsonl",
                          "--out", str(tmp_path / "o")])


def test_local_render_starts_no_modal_run():
    """render_local without a factory touches nothing paid: every id
    comes back as ERROR text and no sandbox is created."""
    items = [{"id": "a:0", "code": "result = 1"}]
    results, elapsed, cost = render_cloud.render_local(items)
    assert set(results) == {"a:0"}
    assert results["a:0"].startswith(render_cloud.ERROR_PREFIX)
    assert elapsed == 0.0 and cost == 0.0


def test_remote_entry_point_exists_without_calling_it():
    """render_svgs exists (the paid path); tests never call it."""
    assert hasattr(render_cloud.render_svgs, "remote") \
        or callable(render_cloud.render_svgs)
