# Muse Code: "Forge mission control" dashboard (user request 2026-10-30: "a cute dashboard in Chrome showing all
# the agents and all the process in a cool way")

Build ONE read-only dashboard that shows the whole Forge pipeline and every agent at work, live, in Chrome.
All rules in experiments/final/MUSE_SPEC.md "Rules" apply (no network, no Modal runs, no model calls, no commit, never
print keys, never open blind/ or experiments/option-a/, never print any expected*.json). A training run is LIVE: do
not edit any existing file outside `dashboard/` and do not write under results/ except `results/dashboard/`.

## Files (new only)
- `dashboard/build.py`: reads local files only and writes `results/dashboard/index.html` (one self-contained file:
  inline CSS + inline SVG, a little vanilla JS, no external fonts, scripts or CDNs). `--watch N` rebuilds every N
  seconds (default 10); the page reloads itself every 10 s (meta refresh), keeping the scroll position.
- `dashboard/test_build.py`: tests with fake input folders (tmp_path).

## What the page shows (cute and clear: soft colours, rounded cards, one emoji avatar per agent, big numbers)
1. **The pipeline as a train of stations** left → right, each with a status light (done ✅ / running ⏳ / waiting ⏸ /
   stopped ⛔): Factory pilot → Factory main → Training → Practice test (dev) → B-max finish → Final exam → Compare →
   Demo. A station is "done" when its output file exists (paths below), "running" when its log changed in the last
   2 minutes, else "waiting".
2. **Agents panel**, one card per agent with what it did last and when:
   - 🧑‍✈️ Claude (coordinator): last commit message + time (`git log -1`, read-only).
   - 🛠️ Muse Code (builder): rounds from `results/muse-*.jsonl` (name, steps, files written/edited, cost from the
     `run.usage` event at $1.25 / $0.15 cached / $4.25 per M), the latest round on top.
   - 🧑‍🏫 Spark Open (teacher): factory runs `results/factory-*/summary.json` + calls.jsonl (answers, PASS, cost).
   - 🧑‍⚖️ Referee (cloud box + grader): PASS / FAIL / INVALID counts from the same calls.jsonl.
   - 🔎 Verifier: newest 6 reports in `~/agents/verifier/reports/forge-*.md` (title line + "Verdict:" line + date).
   - 🌱 Glimmer (student): training status from `results/train-final-2026-10-30.log` (see 3).
3. **Training card**: parse the training log for loss per step (any line with "loss" and a number), current step /
   total, minutes, and $ if printed; draw a small SVG line chart of the loss going down. If no loss lines yet, show the
   last 5 log lines (skip Modal "Uploaded/Created" noise).
4. **Factory card**: pass rate per family (10 small bars), kept records total (`results/factory-train-*/train_records.jsonl`
   lines), and the 10 gallery SVGs from `results/factory-gallery/svgs/` as small thumbnails.
5. **Money card**: a fuel gauge of spent vs the budget, with the budget read from a small `dashboard/budget.json`
   ({"budget": 65, "base_spent_before_logs": ...}); spent = Muse (all logs) + factory teacher costs + an optional
   `extra` list in budget.json for Modal amounts entered by hand. Show the parts.
6. **Timeline** at the bottom: the last 15 events (commits, Muse rounds, verifier reports, factory runs) with times.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q dashboard` passes.
- `~/projects/forge/.venv/bin/python dashboard/build.py` writes results/dashboard/index.html from the real files,
  without errors, in under 5 s; the page has the 6 sections.
- The page makes no network request (no http(s):// in src/href attributes) and contains no key-like strings.
Report: files written, the pytest line, and anything you did not follow.
