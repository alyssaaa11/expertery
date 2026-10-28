# Change spec for runner.py (after the verifier audit, user approved 2026-10-28)

Change `runner.py` and `test_runner.py` only, plus `../../deploy/modal_glimmer.py` (item 5). Everything else is frozen.

1. **Request body:** `{"model", "messages", "max_tokens": 16000, "temperature": 1.0, "top_p": 0.95, "top_k": 64}` for
   all three arms (was max_tokens 8000, temperature 0.6, no top_p/top_k).
2. **Decision (compute_decision), first match wins, rates compared in whole percentage points (round(rate*100)):**
   1. B ≥ 80 → `STOP (manual is enough)`
   2. C < 20 → `Spark can't teach`
   3. B ≤ 60 and C ≥ 30 and C − B ≥ 25 → `GO to training`
   4. otherwise → `grey zone`
   If any arm has INVALID > 5%, prefix `run not valid (INVALID > 5% in an arm); `. If B or C has no scored calls,
   `grey zone (too few scored calls)`. Remove the old 15–25 grey-band override.
3. **Arm C cap:** besides the total `--budget` (default 5.0), stop sending new arm-C calls once arm C's own estimate
   passes `--budget-c` (default 3.0). Record it in summary.json and report.md.
4. **Cost note:** report.md must say: "GPU estimate covers only the runner's own wall-clock; the real Modal cost (incl.
   cold start) comes from `modal billing report`." Add an optional `--gpu-start <unix seconds>` so run_live.sh can pass the
   deploy start time; when given, the GPU estimate uses that start instead of the runner's start.
5. **deploy/modal_glimmer.py:** change `--max-model-len` from 16384 to 32768. Nothing else in that file.
6. **Tests:** update/add tests for: the new body (incl. top_p/top_k, 16000), every decision branch including the old
   problem cases (B=40,C=60 → grey; B=40,C=65 → GO; B=85,C=100 → STOP; B=80,C=95 → STOP; C=15 → can't teach), the
   arm-C cap, and `--gpu-start`. All tests must pass with the venv python, no network.
