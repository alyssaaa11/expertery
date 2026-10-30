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

Never `modal run forge_train.py::train`; it bypasses the exam guard and
the money cap. Launch only via the local entrypoints below (`smoke` /
`full`), which run the guard first, derive every timeout from the cap,
and wrap the remote calls in `app.run()`.
"""

import argparse
import difflib
import json
import math
import os
import re
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

# Money-cap timeout split (spec edit A6): merge + serve are reserved first,
# the rest goes to train. Train is refused below 15 min.
MERGE_RESERVE_S = 12 * 60  # H100
SERVE_RESERVE_S = 6 * 60  # A100-80GB
MIN_TRAIN_S = 15 * 60
STARTUP_TIMEOUT_S = 300  # Modal startup allowance, included in worst-case cost
DEADLINE_MARGIN_S = 240  # train() stops this far before its timeout
CHECKPOINT_EVERY_STEPS = 25  # save the adapter this often
EXAM_REFUSE_RATIO = 0.9  # exact-number text ratio that refuses a record
EXAM_WARN_RATIO = 0.8  # number-collapsed text ratio that only warns
EXAM_REFUSE_FRAC = 0.05  # abort only when more than this share is refused
EXAM_TOL = 1e-6  # bbox/volume match tolerance for the code guard
DATA_UPLOAD_MB = 5.0  # put the training data on the volume above this size
SERVE_READY_S = 3 * 60  # format check: at most one prompt, this long after ready
SERVE_REQUEST_TIMEOUT_S = 120  # one-prompt request budget; ready + prompt fits the timeout

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


def plan_timeouts(cap_dollars, steps, startup_s=0, spent_dollars=0.0):
    """Derive each Modal function's timeout from the money left.

    `steps` is a list of (name, rate_per_hour, want_seconds), charged in
    order. `startup_s` is the Modal startup allowance per function: the
    worst-case cost of a step is (startup_s + want) * rate, and that is
    what must fit in the money left. `spent_dollars` carries earlier spend
    in the same entrypoint run (train -> merge -> serve share one cap).
    Returns {name: seconds} plus `_left`. Raises CapExceeded when a step
    does not fit in the money left (refuses to start it).
    """
    left = float(cap_dollars) - float(spent_dollars or 0.0)
    out = {}
    for name, rate, want in steps:
        cost = dollars_for_seconds(startup_s + want, rate)
        if cost > left:
            raise CapExceeded(
                "step %r wants %ds + %ds startup ($%.2f at $%.2f/h) but only "
                "$%.2f is left of the $%.2f cap; refusing to start it"
                % (name, want, startup_s, cost, rate, left, cap_dollars)
            )
        out[name] = want
        left -= cost
    out["_left"] = round(left, 2)
    return out


def split_cap(cap_dollars, spent_dollars=0.0, startup_s=STARTUP_TIMEOUT_S):
    """Reserve merge + serve first, hand the rest to train.

    Merge gets 12 min H100, serve 6 min A100; train gets whatever the cap
    still covers (startup included). Refuses (CapExceeded) when train
    would get under 15 min. Returns {train, merge, serve, startup_s}.
    """
    merge_cost = dollars_for_seconds(startup_s + MERGE_RESERVE_S, H100_RATE)
    serve_cost = dollars_for_seconds(startup_s + SERVE_RESERVE_S, A100_RATE)
    left = float(cap_dollars) - float(spent_dollars or 0.0)
    if merge_cost + serve_cost > left:
        raise CapExceeded(
            "cap $%.2f (spent $%.2f) cannot reserve merge $%.2f + serve "
            "$%.2f; refusing" % (cap_dollars, spent_dollars or 0.0,
                                 merge_cost, serve_cost)
        )
    train_budget = left - merge_cost - serve_cost
    train_s = train_budget * 3600.0 / H100_RATE - startup_s
    if train_s < MIN_TRAIN_S:
        raise CapExceeded(
            "cap $%.2f leaves only %ds for train (under %ds); refusing"
            % (cap_dollars, max(0, int(train_s)), MIN_TRAIN_S)
        )
    return {"train": int(train_s), "merge": MERGE_RESERVE_S,
            "serve": SERVE_RESERVE_S, "startup_s": startup_s}


def worst_case_cost(plan, rates, startup_s=0):
    """Worst-case total $ of a timeout plan: sum of (startup + t) * rate."""
    total = 0.0
    for name, seconds in plan.items():
        if name.startswith("_"):
            continue
        total += dollars_for_seconds(startup_s + seconds, rates[name])
    return total


def plan_optimizer_steps(n_examples, epochs, grad_accum, max_steps=None):
    """Pure schedule: MICRO-steps (one example each) vs OPTIMIZER steps.

    Loops epochs x examples; an optimizer step fires every grad_accum
    micro-steps, plus once more at the end for a leftover partial group.
    `max_steps` caps OPTIMIZER steps. Returns {"micro_steps",
    "optimizer_steps", "groups"} where groups lists each optimizer step's
    micro-step count (the last may be a smaller partial group).
    """
    if grad_accum < 1:
        raise ValueError("grad_accum must be >= 1")
    total_micro = max(0, int(n_examples)) * max(0, int(epochs))
    full = total_micro // grad_accum
    groups = [grad_accum] * full
    leftover = total_micro - full * grad_accum
    if leftover:
        groups.append(leftover)
    if max_steps is not None:
        groups = groups[:max(0, int(max_steps))]
    return {"micro_steps": sum(groups),
            "optimizer_steps": len(groups),
            "groups": groups}


def load_training_records(path):
    """Read training records from JSONL or a JSON array (both accepted).

    Validates each record has non-empty "text" and "code" strings.
    Returns the list of dicts. Raises ValueError on bad records.
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    stripped = raw.strip()
    if not stripped:
        return []
    records = None
    if stripped.startswith("["):
        records = json.loads(stripped)
        if not isinstance(records, list):
            raise ValueError("JSON training data must be a list of records")
    else:
        records = [json.loads(line) for line in stripped.splitlines()
                   if line.strip()]
    for i, rec in enumerate(records):
        if (not isinstance(rec, dict) or not isinstance(rec.get("text"), str)
                or not rec["text"].strip()
                or not isinstance(rec.get("code"), str)
                or not rec["code"].strip()):
            raise ValueError(
                "record %d needs non-empty \"text\" and \"code\" strings" % i)
    return records


