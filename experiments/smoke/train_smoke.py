"""Forge training SMOKE TEST (user yes 2026-10-29, cap ~$1.5). Written by Claude as a test harness.

One `modal run` (ephemeral app, stops by itself):
  1. train()  on 1x H100 (timeout 14 min ≈ $0.92 max): load Muse Glimmer 30B bf16 from the forge-hf-cache volume,
     LoRA r=16/alpha=32 on the language model's q,k,v,o,gate,up,down, 10 optimizer steps (8 short examples, then 2
     steps on an 8,192-token sequence to measure worst-case memory), loss only on the answer, save the adapter to the
     forge-lora volume.
  2. serve()  on 1x A100-80GB (timeout 12 min ≈ $0.50 max): vLLM with --enable-lora --lora-modules forge=<adapter>,
     check /v1/models lists `forge`, send ONE request with the short prompt (no manual) for a new job, return the reply.
Hard money ceiling from the timeouts ≈ $1.42 (+ small CPU/RAM). Results are written to results/smoke-2026-10-29/.

    modal run experiments/smoke/train_smoke.py
"""
import json, os, subprocess, time

import modal

MODEL = "meta-models/Muse-Glimmer-30B"
SYSTEM = ("You write CadQuery Python code. Units are millimetres. Assign the final solid to a variable named result. "
          "Reply with exactly one Python code block and nothing else.")
TEST_JOB = ("A spacer block. Block: X from 0 to 30, Y from 0 to 20, Z from 0 to 10. A 6 mm hole goes through it along "
            "the Z axis, centred at (X, Y) = (15, 10).")
HERE = os.path.dirname(os.path.abspath(__file__))

image = (modal.Image.from_registry(
    "vllm/vllm-openai:muse-glimmer",
    setup_dockerfile_commands=['RUN ln -sf "$(command -v python3)" /usr/local/bin/python'
                               ' && (python -m pip --version || python -m ensurepip)'],
).entrypoint([]).pip_install("peft").add_local_file(os.path.join(HERE, "smoke_examples.json"), "/smoke_examples.json"))
hf_cache = modal.Volume.from_name("forge-hf-cache", create_if_missing=True)
lora_vol = modal.Volume.from_name("forge-lora", create_if_missing=True)
app = modal.App("forge-train-smoke")


@app.function(image=image, gpu="H100", timeout=14 * 60,
              volumes={"/root/.cache/huggingface": hf_cache, "/vol": lora_vol})
