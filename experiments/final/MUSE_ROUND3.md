# Muse Code round 3: teach HOW, not only the answer (Spark's reasoning in the training data)
# (user decision 2026-10-30 after the dev check STOP: "start with Spark"; verifier READY WITH 3 EDITS, applied:
# forge-round3-prebuild-2026-10-30)

Why: the first training used {job text → Spark's code} only. Every example's first loss tokens were ` to` `=user`
(answer directly), so Glimmer learned to skip its thinking turn and copy Spark's style: dev 38% (gate 80%). Baseten
returns Spark's thinking in `choices[0].message.reasoning_content` (see ~/.claude/skills/baseten-muse-spark/SKILL.md),
but teacher.py never stored it. Now the training data must hold Spark's worked solution: thinking + code.

Read first: experiments/factory/teacher.py, experiments/train/forge_train.py (render_full, encode_example,
filter_batch, the train function, GPU_MEM_STOP_GB, cost model), experiments/final/runner_final.py (FT body),
results/train-final/train.json (`first_example`, `first_loss_tokens`: the rendered format of the first training), and
~/.claude/skills/baseten-muse-spark/SKILL.md. All rules in experiments/final/MUSE_SPEC.md "Rules" apply (no network,
no Modal runs, no model calls, no commit, never print keys, never open blind/ or experiments/option-a/, never print
any expected*.json). Do not edit experiments/final/cloud_cq.py, run_cq_box.py, generator.py, make_jobs.py, jobs*.jsonl,
split.json, anything under results/, or frozen files.

## Build in this round ONLY
1. **teacher.py stores the thinking:** `parse_response` also returns `message.reasoning_content` (None/"" when absent).
   calls.jsonl records get `reasoning` (the full text) and `reasoning_chars`; train_records rows become
   {"id","text","code","reasoning","teacher":"spark"}. A PASS whose reasoning is empty is still recorded but flagged
   `reasoning_missing: true` and excluded from train_records (count it in summary.json). Teacher prompt, model, body,
   sampling, grader and budget guard unchanged. summary.json adds: n_with_reasoning, reasoning_chars median/max,
   n_reasoning_mentions_manual (reasoning text matching /\bmanual\b/i).
2. **forge_train.py trains thinking + answer:** when a record has `reasoning`, the target is Glimmer's own two-turn
   assistant format: a thinking turn holding the reasoning, then the user-facing turn holding the code block, built
   with the tokenizer's chat template (find how the template represents an assistant thinking/"to=self" turn, e.g. a
   `reasoning`/`thinking` field on the assistant message; do NOT hand-write special tokens if the template can render
   it). Loss on both turns (thinking + answer), never on the prompt. Records without `reasoning` keep today's format.
   The prompt (system + job text, no manual) is unchanged and must equal what runner_final's FT sends at serve time.
   - **H1:** `render_full`'s fallback (prompt + answer + eos when the template output does not start with the prompt)
     must RAISE for records with reasoning, never silently drop the thinking turn.
   - New `--format-check` mode (offline, needs only the tokenizer files; if they are not available locally, make the
     check run inside the Modal train function's first lines and print it before training): render one record and
     print the full rendered text + the first 40 loss tokens.
     **H2:** it must work on a FAKE reasoning record (`--format-check --fake`), so it can run BEFORE the factory re-run
     (many templates strip reasoning from history; we must know first). If it needs Modal (tokenizer only there), make
     it a tiny CPU Modal function that loads only the tokenizer (no GPU, no weights).
     **H3, pass condition (print PASS/FAIL):** (a) the first loss tokens open the thinking turn (the template's
     analysis/to=self turn), (b) the code turn follows it, (c) the rendered prompt is byte-equal to the prompt
     runner_final's FT arm sends (build it with runner_final's own function).
3. **Memory for long examples:** train on **H200** (gpu="H200", $ rate constant `H200_RATE = 4.54` used by the cost
   model and caps), keep gradient checkpointing, raise the per-example limit to `max_tokens=12288`, and set
   GPU_MEM_STOP_GB to 135 for H200. Examples longer than the limit are dropped and counted (as today). Merge stays as
   it is (or H200 if simpler; say which).
4a. **Base control arm A (verifier P5):** runner_final gets `--arms A`: base Glimmer, the SAME short prompt and body as
   FT except model name `muse-glimmer`, endpoint GLIMMER_URL/GLIMMER_KEY (served by deploy/modal_glimmer.py, same vLLM
   flags). Same factory/first-test grader routing and records as FT. Test: A's messages/body equal FT's except the model.
   And a matching session script `experiments/final/run_base_session.sh` (copy of run_final_session.sh for app
   forge-glimmer and deploy/modal_glimmer.py).
4b. **Budget fix (verifier D1):** in run_final_session.sh (and run_base_session.sh) `run()` passes `--budget "$CAP"`
   (budget_left stays only as the refuse-to-start check), so time and reserve are no longer subtracted twice. Test.
4. **Serving check:** runner_final FT keeps the same body (no reasoning_strength, max_tokens 16000); add
   `reasoning_chars` (length of `message.reasoning_content`) to every FT calls.jsonl record.
5. Tests (offline, fake HTTP/tokenizer): reasoning stored and carried into train_records; empty reasoning excluded and
   counted; manual-mention count; a record with reasoning renders thinking-then-answer with loss on both and the
   prompt masked; a record without reasoning renders exactly as before (byte-equal to today's render); cost model
   uses H200_RATE; GPU stop at 135; `smoke --cap-dollars 2.0` still CAP REFUSED.

## Done when
- `~/projects/forge/.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad
  experiments/train experiments/common dashboard` passes (303 + the new tests).
- `forge_train.py smoke --cap-dollars 2.0` prints CAP REFUSED and exits 2.
- `teacher.py --ids pilot --out X --budget-dollars 1` with no BASETEN_KEY exits 2.
Report: files changed, the pytest line, how the chat template represents the thinking turn (quote the template lines
you relied on), the --format-check plan, and anything not followed.
