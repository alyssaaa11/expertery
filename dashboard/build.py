#!/usr/bin/env python3
"""Forge mission-control dashboard: read-only, offline, one self-contained page.

Reads local files only (never network / Modal / models / commits) and writes
results/dashboard/index.html with inline CSS, inline SVG and a little vanilla JS.

Station status rule: done when the output file exists, running when the log
changed in the last 2 minutes, stopped when the log tail names a stop/failure,
else waiting.
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = DASHBOARD_DIR.parent
DEFAULT_RESULTS = DEFAULT_ROOT / "results"
DEFAULT_VERIFIER = Path.home() / "agents" / "verifier" / "reports"
DEFAULT_BUDGET = DASHBOARD_DIR / "budget.json"
DEFAULT_OUT = DEFAULT_RESULTS / "dashboard" / "index.html"

RUNNING_AFTER_S = 120  # a log touched in the last 2 minutes means "running"

COST_IN_PER_M = 1.25  # $ per M uncached input tokens (Muse rounds)
COST_CACHED_PER_M = 0.15  # $ per M cached input tokens
COST_OUT_PER_M = 4.25  # $ per M output tokens

STOP_WORDS = re.compile(
    r"\b(STOP|STOPPED|FAILED|ABORTED|INCOMPLETE|REFUSED|Traceback)\b",
    re.IGNORECASE,
)

# 8 stations of the Forge pipeline: label, output glob(s), log file.
STATIONS = [
    ("Factory pilot", ["results/factory-pilot-2026-10-30/summary.json"],
     "results/factory-pilot-2026-10-30.log"),
    ("Factory main", ["results/factory-main-2026-10-30/summary.json"],
     "results/factory-main-2026-10-30.log"),
    ("Training", ["results/train-final-*/summary.json"],
     "results/train-final-2026-10-30.log"),
    ("Practice test (dev)", ["results/dev-*/summary.json"], None),
    ("B-max finish", ["results/bmax-fill-*/summary.json"], None),
    ("Final exam", ["results/final-*/summary.json"], None),
    ("Compare", ["results/compare-*.md"], None),
    ("Demo", ["results/demo-*.md"], None),
]


def esc(text: object) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def scrub(text: object) -> str:
    """Remove URLs and key-like tokens so the page leaks nothing sensitive."""
    s = "" if text is None else str(text)
    s = re.sub(r"https?://\S+", "(link)", s)
    s = re.sub(r"\b((?:sk|ap|AKIA|xox)[A-Za-z0-9_\-]{8,})\b", "[redacted]", s)
    s = re.sub(r"\b[A-Za-z0-9_\-+=]{30,}\b", "[redacted]", s)
    return s


def fmt_time(ts: float | None) -> str:
    if not ts:
        return "n/a"
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")


def fmt_age(ts: float | None, now: float | None = None) -> str:
    if not ts:
        return "n/a"
    mins = max(0, int(((now if now is not None else time.time()) - ts) // 60))
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 48:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def muse_cost_from_models(models: list) -> float:
    total = 0.0
    for m in models or []:
        try:
            inp = float(m.get("input_tokens", 0) or 0)
            cached = float(m.get("cached_tokens", 0) or 0)
            out = float(m.get("output_tokens", 0) or 0)
        except (TypeError, ValueError):
            continue
        total += ((inp - cached) * COST_IN_PER_M
                  + cached * COST_CACHED_PER_M
                  + out * COST_OUT_PER_M) / 1e6
    return total


def collect_muse_rounds(results_dir: Path) -> list[dict]:
    """One entry per results/muse-*.jsonl: name, steps, writes/edits, cost."""
    rounds = []
    for path in sorted(results_dir.glob("muse-*.jsonl")):
        steps = writes = edits = 0
        cost = 0.0
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    pt = rec.get("payload_type")
                    if pt == "task.lifecycle.completed":
                        steps += 1
                    elif pt == "task.lifecycle.side_effect_intent":
                        op = (rec.get("payload", {}).get("event", {})
                              .get("operation", ""))
                        if op == "tool:write_file":
                            writes += 1
                        elif op == "tool:edit_file":
                            edits += 1
                    elif pt == "run.usage":
                        cost += muse_cost_from_models(
                            rec.get("payload", {}).get("models", []))
        except OSError:
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        rounds.append({
            "name": path.stem[len("muse-"):],
            "steps": steps, "writes": writes, "edits": edits,
            "cost": cost, "mtime": mtime,
        })
    rounds.sort(key=lambda r: r["mtime"], reverse=True)
    return rounds


def collect_factory_runs(results_dir: Path) -> list[dict]:
    """One entry per results/factory-*/summary.json with verdict counts."""
    runs = []
    for path in sorted(results_dir.glob("factory-*/summary.json")):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        verdicts = {"PASS": 0, "FAIL": 0, "INVALID": 0}
        calls_path = path.parent / "calls.jsonl"
        if calls_path.exists():
            try:
                with open(calls_path, encoding="utf-8",
                          errors="replace") as fh:
                    for line in fh:
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        v = rec.get("verdict", "INVALID")
                        verdicts[v if v in verdicts else "INVALID"] += 1
            except OSError:
                pass
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        runs.append({
            "name": path.parent.name, "summary": summary,
            "verdicts": verdicts, "mtime": mtime,
        })
    runs.sort(key=lambda r: r["mtime"], reverse=True)
    return runs


def kept_records_total(results_dir: Path) -> int:
    total = 0
    for path in sorted(results_dir.glob("factory-train-*/train_records.jsonl")):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                total += sum(1 for _ in fh)
        except OSError:
            continue
    return total


def collect_verifier(verifier_dir: Path, n: int = 6) -> list[dict]:
    """Newest forge-*.md reports: title line, Verdict line, date."""
    try:
        paths = sorted(verifier_dir.glob("forge-*.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:n]
    except OSError:
        return []
    reports = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            mtime = path.stat().st_mtime
        except OSError:
            continue
        title, verdict = path.stem, "Verdict: ?"
        for line in text.splitlines():
            s = line.strip()
            if title == path.stem and s.startswith("#"):
                title = s.lstrip("#").strip()
            if s.lower().startswith("verdict:"):
                verdict = s
                break
        reports.append({"title": title, "verdict": verdict,
                        "mtime": mtime, "name": path.name})
    return reports


def git_info(root: Path, n: int = 5) -> list[dict]:
    """Read-only `git log`; empty list when git is unavailable."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "log", f"-{n}",
             "--format=%ct%x00%s%x00%h"],
            capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    commits = []
    for line in proc.stdout.splitlines():
        parts = line.split("\0")
        if len(parts) != 3:
            continue
        try:
            ts = float(parts[0])
        except ValueError:
            continue
        commits.append({"ts": ts, "msg": parts[1], "short": parts[2]})
    return commits