def train():
    import torch, transformers
    from peft import LoraConfig, get_peft_model
    t0 = time.time(); out = {"transformers": str(transformers.__version__), "torch": str(torch.__version__)}
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    tok = transformers.AutoTokenizer.from_pretrained(MODEL)
    model, errs = None, []
    for cls in ("AutoModelForMultimodalLM", "AutoModelForImageTextToText", "AutoModelForCausalLM"):
        C = getattr(transformers, cls, None)
        if C is None:
            continue
        try:
            model = C.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
            out["model_class"] = cls; break
        except Exception as e:  # try the next class
            errs.append(f"{cls}: {e!r}"[:300])
    if model is None:
        out = {**out, "error": "could not load model", "tries": errs}; print("TRAIN_JSON " + json.dumps(out)); return out
    out["load_s"] = round(time.time() - t0, 1)
    names = [n for n, _ in model.named_modules()]
    lm = [n for n in names if "language_model" in n]
    pat = (r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)" if lm else
           r".*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)")
    out["lora_pattern"] = pat
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.0, target_modules=pat,
                                             task_type="CAUSAL_LM"))
    out["trainable_params"] = sum(p.numel() for p in model.parameters() if p.requires_grad)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model.config.use_cache = False

    def encode(ex, pad_to=None):
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": ex["text"]}]
        answer = "```python\n" + ex["code"] + "\n```"
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        full = tok.apply_chat_template(msgs + [{"role": "assistant", "content": answer}], tokenize=False)
        if not full.startswith(prompt):  # template renders history differently: fall back to prompt + answer
            full = prompt + answer + (tok.eos_token or "")
        p_ids = tok(prompt, add_special_tokens=False)["input_ids"]
        ids = tok(full, add_special_tokens=False)["input_ids"]
        if pad_to:  # worst-case memory probe: repeat the answer part up to pad_to tokens
            body = ids[len(p_ids):]
            while len(ids) < pad_to:
                ids = ids + body
            ids = ids[:pad_to]
        labels = [-100] * len(p_ids) + ids[len(p_ids):]
        return torch.tensor([ids], device="cuda"), torch.tensor([labels], device="cuda")

    exs = json.load(open("/smoke_examples.json"))
    out["rendered_example_tail"] = tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": exs[0]["text"]},
         {"role": "assistant", "content": "```python\n...\n```"}], tokenize=False)[-400:]
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    model.train(); steps = []
    for step in range(10):
        long = step >= 8
        ids, labels = encode(exs[step % 8], pad_to=8192 if long else None)
        torch.cuda.synchronize(); ts = time.time()
        try:
            loss = model(input_ids=ids, labels=labels).loss
            loss.backward(); opt.step(); opt.zero_grad(set_to_none=True)
            torch.cuda.synchronize()
            steps.append({"step": step + 1, "tokens": ids.shape[1], "loss": round(loss.item(), 4),
                          "seconds": round(time.time() - ts, 2)})
        except torch.cuda.OutOfMemoryError as e:
            steps.append({"step": step + 1, "tokens": ids.shape[1], "error": "OOM " + str(e)[:200]})
            opt.zero_grad(set_to_none=True); torch.cuda.empty_cache()
    out["steps"] = steps
    out["peak_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 1)
    out["gpu_total_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)
    model.save_pretrained("/vol/smoke")
    lora_vol.commit()
    out["adapter_files"] = sorted(os.listdir("/vol/smoke"))
    out["train_total_s"] = round(time.time() - t0, 1)
    out = json.loads(json.dumps(out, default=str))  # plain types only: the local side has no torch
    print("TRAIN_JSON " + json.dumps(out))
    return out


@app.function(image=image, gpu="A100-80GB", timeout=12 * 60,
              volumes={"/root/.cache/huggingface": hf_cache, "/vol": lora_vol})
def serve():
    import urllib.request
    lora_vol.reload(); t0 = time.time(); out = {}
    log = open("/tmp/vllm.log", "w")
    proc = subprocess.Popen(["vllm", "serve", MODEL, "--served-model-name", "muse-glimmer", "--port", "8000",
                             "--max-model-len", "8192", "--enable-lora", "--max-lora-rank", "16",
                             "--lora-modules", "forge=/vol/smoke", "--enable-auto-tool-choice",
                             "--tool-call-parser", "muse_glimmer", "--reasoning-parser", "muse_glimmer",
                             "--generation-config", "auto"], stdout=log, stderr=subprocess.STDOUT)
    ready = False
    while time.time() - t0 < 9 * 60:
        if proc.poll() is not None:
            break
        try:
            models = json.load(urllib.request.urlopen("http://localhost:8000/v1/models", timeout=5))
            out["models"] = [m["id"] for m in models["data"]]; ready = True; break
        except Exception:
            time.sleep(5)
    out["ready_s"] = round(time.time() - t0, 1)
    if not ready:
        log.flush()
        out["error"] = "vLLM did not come up (exit %s)" % proc.poll()
        full = open("/tmp/vllm.log").read()
        out["error_lines"] = [l[:400] for l in full.splitlines()
                              if any(w in l for w in ("Error", "error:", "Exception", "assert", "LoRA", "lora"))
                              and 'File "' not in l][-40:]
        out["log_tail"] = full[-1500:]
        proc.kill(); out = json.loads(json.dumps(out, default=str)); print("SERVE_JSON " + json.dumps(out)); return out
    body = {"model": "forge", "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": TEST_JOB}],
            "max_tokens": 6000, "temperature": 1.0, "top_p": 0.95, "top_k": 64}
    req = urllib.request.Request("http://localhost:8000/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    ts = time.time()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=150))
        msg = r["choices"][0]["message"]
        out.update(answer=msg.get("content"), reasoning_len=len(msg.get("reasoning_content") or msg.get("reasoning") or ""),
                   finish_reason=r["choices"][0].get("finish_reason"), usage=r.get("usage"),
                   answer_s=round(time.time() - ts, 1))
    except Exception as e:
        out["error"] = f"request failed: {e!r}"[:300]
        out["log_tail"] = open("/tmp/vllm.log").read()[-2000:]
    proc.kill()
    out = json.loads(json.dumps(out, default=str)); print("SERVE_JSON " + json.dumps(out))
    return out


@app.local_entrypoint()
def serve_only():
    res_dir = os.path.expanduser("~/projects/forge/results/smoke-2026-10-29")
    s = serve.remote()
    json.dump(s, open(os.path.join(res_dir, "serve.json"), "w"), indent=1)
    print("SERVE", json.dumps(s)[:3000])


@app.local_entrypoint()
def main():
    res_dir = os.path.expanduser("~/projects/forge/results/smoke-2026-10-29"); os.makedirs(res_dir, exist_ok=True)
    t = train.remote()
    json.dump(t, open(os.path.join(res_dir, "train.json"), "w"), indent=1)
    print("TRAIN", json.dumps({k: v for k, v in t.items() if k != "rendered_example_tail"})[:1500])
    if t.get("error") or not t.get("adapter_files"):
        print("SKIP SERVE: training failed"); return
    s = serve.remote()
    json.dump(s, open(os.path.join(res_dir, "serve.json"), "w"), indent=1)
    print("SERVE", json.dumps(s)[:2000])


@app.function(image=image, gpu="H100", timeout=8 * 60,
              volumes={"/root/.cache/huggingface": hf_cache, "/vol": lora_vol})
def merge():
    """Merge fallback (vLLM LoRA crashed: lora_shrink AssertionError, vLLM issue 53254, image too old)."""
    import torch, transformers, shutil
    from peft import PeftModel
    lora_vol.reload(); t0 = time.time()
    base = transformers.AutoModelForMultimodalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map="cuda")
    merged = PeftModel.from_pretrained(base, "/vol/smoke").merge_and_unload()
    if os.path.exists("/vol/merged"):
        shutil.rmtree("/vol/merged")
    merged.save_pretrained("/vol/merged", safe_serialization=True, max_shard_size="5GB")
    transformers.AutoProcessor.from_pretrained(MODEL).save_pretrained("/vol/merged")
    transformers.AutoTokenizer.from_pretrained(MODEL).save_pretrained("/vol/merged")
    lora_vol.commit()
    out = {"merge_s": round(time.time() - t0, 1), "files": len(os.listdir("/vol/merged"))}
    print("MERGE_JSON " + json.dumps(out)); return out


