# Fix spec for Muse Code: training pipeline (verifier NO-GO, report forge-train-pipeline-2026-10-29)

Status: written by Claude 2026-10-29; needs the user's yes before Muse Code runs. Same rules as MUSE_SPEC.md (edit only
files in experiments/train/ and experiments/common/; never open blind/, experiments/option-a/ or expected*.json
contents EXCEPT that the exam guard in item 3 may read experiments/first-test/jobs.py texts and use
experiments/first-test/expected.json through code, without printing it; no network, no Modal runs, no commit).

1. **Training loop (forge_train.py ~303-365):** count MICRO-steps (one example each) and OPTIMIZER steps separately:
   total optimizer steps = ceil(n_examples × epochs / grad_accum); loop over epochs × examples, call opt.step() every
   grad_accum micro-steps and once more at the end for a leftover partial group. `max_steps` limits OPTIMIZER steps.
   Record peak GPU memory AFTER the first opt.step() (when AdamW state exists) and stop then if > 76 GB. Put the
   schedule logic in a pure function (no torch) and test it offline: 400 examples, 2 epochs, accum 8 → 100 optimizer
   steps using all 800 micro-steps; 16 examples, 1 epoch → 2 steps; 8 examples with max_steps 10 and accum 1 → 10 steps.
2. **Data reaches Modal:** the local entrypoint reads the local JSONL (and also accepts a JSON array, as
   experiments/smoke/smoke_examples.json is), validates each record has "text" and "code", and passes the records
   themselves (a list of dicts) to train.remote(), not a path. Test both input formats.
3. **Exam guard (local, before any remote call):** refuse to train if any training record (a) has text with
   normalized similarity ≥ 0.8 to any of the 33 first-test job texts (difflib ratio after lowercasing and collapsing
   numbers to a placeholder is fine, and also exact-number comparison), or (b) when its code is built, matches an exam
   reference part at 1e-6 (use experiments/common/score_one.py logic against each job's reference build from
   experiments/first-test/jobs.py, in the sandbox). Save the guard report to results/train-<out>/exam_guard.json (counts
   only, no reference values). Test with a fake exam set.
4. **Timeouts from the money cap:** apply the planned timeouts with `.with_options(timeout=...)` (or equivalent) at call
   time; `gpu_minutes` and `--cap-dollars` must really bound each function; subtract earlier spend in the same
   entrypoint run (train → merge → serve share one cap). Test that a cap of $1.50 gives timeouts whose worst-case total
   cost ≤ $1.50.
5. **Log what the model is trained on:** train_log.json gets the fully rendered first training example (prompt +
   answer) and the first 40 decoded tokens that carry loss, so we can see exactly which tokens are learned.
6. **serve_merged:** stop using it for scoring; keep it only for a quick format check (one prompt, ≤ 3 min after ready,
   overall timeout from the cap). Final-exam scoring will use the existing runner (separate spec later).
7. **run_session.sh:** `trap ... EXIT INT TERM HUP`; run each runner call in its own process group and kill that group
   in the trap; the trap always runs `modal app stop forge-glimmer -y` and prints whether it stopped. Test with a dummy
   runner command that sleeps, sending TERM to the script.
8. **Budget reserve:** budget_left gets a `--reserve` (default $0.30) subtracted before handing a budget to a runner
   call, because the runner's guard stops only NEW calls and in-flight answers still cost money.
Run `~/projects/forge/.venv/bin/python -m pytest -q experiments/train experiments/common` until all pass. Short report:
files changed, the pytest line, anything not followed.

## Spec edits from the verifier's spec check (forge-train-fixspec-2026-10-29, READY WITH 5 SPEC EDITS) — binding
1. **Deadline inside train (item 4, A6):** train() gets `deadline_s` = its timeout minus 240 s. When the time left falls
   below that margin, it stops after the current optimizer step and saves the adapter and train_log.json (marked
   `stopped_at_deadline`). It also saves the adapter every 25 optimizer steps. Split the cap as: merge 12 min H100 +
   serve 6 min A100 reserved first, the rest to train. Refuse if train gets under 15 min.
2. **Exam guard refusals (item 3a, A3):** refuse a record only if (i) its exact-number text ratio is ≥ 0.9 to an exam
   text, or (ii) its built part matches an exam part. Number-collapsed ratios ≥ 0.8 are counted in exam_guard.json as
   warnings, not refusals. Drop refused records, and abort only if more than 5% are refused.
3. **Exam guard building (item 3b, A4):** build the 33 references in-process with jobs.py (trusted code); run only the
   training record's code in the sandbox. Compare bbox and volume first (1e-6) and run the full score only on a match.
4. **Startup in the cost (item 4, A7):** set `startup_timeout` explicitly (e.g. 600 s) on each function and include it in
   the worst-case cost: (startup + timeout) × rate ≤ cap.
5. **Trap that really fires (item 7, A10):** start each runner call in the background (`cmd & RPID=$!; wait $RPID`) so
   the trap can run. In the trap, kill the runner and its children (`kill -TERM $RPID; pkill -TERM -P $RPID`; macOS has
   no setsid). Then run `modal app stop`. The TERM test must show the dummy runner dead and "app stopped" printed.
Also (cheap, same session): LR schedule and logs per optimizer step, the partial last group scaled by its real size (A2);
epochs = 2 in the max_steps test (A1); `--spent-dollars` to carry earlier spend (A8); upload data to the volume when it
is over 5 MB (A9); the smoke entrypoint uses the same loader (A11).
