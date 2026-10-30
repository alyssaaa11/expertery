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
`--escalate` (decision, user 2026-10-29): for every id Spark FAILED, ask Muse Wonder (`muse-wonder-1.0`, api.meta.ai,
META_HERDSHOT_API_KEY, same prompt) once; keep its answer only if it PASSES at 1e-6. Each record gets `teacher: spark|wonder`;
summary reports the share of records from Wonder (why: privacy reporting; Wonder is a closed API). Separate budget
`--budget-w` (Meta credit).
`--retry-failed` re-asks only FAILed ids (k = 2 at most) while the budget lasts. The budget guard stops new calls when
spent + 8 in-flight calls × $0.075 would pass the budget (why: in-flight answers still cost money, verifier A2).
Log `cached_tokens` from usage in every record (why: x-session-affinity caching is not verified; cost depends on it).
Output: calls.jsonl, summary.json (pass rate per family, tokens, cost), and `train_records.jsonl` = {"id","text","code"}
for every PASS at 1e-6 among non-dev ids (code = the teacher's extracted code).

## 3. Tests (offline, fake HTTP)
Generator determinism (same seed → same file), every reference valid, wrong variants fail, overlap check, dev split
excluded from pilot/train records, budget guard math with cached tokens, a fake teacher reply that PASSes ends up in
train_records.jsonl and a FAIL does not. Run `~/projects/forge/.venv/bin/python -m pytest -q experiments/factory`.

## 4. Learning loop: `patterns.py` (decision, user 2026-10-30: "if it detects repeating broken patterns it could improve that part")
Note: written into this file after Muse round 1 (Claude's edit missed this file; Muse built §2c from the round brief).
Goal: find failures that repeat, so the cause is fixed in the factory before the next run instead of paying for the same
failure again. The loop **suggests**; the user approves every fix (decision, user 2026-10-30); Muse Code applies it.
CLI: `patterns.py --runs <teacher run dir> [<dir> ...] --out <dir> [--min-count 3]`.
- Reads only calls.jsonl from factory teacher runs (refuses any path under blind/, experiments/option-a/,
  experiments/first-test/; skips dev ids). No network, no model calls, edits no file; writes patterns.json + patterns.md.
- Every FAIL or error gets a signature (category, key). Categories: `harness` (box error, timeout, no BREP, grader
  exception), `no_code`, `run_error` (exception type + message with numbers replaced by N), `wrong_shape` (sorted failed checks).
- A signature seen >= min-count times is a pattern. Kind: `our_bug` if harness; `our_wording` if wrong_shape and >= 80%
  of its hits in one family; `teacher_habit` if run_error/no_code, or wrong_shape spread over >= 2 families.
- patterns.md: one row per pattern: kind, signature, count, families, 2 example ids, where to fix
  (our_bug -> factory/box code; our_wording -> that family in generator.py; teacher_habit -> teacher_notes.md).
- `teacher_notes.md` (starts empty): notes added to the teacher prompt after the manual; never in Glimmer's training prompt.
- Every teacher call logs `factory_version` = sha256 of generator.py + teacher.py + teacher_notes.md (first 12 hex).
- Locked (never suggested or changed): checks.py tolerances (1e-6 / 0.2%), the cloud box and grader, the dev split, the
  exam files, the overlap check. Why: changing the referee would raise the pass rate without better data.
- When: after the pilot and before any retry or main run, never during a run. After a family text change: re-run the
  make_jobs self-check + overlap check and Claude's blind rebuild for that family, then re-freeze (sha256).
- After a wording fix: re-run make_jobs and re-freeze jobs.jsonl, split.json and jobs_dev.jsonl by sha256 before the dev
  check (verifier F5). The training report discloses that our_wording fixes push data towards phrasings the teacher can
  solve (verifier N1).
- patterns.py also refuses records whose id is not `F<n>-<m>` or is a dev id (verifier F4: pointed at results/ it would
  read exam and baseline runs).
- Tests: 3 identical run errors over 2 families -> teacher_habit; 3 harness -> our_bug; 3 wrong_shape in one family ->
  our_wording; 2 hits -> no pattern; dev ids ignored; forbidden path -> exit 2; factory_version changes with teacher_notes.md.
