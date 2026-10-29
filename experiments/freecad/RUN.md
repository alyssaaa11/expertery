# FreeCAD gap test: exact run commands (verifier GO WITH 3 FIXES, forge-freecad-prerun-2026-10-29)

Needs the user's "yes run". Caps: Modal + Baseten $3.50 for the session; Meta (Wonder) $3.00. Out dir
`OUT=~/projects/forge/results/freecad-gap-2026-10-29`.
Keys are exported by Claude in the same shell from envsave's OPAQUE ids (verifier A1: `envsave get NAME` does not
work, so run_fc_session.sh's key lines fail safe; it is not used, run_session.sh is called directly with the same
hook; fix the wrapper in the next Muse round). Values are never printed.

1. Session (Glimmer deploy + pilot + main), with the hook from run_fc_session.sh:
   `export BASETEN_KEY=$(envsave get <Baseten opaque id>)`
   `export RUN_SESSION_RUNNER_CMD="$PWD/.venv/bin/python -I $PWD/experiments/freecad/runner_fc.py --workers 8 --budget-c 3.00 --budget-w 3.00"`
   `experiments/common/run_session.sh $OUT 3.50 --pilot "dry:pilot:G,S:1" --run "main:main-GS:G,S:1"`
   Pilot gate before touching GO (within 5 min, Modal scaledown 300 s): 6 answers; 0 harness and 0 INVALID; every
   answer has a grader verdict; S usage logged; G latency sane; Spark's dry verdicts plausible. Otherwise STOP.
2. Wonder single test call (no GPU): `export META_HERDSHOT_API_KEY=$(envsave get <HerdShot opaque id>)`
   `.venv/bin/python -I experiments/freecad/runner_fc.py --jobs dry --out $OUT/w-smoke --arms W --w-smoke --budget-w 0.50`
   If `/v1/chat/completions` is refused, repeat with `--w-endpoint https://api.meta.ai/v1/responses`. Check the usage
   fields (reasoning counted as output?) before step 3.
3. Wonder rescues on S's FAILs only: `.venv/bin/python -I experiments/freecad/runner_fc.py --jobs main --out $OUT/main-W
   --arms W --escalate-from $OUT/main-GS --budget-w 3.00 --budget 10` (`--budget 10` so only `--budget-w` decides,
   verifier A4; no Modal GPU or Baseten calls happen in this step).
4. Decision over G + S + W: `runner_fc.evaluate_fc_decision(records)` on main-GS/calls.jsonl + main-W/calls.jsonl.
   Report both lines: the runner's label AND the governing PLAN rule 5/6 (disagreement → stay on CadQuery).