# ------------------------------------------------------------ exam guard
# Local guard, run BEFORE any remote call. Text side: difflib ratio after
# lowercasing; exact-number ratios >= 0.9 refuse, number-collapsed ratios
# >= 0.8 warn. Code side: the exam references are built in-process with
# experiments/first-test/jobs.py (trusted code); only the training
# record's code runs in cloud_cq's box (never on the Mac), measured
# grader-side. bbox + volume are compared first at
# 1e-6 and the full score runs only on a match. Refused records are
# dropped; the run aborts only when more than 5% are refused. The saved
# report holds counts only, never reference values.

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_NUM_TOKEN = " #NUM "


def normalize_exact(text):
    """Lowercased text with numbers kept (for the refusal ratio)."""
    return (text or "").lower()


def normalize_collapsed(text):
    """Lowercased text with every number replaced by a placeholder."""
    return _NUM_RE.sub(_NUM_TOKEN, (text or "").lower())


def text_ratios(text, exam_text):
    """(exact_ratio, collapsed_ratio) of a training text vs an exam text."""
    exact = difflib.SequenceMatcher(
        None, normalize_exact(text), normalize_exact(exam_text)).ratio()
    collapsed = difflib.SequenceMatcher(
        None, normalize_collapsed(text),
        normalize_collapsed(exam_text)).ratio()
    return exact, collapsed


