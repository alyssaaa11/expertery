# Spec for Muse Code: factory (practice-job generator + teacher runner) — DRAFT, needs verifier + user yes

Rules: work in ~/projects/forge; new files only in experiments/factory/; never open blind/ folders,
experiments/option-a/, or expected*.json contents; no network, no model calls, no commit, never print keys; reuse
experiments/first-test/checks.py (TOL_DIFF = 1e-6) and runner.run_code with experiments/b2-hint/sandbox_cq.sb.

## 1. `generator.py`: deterministic practice jobs (seed 20261029)
Ten NEW hard-style families (each job = 4-8 features placed by exact relations; numbers vary per job within safe
ranges; every job's text gives every coordinate, like experiments/first-test/jobs.py texts):
1. Spool / bobbin: two flanges, a core, a wire slot through one flange, a centre bore.
2. Manifold block: a block with 2-3 cross-drilled ports along X and Y at given heights, one blind port from the top.
3. Dovetail slide: a block with a dovetail groove along X (given angle and widths) and two end holes. (replaces the polar
   flange plate: too close to exam M6, verifier A3)
4. Cam plate: a disk with an eccentric bore and a keyless slot at a given angle.
5. Pipe tee fitting: a main tube along X with a branch tube along Y, both bored through, a flange at one end.
   (replaces the battery holder: grid pockets too close to exam H15, verifier A3; recommended to the user)
6. Triangular lattice panel: a plate with a row of alternating triangular cut-outs and a solid border. (replaces the
   comb/fork: too close to exams H9/H4, verifier A3)
7. T-slot rail: a bar with a T-shaped slot along its length and end holes.
8. Bezel frame: a frame with a rounded-rectangle window and four mounting tabs with holes.
9. Ported cap: a cylinder cap with a side port (horizontal cylinder) and a top recess.
10. Funnel / hopper: a cone frustum shell with a cylindrical spout and a top rim. (replaces the stepped rail: too close
   to exam H11, verifier A3; recommended to the user)
Family → nearest exam job (checked by Claude from experiments/first-test/jobs-list.md; why it matters: a near-copy lets
the trained model memorise exam answers and makes the final exam invalid):
| Family | Nearest exam job | Distance |
|---|---|---|
| 1 spool | M5 stepped shaft (cylinders on one axis) | different: flanges, slot through a flange |
| 2 manifold | H6 bearing housing (block + bores) | different: orthogonal ports at set heights |
| 3 dovetail | M2 T-profile (extruded profile) | different: cut groove with an angle |
| 4 cam plate | M12 pulley / M6 flange (disk + bore) | different: eccentric bore, angled slot |
| 5 pipe tee | H10 pipe clamp | different: two crossing bored tubes |
| 6 lattice | H15 vented lid (pattern of cut-outs) | different: triangles, alternating orientation |
| 7 T-slot | M7 U-channel | different: T-shaped undercut slot |
| 8 bezel | H2 board plate | different: rounded window, outside tabs |
| 9 ported cap | M3 open box / H1 enclosure | different: cylindrical, side port |
| 10 funnel | none close (no cones in the exam) | different |
Parameter ranges: every family defines min/max for each number so that features never touch or overlap by accident
(if they did, references could be invalid solids and teacher FAILs would measure our bug, not the teacher).
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
($1.25/M uncached input, $0.15/M cached, $4.25/M output); the stop rule is the in-flight rule below.
Pilot = the 20 non-dev ids that come first per family (2 per family), never dev ids.
`--ids train` skips every id that already has an answer in earlier runs' calls.jsonl (pass `--prior <dirs>`), and
train_records.jsonl holds at most one record per id (the first PASS). Why: without this the pilot jobs get paid for
twice and the same job could appear twice in training (verifier A6).
`--retry-failed` re-asks only FAILed ids (k = 2 at most) while the budget lasts. The budget guard stops new calls when
spent + 8 in-flight calls × $0.075 would pass the budget (why: in-flight answers still cost money, verifier A2).
Log `cached_tokens` from usage in every record (why: x-session-affinity caching is not verified; cost depends on it).
Output: calls.jsonl, summary.json (pass rate per family, tokens, cost), and `train_records.jsonl` = {"id","text","code"}
for every PASS at 1e-6 among non-dev ids (code = the teacher's extracted code).

## 3. Tests (offline, fake HTTP)
Generator determinism (same seed → same file), every reference valid, wrong variants fail, overlap check, dev split
excluded from pilot/train records, budget guard math with cached tokens, a fake teacher reply that PASSes ends up in
train_records.jsonl and a FAIL does not. Run `~/projects/forge/.venv/bin/python -m pytest -q experiments/factory`.
