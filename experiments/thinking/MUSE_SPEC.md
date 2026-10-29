# Muse Code spec: run the thinking exam in the FreeCAD runner (+ open report nits)

Status: written by Claude 2026-10-29. It needs the verifier's check and the user's yes before Muse Code runs.

The rules from experiments/freecad/SPEC.md still apply:
- Edit only files in experiments/freecad/ and experiments/common/dashboard.py. Do not edit experiments/thinking/; it is
  frozen. Read thinking_jobs.py and STANDARDS.md there, but never open or print experiments/thinking/expected.json.
  Only code may use it, through cloud_grade.
- Never open blind/ or experiments/option-a/. Never print any expected*.json.
- No network, no Modal runs, no commit.
- Tests use small fake expected dicts, never the real files.

## Why
The FreeCAD gap test showed the first exam is dictation: every coordinate is in the text (Glimmer 93%). The new exam
in experiments/thinking/ gives only goals and a company standard, NDS-1. The model must derive the sizes. The runner
must run this exam with the same box, grader and arms, and with no change to the first-test path.

## 1. `--exam {first-test,thinking}` (default first-test, so old commands behave the same)
- **Jobs.** For thinking, import JOBS from experiments/thinking/thinking_jobs.py with the same keys (id, level, text,
  build). level "dry" (D1, D2 and the calibration jobs C1-C3) is the pilot; levels "medium" and "hard" are the main
  exam (13 jobs: T2, T5-T10, E1-E6). Select by level, never by a hard-coded id list. Do not import first-test's jobs.py for this exam, because
  both exams use the ids D1 and D2.
- **Prompt.** The user message is FC_MANUAL_PREFIX + manual, then "\n\nHere is the company design standard. Apply
  it.\n\n" + the contents of experiments/thinking/STANDARDS.md, then "\n\n" + the job text. Keep the system prompt
  unchanged. Freeze the standard by SHA-256, the same way as the manual: compute the hash at build time, write it as a
  constant, and refuse to run on a mismatch.
- **Grader.** Change `grade(job_id, step_bytes, exam="first-test")`. The image bakes both exams:
  - /grader/first-test/{jobs.py, expected.json}
  - /grader/thinking/{thinking_jobs.py, expected.json}
  - checks.py, shared
  The function picks the exam's folder, so one exam's ids never resolve against the other's jobs. Give `check_refs`
  the same `exam` parameter, plus a CLI `cloud_grade.py --check-refs --exam thinking` that must print REFS 13/13 PASS.
- **Output.** Write `exam` into every calls.jsonl record and into summary.json.

## 2. Wonder per failed sample
At k = 3, `--escalate-from` returns failed (job, rep) pairs, not a set of job ids. W makes one try per failed S
sample, with the same rep index. The teacher T passes a (job, rep) if S passed it or W rescued it. This is the
denominator in experiments/thinking/PLAN.md.

## 3. The thinking decision (exact rules from experiments/thinking/PLAN.md; first-test keeps its own)
- `decide_thinking(records)`: rates are PASS ÷ (PASS + FAIL) over all answers of an arm.
- Wins: count a job when S passes ≥ 2 of 3 and G passes ≤ 1 of 3.
- Apply the rules in this order:
  0. Harness/INVALID > 5% in any arm → RUN INVALID.
  1. S < 60% → "INVALID: exam too hard or ambiguous; write new jobs".
  2. S ≥ 70%, S − G ≥ 25, and wins ≥ 4 → "gap found: factory target = company-standard thinking jobs in FreeCAD".
  3. G ≥ 70% → "no gap: next test = same jobs without the standard".
  4. Otherwise → "grey: decide with the user".
- Evaluate the rules on S and on T. If they disagree, the S result governs. Print the "Governing rule" line only on
  disagreement.
- Report Wonder's share of T's passes.
- Tests: one fake-record case per rule, one S/T disagreement case, and one boundary case each at exactly 60, 70 and 25.

## 4. Open nits from the FreeCAD gap test (all small)
1. **`-I` fix.** runner_fc.py adds its own folder (HERE) to sys.path before importing cloud_exec, so it also works
   under `python -I`. Leave run_fc_session.sh's command as it is.
2. **Live writing.** Append each record to calls.jsonl as soon as it is graded (flush), not only at the end. The
   final file must hold the same records as now.
3. **Costs in `--summarize`.** It keeps the per-arm costs and token counts from the two runs; today it drops them. Do
   not print an empty "W" heading when W has no records.
4. **Spark cost.** Charge Spark cached input at the cached price, using cached_tokens; today it charges it as uncached.
5. **Dashboard.** experiments/common/dashboard.py, for runner_fc runs:
   - read calls.jsonl live;
   - show boxes run and grader calls (count of records with a box result or grade);
   - show the GPU minutes from `--gpu-start` (now − start);
   - show the exam name.
   It must not change for first-test runs.
6. **Session script.** run_fc_session.sh passes `--exam` through. Use a spec form "<exam>:<jobs>:<subdir>:<arms>:<k>",
   and keep the old 4-field form meaning first-test.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/freecad experiments/common` passes all tests: the old
  107 plus the new ones.
- `runner_fc.py --exam thinking --jobs dry --out X` with no keys exits 2 with the missing-variable message. It must not
  make a network or Modal call.
- An offline test shows the thinking prompt contains the manual, the standard and the job text in that order.

Report: list the files changed, give the pytest line, and name anything not followed.

## Round 2 (binding; from the verifier's early blocker and the user's 2026-10-29 points)
1. **Verdict at 1e-6 for the thinking exam.** For `--exam thinking`, the PASS/FAIL that rates and decisions use is the
   grader's `tight` field (1e-6). Record the 0.2% `verdict` next to it, and report it as a second table titled "0.2%
   (for reference, not the decision)". Why: at 0.2% the verifier found 4 rule-breaking answers that PASS (a pilot
   through the floor, a counterbore from the wrong side). first-test keeps 0.2% as before.
   Test: a fake record with verdict PASS and tight FAIL counts as FAIL under the thinking exam and as PASS under
   first-test.
2. **Speed and cost per answer as a main result.** summary.json and report.md give, per arm:
   - median and mean wall time per answer in seconds, from request sent to response received;
   - mean input tokens, cached tokens and output tokens;
   - $ per answer;
   - answers per dollar.
   Put this table directly under the accuracy table, under the heading "Speed and cost per answer". Also write the
   ratios G÷S and S÷G for time and $. Every calls.jsonl record already has, or must get, `t_call_s` (wall time of the
   model call only) and its usage.
3. **Frozen standard.** The STANDARDS.md SHA-256 constant must equal
   f9aa341e6224fdfbf0770900b9404fbf3146577e0640b91b5cc1e6b31784877c (NDS-1 with 40 rules).
4. **Call timeout and tokens.** The prompt is now longer (manual + a 40-rule standard). Keep max_tokens and the call
   timeout as for the first-test FreeCAD run, and log the prompt token count of the first call per arm.
