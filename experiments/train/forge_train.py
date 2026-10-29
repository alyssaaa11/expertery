"""Forge training pipeline (Modal app ``forge-train``).

Facts verified in the smoke test (results/smoke-2026-10-29,
forge-wiki/wiki/findings/training-smoke-2026-10-29.md):

- image ``vllm/vllm-openai:muse-glimmer`` + the python symlink line from
  deploy/modal_glimmer.py + ``pip_install("peft")``;
- transformers 5.15 loads the model with ``AutoModelForMultimodalLM``;
- LoRA target regex
  ``.*language_model.*\\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)``
  (104.8M trainable params);
- volumes ``forge-hf-cache`` at /root/.cache/huggingface (weights already
  cached) and ``forge-lora`` at /vol;
- an 8,192-token step OOMs on H100 (peak 80.2 GB);
- vLLM ``--enable-lora`` crashes on this image (lora_shrink
  AssertionError), the merged model serves fine;
- Modal function returns must be plain JSON types (the local side has no
  torch).

The module imports without modal/torch/transformers so the pure helpers
(prompt building, cap math, plain-JSON scrub) are unit-testable offline.
Heavy imports live inside the Modal functions.
"""

import argparse
import json
import os
import sys

MODEL = "meta-models/Muse-Glimmer-30B"
# System message = the first-test SYSTEM_PROMPT (experiments/first-test/runner.py).
SYSTEM_PROMPT = (
    "You write CadQuery Python code. Units are millimetres. "
    "Assign the final solid to a variable named result. "
    "Reply with exactly one Python code block and nothing else."
)
LORA_PATTERN = (
    r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"
)
LORA_FALLBACK_PATTERN = (
    r".*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"
)
IMAGE_REF = "vllm/vllm-openai:muse-glimmer"
HF_CACHE_MOUNT = "/root/.cache/huggingface"
LORA_MOUNT = "/vol"
GPU_MEM_STOP_GB = 76.0  # stop cleanly above this after the first optimizer step

H100_RATE = 3.95  # $/h
A100_RATE = 2.50  # $/h

# Smoke-test job (the TEST_JOB in experiments/smoke/train_smoke.py).
SMOKE_JOB = (
    "A spacer block. Block: X from 0 to 30, Y from 0 to 20, Z from 0 to 10. "
    "A 6 mm hole goes through it along the Z axis, centred at (X, Y) = (15, 10)."
)
SMOKE_EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "smoke",
    "smoke_examples.json",
)
SERVE_MODEL_NAME = "forge"
SERVE_MAX_MODEL_LEN = 8192
SERVE_MAX_TOKENS = 6000
SERVE_TEMPERATURE = 1.0
SERVE_TOP_P = 0.95
SERVE_TOP_K = 64
# Log lines kept on a serve failure: every line mentioning one of these.
ERROR_WORDS = ("Error", "Exception", "assert")


# ------------------------------------------------------------- pure helpers


def build_answer_text(code):
    """The assistant side of a training example: one fenced code block."""
    return "```python\n" + code + "\n```"


def build_messages(text):
    """Short prompt only: system (= first-test SYSTEM_PROMPT) + job text."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]


def render_prompt(tokenizer, text):
    """Prompt string via the tokenizer's chat template."""
    return tokenizer.apply_chat_template(
        build_messages(text), tokenize=False, add_generation_prompt=True
    )


def render_full(tokenizer, text, code):
    """Prompt + assistant answer via the chat template.

    Falls back to prompt + answer + eos when the template renders history
    differently (same fallback as the smoke test).
    """
    prompt = render_prompt(tokenizer, text)
    answer = build_answer_text(code)
    full = tokenizer.apply_chat_template(
        build_messages(text) + [{"role": "assistant", "content": answer}],
        tokenize=False,
    )
    if not full.startswith(prompt):
        full = prompt + answer + (tokenizer.eos_token or "")
    return prompt, full


def encode_example(tokenizer, text, code, max_tokens=4096):
    """Tokenize one example; loss only on the assistant part.

    Returns {"input_ids", "labels", "tokens", "dropped"} where labels are
    -100 before the assistant part. Examples longer than max_tokens are
    dropped (dropped=True, ids/labels empty).
    """
    prompt, full = render_full(tokenizer, text, code)
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    ids = tokenizer(full, add_special_tokens=False)["input_ids"]
    if len(ids) > max_tokens:
        return {"input_ids": [], "labels": [], "tokens": len(ids), "dropped": True}
    labels = [-100] * len(prompt_ids) + ids[len(prompt_ids):]
    return {"input_ids": ids, "labels": labels, "tokens": len(ids), "dropped": False}


