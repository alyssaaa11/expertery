# Muse Code round R5: Glimmer's own guided solutions as training data (DRAFT v2, for the verifier)
# (user decisions 2026-10-31: plan experiments/r5/PLAN.md v2, option B = no CAD-Coder)

Why: R1/R3 trained on 154-167 examples; this round builds the tools to make ~1,600+ rows, all with Glimmer's own
thinking, from 2,000 new factory jobs: first tries, self-fixes from the referee's text, and Spark-hinted retries
(hint removed before training). Plan and caps: experiments/r5/PLAN.md. All rules in experiments/final/MUSE_SPEC.md "Rules" apply (no network, no Modal
runs, no model calls, no commit, never print keys, never open blind/ or experiments/option-a/, never print any
expected*.json). Do not edit experiments/final/cloud_cq.py, run_cq_box.py, generator.py's existing families or SEED,
jobs*.jsonl, split.json, RULE_CARD.md, anything under results/, or frozen files.

Read first: experiments/factory/generator.py + make_jobs.py, experiments/factory/teacher.py (Baseten call, budget
guard, parse_response), experiments/final/runner_final.py (A and FT arms, FORGE_RULE_CARD, records), experiments/final/
cloud_cq.py (the cloud CadQuery box, grade + measure_brep), experiments/train/forge_train.py (render_full,
encode_example, reasoning records, exam guard, cost model, H200_RATE), results/train-r3/train.json (first_example,
first_loss_tokens), ~/.claude/skills/baseten-muse-spark/SKILL.md.

## Build in this round ONLY
1. **New job sets (make_jobs.py `--seed S --per-family N --prefix P --out FILE`)** (dedup also by measured volume + bbox): same 10 families and generator
   code, a new seed, ids `P-F<f>-<i>`. Refuse a seed equal to SEED (20261029). Dedup: drop any job whose text equals
   (or whose rounded parameter tuple equals) a job in jobs.jsonl, jobs_dev.jsonl or the exam (experiments/first-test/
   jobs.py); print the count. Writes jobs + references in the same format as jobs.jsonl. Two sets will be made:
   `R5T` (seed 20261031, 200 per family = 2,000) and `R5D` (seed 20261131, 10 per family = 100).
2. **Runner stores Glimmer's thinking**: today arm A/FT records only `reasoning_len` (length), and `reasoning_chars` is 0.
   Find where the served vLLM puts the reasoning text (`message.reasoning_content`, `message.reasoning`, or the
   content before the code block; check ALL of them, take the first non-empty) and store it as `reasoning` (full text) in every calls.jsonl record; set
   `reasoning_chars` from it. Add `--jobs-file` support for the new sets if not already enough, and allow `--workers`
   up to 16 (deploy max_inputs=16; the session scripts pass it through).
3. **hints.py (Spark hints, PLAN step 5)**: input = a calls.jsonl of FAILED records (job id, job text, Glimmer's code,
   referee failed_checks). For each, call Spark Open on Baseten (reuse teacher.py's client, key handling and budget
   guard) with a fixed hint prompt: "You are a CAD tutor. A student wrote this CadQuery code for the job; the referee
   says these checks failed: …. Give ONE short hint (max 60 words) that points to the mistake. Do NOT write code."
   Reject a hint that contains a code fence, `cq.`, `import`, or more than 60 words (record `hint_rejected`). Output
   hints.jsonl {id, hint, hint_words, rejected, usd}. `--budget` dollars (hard stop, like teacher.py). summary.json:
   n, n_rejected, usd, usd per hint.
4. **Retry with hint (runner_final `--hints FILE`)**: for jobs in the hints file, append to the user message:
   "\n\nHint from a tutor: <hint>". The record keeps `hint` so the trainer can STRIP it. Everything else (body, card,
   grader) is unchanged.
5. **Self-fix retry (runner_final `--selffix FILE`)**: for each FAILED record, the user message becomes the job text +
   "\n\nYour code:\n```python\n<code>\n```\nWhat happened:\n<feedback>\nFix the code." The feedback comes from ONE
   function `selffix_feedback(record)` (also used in product mode) and is REFERENCE-FREE: the last 15 lines of the error
   trace if it crashed, the number of separate solids, and the answer's own measured volume + bbox. It must never contain
   expected values, reference measurements or failed-check names that reveal them (test with a record whose expected
   values are known: none of them may appear in the text). Records keep `selffix_of` (the
   first try's record id). Same body, card and grader.
6. **build_mix.py**: inputs = the R5T first-try, self-fix and hint-retry calls.jsonl files (PASS only). First-try rows:
   job text → thinking + code. Self-fix rows: job + wrong code + referee text → thinking + fixed code. Hint-retry PASSes:
   added as BOTH kinds with the hint STRIPPED; drop them if the reasoning says "hint"/"tutor" or copies ≥ 8 words of
   the hint. Rows with reasoning < 200 chars are dropped (no code-only rows). At most 2 rows per job. Output train_records.jsonl rows {id, text, code, reasoning, source}.
   Assert: no row contains "Hint from a tutor", no dev/exam id or text, no
   Wonder output. Print the rows per source and the token totals.
7. **forge_train.py on the mix**: same LoRA (r 16, alpha 32, lr 1e-4, 2 epochs), max_tokens 8192, H200; the rule card is baked into the training image as a file (not an env var) and its sha256
   (586b59607b0123dc5a64734d8a854ad1b3ca4eb83a1c223aacb175d7a6dbe80b) is checked inside the container; every row's
   prompt = runner_final's FT system prompt WITH the rule card + the row's text (build it with runner_final's own
   function). Every row → thinking turn + code (as in R3). Loader provenance: accept sources glimmer-first/-selffix/-hinted with
   R5T ids only (replaces the Spark-PASS rule). Shuffle seed 20261031. Save the adapter every half epoch. Log first_loss_tokens
   PER SOURCE, rows dropped for length per source, loss per step, and a cost estimate before start; `--cap-dollars`
   refuses to start if the estimate is over the cap (estimate from tokens × measured R3 throughput).
8. **Tests (offline, fake HTTP/tokenizer/box)**: new seed refused when equal to SEED; dedup removes a copied job;
   reasoning text stored; hint rejection rules; hint appended at serve and stripped in build_mix;
   self-fix prompt built by selffix_feedback and free of expected values; hint-citing retries dropped; mix asserts fire; per-source
   first-loss-token logging; `--cap-dollars` refusal.

## Report back
Files changed, pytest count, and for each item how to run it. Do not run anything paid.
