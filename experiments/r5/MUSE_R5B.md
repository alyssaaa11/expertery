# Muse Code round R5b: fix the R5 build (verifier FAIL forge-r5-build-2026-10-31, B1-B6 + N1-N2)

Read first: ~/agents/verifier/reports/forge-r5-build-2026-10-31.md (findings B1-B6, N1, N2 with file:line), this round's
earlier spec experiments/r5/MUSE_R5.md, PLAN.md, and the code you wrote in commit e473fda. All rules in
experiments/final/MUSE_SPEC.md "Rules" apply (no network, no Modal runs, no model calls, no commit, never print keys,
never open blind/ or experiments/option-a/, never print any expected*.json). **Exception this round: you MAY edit
experiments/final/cloud_cq.py, but only for B3 (sandbox reuse helpers, if needed) and B5 (grader job lookup). Its
scoring, BREP path and measurement code must not change.** Old factory/exam grading must give the same verdicts as today.

## Fix in this round ONLY
1. **B1, the cloud check runs in the app**: make_jobs `--cloud-check` wraps all remote calls in
   `with modal.enable_output(), cloud_cq._app.run():`, as runner_final.py does (~line 1310). Add a fake test proving
   that the remote calls happen inside an app context (the fake raises if called outside).
2. **B2, honest budget and output**: the per-job cost = measured sandbox seconds × ($0.142 per core-hour × cores +
   $0.024 per GiB-hour × GiB) + grader calls, from the box's actual size. Print it after the first 20 jobs and
   stop if the projected total exceeds `--budget`. Jobs that were not checked, or whose reference fails to build
   exactly one valid solid, are DROPPED from the output (listed in a `<out>.dropped.json` with reasons). Exit non-zero
   if any reference failed or the budget stopped the run before every job was checked.
3. **B3, one reused box**: build the sandbox ONCE (`build_sandbox()`), pass it to every `run_answer_in_box(code,
   sandbox=box)`, and terminate it at the end (also on error, in `finally`). If the box dies, rebuild once, then stop.
4. **B4, measured dedup across sets**: save each set's measures to `<out>.measures.json` (id → volume, bbox). The
   volume + bbox dedup compares the new set against every given `--dedup-against` measures file and against the
   measures of jobs.jsonl and the exam. For the old sets, compute those measures in the same cloud run (one batch),
   and say how many were measured.
5. **B5, the grader knows R5 jobs**: `grade('factory', id, brep)` must find R5T and R5D ids. Either bake
   experiments/r5/jobs_r5t.jsonl + jobs_r5d.jsonl into the grader image next to the current jobs.jsonl, or pass the
   job's reference with the call. Pick the simplest and say which. Unknown ids must raise a clear error, not
   StopIteration. Add a `check-refs` path for the R5 files (every reference graded against itself must PASS) and a
   test. Old ids grade exactly as before (test).
6. **B6, the card is in the training prompt**: `render_full`/`build_messages` for R5 rows build the SAME messages as
   runner_final's FT arm WITH the rule card (use runner_final's own function). The training image adds the card file
   (`add_local_file` to /training/rule_card.md), FORGE_RULE_CARD points to it, the sha256 is checked in the container,
   and the "card in prompt" assert runs on the ACTUAL first training render (not on ft0). `check_format`'s
   prompt_matches_ft must be True for R5 rows. Test with a fake tokenizer.
7. **N1, the real token estimate**: count tokens with the Glimmer tokenizer (tokenizer.json is data; use the cached
   copy in .cache/glimmer-tokenizer if present, otherwise inside the container before training) and include the
   system prompt + card tokens per row. Implement the PLAN's 75% rule: if the estimate exceeds 0.75 × `--cap-dollars`,
   subsample first-try rows with seed 20261031 (keep all self-fix rows) until it fits; log what was dropped.
8. **N2, hinted rows**: hint-retry PASSes become FIRST-TRY rows only (job text → thinking + code, hint stripped), never
   self-fix rows. Also fix the `--dev-ids` text assert so it loads R5D texts from the R5D file.

## Tests
Offline, with fakes, for every item above. Keep all current tests passing (343 today, folders final, factory, freecad,
train, r5, common).

## Report back
Files changed, pytest count, and for each item how it was fixed. Do not run anything paid.