@app.function(image=image, gpu="A100-80GB", timeout=8 * 60,
              volumes={"/root/.cache/huggingface": hf_cache, "/vol": lora_vol})
def serve_merged():
    import urllib.request
    lora_vol.reload(); t0 = time.time(); out = {}
    log = open("/tmp/vllm.log", "w")
    proc = subprocess.Popen(["vllm", "serve", "/vol/merged", "--served-model-name", "forge", "--port", "8000",
                             "--max-model-len", "8192", "--enable-auto-tool-choice",
                             "--tool-call-parser", "muse_glimmer", "--reasoning-parser", "muse_glimmer",
                             "--generation-config", "auto"], stdout=log, stderr=subprocess.STDOUT)
    ready = False
    while time.time() - t0 < 6 * 60:
        if proc.poll() is not None:
            break
        try:
            models = json.load(urllib.request.urlopen("http://localhost:8000/v1/models", timeout=5))
            out["models"] = [m["id"] for m in models["data"]]; ready = True; break
        except Exception:
            time.sleep(5)
    out["ready_s"] = round(time.time() - t0, 1)
    if ready:
        body = {"model": "forge", "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": TEST_JOB}],
                "max_tokens": 6000, "temperature": 1.0, "top_p": 0.95, "top_k": 64}
        req = urllib.request.Request("http://localhost:8000/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        ts = time.time()
        try:
            r = json.load(urllib.request.urlopen(req, timeout=150))
            msg = r["choices"][0]["message"]
            out.update(answer=msg.get("content"), reasoning_len=len(msg.get("reasoning_content") or msg.get("reasoning") or ""),
                       finish_reason=r["choices"][0].get("finish_reason"), usage=r.get("usage"),
                       answer_s=round(time.time() - ts, 1))
        except Exception as e:
            out["error"] = f"request failed: {e!r}"[:300]
    else:
        out["error"] = "vLLM (merged) did not come up (exit %s)" % proc.poll()
    if out.get("error"):
        full = open("/tmp/vllm.log").read()
        out["error_lines"] = [l[:400] for l in full.splitlines()
                              if any(w in l for w in ("Error", "error:", "Exception", "assert")) and 'File "' not in l][-30:]
    proc.kill()
    out = json.loads(json.dumps(out, default=str)); print("SERVE_JSON " + json.dumps(out)); return out


@app.local_entrypoint()
def merge_and_serve():
    res_dir = os.path.expanduser("~/projects/forge/results/smoke-2026-10-29")
    m = merge.remote()
    json.dump(m, open(os.path.join(res_dir, "merge.json"), "w"), indent=1); print("MERGE", m)
    s = serve_merged.remote()
    json.dump(s, open(os.path.join(res_dir, "serve_merged.json"), "w"), indent=1)
    print("SERVE", json.dumps(s)[:3000])