def check_text_record(text, exam_texts):
    """Classify one record's text: ("refuse"|"warn"|"ok", detail dict).

    Refuse when the exact-number ratio to any exam text is >= 0.9;
    warn (counted, not refused) when a number-collapsed ratio is >= 0.8.
    `exam_texts` is injectable so tests can use a fake exam set.
    """
    best_exact, best_collapsed = 0.0, 0.0
    for exam in exam_texts:
        exact, collapsed = text_ratios(text, exam)
        best_exact = max(best_exact, exact)
        best_collapsed = max(best_collapsed, collapsed)
    detail = {"exact_ratio": round(best_exact, 4),
              "collapsed_ratio": round(best_collapsed, 4)}
    if best_exact >= EXAM_REFUSE_RATIO:
        return "refuse", detail
    if best_collapsed >= EXAM_WARN_RATIO:
        return "warn", detail
    return "ok", detail


def measurements_match(m, e, tol=EXAM_TOL):
    """Prefilter: bbox faces and volume agree within tol (default 1e-6)."""
    try:
        if abs(m["volume"] - e["volume"]) > tol:
            return False
        return all(abs(a - b) <= tol for a, b in zip(m["bbox"], e["bbox"]))
    except (KeyError, TypeError):
        return False


def code_matches_exam(train_meas, ref_meases, full_score_fn=None, tol=EXAM_TOL):
    """True when the training part matches an exam reference part.

    bbox + volume are compared first at tol; the full score runs only on
    a prefilter hit. `full_score_fn(train_meas, ref_meas)` defaults to a
    strict pass (prefilter decides); pass the checks.score-based scorer
    for the real decision. Returns (matched, job_index or None).
    """
    for i, ref in enumerate(ref_meases):
        if not measurements_match(train_meas, ref, tol):
            continue
        if full_score_fn is None:
            return True, i
        try:
            if full_score_fn(train_meas, ref):
                return True, i
        except Exception:
            continue
    return False, None


