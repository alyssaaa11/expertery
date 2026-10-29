# Muse Code spec: cloud CadQuery box, factory, trained arm, final comparison (DRAFT)

Status: written by Claude 2026-10-29. Needs the verifier's check and the user's yes before Muse Code runs.
Plan: experiments/final/PLAN.md. Factory details: experiments/factory/SPEC.md (binding, with the changes in §2 here).

## Rules
- Work in ~/projects/forge. New files only in experiments/final/, experiments/factory/ and deploy/modal_forge.py; the
  one allowed edit outside them is §5 (runner_fc.py cached tokens) and §4's guard hook in experiments/train/forge_train.py.
- Do not edit frozen files: experiments/first-test/*, experiments/b2-hint/*, experiments/bmax/*, deploy/modal_glimmer.py,
  experiments/thinking/*. Import from them instead.
- Never open blind/ or experiments/option-a/; never print any expected*.json; code may use expected.json only inside
  the grader image.
- No network, no Modal runs, no model calls, no commit, never print keys. Tests are offline; any test that could reach
  Modal monkeypatches it to raise.
- Why the cloud: user rule "the Mac is the office": no AI-written answer code runs on the Mac.

## 1. `experiments/final/cloud_cq.py`: cloud CadQuery box + grader
Same design as experiments/freecad/cloud_exec.py and cloud_grade.py (read both):
- Box: a fresh Modal Sandbox per answer (block_network=True, no secrets, no volumes, cpu 1, memory 1024-4096 MiB,
  90 s box, 60 s run = runner.RUN_TIMEOUT). Image: python:3.12-slim + the libGL apt line + `cadquery==2.8.0 cadquery-ocp==7.9.3.1` (the
  Mac's versions; the grader pins the same) + a small run script. It holds no references, jobs or expected files.
- The run script executes answer.py, takes the `result` variable (same rule as runner.run_code: Workplane → its
  solid), and writes the part as **BREP** (exact; not STEP) plus a run-error text if it failed.
- Grader: a Modal function (app `forge-cq-grader`, cpu 1) with CadQuery 2.8 and checks.py baked in, plus
  /grader/first-test/{jobs.py, expected.json} and /grader/factory/jobs.jsonl. `grade(exam, job_id, brep_bytes)` →
  {verdict (0.2%, checks.TOL_DIFF), tight (1e-6), fails, measurements}. For first-test it scores against expected.json
  exactly as runner.py does; for factory it builds the job's reference program in the grader and scores both ways.
- `--check-refs --exam first-test|factory`: each reference built in the box → BREP → grader must PASS at 1e-6.
  Prints `REFS n/n PASS`.
- `--regrade <baseline results dir>`: re-run each recorded answer's code (from calls.jsonl) in the box, grade it, and
  write regrade.json with old verdict, new verdict (0.2%) and new tight (1e-6), per answer (the 199 final
  answers: BR 30, B2 90, BX 79), plus a measure-equality column: box measurements vs the recorded ones at the
  recorded print precision; print `MEASURE same=X changed=Y`; print `REGRADE same=X changed=Y`. (PLAN step 1.)
- Tests: BREP round trip of a simple part keeps volume and bbox at 1e-9; a fake sandbox returns bytes → grader
  verdict path; image file list has no references; regrade counts with fake records.

## 2. Factory (experiments/factory/SPEC.md, build it, with these changes)
- Teacher answers run in cloud_cq's box and are graded by its grader at 1e-6 (not runner.run_code on the Mac).
- Reference programs and the generator's own self-checks (valid solids, wrong variants fail) are trusted generator
  code and may run locally in tests.
- cached tokens: read `usage["prompt_tokens_details"]["cached_tokens"]` when present, else `usage["cached_tokens"]`,
  else 0. Test with the real Baseten usage shape (numbers illustrative):
  `{"prompt_tokens": 8307, "completion_tokens": 3438, "prompt_tokens_details": {"cached_tokens": 7552}}`.
- `make_jobs.py` also writes the 20 dev jobs as a jobs file usable by §3 (`--jobs-file`).

## 3. `experiments/final/runner_final.py`: the trained arm FT on the same yardstick
- Import from experiments/first-test/runner.py (frozen, unchanged): SYSTEM_PROMPT, build_messages, build_body,
  the code extraction, the summary/statistics helpers. Arm FT = arm A's messages (system + job text, no manual, no
  hint) and arm A's body (max_tokens 16000, temperature 1.0, top_p 0.95, top_k 64), with model "forge".
  Test: FT's messages and body equal runner.build_messages("A", …) / build_body(…) except the model name.
- Endpoint from env FORGE_URL / FORGE_KEY (missing → exit 2 with the variable name, no network).
- `--jobs dry|main` (first-test levels, as runner.py) or `--jobs-file <factory dev file>`; `--k`, `--workers 8`,
  `--budget`, `--gpu-start`, `--out`.
- Each answer: extract code → cloud box → cloud grader. calls.jsonl per answer (append live under a lock): job, rep,
  level, verdict (0.2%), tight (1e-6), fails, usage (prompt, completion, reasoning length), t_call_s, finish_reason.
- summary.json + report.md: pass rate all/medium/hard at 0.2% (decision) and at 1e-6 (reference), pass@k, tokens per
  correct part, seconds per answer (median, mean), arm wall-clock, $ per correct part = wall-clock h × $2.50 ÷ PASS.
- Budget guard as runner_fc (money left = cap − GPU time since gpu-start × $2.50/h; stop new calls when ≤ reserve).

## 3b. Arm BX on the cloud box, only for missing answers (user: "finish until the 30 jobs")
- `runner_final.py --arms BX --fill-missing results/bmax-baseline-2026-10-29/main-B2BX`: run only the (job, rep)
  pairs with no BX final record (expected: H12 ×2, H13-H15 ×3 = 11), endpoint GLIMMER_URL/GLIMMER_KEY (base Glimmer).
- Same loop as the frozen runner.do_bx_call: import build_messages("BX", …), build_bx_body, bx_self_check_message,
  BX_MAX_CALLS, BX_ERROR_HEAD, the examples and hint from the frozen files. The only change: each program runs in the
  cloud box, which returns (run_error, measure) in the same measure format as run_code_sandboxed (xmin…zmax, volume,
  solids), and the verdict comes from the cloud grader. Write per-round + final records like run_suite does.
- Test: with fake model replies and a fake executor, the cloud BX loop sends exactly the same message list, round by
  round, as runner.do_bx_call does with the same fake executor (build, run error, self-check, no-code-block end).
- Default `--workers 12` for `--fill-missing` (one wave). If fewer final records than missing pairs exist at the end,
  exit 3 with "INCOMPLETE: ask the user" and write no summary that compare.py would accept.
- Log the vLLM image digest (from the server) into summary.json for every session.
- compare.py merges these records with the baseline BX records (no (job, rep) twice; refuses on a duplicate).

## 4. Exam guard on the cloud box
forge_train.py's code check (run_train_code / default_train_meas) gets a hook to use cloud_cq's box for the training
record's code (measurements back from the grader-side measure of the BREP). The local sandbox path is removed for
training records. Exam references are still built in-process (trusted jobs.py). Test with a fake box.

## 5. C1 fix in experiments/freecad/runner_fc.py
`cached_tokens_of` reads the nested Baseten field first (same rule as §2). Test with the real usage shape above.

## 6. `deploy/modal_forge.py`: serve the trained model
Copy of deploy/modal_glimmer.py's settings (A100-80GB, same vLLM image and flags, max-model-len 32768, max_containers
1, 5-min scale-down, secret forge-glimmer) except: app `forge-trained`, model path `/vol/<name>/merged` from the
`forge-lora` volume (name from env FORGE_MODEL_NAME, default `final`), served name `forge`.
And `experiments/final/run_final_session.sh`: same behaviour as experiments/freecad/run_fc_session.sh (deploy, wait
ready, optional pilot + GO/STOP, whole-session cap with reserve, trap that always stops the app and prints it), for
runner_final.py with app forge-trained.

## 7. `experiments/final/compare.py`: the pre-registered decision (PLAN step 6)
Inputs: FT's run dir and the baseline dirs results/bmax-baseline-2026-10-29/main-B2BX and main-BR. Paired bootstrap
over the 30 jobs (10,000 resamples, seed 20261029), per-job pass rate over that arm's answers (BX uses the answers it
has). If any of the 30 jobs still has no BX answer, compare.py refuses (exit 2) and names the jobs. Tokens per correct part are printed
split into prompt and completion; bar (d) prints wall-clock and $ per correct part first. Prints each bar (a)-(d) with the numbers and PASS/FAIL, then "CLAIM HOLDS" only if all four pass. Tables for
all/medium/hard. Tests: fake records for each bar at its boundary (−5, −15, 1.5×, ÷3) and one all-pass case, and the refusal
when a job has no BX answer.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common` passes (the old 150 plus the new tests).
- `runner_final.py --jobs main --out X` with no keys exits 2 with the missing-variable message, no network.
- `forge_train.py smoke --cap-dollars 2.0` still prints CAP REFUSED and exits 2.
Report: files changed, the pytest line, anything not followed.
