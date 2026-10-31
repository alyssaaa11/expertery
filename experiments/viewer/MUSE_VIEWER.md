# Muse Code round: answer viewer (user request 2026-10-31: "I need to be aware of all… I don't even know how Glimmer is answering")

Goal: one static HTML page per run where the user sees every answer: the task, Glimmer's thinking, its code, a
picture of ITS part next to the CORRECT part, and the referee's verdict. It is also the start of the demo video.

Rules: all of experiments/final/MUSE_SPEC.md "Rules" (no network, no Modal runs, no model calls, no commit, never print
keys, never open blind/ or experiments/option-a/, never print any expected*.json). **Do not edit any existing file**
(a paid run is using experiments/final/* right now). Put everything in a NEW folder experiments/viewer/.
AI-written answer code never runs on the Mac: Glimmer's code is rendered ONLY inside the cloud CadQuery box.

Read first: experiments/factory/gallery.py (SVG export settings SVG_OPT, the card HTML), experiments/final/cloud_cq.py
(build_image, sandbox_kwargs, run_answer_in_box, run_cq_box.py, the BREP path; reuse by IMPORT, do not copy or edit),
experiments/final/runner_final.py (calls.jsonl record fields: job, verdict, fails, failed_checks, measurements,
run_error, code, reasoning, reasoning_chars, completion_tokens, seconds, prompt_tokens).

## Build
1. `experiments/viewer/render_cloud.py`: a NEW Modal app `forge-viewer` with one function `render_svgs(items)` that, in
   ONE sandbox built with cloud_cq's image and sandbox_kwargs (lifetime ≤ 2 h, network blocked), runs each answer code
   with the same runner script as the grader (so `result` is taken the same way), exports the shape to SVG with
   gallery's SVG_OPT, and returns {id: svg_text | error_text}. Each answer gets the same 60 s limit as grading. A
   `--budget` dollars hard stop (sandbox seconds × the cloud_cq rates). References are trusted generator code, but
   render them in the same box too (simplest and the same view).
2. `experiments/viewer/make_viewer.py --run <results dir with calls.jsonl> --jobs <jobs file> --out <dir>
   [--limit N] [--budget 0.30] [--offline]`:
   - reads calls.jsonl + the jobs file; for each record: task text, verdict (big ✓ PASS / ✗ FAIL / ⚠ crash), the
     referee's fails list, the answer's own measurements, Glimmer's thinking (collapsed `<details>`, full text), its code
     (`<pre>`, HTML-escaped), the crash's last lines, tokens and seconds;
   - the two pictures side by side: "Glimmer's part" and "correct part" (SVG from render_cloud; `--offline` = no
     pictures, for tests);
   - a summary at the top: pass rate, crashes, wrong shapes, per family table, median tokens and seconds;
   - filters (plain HTML anchors, no JS libraries): all / pass / fail / crash, and by family;
   - writes `<out>/index.html` (one file, inline SVG, no network) and `<out>/svgs.json` (cache, so re-runs cost $0).
3. Tests (offline, fake render): HTML-escaping of code and thinking (a `<script>` in code must appear as text);
   cache reuse; budget stop; the page counts match calls.jsonl; no reference code or expected values appear as text on
   the page (only the reference PICTURE).

## Report back
Files, pytest count, the exact commands. Do not run anything paid.
