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