def station_status(root: Path, out_patterns: list[str], log_rel: str | None,
                    now: float | None = None) -> tuple[str, str]:
    """Return (state, emoji): done / running / stopped / waiting."""
    now = time.time() if now is None else now
    for pattern in out_patterns:
        matches = glob.glob(str(root / pattern))
        if any(os.path.exists(m) for m in matches):
            return ("done", "✅")
    if log_rel:
        log_path = root / log_rel
        try:
            age = now - log_path.stat().st_mtime
        except OSError:
            return ("waiting", "⏸")
        if age <= RUNNING_AFTER_S:
            return ("running", "⏳")
        try:
            tail = log_path.read_bytes()[-2048:].decode("utf-8", "replace")
        except OSError:
            return ("waiting", "⏸")
        if STOP_WORDS.search(tail):
            return ("stopped", "⛔")
    return ("waiting", "⏸")


LOSS_RE = re.compile(r"loss[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)",
                     re.IGNORECASE)
STEP_RE = re.compile(r"step\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)
MIN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*min", re.IGNORECASE)
DOLLAR_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")
NOISE_RE = re.compile(r"upload|creat", re.IGNORECASE)


def parse_training(log_path: Path) -> dict:
    """Loss per step, current/total step, minutes, $; else last log lines."""
    info: dict = {"losses": [], "step": None, "total": None,
                  "minutes": None, "dollars": None, "tail": []}
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return info
    lines = text.splitlines()
    for line in lines:
        if "loss" in line.lower():
            m = LOSS_RE.search(line)
            if m:
                try:
                    info["losses"].append(float(m.group(1)))
                except ValueError:
                    pass
        m = STEP_RE.search(line)
        if m:
            info["step"], info["total"] = int(m.group(1)), int(m.group(2))
        m = MIN_RE.search(line)
        if m:
            try:
                info["minutes"] = float(m.group(1))
            except ValueError:
                pass
        m = DOLLAR_RE.search(line)
        if m:
            try:
                info["dollars"] = float(m.group(1))
            except ValueError:
                pass
    clean = [ln for ln in lines if ln.strip() and not NOISE_RE.search(ln)]
    info["tail"] = clean[-5:]
    return info


def clean_gallery_svg(text: str) -> str:
    """Make a gallery SVG safe to inline: no prolog, namespaces, links."""
    text = re.sub(r"<\?xml.*?\?>", "", text, flags=re.DOTALL)
    text = re.sub(r'\sxmlns(?::\w+)?="[^"]*"', "", text)
    text = re.sub(r"\s(?:xlink:)?href=\"[^\"]*\"", "", text)
    text = re.sub(r"<script.*?</script>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\swidth=\"[^\"]*\"", "", text, count=1)
    text = re.sub(r"\sheight=\"[^\"]*\"", "", text, count=1)
    text = re.sub(r"<svg\b", "<svg style=\"width:100%;height:auto;"
                  "max-height:130px\" ", text, count=1)
    return text.strip()


def collect_gallery(results_dir: Path, want: int = 10) -> list[dict]:
    svgs = sorted((results_dir / "factory-gallery" / "svgs").glob("*.svg"))
    thumbs = []
    for path in svgs[:want]:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        thumbs.append({"name": path.stem, "svg": clean_gallery_svg(raw)})
    return thumbs


def load_budget(budget_path: Path) -> dict:
    try:
        data = json.loads(budget_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    try:
        budget = float(data.get("budget", 65))
    except (TypeError, ValueError):
        budget = 65.0
    try:
        base = float(data.get("base_spent_before_logs", 0) or 0)
    except (TypeError, ValueError):
        base = 0.0
    extra = []
    raw_extra = data.get("extra", [])
    if isinstance(raw_extra, list):
        for item in raw_extra:
            if not isinstance(item, dict):
                continue
            try:
                amount = float(item.get("amount", 0) or 0)
            except (TypeError, ValueError):
                continue
            extra.append({"label": str(item.get("label", "extra")),
                          "amount": amount})
    return {"budget": budget, "base": base, "extra": extra}


def compute_money(budget: dict, rounds: list[dict],
                  runs: list[dict]) -> dict:
    muse_total = sum(r.get("cost", 0.0) for r in rounds)
    factory_total = sum(float(r.get("summary", {}).get("cost_dollars", 0)
                                  or 0) for r in runs)
    extra_total = sum(e["amount"] for e in budget["extra"])
    spent = budget["base"] + muse_total + factory_total + extra_total
    pct = min(100.0, 100.0 * spent / budget["budget"]) if budget["budget"] else 0
    return {"muse": muse_total, "factory": factory_total,
            "extra_total": extra_total, "spent": spent, "pct": pct}


def loss_chart_svg(losses: list[float], width: int = 280,
                   height: int = 96) -> str:
    if not losses:
        return ""
    lo, hi = min(losses), max(losses)
    span = (hi - lo) or 1.0
    n = len(losses)
    pts = []
    for i, v in enumerate(losses):
        x = 8 + (i / max(1, n - 1)) * (width - 16)
        y = 8 + (1 - (v - lo) / span) * (height - 16)
        pts.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="loss chart" class="chart">'
        f'<polyline points="{" ".join(pts)}" /></svg>'
    )


CSS = """
:root{--bg:#fdf6f0;--card:#ffffff;--ink:#4a3f55;--soft:#f3e8ff;
--pink:#ffd9e8;--mint:#d7f5e3;--sky:#d9ecff;--peach:#ffe8cf;
--line:#e8d9f0;--accent:#a06cd5}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);
font-family:Verdana,Geneva,DejaVu Sans,sans-serif;margin:0;padding:16px}
h1{text-align:center;font-size:1.6em;margin:8px 0 2px}
.sub{text-align:center;opacity:.75;margin:0 0 14px}
h2{font-size:1.15em;margin:22px 0 8px}
.grid{display:flex;flex-wrap:wrap;gap:12px}
.card{background:var(--card);border:2px solid var(--line);
border-radius:18px;padding:12px 14px;flex:1 1 260px;min-width:240px}
.card h3{margin:0 0 6px;font-size:1em}
.bignum{font-size:1.8em;font-weight:bold}
.stations{display:flex;flex-wrap:wrap;gap:8px}
.station{background:var(--card);border:2px solid var(--line);
border-radius:14px;padding:8px 10px;min-width:120px;flex:1 1 120px;
text-align:center}
.station .light{font-size:1.5em}
.station .lbl{font-weight:bold;font-size:.85em}
.station .st{font-size:.75em;opacity:.8}
.station.done{background:var(--mint)}
.station.running{background:var(--sky)}
.station.stopped{background:#ffd4d4}
.bar{height:10px;background:#eee;border-radius:6px;overflow:hidden}
.bar>i{display:block;height:100%;background:var(--accent);
border-radius:6px}
.gauge{height:22px;background:#eee;border-radius:12px;overflow:hidden}
.gauge>i{display:block;height:100%;
background:linear-gradient(90deg,#7bd88f,#ffd166,#ff8fa3)}
ul.tight{margin:6px 0;padding-left:18px}
.muted{font-size:.82em;opacity:.8}
.thumbs{display:flex;flex-wrap:wrap;gap:8px}
.thumb{background:#fff;border:1px solid var(--line);border-radius:12px;
padding:4px;width:150px;text-align:center}
.chart{width:100%;max-width:320px;height:auto}
.chart polyline{fill:none;stroke:var(--accent);stroke-width:2}
table{border-collapse:collapse;font-size:.85em}
td,th{padding:2px 8px 2px 0;text-align:left}
pre{background:#faf5ff;border-radius:10px;padding:8px;font-size:.78em;
overflow-x:auto;white-space:pre-wrap}
"""


def section_pipeline(root: Path) -> str:
    cards = []
    for label, outs, log_rel in STATIONS:
        state, emoji = station_status(root, outs, log_rel)
        cards.append(
            f'<div class="station {state}"><div class="light">{emoji}</div>'
            f'<div class="lbl">{esc(label)}</div>'
            f'<div class="st">{state}</div></div>')
    return ("<h2>1. Pipeline train</h2>"
            f'<div class="stations">{"".join(cards)}</div>')


def section_agents(root: Path, results_dir: Path, verifier_dir: Path,
                   rounds: list[dict], runs: list[dict],
                   reports: list[dict], train: dict) -> str:
    commits = git_info(root, n=1)
    if commits:
        coord = (f"{esc(scrub(commits[0]['msg']))}<br>"
                 f"<span class='muted'>{esc(commits[0]['short'])} · "
                 f"{esc(fmt_time(commits[0]['ts']))}</span>")
    else:
        coord = "<span class='muted'>no git history available</span>"

    if rounds:
        items = []
        for r in rounds:
            items.append(
                f"<li><b>{esc(r['name'])}</b>: {r['steps']} steps, "
                f"{r['writes']} written / {r['edits']} edited, "
                f"${r['cost']:.2f} <span class='muted'>"
                f"({esc(fmt_age(r['mtime']))})</span></li>")
        builder = f"<ul class='tight'>{''.join(items)}</ul>"
        muse_big = f"${sum(r['cost'] for r in rounds):.2f}"
    else:
        builder = "<span class='muted'>no Muse rounds yet</span>"
        muse_big = "$0.00"

    if runs:
        teacher_rows = []
        for r in runs:
            s = r["summary"]
            teacher_rows.append(
                f"<tr><td>{esc(r['name'])}</td>"
                f"<td>{s.get('n_calls', '?')} answers</td>"
                f"<td>{s.get('n_pass', '?')} PASS</td>"
                f"<td>${float(s.get('cost_dollars', 0) or 0):.2f}</td></tr>")
        teacher = ("<table>" + "".join(teacher_rows) + "</table>")
        tp = sum(r["verdicts"]["PASS"] for r in runs)
        tf = sum(r["verdicts"]["FAIL"] for r in runs)
        ti = sum(r["verdicts"]["INVALID"] for r in runs)
        referee = (f'<div class="bignum">{tp} ✅ / {tf} ❌ / {ti} ⚠️</div>'
                   "<span class='muted'>PASS / FAIL / INVALID</span>")
    else:
        teacher = "<span class='muted'>no factory runs yet</span>"
        referee = "<span class='muted'>no grades yet</span>"

    if reports:
        ver = "".join(
            f"<li><b>{esc(scrub(rep['title']))}</b><br>"
            f"<span class='muted'>{esc(scrub(rep['verdict']))} · "
            f"{esc(fmt_time(rep['mtime']))}</span></li>" for rep in reports)
        verifier = f"<ul class='tight'>{ver}</ul>"
    else:
        verifier = "<span class='muted'>no verifier reports yet</span>"

    if train["losses"]:
        glimmer = (f"<div class='bignum'>step {train['step']} / "
                   f"{train['total']}</div>"
                   f"<span class='muted'>loss {train['losses'][-1]:.4f}"
                   f"</span>")
    elif train["tail"]:
        glimmer = ("<span class='muted'>warming up, last log:</span><pre>"
                   + esc(scrub("\n".join(train["tail"]))) + "</pre>")
    else:
        glimmer = "<span class='muted'>training not started</span>"

    return (
        "<h2>2. Agents at work</h2><div class='grid'>"
        f"<div class='card'><h3>🧑‍✈️ Claude (coordinator)</h3>{coord}</div>"
        f"<div class='card'><h3>🛠️ Muse Code (builder)</h3>"
        f"<div class='bignum'>{muse_big}</div>{builder}</div>"
        f"<div class='card'><h3>🧑‍🏫 Spark Open (teacher)</h3>{teacher}</div>"
        f"<div class='card'><h3>🧑‍⚖️ Referee (cloud box + grader)</h3>"
        f"{referee}</div>"
        f"<div class='card'><h3>🔎 Verifier</h3>{verifier}</div>"
        f"<div class='card'><h3>🌱 Glimmer (student)</h3>{glimmer}</div>"
        "</div>")


def section_training(train: dict) -> str:
    if train["losses"]:
        step_txt = (f"{train['step']} / {train['total']}"
                    if train["step"] is not None else f"{len(train['losses'])} pts")
        extra = []
        if train["minutes"] is not None:
            extra.append(f"{train['minutes']:.1f} min")
        if train["dollars"] is not None:
            extra.append(f"${train['dollars']:.2f}")
        body = (
            f"<div class='bignum'>loss {train['losses'][-1]:.4f}</div>"
            f"<div>step {esc(step_txt)}"
            + (f" · {' · '.join(extra)}" if extra else "") + "</div>"
            + loss_chart_svg(train["losses"]))
    elif train["tail"]:
        body = ("<span class='muted'>no loss lines yet, last log lines:</span>"
                "<pre>" + esc(scrub("\n".join(train["tail"]))) + "</pre>")
    else:
        body = "<span class='muted'>training log not found</span>"
    return f"<h2>3. Training</h2><div class='grid'><div class='card'>{body}</div></div>"


def section_factory(runs: list[dict], kept: int, thumbs: list[dict]) -> str:
    main = runs[0] if runs else None
    fams = (main["summary"].get("families", {}) if main else {})
    bars = []
    for fam in sorted(fams, key=lambda k: int(k) if str(k).isdigit() else k):
        try:
            rate = float(fams[fam].get("pass_rate", 0) or 0)
        except (TypeError, ValueError):
            rate = 0.0
        bars.append(
            f"<div>F{fam} {rate:.0%}<div class='bar'>"
            f"<i style='width:{rate * 100:.0f}%'></i></div></div>")
    bars_html = "".join(bars) if bars else "<span class='muted'>no data</span>"
    thumbs_html = "".join(
        f"<div class='thumb'><div class='muted'>{esc(t['name'])}</div>"
        f"{t['svg']}</div>" for t in thumbs)
    if not thumbs_html:
        thumbs_html = "<span class='muted'>no gallery SVGs yet</span>"
    return (
        "<h2>4. Factory</h2><div class='grid'>"
        f"<div class='card'><h3>Pass rate per family</h3>{bars_html}</div>"
        f"<div class='card'><h3>Kept records</h3>"
        f"<div class='bignum'>{kept}</div></div>"
        f"<div class='card'><h3>Gallery</h3><div class='thumbs'>"
        f"{thumbs_html}</div></div></div>")


def section_money(budget: dict, money: dict) -> str:
    parts = [f"<tr><td>Before logs (base)</td><td>${budget['base']:.2f}</td></tr>",
             f"<tr><td>Muse Code (all rounds)</td><td>${money['muse']:.2f}</td></tr>",
             f"<tr><td>Factory teacher</td><td>${money['factory']:.2f}</td></tr>"]
    for e in budget["extra"]:
        parts.append(f"<tr><td>{esc(scrub(e['label']))}</td>"
                     f"<td>${e['amount']:.2f}</td></tr>")
    return (
        "<h2>5. Money</h2><div class='grid'><div class='card'>"
        f"<div class='bignum'>${money['spent']:.2f} / ${budget['budget']:.0f}</div>"
        f"<div class='gauge'><i style='width:{money['pct']:.1f}%'></i></div>"
        f"<div class='muted'>{money['pct']:.0f}% of budget</div>"
        "<table>" + "".join(parts) + "</table></div></div>")


def section_timeline(events: list[dict]) -> str:
    items = "".join(
        f"<li>{esc(fmt_time(e['ts']))} — {esc(scrub(e['text']))}</li>"
        for e in events[:15])
    if not items:
        items = "<li class='muted'>nothing yet</li>"
    return (f"<h2>6. Timeline (last {min(15, len(events))})</h2>"
            f"<div class='card'><ul class='tight'>{items}</ul></div>")


def collect_events(root: Path, rounds: list[dict], runs: list[dict],
                   reports: list[dict]) -> list[dict]:
    events: list[dict] = []
    for c in git_info(root, n=5):
        events.append({"ts": c["ts"], "text": f"📝 {c['msg']}"})
    for r in rounds:
        events.append({"ts": r["mtime"],
                       "text": f"🛠️ Muse round {r['name']}: "
                               f"{r['steps']} steps, ${r['cost']:.2f}"})
    for rep in reports:
        events.append({"ts": rep["mtime"],
                       "text": f"🔎 verifier: {rep['title']}"})
    for r in runs:
        s = r["summary"]
        events.append({"ts": r["mtime"],
                       "text": f"🧑‍🏫 factory {r['name']}: "
                               f"{s.get('n_pass', '?')}/{s.get('n_calls', '?')} PASS"})
    events.sort(key=lambda e: e["ts"], reverse=True)
    return events


def build_page(root: Path, results_dir: Path, verifier_dir: Path,
               budget_path: Path) -> str:
    now = time.time()
    rounds = collect_muse_rounds(results_dir)
    runs = collect_factory_runs(results_dir)
    reports = collect_verifier(verifier_dir)
    train = parse_training(results_dir / "train-final-2026-10-30.log")
    kept = kept_records_total(results_dir)
    thumbs = collect_gallery(results_dir)
    budget = load_budget(budget_path)
    money = compute_money(budget, rounds, runs)
    events = collect_events(root, rounds, runs, reports)
    stamp = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="10">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forge mission control</title>
<style>{CSS}</style>
</head>
<body>
<h1>🚂 Forge mission control</h1>
<p class="sub">live snapshot {esc(stamp)} · refreshes every 10 s</p>
{section_pipeline(root)}
{section_agents(root, results_dir, verifier_dir, rounds, runs, reports, train)}
{section_training(train)}
{section_factory(runs, kept, thumbs)}
{section_money(budget, money)}
{section_timeline(events)}
<script>
try {{
  var y = sessionStorage.getItem("forge-scroll");
  if (y !== null) {{ window.scrollTo(0, Number(y)); }}
}} catch (e) {{}}
window.addEventListener("scroll", function () {{
  try {{ sessionStorage.setItem("forge-scroll", String(window.scrollY)); }}
  catch (e) {{}}
}}, {{ passive: true }});
</script>
</body>
</html>
"""


def build_once(root: Path, results_dir: Path, verifier_dir: Path,
               budget_path: Path, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        build_page(root, results_dir, verifier_dir, budget_path),
        encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Forge dashboard")
    parser.add_argument("--watch", nargs="?", const=10, default=None,
                        type=int, metavar="N",
                        help="rebuild every N seconds (default 10)")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--verifier", default=str(DEFAULT_VERIFIER))
    parser.add_argument("--budget", default=str(DEFAULT_BUDGET))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)
    root, results = Path(args.root), Path(args.results)
    verifier, budget, out = Path(args.verifier), Path(args.budget), Path(args.out)
    if args.watch is None:
        build_once(root, results, verifier, budget, out)
        print(f"wrote {out}")
        return 0
    interval = max(1, args.watch)
    while True:
        build_once(root, results, verifier, budget, out)
        print(f"wrote {out}")
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
