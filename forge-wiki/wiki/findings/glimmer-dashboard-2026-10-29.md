# Glimmer live dashboard (step-2 baseline run, 2026-10-29)

**Summary**: A page that shows how Glimmer is doing in the baseline run: pass rate, answers done, tokens and model time
per version (plain, hint 1 try, all fair fixes), every answer job by job (hover a cell for why it failed), and the GPU
time and cost so far. Open it in Google Chrome; it reloads every 20 s while the run is going.

**Open**: `forge-wiki/wiki/assets/dashboards/glimmer-baseline-2026-10-29.html` (double-click, or
`open -a "Google Chrome" <path>`). Made by `experiments/bmax/glimmer_dashboard.py` (`--loop` rewrites it every 20 s until
the run's GPU is stopped; data from `results/bmax-baseline-2026-10-29/*/calls.jsonl`, embedded in the page because
Chrome blocks file:// fetches).

**Last updated**: 2026-10-29

---
- Hint and all-fixes results are written by the runner when that part of the run ends, so until then the page shows a live
  counter of answers that have gone through the sandbox.
- verified (11:12, main-BR/calls.jsonl): **plain Glimmer 26/30 = 87%** on the 30 held-out jobs (first test: 20/30 = 67%,
  same prompt, then unsandboxed and served the same way). That is +20 points, right at the edge of the PLAN's luck check
  (67% ± 20). Failures: M12, M14, H2, H6.