def filter_batch(tokenizer, examples, max_tokens=4096):
    """Encode examples, dropping ones longer than max_tokens.

    Returns (kept, dropped_count).
    """
    kept = []
    dropped = 0
    for ex in examples:
        enc = encode_example(tokenizer, ex["text"], ex["code"], max_tokens)
        if enc["dropped"]:
            dropped += 1
        else:
            kept.append({**ex, **enc})
    return kept, dropped


def seconds_for_dollars(dollars, rate_per_hour):
    """GPU seconds buyable with `dollars` at `rate_per_hour`."""
    return dollars * 3600.0 / rate_per_hour


def dollars_for_seconds(seconds, rate_per_hour):
    """Cost of `seconds` of GPU time at `rate_per_hour`."""
    return seconds * rate_per_hour / 3600.0


class CapExceeded(RuntimeError):
    """Raised when a step does not fit in the money left."""


def plan_timeouts(cap_dollars, steps):
    """Derive each Modal function's timeout from the money left.

    `steps` is a list of (name, rate_per_hour, want_seconds), charged in
    order. Returns {name: seconds}. Raises CapExceeded when a step does
    not fit in the money left (refuses to start it).
    """
    left = float(cap_dollars)
    out = {}
    for name, rate, want in steps:
        cost = dollars_for_seconds(want, rate)
        if cost > left:
            raise CapExceeded(
                "step %r wants %ds ($%.2f at $%.2f/h) but only $%.2f is left of "
                "the $%.2f cap; refusing to start it"
                % (name, want, cost, rate, left, cap_dollars)
            )
        out[name] = want
        left -= cost
    out["_left"] = round(left, 2)
    return out


def default_plan(cap_dollars, train_s=14 * 60, merge_s=10 * 60, serve_s=10 * 60):
    """Timeout plan for the train -> merge -> serve pipeline."""
    return plan_timeouts(
        cap_dollars,
        [
            ("train", H100_RATE, train_s),
            ("merge", H100_RATE, merge_s),
            ("serve", A100_RATE, serve_s),
        ],
    )


def ensure_plain_json(obj):
    """Round-trip through JSON so Modal returns are plain JSON types.

    The local side has no torch; tensors/arrays become strings.
    """
    return json.loads(json.dumps(obj, default=str))


# ---------------------------------------------------------------- Modal app

try:
    import modal
except ImportError:  # offline / local test: helpers above still import
    modal = None

