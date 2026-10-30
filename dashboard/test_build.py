"""Offline tests for dashboard/build.py using fake input folders."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build


def _usage(models):
    return {"payload_type": "run.usage", "payload": {"models": models}}


def _side_effect(op):
    return {"payload_type": "task.lifecycle.side_effect_intent",
            "payload": {"event": {"operation": op}}}


def make_fake_tree(tmp: Path) -> dict:
    results = tmp / "results"
    results.mkdir()
    # One fake Muse round: 3 steps, 1 write, 2 edits, known cost.
    models = [{"input_tokens": 1_000_000, "cached_tokens": 600_000,
               "output_tokens": 100_000}]
    lines = ([{"payload_type": "task.lifecycle.completed"}] * 3
             + [_side_effect("tool:write_file")]
             + [_side_effect("tool:edit_file")] * 2
             + [_usage(models)])
    (results / "muse-demo.jsonl").write_text(
        "\n".join(json.dumps(line) for line in lines), encoding="utf-8")
    # One fake factory run.
    run = results / "factory-demo-2026-10-30"
    run.mkdir()
    (run / "summary.json").write_text(json.dumps({
        "n_calls": 4, "n_pass": 3, "cost_dollars": 0.10,
        "families": {str(i): {"n_calls": 2, "n_pass": 2 if i < 10 else 1,
                              "pass_rate": 1.0 if i < 10 else 0.5}
                     for i in range(1, 11)},
    }), encoding="utf-8")
    (run / "calls.jsonl").write_text("\n".join(json.dumps({"verdict": v})
        for v in ["PASS", "PASS", "FAIL", "INVALID"]), encoding="utf-8")
    train = results / "factory-train-2026-10-30"
    train.mkdir()
    (train / "train_records.jsonl").write_text("{}\n{}\n{}\n",
                                               encoding="utf-8")
    # Training log with losses.
    (results / "train-final-2026-10-30.log").write_text(
        "step 1/10 loss 2.5\nstep 2/10 loss 1.5\nstep 3/10 loss 1.0 "
        "12.5 min $0.33\n", encoding="utf-8")
    # Gallery SVG with a prolog + namespace + link (must be cleaned).
    svgs = results / "factory-gallery" / "svgs"
    svgs.mkdir(parents=True)
    (svgs / "F1.svg").write_text(
        '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" '
        'width="800" height="240" viewBox="0 0 8 8">'
        '<a href="http://example.com"><circle cx="4" cy="4" r="3"/>'
        "</a></svg>", encoding="utf-8")
    # Verifier reports (newest first by mtime via creation order).
    verifier = tmp / "reports"
    verifier.mkdir()
    (verifier / "forge-a.md").write_text(
        "# Check A\nblah\nVerdict: PASS\n", encoding="utf-8")
    (verifier / "forge-b.md").write_text(
        "# Check B https://secret.example/x\nVerdict: FAIL\n", encoding="utf-8")
    budget = tmp / "budget.json"
    budget.write_text(json.dumps(
        {"budget": 65, "base_spent_before_logs": 10.0,
         "extra": [{"label": "hand-entered", "amount": 0.5}]}),
        encoding="utf-8")
    return {"root": tmp, "results": results, "verifier": verifier,
            "budget": budget}


def test_muse_round_cost_and_counts(tmp_path):
    ctx = make_fake_tree(tmp_path)
    rounds = build.collect_muse_rounds(ctx["results"])
    assert len(rounds) == 1
    r = rounds[0]
    assert r["name"] == "demo"
    assert r["steps"] == 3
    assert r["writes"] == 1 and r["edits"] == 2
    # (1M-600k)*1.25 + 600k*0.15 + 100k*4.25, per million.
    assert abs(r["cost"] - (400_000 * 1.25 + 600_000 * 0.15
                            + 100_000 * 4.25) / 1e6) < 1e-9


def test_factory_verdicts_and_money(tmp_path):
    ctx = make_fake_tree(tmp_path)
    runs = build.collect_factory_runs(ctx["results"])
    assert len(runs) == 1
    assert runs[0]["verdicts"] == {"PASS": 2, "FAIL": 1, "INVALID": 1}
    budget = build.load_budget(ctx["budget"])
    money = build.compute_money(budget, build.collect_muse_rounds(
        ctx["results"]), runs)
    assert abs(money["factory"] - 0.10) < 1e-9
    assert abs(money["spent"] - (10.0 + money["muse"] + 0.10 + 0.5)) < 1e-9
    assert 0 < money["pct"] < 100


def test_training_loss_parsing(tmp_path):
    ctx = make_fake_tree(tmp_path)
    train = build.parse_training(
        ctx["results"] / "train-final-2026-10-30.log")
    assert train["losses"] == [2.5, 1.5, 1.0]
    assert (train["step"], train["total"]) == (3, 10)
    assert train["minutes"] == 12.5
    assert train["dollars"] == 0.33
    assert "<polyline" in build.loss_chart_svg(train["losses"])


def test_training_fallback_tail_skips_noise(tmp_path):
    log = tmp_path / "t.log"
    log.write_text("first\n✓ Uploaded stuff\n✓ Created thing\nlast\n",
                   encoding="utf-8")
    train = build.parse_training(log)
    assert train["losses"] == []
    assert train["tail"] == ["first", "last"]


def test_station_statuses(tmp_path):
    root = tmp_path
    (root / "results").mkdir()
    out = root / "results" / "x" / "summary.json"
    out.parent.mkdir(parents=True)
    out.write_text("{}", encoding="utf-8")
    assert build.station_status(root, ["results/x/summary.json"],
                                None)[0] == "done"
    assert build.station_status(root, ["results/missing/summary.json"],
                                None)[0] == "waiting"
    log = root / "results" / "fresh.log"
    log.write_text("working\n", encoding="utf-8")
    assert build.station_status(root, ["results/missing/summary.json"],
                                "results/fresh.log")[0] == "running"
    old = root / "results" / "old.log"
    old.write_text("STOP, out of money\n", encoding="utf-8")
    import os
    import time as _time
    os.utime(old, (_time.time() - 600, _time.time() - 600))
    assert build.station_status(root, ["results/missing/summary.json"],
                                "results/old.log")[0] == "stopped"


def test_page_has_six_sections_no_links_no_keys(tmp_path):
    ctx = make_fake_tree(tmp_path)
    html = build.build_page(ctx["root"], ctx["results"], ctx["verifier"],
                            ctx["budget"])
    for i in range(1, 7):
        assert f"<h2>{i}." in html
    for needle in ["Claude", "Muse Code", "Spark Open", "Referee",
                   "Verifier", "Glimmer"]:
        assert needle in html
    assert 'http-equiv="refresh"' in html  # self-reload, not a request
    assert not re.search(r'(src|href)\s*=\s*["\']https?://', html)
    assert "https://secret.example" not in html
    assert "http://example.com" not in html
    # gallery SVG inlined but cleaned: no prolog, xmlns, or href left.
    assert "<?xml" not in html
    assert "http://www.w3.org" not in html
    assert "<circle" in html
