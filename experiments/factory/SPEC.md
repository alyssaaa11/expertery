# Spec for Muse Code: factory (practice-job generator + teacher runner) — DRAFT, needs verifier + user yes

Rules: work in ~/projects/forge; new files only in experiments/factory/; never open blind/ folders,
experiments/option-a/, or expected*.json contents; no network, no model calls, no commit, never print keys; reuse
experiments/first-test/checks.py (TOL_DIFF = 1e-6) and runner.run_code with experiments/b2-hint/sandbox_cq.sb.

## 1. `generator.py`: deterministic practice jobs (seed 20261029)
Ten NEW hard-style families (each job = 4-8 features placed by exact relations; numbers vary per job within safe
ranges; every job's text gives every coordinate, like experiments/first-test/jobs.py texts):
1. Spool / bobbin: two flanges, a core, a wire slot through one flange, a centre bore.
2. Manifold block: a block with 2-3 cross-drilled ports along X and Y at given heights, one blind port from the top.
3. Polar-pattern flange plate: plate with N holes on a bolt circle (N 4-8), a central boss with a bore.
4. Cam plate: a disk with an eccentric bore and a keyless slot at a given angle.
5. Battery holder: a box with an M×N grid of cell pockets and a slot in one wall.
6. Comb / fork: a base bar with N tines of given width/gap/length.
7. T-slot rail: a bar with a T-shaped slot along its length and end holes.
8. Bezel frame: a frame with a rounded-rectangle window and four mounting tabs with holes.
9. Ported cap: a cylinder cap with a side port (horizontal cylinder) and a top recess.
10. Stepped mounting rail: a rail with 3 height steps and a hole on each step.
Each family: a function params → (text, reference_program_source); 20 jobs per family (200), ids F<family>-<n>.
`make_jobs.py` writes experiments/factory/jobs.jsonl (id, family, text, reference source) and a seed-chosen dev split
(2 per family = 20 dev ids) into split.json. Self-check: every reference builds one valid solid in-process; two
"wrong" variants per family (a moved feature, a wrong size) FAIL at 1e-6; print a 10-family table.
Overlap self-check: no job text has difflib ratio ≥ 0.9 (exact numbers) to any first-test job text (read texts from
experiments/first-test/jobs.py).

## 2. `teacher.py`: Spark Open on Baseten
CLI: `teacher.py --jobs jobs.jsonl --ids pilot|train|all --out <dir> --budget-dollars X [--k 1] [--retry-failed]`.
Prompt = system "You write CadQuery Python code. Units are millimetres. Assign the final solid to a variable named result.
Reply with exactly one Python code block and nothing else." + user "Here is the CadQuery manual. Use it.\n\n" + manual
+ "\n\n" + job text. Body: model meta-models/muse-spark-open-1026, max_tokens 16000, temperature 1.0, top_p 0.95,
header x-session-affinity (same value per run, for prompt caching). Key from env BASETEN_KEY. 8 parallel workers.
Each answer: extract the code, run it in the sandbox, score against the job's reference at 1e-6. Log per call: id,
usage (incl. prompt_tokens_details.cached_tokens), latency, verdict, fails. Budget guard counts cost from usage
($1.25/M uncached input, $0.15/M cached, $4.25/M output) and stops new calls when the next call would pass the budget.
Pilot = the 20 non-dev ids that come first per family (2 per family), never dev ids.
Output: calls.jsonl, summary.json (pass rate per family, tokens, cost), and `train_records.jsonl` = {"id","text","code"}
for every PASS at 1e-6 among non-dev ids (code = the teacher's extracted code).

## 3. Tests (offline, fake HTTP)
Generator determinism (same seed → same file), every reference valid, wrong variants fail, overlap check, dev split
excluded from pilot/train records, budget guard math with cached tokens, a fake teacher reply that PASSes ends up in
train_records.jsonl and a FAIL does not. Run `~/projects/forge/.venv/bin/python -m pytest -q experiments/factory`.
