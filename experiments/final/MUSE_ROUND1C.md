# Muse Code round 1c: job text = reference (verifier G1, forge-factory-fix-2026-10-30) — waits for the user's yes

The verifier parsed all 200 jobs: in 4 families the job text does not state what the reference builds, so no answer
faithful to the text can pass at 1e-6 (evidence: ~/agents/verifier/reports/forge-factory-fix-2026-10-30.evidence/04-text-vs-ref.txt).
| Family | Jobs | Example (text vs reference) |
|---|---|---|
| F3 dovetail | 17/20 | F3-1 floor width 21.2 vs 21.3; floor centre 27.8 vs 27.75 |
| F4 cam plate | width 9/20; ends 20/20 | slot width 5.9 vs 6.0; square ends never stated |
| F7 T-slot | 13/20 | F7-1 slot centre 21.4 vs 21.45 |
| F10 funnel | 20/20 | rim "4.9 wide" vs 8.2; recess bottom diameter not given |
All rules in experiments/final/MUSE_SPEC.md "Rules" apply (no network, no Modal, no model calls, no commit, never print
keys, never open blind/ or experiments/option-a/, never print any expected*.json). Do not edit checks.py or cloud_cq.py.

## Build in this round ONLY (experiments/factory/)
- `generator.py`: in every family, **round each parameter to the printed precision first, then build the reference
  from exactly the printed numbers** (no derived or unrounded value may reach the reference). F4: the text says
  "square ends" (or whatever the reference builds), and the slot width printed = the width built. F10: the text gives the
  rim's inner and outer diameters and the recess bottom diameter. Keep seed 20261029, ids, families, 20 jobs each, and
  the parameter ranges (features must still not touch by accident).
- `make_jobs.py` self-check: a new column TEXT=REF per family. For every job, re-parse the numbers in the text and assert
  that each number the reference program uses (its literal numbers, after rounding) appears in the text; a family
  passes only at 20/20. Keep VALID, WRONG-1/2 and OVERLAP. Why: --check-refs grades a reference against itself and
  cannot see this.
- Re-run make_jobs.py (jobs.jsonl, split.json, jobs_dev.jsonl change; the dev ids may stay the same if the seed logic
  allows; report whether they did). factory_version changes automatically.
- Tests: a family whose text prints 21.2 while its reference uses 21.3 fails TEXT=REF; every family passes TEXT=REF on
  the generated file.
- `patterns.py` (verifier note, forge-factory-fix-2026-10-30): an API/HTTP error from the teacher model (no answer
  produced because the call failed) is kind `our_bug` (category `harness`), not `teacher_habit`. Test for it.
- `experiments/train/forge_train.py` exam guard (verifier note): open `cloud_cq._app.run()` once for the whole guard
  pass, not once per record (slow). Keep the F1 test passing.
- `gallery.py`: the SVG must not be clipped (fit the viewBox to the drawing with a margin). Small.

## Done when
- pytest (same 5 folders) passes: 237 plus the new tests.
- make_jobs prints the table with TEXT=REF 20/20 in all 10 families and SELF-CHECK OK.
- gallery.py rewrites results/factory-gallery/index.html (10 cards, not clipped).
Report: files changed, the pytest line, the new self-check table, sha256 of the new jobs.jsonl/split.json/jobs_dev.jsonl,
whether the dev ids changed, and anything not followed.
