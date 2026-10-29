# Spec for Muse Code: Forge training pipeline, run script with session cap, dashboard, strict single-answer check

Status: written by Claude 2026-10-29 after the user's rule correction ("code must be done with Muse Code"; user said
"fix that"). Replaces scripts Claude wrote earlier (kept only as records of runs that already happened):
`experiments/smoke/train_smoke.py`, `experiments/smoke/score_answer.py`, `experiments/bmax/run_session_v2.sh`,
`experiments/bmax/glimmer_dashboard.py`. You may READ those files as working references (they ran successfully); write
the new code yourself.

## Rules
- Work in ~/projects/forge. New files only in `experiments/train/` and `experiments/common/`. Do not edit anything
  else (frozen files and records stay untouched). Never open any `blind/` folder, `experiments/option-a/`, or the
  contents of `expected*.json`.
- No network, no Modal runs, no model calls, no commit, never print keys. Tests must run offline without a GPU.
- Run `~/projects/forge/.venv/bin/python -m pytest -q experiments/train experiments/common` until all pass.

## 1. `experiments/train/forge_train.py` (Modal app `forge-train`)
Facts verified in the smoke test (results/smoke-2026-10-29, forge-wiki/wiki/findings/training-smoke-2026-10-29.md):
image `vllm/vllm-openai:muse-glimmer` + the python symlink line from deploy/modal_glimmer.py + `pip_install("peft")`;
transformers 5.15 loads the model with `AutoModelForMultimodalLM`; LoRA target regex
`.*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)` (104.8M trainable params); volumes
`forge-hf-cache` at /root/.cache/huggingface (weights already cached) and `forge-lora` at /vol; an 8,192-token step
OOMs on H100 (peak 80.2 GB); vLLM `--enable-lora` crashes on this image (lora_shrink AssertionError), the merged model
serves fine; Modal function returns must be plain JSON types (the local side has no torch).
Functions:
- `train(data_path, out_name, epochs=2, lr=1e-4, r=16, alpha=32, max_tokens=4096, grad_accum=8, gpu_minutes=45)`:
  data = JSONL of {"text", "code"} (uploaded with the call or read from the volume); short prompt only (system message =
  the first-test SYSTEM_PROMPT, user = text, assistant = "```python\n<code>\n```"), built with the tokenizer's chat
  template; loss only on the assistant part (labels -100 before it); drop examples longer than max_tokens and report how
  many; bf16, gradient checkpointing, AdamW, cosine schedule with 5% warmup; log loss, tokens and seconds per optimizer
  step; after the first optimizer step, record peak GPU memory and STOP cleanly (save nothing, report) if it is above
  76 GB; save the adapter to /vol/<out_name>/adapter and a train_log.json; return plain JSON and print it as
  `TRAIN_JSON {...}`. GPU H100, Modal timeout = gpu_minutes.
- `merge(out_name)`: H100, timeout 10 min: base + adapter → `merge_and_unload()` → save safetensors (5 GB shards) +
  processor + tokenizer to /vol/<out_name>/merged; return plain JSON (`MERGE_JSON`).
- `serve_merged(out_name, prompts)`: A100-80GB, timeout 10 min: `vllm serve /vol/<out_name>/merged --served-model-name
  forge --max-model-len 8192` + the Glimmer parsers; wait until /v1/models lists `forge`; send each prompt (short
  prompt: system + job text; temperature 1.0, top_p 0.95, top_k 64, max_tokens 6000); return answers with usage,
  latency, finish_reason, reasoning length; on failure return ALL log lines that contain Error/Exception/assert (not
  only the tail). Plain JSON (`SERVE_JSON`).
- Local entrypoints: `smoke` (train on experiments/smoke/smoke_examples.json, 10 steps max via a `max_steps` option,
  then merge + serve the smoke test job from train_smoke.py) and `full --data <jsonl> --out <name> [--cap-dollars X]`.
  Every entrypoint takes `--cap-dollars` and derives each function's timeout from the money left (H100 $3.95/h,
  A100 $2.50/h), refusing to start a step that does not fit. Results go to results/train-<out>/.

## 2. `experiments/common/run_session.sh` (glimmer evaluation session with a whole-session cap)
Same behaviour as experiments/bmax/run_session_v2.sh (read it): one deploy of deploy/modal_glimmer.py, wait for ready,
run the given runner commands one after another, each with `--budget` = money LEFT = cap − GPU time since deploy ×
$2.50/h (refuse to start when ≤ $0.05), optional pilot + GO/STOP file pause, always stop the app (`modal app stop
forge-glimmer -y`) and print whether it stopped. Make the arms/jobs/k a parameter instead of hard-coding them.

## 3. `experiments/common/dashboard.py` (live run dashboard)
Same output as experiments/bmax/glimmer_dashboard.py (read it), but general: `--run <results dir>` and an arms list
(name, label, description, expected answers, colour) from a small JSON config; page reloads every 20 s; data embedded in
the HTML (Chrome blocks file:// fetch); `--loop` until the session log shows the app stopped; output path argument.
Keep the status colours with ✓ ✗ ! symbols (not colour alone) and the light/dark CSS.

## 4. `experiments/common/score_one.py` (strict single-answer check)
Given a reply text (or file) and a reference CadQuery program (file), extract the code, run it in the sandbox
(`runner.run_code` with experiments/b2-hint/sandbox_cq.sb), and score with experiments/first-test/checks.py at
TOL_DIFF = 1e-6. Prints PASS or FAIL with reasons.

## 5. Tests (offline, no GPU, no network)
Prompt/label building with a fake tokenizer (labels masked before the answer; long examples dropped); cap → timeout
math (refuses when the money left is too small); plain-JSON returns; run_session.sh budget-left formula (call the
helper with fixed numbers); dashboard renders from a tiny fake calls.jsonl; score_one PASS/FAIL on a known-good and a
known-wrong program. Finish with a short report: files, the pytest line, anything you could not follow.