def exam_job_texts():
    """The 33 first-test job texts (for the text guard)."""
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "first-test", "jobs.py")
    spec = importlib.util.spec_from_file_location("exam_jobs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [j["text"] for j in mod.JOBS]


def build_exam_shapes():
    """Build the exam reference shapes in-process with jobs.py.

    Trusted code, no sandbox. Returns [(job_id, shape)]. Needs cadquery.
    """
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "first-test", "jobs.py")
    spec = importlib.util.spec_from_file_location("exam_jobs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [(j["id"], j["build"]()) for j in mod.JOBS]


def _final_cq():
    """Import cloud_cq lazily (no Modal import at module load)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "final")
    sys.path.insert(0, path)
    try:
        import cloud_cq as _mod
    finally:
        try:
            sys.path.remove(path)
        except ValueError:
            pass
    return _mod


# The training record's code runs in cloud_cq's box, never on the Mac
# (MUSE_SPEC section 4); only the exam references are built in-process
# (trusted jobs.py). Both box steps are injectable for tests.
_box_exec_fn = None  # (code) -> cloud_cq.run_answer_in_box dict
_box_measure_fn = None  # (brep_bytes) -> grader-side measurements dict


def set_box_fns(exec_fn=None, measure_fn=None):
    """Inject fake box steps (tests). Returns the previous pair."""
    global _box_exec_fn, _box_measure_fn
    old = (_box_exec_fn, _box_measure_fn)
    if exec_fn is not None:
        _box_exec_fn = exec_fn
    if measure_fn is not None:
        _box_measure_fn = measure_fn
    return old


def default_box_exec(code, timeout=60.0):
    """Real box call (needs modal). Tests inject a fake instead."""
    return _final_cq().run_answer_in_box(code)


def default_box_measure(brep_bytes):
    """Real grader-side measure of a BREP (needs modal)."""
    return _final_cq().measure_brep.remote(bytes(brep_bytes))


def run_train_code(code, timeout=60.0, sandbox_dir=None):
    """Run one training record's code in cloud_cq's box.

    Returns (brep_bytes_or_None, error_or_None). The local sandbox path
    is removed for training records: nothing the model wrote runs on
    the Mac. `sandbox_dir` is ignored (kept for the old signature).
    """
    exec_fn = _box_exec_fn or default_box_exec
    try:
        boxed = exec_fn(code)
    except Exception as e:  # noqa: BLE001 -- box down: no measurement
        return None, "harness: %s: %s" % (type(e).__name__, e)
    if boxed is None or boxed.get("brep_bytes") is None:
        return None, (boxed or {}).get("run_error") or \
            "the answer wrote no BREP"
    return boxed["brep_bytes"], None


def default_train_meas(code, timeout=60.0):
    """Run a training record's code in the box and measure the BREP
    grader-side (None on failure)."""
    brep, _err = run_train_code(code, timeout=timeout)
    if brep is None:
        return None
    measure_fn = _box_measure_fn or default_box_measure
    try:
        return measure_fn(brep)
    except Exception:  # noqa: BLE001 -- grader down: no measurement
        return None


def guard_records(records, exam_texts=None, ref_meases=None,
                  train_meas_fn=None, full_score_fn=None):
    """Run the exam guard over training records.

    `exam_texts`: exam job texts (default: the real 33 from jobs.py).
    `ref_meases`: exam reference {"bbox", "volume"} dicts (default: built
    in-process from jobs.py when cadquery is available, else skipped).
    `train_meas_fn(code)`: returns a {"bbox","volume",...} dict for a
    training record's code (default: run + measure). Returns
    (kept, refused_indices, report) where report holds counts only.
    Refused records are dropped; abort = refused share over 5%.
    """
    if exam_texts is None:
        exam_texts = exam_job_texts()
    if ref_meases is None and train_meas_fn is None:
        # Fail closed: when the exam references cannot be built, refuse to
        # train rather than silently passing the code guard. An explicit
        # ref_meases=[] (tests) still skips the code side.
        try:
            ft = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "first-test")
            if ft not in sys.path:
                sys.path.insert(0, ft)
            import checks as _checks
            ref_meases = [_checks.measure(shape)
                          for _jid, shape in build_exam_shapes()]
        except Exception as e:
            raise RuntimeError(
                "exam guard cannot build the exam references (%r); "
                "refusing to train" % (e,))
    if train_meas_fn is None and ref_meases:
        train_meas_fn = default_train_meas
    kept, refused = [], []
    n_warn = n_ref_text = n_ref_code = 0
    for idx, rec in enumerate(records):
        verdict, _ = check_text_record(rec.get("text", ""), exam_texts)
        if verdict == "refuse":
            refused.append(idx)
            n_ref_text += 1
            continue
        if verdict == "warn":
            n_warn += 1
        matched = False
        if ref_meases and train_meas_fn is not None:
            try:
                meas = train_meas_fn(rec.get("code", ""))
            except Exception:
                meas = None
            if meas is not None:
                matched, _ = code_matches_exam(meas, ref_meases,
                                              full_score_fn)
        if matched:
            refused.append(idx)
            n_ref_code += 1
            continue
        kept.append(rec)
    n = len(records)
    report = {"n_records": n, "n_refused_text": n_ref_text,
              "n_warned_text": n_warn, "n_refused_code": n_ref_code,
              "n_refused": len(refused), "n_kept": len(kept),
              "refused_frac": round(len(refused) / n, 4) if n else 0.0,
              "aborted": bool(n and len(refused) / n > EXAM_REFUSE_FRAC)}
    return kept, refused, report


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

    @app.function(image=image, gpu="H100", timeout=45 * 60,
                 startup_timeout=STARTUP_TIMEOUT_S, volumes=VOLUMES)
    def train(
        data,
        out_name,
        epochs=2,
        lr=1e-4,
        r=16,
        alpha=32,
        max_tokens=4096,
        grad_accum=8,
        gpu_minutes=45,
        max_steps=None,
        timeout_s=None,
        deadline_margin_s=DEADLINE_MARGIN_S,
    ):
        """LoRA-tune Glimmer on [{"text", "code"}] records; short prompt only.

        `data` is the records themselves (a list of dicts, JSON-serialised
        by the entrypoint), or a volume-relative path holding JSONL when
        the payload was over 5 MB. Loss only on the assistant part
        (labels -100 before it); examples longer than max_tokens are
        dropped and counted. bf16, gradient checkpointing, AdamW, cosine
        schedule with 5% warmup (LR set per OPTIMIZER step). MICRO-steps
        (one example each) accumulate gradients; an optimizer step fires
        every grad_accum micro-steps plus once more for a leftover partial
        group (scaled by its real size); `max_steps` caps OPTIMIZER steps.
        After the first optimizer step the peak GPU memory is recorded and
        the run STOPs cleanly (saving nothing) above 76 GB. The adapter is
        saved every 25 optimizer steps; when less than deadline_margin_s
        of the timeout is left, training stops after the current optimizer
        step and saves (marked stopped_at_deadline). Saves the adapter to
        /vol/<out_name>/adapter plus a train_log.json holding the fully
        rendered first training example and the first 40 decoded tokens
        that carry loss. Returns plain JSON, printed as TRAIN_JSON {...}.
        """
        import time

        import torch
        import transformers
        from peft import LoraConfig, get_peft_model

        t0 = time.time()
        timeout = timeout_s or int(gpu_minutes * 60)
        deadline_s = timeout - deadline_margin_s
        out = {
            "transformers": str(transformers.__version__),
            "torch": str(torch.__version__),
            "timeout_s": timeout,
            "deadline_s": deadline_s,
        }
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        if isinstance(data, str):  # staged on the volume (> 5 MB payloads)
            raw = open(os.path.join(LORA_MOUNT, data), encoding="utf-8").read().splitlines()
            examples = [json.loads(line) for line in raw if line.strip()]
        else:
            examples = [dict(ex) for ex in data]
        for i, ex in enumerate(examples):
            if (not isinstance(ex.get("text"), str) or not ex["text"].strip()
                    or not isinstance(ex.get("code"), str)
                    or not ex["code"].strip()):
                raise ValueError(
                    "record %d needs non-empty text and code" % i)
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
            return ids, labels, prompt, full

        kept, dropped = [], 0
        for ex in examples:
            prompt, full = _remote_render(tok, ex["text"], ex["code"])
            if len(tok(full, add_special_tokens=False)["input_ids"]) > max_tokens:
                dropped += 1
                continue
            kept.append(ex)
        out["examples"], out["dropped"] = len(kept), dropped
        if kept:
            prompt0, full0 = _remote_render(tok, kept[0]["text"], kept[0]["code"])
            ids0, labels0, _, _ = encode(kept[0])
            loss_toks = [tok.decode([i]) for i, lab in zip(ids0, labels0)
                         if lab != -100][:40]
            out["first_example"] = {"prompt": prompt0, "full": full0}
            out["first_loss_tokens"] = loss_toks

        # Same schedule as plan_optimizer_steps (inlined: the remote
        # container cannot rely on the local module's helpers).
        if grad_accum < 1:
            raise ValueError("grad_accum must be >= 1")
        total_micro = len(kept) * epochs
        sched_groups = [grad_accum] * (total_micro // grad_accum)
        if total_micro % grad_accum:
            sched_groups.append(total_micro % grad_accum)
        if max_steps is not None:
            sched_groups = sched_groups[:max(0, int(max_steps))]
        sched = {"micro_steps": sum(sched_groups),
                 "optimizer_steps": len(sched_groups),
                 "groups": sched_groups}
        total_steps = sched["optimizer_steps"]
        out["schedule"] = sched
        opt = torch.optim.AdamW(
            [p for p in model.parameters() if p.requires_grad], lr=lr
        )
        warmup = max(1, int(0.05 * total_steps)) if total_steps else 1

        def lr_at(step):
            if step < warmup:
                return lr * (step + 1) / warmup
            prog = (step - warmup) / max(1, total_steps - warmup)
            import math as _math

            return lr * 0.5 * (1.0 + _math.cos(_math.pi * prog))

        def save_adapter():
            dest = os.path.join(LORA_MOUNT, out_name, "adapter")
            os.makedirs(dest, exist_ok=True)
            model.save_pretrained(dest)
            json.dump(out, open(os.path.join(dest, "train_log.json"), "w"), indent=1)
            lora_vol.commit()
            out["adapter"] = dest

        model.train()
        opt_steps, micro_in_group, mem_stop, deadline_stop = 0, 0, False, False
        group_loss, group_toks = 0.0, 0
        out["steps"] = steps = []
        micro_iter = (ex for _epoch in range(epochs) for ex in kept)
        for ex in micro_iter:
            if opt_steps >= total_steps:
                break
            ids, labels, _, _ = encode(ex)
            ids_t = torch.tensor([ids], device="cuda")
            lab_t = torch.tensor([labels], device="cuda")
            torch.cuda.synchronize()
            ts = time.time()
            group_size = sched["groups"][opt_steps] if opt_steps < len(sched["groups"]) else grad_accum
            loss = model(input_ids=ids_t, labels=lab_t).loss / group_size
            loss.backward()
            group_loss += float(loss) * group_size
            group_toks += len(ids)
            micro_in_group += 1
            torch.cuda.synchronize()
            micro_s = round(time.time() - ts, 2)
            if micro_in_group >= group_size:
                for group in opt.param_groups:
                    group["lr"] = lr_at(opt_steps)
                opt.step()
                opt.zero_grad(set_to_none=True)
                opt_steps += 1
                micro_in_group = 0
                steps.append(
                    {
                        "step": opt_steps,
                        "micro_steps": group_size,
                        "tokens": group_toks,
                        "loss": round(group_loss / group_size, 4),
                        "lr": lr_at(opt_steps - 1),
                        "seconds": micro_s,
                    }
                )
                group_loss, group_toks = 0.0, 0
                if opt_steps == 1:
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
                if opt_steps % CHECKPOINT_EVERY_STEPS == 0:
                    save_adapter()
                if time.time() - t0 > deadline_s:
                    deadline_stop = True
                    break
        out["train_total_s"] = round(time.time() - t0, 1)
        out["stopped_at_deadline"] = bool(deadline_stop)
        if not mem_stop and opt_steps:
            save_adapter()
            json.dump(
                out, open(os.path.join(LORA_MOUNT, out_name, "adapter",
                                       "train_log.json"), "w"), indent=1
            )
            lora_vol.commit()
        out = ensure_plain_json(out)
        print("TRAIN_JSON " + json.dumps(out))
        return out

    @app.function(image=image, gpu="H100", timeout=MERGE_RESERVE_S,
                 startup_timeout=STARTUP_TIMEOUT_S, volumes=VOLUMES)
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

    @app.function(image=image, gpu="A100-80GB", timeout=SERVE_RESERVE_S,
                 startup_timeout=STARTUP_TIMEOUT_S, volumes=VOLUMES)
    def serve_merged(out_name, prompts):
        """Quick format check on the merged model (NOT scoring).

        Serves the merged model, answers at most ONE prompt (short prompt:
        system + job text; temperature 1.0, top_p 0.95, top_k 64,
        max_tokens 6000), giving it at most SERVE_READY_S after ready.
        Final-exam scoring uses the existing runner (separate spec).
        Returns the answer with usage, latency, finish_reason and reasoning
        length. On failure returns ALL log lines containing
        Error/Exception/assert.
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
        # Ready wait and the single prompt both fit inside the function's
        # timeout: at most SERVE_READY_S to come up, then one request of at
        # most SERVE_REQUEST_TIMEOUT_S.
        while time.time() - t0 < SERVE_READY_S:
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
            for prompt in list(prompts)[:1]:  # format check: one prompt only
                if time.time() - t0 - out["ready_s"] > SERVE_READY_S:
                    answers.append({"prompt": prompt,
                                    "error": "format check budget exceeded"})
                    break
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
                    r = json.load(urllib.request.urlopen(
                        req, timeout=SERVE_REQUEST_TIMEOUT_S))
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


class ExamRefused(RuntimeError):
    """Raised when the local exam guard aborts the run (> 5% refused)."""


def data_needs_volume_stage(records):
    """True when the records payload is over 5 MB (stage on the volume)."""
    return len(json.dumps(records).encode("utf-8")) > DATA_UPLOAD_MB * 1024 * 1024


def stage_data(records, out_name):
    """Payload for train.remote(): records inline, or a volume path.

    Payloads over 5 MB are uploaded to forge-lora as
    <out_name>/train_data.jsonl (JSONL) and the volume-relative path is
    returned instead. Needs modal installed for the upload path.
    """
    if not data_needs_volume_stage(records):
        return [dict(r) for r in records]
    if modal is None:
        raise RuntimeError("modal is not installed; cannot stage data")
    import tempfile
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    try:
        for rec in records:
            tmp.write(json.dumps(rec) + "\n")
        tmp.close()
        with lora_vol.batch_upload() as batch:
            batch.put_file(tmp.name, "%s/train_data.jsonl" % out_name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return "%s/train_data.jsonl" % out_name


def guard_or_abort(records, res_dir, exam_texts=None, ref_meases=None,
                  train_meas_fn=None):
    """Run the exam guard, save exam_guard.json (counts only), abort if needed.

    Returns the kept records. Raises ExamRefused when more than 5% of the
    records are refused. The optional hooks inject a fake exam set in tests.
    """
    kept, _refused, report = guard_records(
        records, exam_texts=exam_texts, ref_meases=ref_meases,
        train_meas_fn=train_meas_fn)
    with open(os.path.join(res_dir, "exam_guard.json"), "w") as f:
        json.dump(report, f, indent=1)
    print("EXAM_GUARD %s" % json.dumps(report))
    if report["aborted"]:
        raise ExamRefused(
            "exam guard refused %d/%d records (%.1f%%); aborting" % (
                report["n_refused"], report["n_records"],
                100.0 * report["refused_frac"]))
    return kept


def _pipeline(data_arg, out_name, split, res_dir, train_kwargs,
              serve_prompts, spent_dollars=0.0):
    """Shared train -> merge -> format-check pipeline. Returns the split.

    The remote calls run inside `app.run()` (with output enabled), so the
    entrypoints work from the forge venv: `.remote()` needs a running app.
    """
    if modal is None or globals().get("app") is None:
        raise RuntimeError("modal is not installed; cannot run remotely")
    startup = split["startup_s"]
    # Launchable from the forge venv: remote calls need a running app.
    with modal.enable_output():
        with app.run():
            t = train.with_options(timeout=split["train"]).remote(
                data_arg, out_name, timeout_s=split["train"], **train_kwargs)
            json.dump(t, open(os.path.join(res_dir, "train.json"), "w"), indent=1)
            print("TRAIN", json.dumps(
                {k: v for k, v in t.items() if k != "steps"})[:1500])
            if t.get("error") or t.get("mem_stop"):
                print("SKIP MERGE/SERVE: training stopped")
                return split
            spent = spent_dollars + dollars_for_seconds(
                startup + float(t.get("train_total_s") or split["train"]),
                H100_RATE)
            # Re-derive merge/serve from the money left (train -> merge ->
            # serve share one cap); refuses when the remainder no longer
            # fits them.
            plan_timeouts(float(split["cap_dollars"]), [
                ("merge", H100_RATE, split["merge"]),
                ("serve", A100_RATE, split["serve"]),
            ], startup_s=startup, spent_dollars=spent)
            m = merge.with_options(timeout=split["merge"]).remote(out_name)
            json.dump(m, open(os.path.join(res_dir, "merge.json"), "w"), indent=1)
            print("MERGE", m)
            if serve_prompts:
                s = serve_merged.with_options(timeout=split["serve"]).remote(
                    out_name, list(serve_prompts)[:1])  # one prompt only
                json.dump(s, open(os.path.join(res_dir, "serve.json"), "w"),
                          indent=1)
                print("SERVE", json.dumps(s)[:2000])
            else:
                print("SKIP SERVE: no format-check prompt given")
    return split


def run_smoke(cap_dollars, spent_dollars=0.0):
    """Smoke pipeline: guard + train (max_steps 10, epochs 2) + merge + check.

    Timeout split: merge 12 min H100 + serve 6 min A100 reserved first,
    the rest to train (refused under 15 min). Raises CapExceeded when a
    step does not fit; planning works offline.
    """
    records = load_training_records(SMOKE_EXAMPLES)  # same loader (JSON ok)
    split = split_cap(cap_dollars, spent_dollars)
    split["cap_dollars"] = float(cap_dollars)
    if modal is None:
        raise RuntimeError("modal is not installed; cannot run remotely")
    res_dir = results_dir("smoke")
    kept = guard_or_abort(records, res_dir)
    data_arg = stage_data(kept, "smoke")
    return _pipeline(data_arg, "smoke", split, res_dir,
                     {"epochs": 2, "max_steps": 10}, [SMOKE_JOB],
                     spent_dollars)


def run_full(data, out_name, cap_dollars, spent_dollars=0.0, max_steps=None,
             prompts=()):
    """Full pipeline on a JSONL/JSON file; timeouts derived from the cap left."""
    records = load_training_records(data)
    split = split_cap(cap_dollars, spent_dollars)
    split["cap_dollars"] = float(cap_dollars)
    if modal is None:
        raise RuntimeError("modal is not installed; cannot run remotely")
    res_dir = results_dir(out_name)
    kept = guard_or_abort(records, res_dir)
    data_arg = stage_data(kept, out_name)
    kwargs = {"epochs": 2}
    if max_steps is not None:
        kwargs["max_steps"] = max_steps
    return _pipeline(data_arg, out_name, split, res_dir, kwargs,
                     list(prompts), spent_dollars)


def main(argv=None):
    """Local entrypoints: `smoke` and `full --data <jsonl> --out <name>`.

    Every entrypoint takes --cap-dollars and derives each function's
    timeout from the money left, refusing to start a step that does not fit.
    """
    parser = argparse.ArgumentParser(description="Forge training pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    smoke = sub.add_parser("smoke", help="train/merge/serve on the smoke examples")
    smoke.add_argument("--cap-dollars", type=float, required=True)
    smoke.add_argument("--spent-dollars", type=float, default=0.0,
                       help="earlier spend in this run (shares the cap)")
    full = sub.add_parser("full", help="train/merge/serve on a JSONL file")
    full.add_argument("--data", required=True)
    full.add_argument("--out", required=True)
    full.add_argument("--cap-dollars", type=float, required=True)
    full.add_argument("--spent-dollars", type=float, default=0.0,
                      help="earlier spend in this run (shares the cap)")
    full.add_argument("--max-steps", type=int, default=None,
                      help="cap OPTIMIZER steps")
    full.add_argument("--prompt", action="append", default=[],
                      help="job text for the one-prompt format check")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "smoke":
            run_smoke(args.cap_dollars, spent_dollars=args.spent_dollars)
        else:
            run_full(args.data, args.out, args.cap_dollars,
                     spent_dollars=args.spent_dollars,
                     max_steps=args.max_steps, prompts=args.prompt)
    except CapExceeded as e:
        print("CAP REFUSED: %s" % e)
        return 2
    except ExamRefused as e:
        print("EXAM REFUSED: %s" % e)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