if modal is not None:
    image = (
        modal.Image.from_registry(
            IMAGE_REF,
            setup_dockerfile_commands=[
                'RUN ln -sf "$(command -v python3)" /usr/local/bin/python'
                " && (python -m pip --version || python -m ensurepip)",
            ],
        )
        .entrypoint([])
        .pip_install("peft")
    )
    hf_cache = modal.Volume.from_name("forge-hf-cache", create_if_missing=True)
    lora_vol = modal.Volume.from_name("forge-lora", create_if_missing=True)
    app = modal.App("forge-train")

    VOLUMES = {HF_CACHE_MOUNT: hf_cache, LORA_MOUNT: lora_vol}

    @app.function(image=image, gpu="H100", timeout=45 * 60, volumes=VOLUMES)
    def train(
        data_path,
        out_name,
        epochs=2,
        lr=1e-4,
        r=16,
        alpha=32,
        max_tokens=4096,
        grad_accum=8,
        gpu_minutes=45,
        max_steps=None,
    ):
        """LoRA-tune Glimmer on JSONL {"text", "code"}; short prompt only.

        Loss only on the assistant part (labels -100 before it); examples
        longer than max_tokens are dropped and counted. bf16, gradient
        checkpointing, AdamW, cosine schedule with 5% warmup. After the
        first optimizer step the peak GPU memory is recorded and the run
        STOPs cleanly (saving nothing) above 76 GB. Saves the adapter to
        /vol/<out_name>/adapter plus a train_log.json. Returns plain JSON
        and prints it as ``TRAIN_JSON {...}``.
        """
        import time

        import torch
        import transformers
        from peft import LoraConfig, get_peft_model

        t0 = time.time()
        out = {
            "transformers": str(transformers.__version__),
            "torch": str(torch.__version__),
        }
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        if os.path.isfile(data_path):
            raw = open(data_path, encoding="utf-8").read().splitlines()
        else:  # read from the volume
            raw = open(os.path.join(LORA_MOUNT, data_path), encoding="utf-8").read().splitlines()
        examples = [json.loads(line) for line in raw if line.strip()]
        tok = transformers.AutoTokenizer.from_pretrained(MODEL)
        model = transformers.AutoModelForMultimodalLM.from_pretrained(
            MODEL, torch_dtype=torch.bfloat16, device_map="cuda"
        )
        out["lora_pattern"] = LORA_PATTERN
        model = get_peft_model(
            model,
            LoraConfig(
                r=r, lora_alpha=alpha, lora_dropout=0.0,
                target_modules=LORA_PATTERN, task_type="CAUSAL_LM",
            ),
        )
        out["trainable_params"] = sum(
            p.numel() for p in model.parameters() if p.requires_grad
        )
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        model.enable_input_require_grads()
        model.config.use_cache = False

        def encode(ex):
            prompt, full = _remote_render(tok, ex["text"], ex["code"])
            p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
            ids = tok(full, add_special_tokens=False)["input_ids"]
            labels = [-100] * len(p_ids) + ids[len(p_ids):]
            return ids, labels

        kept, dropped = [], 0
        for ex in examples:
            prompt, full = _remote_render(tok, ex["text"], ex["code"])
            if len(tok(full, add_special_tokens=False)["input_ids"]) > max_tokens:
                dropped += 1
                continue
            kept.append(ex)
        out["examples"], out["dropped"] = len(kept), dropped

        total_steps = max(1, epochs * max(1, len(kept) // grad_accum))
        if max_steps is not None:
            total_steps = min(total_steps, max_steps)
        opt = torch.optim.AdamW(
            [p for p in model.parameters() if p.requires_grad], lr=lr
        )
        warmup = max(1, int(0.05 * total_steps))

        def lr_at(step):
            if step < warmup:
                return lr * (step + 1) / warmup
            prog = (step - warmup) / max(1, total_steps - warmup)
            import math as _math

            return lr * 0.5 * (1.0 + _math.cos(_math.pi * prog))

        model.train()
        steps, step_no, mem_stop = [], 0, False
        for epoch in range(epochs):
            for ex in kept:
                if step_no >= total_steps:
                    break
                for group in opt.param_groups:
                    group["lr"] = lr_at(step_no)
                ids, labels = encode(ex)
                ids_t = torch.tensor([ids], device="cuda")
                lab_t = torch.tensor([labels], device="cuda")
                torch.cuda.synchronize()
                ts = time.time()
                loss = model(input_ids=ids_t, labels=lab_t).loss / grad_accum
                loss.backward()
                if (step_no + 1) % grad_accum == 0:
                    opt.step()
                    opt.zero_grad(set_to_none=True)
                torch.cuda.synchronize()
                step_no += 1
                steps.append(
                    {
                        "step": step_no,
                        "tokens": len(ids),
                        "loss": round(float(loss) * grad_accum, 4),
                        "seconds": round(time.time() - ts, 2),
                    }
                )
                if step_no == 1:
                    out["peak_gb"] = round(
                        torch.cuda.max_memory_allocated() / 1e9, 1
                    )
                    out["gpu_total_gb"] = round(
                        torch.cuda.get_device_properties(0).total_memory / 1e9, 1
                    )
                    if out["peak_gb"] > GPU_MEM_STOP_GB:
                        out["mem_stop"] = (
                            "peak %.1f GB above %.0f GB after the first "
                            "optimizer step; stopping cleanly, saving nothing"
                            % (out["peak_gb"], GPU_MEM_STOP_GB)
                        )
                        mem_stop = True
                        break
            if step_no >= total_steps or mem_stop:
                break
        out["steps"] = steps
        out["train_total_s"] = round(time.time() - t0, 1)
        if not mem_stop:
            dest = os.path.join(LORA_MOUNT, out_name, "adapter")
            os.makedirs(dest, exist_ok=True)
            model.save_pretrained(dest)
            json.dump(
                out, open(os.path.join(dest, "train_log.json"), "w"), indent=1
            )
            lora_vol.commit()
            out["adapter"] = dest
        out = ensure_plain_json(out)
        print("TRAIN_JSON " + json.dumps(out))
        return out

    @app.function(image=image, gpu="H100", timeout=10 * 60, volumes=VOLUMES)
    def merge(out_name):
        """Base + adapter -> merge_and_unload(); safetensors 5 GB shards."""
        import time

        import torch
        import transformers
        from peft import PeftModel

        lora_vol.reload()
        t0 = time.time()
        base = transformers.AutoModelForMultimodalLM.from_pretrained(
            MODEL, torch_dtype=torch.bfloat16, device_map="cuda"
        )
        merged = PeftModel.from_pretrained(
            base, os.path.join(LORA_MOUNT, out_name, "adapter")
        ).merge_and_unload()
        dest = os.path.join(LORA_MOUNT, out_name, "merged")
        merged.save_pretrained(dest, safe_serialization=True, max_shard_size="5GB")
        transformers.AutoProcessor.from_pretrained(MODEL).save_pretrained(dest)
        transformers.AutoTokenizer.from_pretrained(MODEL).save_pretrained(dest)
        lora_vol.commit()
        out = ensure_plain_json(
            {"merge_s": round(time.time() - t0, 1), "merged": dest}
        )
        print("MERGE_JSON " + json.dumps(out))
        return out

    @app.function(image=image, gpu="A100-80GB", timeout=10 * 60, volumes=VOLUMES)
    def serve_merged(out_name, prompts):
        """Serve the merged model and answer each prompt (short prompt).

        temperature 1.0, top_p 0.95, top_k 64, max_tokens 6000. Returns
        answers with usage, latency, finish_reason and reasoning length.
        On failure returns ALL log lines containing Error/Exception/assert.
        """
        import subprocess
        import time
        import urllib.request

        lora_vol.reload()
        t0 = time.time()
        out = {}
        log = open("/tmp/vllm.log", "w")
        proc = subprocess.Popen(
            [
                "vllm", "serve", os.path.join(LORA_MOUNT, out_name, "merged"),
                "--served-model-name", SERVE_MODEL_NAME,
                "--port", "8000",
                "--max-model-len", str(SERVE_MAX_MODEL_LEN),
                "--enable-auto-tool-choice",
                "--tool-call-parser", "muse_glimmer",
                "--reasoning-parser", "muse_glimmer",
                "--generation-config", "auto",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        ready = False
        while time.time() - t0 < 8 * 60:
            if proc.poll() is not None:
                break
            try:
                models = json.load(
                    urllib.request.urlopen(
                        "http://localhost:8000/v1/models", timeout=5
                    )
                )
                if SERVE_MODEL_NAME in [m["id"] for m in models["data"]]:
                    ready = True
                    break
                time.sleep(5)
            except Exception:
                time.sleep(5)
        out["ready_s"] = round(time.time() - t0, 1)
        answers = []
        if ready:
            for prompt in prompts:
                body = {
                    "model": SERVE_MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": SERVE_MAX_TOKENS,
                    "temperature": SERVE_TEMPERATURE,
                    "top_p": SERVE_TOP_P,
                    "top_k": SERVE_TOP_K,
                }
                req = urllib.request.Request(
                    "http://localhost:8000/v1/chat/completions",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                )
                ts = time.time()
                try:
                    r = json.load(urllib.request.urlopen(req, timeout=300))
                    msg = r["choices"][0]["message"]
                    answers.append(
                        {
                            "prompt": prompt,
                            "answer": msg.get("content"),
                            "reasoning_len": len(
                                msg.get("reasoning_content")
                                or msg.get("reasoning")
                                or ""
                            ),
                            "finish_reason": r["choices"][0].get("finish_reason"),
                            "usage": r.get("usage"),
                            "answer_s": round(time.time() - ts, 1),
                        }
                    )
                except Exception as e:
                    answers.append({"prompt": prompt, "error": repr(e)[:300]})
        else:
            out["error"] = "vLLM (merged) did not come up (exit %s)" % proc.poll()
        full = open("/tmp/vllm.log").read()
        if out.get("error") or any("error" in a for a in answers):
            out["error_lines"] = [
                line[:400]
                for line in full.splitlines()
                if any(w in line for w in ERROR_WORDS)
            ]
        out["answers"] = answers
        proc.kill()
        out = ensure_plain_json(out)
        print("SERVE_JSON " + json.dumps(out))
        return out

def _remote_render(tok, text, code):
    """Render (prompt, full) with the tokenizer's chat template."""
    return render_full(tok, text, code)


# ------------------------------------------------------- local entrypoints


def results_dir(out_name):
    """Local results dir: results/train-<out>/."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "results",
        "train-%s" % out_name,
    )
    os.makedirs(path, exist_ok=True)
    return path


def run_smoke(cap_dollars, train_s=10 * 60, merge_s=8 * 60, serve_s=8 * 60):
    """Smoke pipeline: train (max_steps) on the smoke examples, merge, serve.

    Returns the timeout plan; raises CapExceeded when a step does not fit.
    Remote calls need modal installed; planning works offline.
    """
    plan = plan_timeouts(
        cap_dollars,
        [
            ("train", H100_RATE, train_s),
            ("merge", H100_RATE, merge_s),
            ("serve", A100_RATE, serve_s),
        ],
    )
    if modal is None:
        raise RuntimeError("modal is not installed; cannot run remotely")
    res_dir = results_dir("smoke")
    t = train.remote(SMOKE_EXAMPLES, "smoke", max_steps=10)
    json.dump(t, open(os.path.join(res_dir, "train.json"), "w"), indent=1)
    print("TRAIN", json.dumps({k: v for k, v in t.items() if k != "steps"})[:1500])
    if t.get("error") or t.get("mem_stop"):
        print("SKIP MERGE/SERVE: training stopped")
        return plan
    m = merge.remote("smoke")
    json.dump(m, open(os.path.join(res_dir, "merge.json"), "w"), indent=1)
    print("MERGE", m)
    s = serve_merged.remote("smoke", [SMOKE_JOB])
    json.dump(s, open(os.path.join(res_dir, "serve.json"), "w"), indent=1)
    print("SERVE", json.dumps(s)[:2000])
    return plan


def run_full(data, out_name, cap_dollars, train_s=45 * 60, merge_s=10 * 60,
             serve_s=10 * 60, prompts=()):
    """Full pipeline on a JSONL file; timeouts derived from the cap left."""
    plan = plan_timeouts(
        cap_dollars,
        [
            ("train", H100_RATE, train_s),
            ("merge", H100_RATE, merge_s),
            ("serve", A100_RATE, serve_s),
        ],
    )
    if modal is None:
        raise RuntimeError("modal is not installed; cannot run remotely")
    res_dir = results_dir(out_name)
    t = train.remote(data, out_name)
    json.dump(t, open(os.path.join(res_dir, "train.json"), "w"), indent=1)
    print("TRAIN", json.dumps({k: v for k, v in t.items() if k != "steps"})[:1500])
    if t.get("error") or t.get("mem_stop"):
        print("SKIP MERGE/SERVE: training stopped")
        return plan
    m = merge.remote(out_name)
    json.dump(m, open(os.path.join(res_dir, "merge.json"), "w"), indent=1)
    print("MERGE", m)
    s = serve_merged.remote(out_name, list(prompts))
    json.dump(s, open(os.path.join(res_dir, "serve.json"), "w"), indent=1)
    print("SERVE", json.dumps(s)[:2000])
    return plan


def main(argv=None):
    """Local entrypoints: `smoke` and `full --data <jsonl> --out <name>`.

    Every entrypoint takes --cap-dollars and derives each function's
    timeout from the money left, refusing to start a step that does not fit.
    """
    parser = argparse.ArgumentParser(description="Forge training pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    smoke = sub.add_parser("smoke", help="train/merge/serve on the smoke examples")
    smoke.add_argument("--cap-dollars", type=float, required=True)
    full = sub.add_parser("full", help="train/merge/serve on a JSONL file")
    full.add_argument("--data", required=True)
    full.add_argument("--out", required=True)
    full.add_argument("--cap-dollars", type=float, required=True)
    full.add_argument("--prompt", action="append", default=[],
                      help="job text to serve (repeatable)")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "smoke":
            run_smoke(args.cap_dollars)
        else:
            run_full(args.data, args.out, args.cap_dollars, prompts=args.prompt)
    except CapExceeded as e:
        print("CAP REFUSED: %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
