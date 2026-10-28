#!/usr/bin/env python3
"""First-test runner: send each job to each contestant model, run the returned
CadQuery code, score it with checks.py, and log everything.

Built to RUNNER_SPEC.md. Uses only the standard library for HTTP
(urllib.request) plus cadquery. Never prints, logs or writes an API key.

CLI: runner.py --jobs dry|main --out <dir> [--budget 5.0]
"""

import argparse
import concurrent.futures
import datetime
import http.client
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import checks  # noqa: E402  (frozen file; imported, not modified)

# ---------------------------------------------------------------- constants

SYSTEM_PROMPT = (
    "You write CadQuery Python code. Units are millimetres. "
    "Assign the final solid to a variable named result. "
    "Reply with exactly one Python code block and nothing else."
)
MANUAL_PREFIX = "Here is the CadQuery manual. Use it.\n\n"

GLIMMER_MODEL = "muse-glimmer"
SPARK_MODEL = "meta-models/muse-spark-open-1026"
BASETEN_URL = "https://inference.baseten.co/v1/chat/completions"

MAX_TOKENS = 8000
TEMPERATURE = 0.6
CALL_TIMEOUT = 600.0      # per-call HTTP timeout, seconds
RETRY_DELAY = 20.0        # wait before the single allowed retry, seconds
RUN_TIMEOUT = 60.0        # per-answer CadQuery execution limit, seconds
MAX_WORKERS = 16
RUN_ERROR_TAIL = 800      # chars of run error kept in calls.jsonl

# Budget guard pricing (RUNNER_SPEC.md).
COST_C_IN_PER_M = 1.25    # $/M input tokens, arm C
COST_C_OUT_PER_M = 4.25   # $/M output tokens, arm C
GPU_DOLLARS_PER_HOUR = 2.50  # arms A+B share one A100-80GB, counted once

FENCE_RE = re.compile(r"```(?:python)?[ \t]*\r?\n?(.*?)```", re.DOTALL)

ARMS = ("A", "B", "C")

# ---------------------------------------------------------------- arms/messages


def arm_model(arm):
    if arm in ("A", "B"):
        return GLIMMER_MODEL
    if arm == "C":
        return SPARK_MODEL
    raise ValueError(f"unknown arm {arm!r}")


def arm_endpoint(arm, glimmer_url):
    if arm in ("A", "B"):
        return glimmer_url.rstrip("/") + "/v1/chat/completions"
    if arm == "C":
        return BASETEN_URL
    raise ValueError(f"unknown arm {arm!r}")


def arm_uses_manual(arm):
    return arm in ("B", "C")


def build_messages(arm, job_text, manual_text):
    """Exactly the spec's messages: system + job text (arm A), or system +
    manual-as-first-user-message + job-text-as-second-user-message (B, C)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    if arm_uses_manual(arm):
        messages.append({"role": "user", "content": MANUAL_PREFIX + manual_text})
    messages.append({"role": "user", "content": job_text})
    return messages


def build_body(model, messages):
    """Exactly the spec's request body keys. Nothing else."""
    return {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }


# ---------------------------------------------------------------- extraction


def extract_code(content):
    """First fenced code block (```python or ```); whole content if none."""
    if not content:
        return content
    m = FENCE_RE.search(content)
    if not m:
        return content
    return m.group(1).strip()


# ---------------------------------------------------------------- HTTP (stdlib only)


def is_retryable(exc):
    """Retryable = network error or HTTP 5xx/429. Nothing else retries."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    return isinstance(
        exc,
        (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            socket.timeout,
            http.client.HTTPException,
            OSError,
        ),
    )


def real_post_fn(endpoint, key, timeout=CALL_TIMEOUT):
    """POST one chat-completions body with urllib only. Returns parsed JSON."""

    def _post(endpoint_arg, body_arg, timeout_arg):
        req = urllib.request.Request(
            endpoint_arg,
            data=json.dumps(body_arg).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_arg) as resp:
            return json.load(resp)

    return _post


def post_with_retry(post_fn, endpoint, body, timeout, sleep_fn):
    """One attempt; a single retry after RETRY_DELAY only for a network
    error or HTTP 5xx/429. Anything else is raised immediately."""
    try:
        return post_fn(endpoint, body, timeout)
    except Exception as first:
        if not is_retryable(first):
            raise
        sleep_fn(RETRY_DELAY)
        return post_fn(endpoint, body, timeout)


def parse_response(data):
    """Split a chat-completions body into (content, finish_reason, usage,
    reasoning_len). Only the reasoning length is kept, never its text."""
    data = data or {}
    try:
        choice = (data.get("choices") or [{}])[0] or {}
    except (AttributeError, IndexError, TypeError):
        choice = {}
    if not isinstance(choice, dict):
        choice = {}
    finish_reason = choice.get("finish_reason")
    msg = choice.get("message") or {}
    if not isinstance(msg, dict):
        msg = {}
    content = msg.get("content")
    if content is None:
        content = ""
    elif not isinstance(content, str):
        parts = []
        try:
            blocks = list(content)
        except TypeError:
            blocks = []
        for block in blocks:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        content = "".join(parts)
    usage = data.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    reasoning_len = 0
    for key in ("reasoning_content", "reasoning", "thought", "thinking"):
        val = msg.get(key, None)
        if val is None:
            val = choice.get(key, None)
        if val:
            reasoning_len = len(val) if isinstance(val, str) else len(str(val))
            break
    return content, finish_reason, usage, reasoning_len


# ---------------------------------------------------------------- code execution (separate process + STEP)


EXPORTER_SNIPPET = (
    "import sys as _sys, tempfile as _tf\n"
    "try:\n"
    "    _r = result\n"
    "except NameError:\n"
    "    print(\"ERROR: no variable named 'result'\", file=_sys.stderr)\n"
    "    _sys.exit(2)\n"
    "_f = _tf.NamedTemporaryFile(suffix='.step', delete=False)\n"
    "_f.close()\n"
    "_p = _f.name\n"
    "from cadquery import exporters as _ex\n"
    "_ex.export(_r, _p)\n"
    "print(_p, flush=True)\n"
)


def run_code(code, python=None, timeout=RUN_TIMEOUT):
    """Run `code` in `<python> -I -c <wrapper>` with cwd /tmp and a 60 s
    limit. The wrapper exports `result` as STEP and prints the path; the
    STEP is imported here. Returns (shape_or_None, error_or_None)."""
    import cadquery as cq

    python = python or sys.executable
    wrapper = (code or "") + "\n" + EXPORTER_SNIPPET
    try:
        proc = subprocess.run(
            [python, "-I", "-c", wrapper],
            cwd="/tmp",
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"timeout after {timeout:g}s running answer code"
    except OSError as e:
        return None, f"could not start answer subprocess: {e}"
    step_path = ""
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line:
            step_path = line
    if proc.returncode != 0 or not step_path or not os.path.isfile(step_path):
        err = (proc.stderr or "").strip() or f"exit {proc.returncode}"
        return None, f"answer code failed (exit {proc.returncode}): {err}"
    try:
        shape = cq.importers.importStep(step_path)
        return shape, None
    except Exception as e:  # noqa: BLE001 -- reported as FAIL, not raised
        return None, f"could not import exported STEP: {e!r}"
    finally:
        try:
            if step_path and os.path.isfile(step_path):
                os.remove(step_path)
        except OSError:
            pass


def score_content(content, finish_reason, build_ref, expected, timeout=RUN_TIMEOUT):
    """Classify one answer. Returns
    (outcome, failed_checks, measurements, code, run_error).

    INVALID: finish_reason == "length", empty content, or a network/HTTP
    error after the retry (signalled by finish_reason=None and content=""
    with run_error set by the caller). INVALID is never FAIL.
    PASS: checks.score passes. FAIL: everything else.
    """
    if finish_reason == "length":
        return ("INVALID", [], None, "", "cut off by the token limit")
    if not content or not content.strip():
        return ("INVALID", [], None, "", "empty reply")
    code = extract_code(content)
    if not code or not code.strip():
        return ("INVALID", [], None, code, "empty reply")
    answer, run_error = run_code(code, timeout=timeout)
    if answer is None:
        return ("FAIL", [], None, code, run_error or "code error")
    try:
        passed, fails, measurements = checks.score(answer, build_ref(), expected)
    except Exception as e:  # noqa: BLE001 -- a broken shape is FAIL
        return ("FAIL", ["scoring error"], None, code, f"scoring raised: {e!r}")
    if passed:
        return ("PASS", [], measurements, code, None)
    return ("FAIL", list(fails), measurements, code, None)


# ---------------------------------------------------------------- one (job, arm) call


def utcnow_iso():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def scrub(text, secrets):
    for secret in secrets:
        if secret and isinstance(secret, str) and secret in (text or ""):
            text = text.replace(secret, "***")
    return text


def do_call(
    job,
    arm,
    model,
    endpoint,
    secrets,
    manual_text,
    expected_for_job,
    post_fn,
    sleep_fn,
    exec_timeout=RUN_TIMEOUT,
    call_timeout=CALL_TIMEOUT,
):
    """Run one (job, arm) pair exactly once: POST, retry once only on a
    network error / HTTP 5xx/429, then score. Never raises for a bad
    answer; network/HTTP failure after the retry is INVALID, never FAIL."""
    body = build_body(model, build_messages(arm, job["text"], manual_text))
    start = utcnow_iso()
    t0 = time.monotonic()
    content, finish_reason, usage, reasoning_len = "", None, {}, 0
    outcome = fails = measurements = code = run_error = None
    try:
        data = post_with_retry(post_fn, endpoint, body, call_timeout, sleep_fn)
        content, finish_reason, usage, reasoning_len = parse_response(data)
        outcome, fails, measurements, code, run_error = score_content(
            content, finish_reason, job["build"], expected_for_job, exec_timeout
        )
    except Exception as e:  # noqa: BLE001 -- failed call => INVALID record
        outcome, fails, measurements, code = "INVALID", [], None, ""
        run_error = f"{type(e).__name__}: {e}"
    seconds = time.monotonic() - t0
    end = utcnow_iso()
    run_error = scrub(run_error, secrets)
    if run_error and len(run_error) > RUN_ERROR_TAIL:
        run_error = run_error[-RUN_ERROR_TAIL:]
    return {
        "job": job["id"],
        "level": job.get("level"),
        "arm": arm,
        "model": model,
        "start": start,
        "start_time": start,
        "end": end,
        "end_time": end,
        "seconds": round(seconds, 3),
        "finish_reason": finish_reason,
        "usage": usage,
        "content": content,
        "reasoning_len": reasoning_len,
        "reasoning_length": reasoning_len,
        "code": code,
        "extracted_code": code,
        "outcome": outcome,
        "fails": fails or [],
        "failed_checks": fails or [],
        "measurements": measurements,
        "run_error": run_error,
    }


# ---------------------------------------------------------------- budget guard


def cost_c_of_usage(usage):
    usage = usage or {}
    try:
        prompt = float(usage.get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt = 0.0
    try:
        completion = float(usage.get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion = 0.0
    return prompt * COST_C_IN_PER_M / 1e6 + completion * COST_C_OUT_PER_M / 1e6


def gpu_cost_of_elapsed(elapsed_s):
    return max(0.0, elapsed_s) * GPU_DOLLARS_PER_HOUR / 3600.0


def estimate_total(c_usages, elapsed_s):
    """Running estimate: arm-C token cost (from usage) + one shared A100
    cost for the whole run's wall-clock time. Arms A and B are never
    charged per call."""
    return sum(cost_c_of_usage(u) for u in c_usages) + gpu_cost_of_elapsed(elapsed_s)


def over_budget(c_usages, elapsed_s, budget):
    return estimate_total(c_usages, elapsed_s) > budget


# ---------------------------------------------------------------- suite


def run_suite(
    jobs,
    expected,
    manual_text,
    out_dir,
    arm_cfgs,
    key_map=None,
    budget=5.0,
    post_fn=None,
    sleep_fn=time.sleep,
    max_workers=MAX_WORKERS,
    exec_timeout=RUN_TIMEOUT,
    call_timeout=CALL_TIMEOUT,
    arms=ARMS,
):
    """Call every (job, arm) pair once with up to `max_workers` concurrent
    calls. Stop sending new calls once the cost estimate passes `budget`.
    Writes calls.jsonl, summary.json and report.md into `out_dir`.

    `arm_cfgs`: {arm: {"endpoint": ..., "model": ...}}.
    `key_map`: {arm: api_key}; keys are only used in the Authorization
    header, never in any record. `post_fn(endpoint, body, timeout)` may be
    a fake for tests; the default posts with urllib.
    Returns (records, summary).
    """
    key_map = key_map or {}
    secrets = [k for k in key_map.values() if k]
    if post_fn is None:
        post_fn = _default_post_fn(arm_cfgs, key_map, call_timeout)
    os.makedirs(out_dir, exist_ok=True)
    pairs = [(job, arm) for job in jobs for arm in arms]
    records = [None] * len(pairs)
    t_start = time.monotonic()
    c_usages = []
    budget_stopped = False
    next_i = 0
    in_flight = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        while next_i < len(pairs) or in_flight:
            while next_i < len(pairs) and len(in_flight) < max_workers:
                if over_budget(c_usages, time.monotonic() - t_start, budget):
                    budget_stopped = True
                    break
                job, arm = pairs[next_i]
                cfg = arm_cfgs[arm]
                fut = pool.submit(
                    do_call,
                    job,
                    arm,
                    cfg["model"],
                    cfg["endpoint"],
                    secrets,
                    manual_text,
                    expected.get(job["id"]),
                    post_fn,
                    sleep_fn,
                    exec_timeout,
                    call_timeout,
                )
                in_flight[fut] = next_i
                next_i += 1
            if budget_stopped and not in_flight:
                break
            if not in_flight:
                break
            done, _ = concurrent.futures.wait(
                in_flight, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for fut in done:
                idx = in_flight.pop(fut)
                job, arm = pairs[idx]
                try:
                    rec = fut.result()
                except Exception as e:  # noqa: BLE001 -- never lose a slot
                    rec = {
                        "job": job["id"],
                        "level": job.get("level"),
                        "arm": arm,
                        "model": arm_cfgs[arm]["model"],
                        "outcome": "INVALID",
                        "fails": [],
                        "failed_checks": [],
                        "measurements": None,
                        "run_error": scrub(
                            f"runner error: {e!r}", secrets
                        )[-RUN_ERROR_TAIL:],
                    }
                records[idx] = rec
                if arm == "C" and isinstance(rec.get("usage"), dict):
                    c_usages.append(rec["usage"])
            if budget_stopped:
                # Drain what is already in flight, but send nothing new.
                while in_flight:
                    done, _ = concurrent.futures.wait(
                        in_flight,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                    for fut in done:
                        idx = in_flight.pop(fut)
                        job, arm = pairs[idx]
                        try:
                            records[idx] = fut.result()
                        except Exception as e:  # noqa: BLE001
                            records[idx] = {
                                "job": job["id"],
                                "level": job.get("level"),
                                "arm": arm,
                                "model": arm_cfgs[arm]["model"],
                                "outcome": "INVALID",
                                "fails": [],
                                "failed_checks": [],
                                "measurements": None,
                                "run_error": scrub(
                                    f"runner error: {e!r}", secrets
                                )[-RUN_ERROR_TAIL:],
                            }
                        if arm == "C" and isinstance(
                            records[idx].get("usage"), dict
                        ):
                            c_usages.append(records[idx]["usage"])
                break
    elapsed = time.monotonic() - t_start
    sent = [r for r in records if r is not None]
    skipped = len(records) - len(sent)
    summary = build_summary(
        sent, c_usages, elapsed, budget, budget_stopped, skipped, arms
    )
    calls_path = os.path.join(out_dir, "calls.jsonl")
    with open(calls_path, "w", encoding="utf-8") as f:
        for rec in sent:
            f.write(json.dumps(rec) + "\n")
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(build_report(summary))
    return sent, summary


def _default_post_fn(arm_cfgs, key_map, call_timeout):
    endpoints = {cfg["endpoint"]: arm for arm, cfg in arm_cfgs.items()}

    def _post(endpoint_arg, body_arg, timeout_arg):
        arm = endpoints.get(endpoint_arg)
        key = key_map.get(arm, "")
        return real_post_fn(endpoint_arg, key, timeout_arg)(
            endpoint_arg, body_arg, timeout_arg
        )

    return _post


# ---------------------------------------------------------------- summary / decision


def arm_stats(records, arm):
    arm_recs = [r for r in records if r.get("arm") == arm]
    n_pass = sum(1 for r in arm_recs if r.get("outcome") == "PASS")
    n_fail = sum(1 for r in arm_recs if r.get("outcome") == "FAIL")
    n_inv = sum(1 for r in arm_recs if r.get("outcome") == "INVALID")
    scored = n_pass + n_fail
    return {
        "n": len(arm_recs),
        "PASS": n_pass,
        "FAIL": n_fail,
        "INVALID": n_inv,
        "pass_rate": (n_pass / scored) if scored else None,
        "invalid_rate": (n_inv / len(arm_recs)) if arm_recs else None,
    }


def compute_decision(rate_b, rate_c, invalid_rates):
    """PLAN.md section 7 from the numbers. Returns (decision, run_valid).

    run_valid is False ("run not valid") if INVALID > 5% in any arm.
    A C-B gap of 15-25 points forces the grey zone even if a rule is met.
    """
    run_valid = all(
        (r is not None and r <= 0.05) for r in invalid_rates.values()
    )
    if rate_b is None or rate_c is None:
        decision = "grey zone (too few scored calls to apply section 7)"
    else:
        gap = rate_c - rate_b
        if 0.15 <= gap <= 0.25:
            decision = (
                "grey zone (C-B gap %.1f points is in the 15-25 grey band)"
                % (gap * 100)
            )
        elif rate_b <= 0.60 and rate_c >= 0.30 and gap >= 0.20:
            decision = "GO to training"
        elif rate_b >= 0.80:
            decision = "STOP (manual is enough)"
        elif rate_c < 0.20:
            decision = "Spark can't teach"
        else:
            decision = "grey zone"
    if not run_valid:
        decision = "run not valid (INVALID > 5% in an arm); " + decision
    return decision, run_valid


def build_summary(records, c_usages, elapsed_s, budget, budget_stopped, skipped, arms):
    per_arm = {arm: arm_stats(records, arm) for arm in arms}
    levels = sorted({r.get("level") for r in records if r.get("level")})
    by_level = {}
    for level in levels:
        by_level[level] = {}
        for arm in arms:
            sub = [r for r in records if r.get("level") == level]
            by_level[level][arm] = arm_stats(sub, arm)
    cost_c = sum(cost_c_of_usage(u) for u in c_usages)
    gpu_total = gpu_cost_of_elapsed(elapsed_s)
    costs = {
        "A": round(gpu_total / 2, 4),
        "B": round(gpu_total / 2, 4),
        "C": round(cost_c, 4),
        "gpu_total": round(gpu_total, 4),
        "total": round(gpu_total + cost_c, 4),
        "note": "Arms A+B share one A100-80GB at $2.50/h over the run "
        "wall-clock, counted once (split evenly for display). Arm C is "
        "input $1.25/M + output $4.25/M tokens from usage.",
    }
    invalid_rates = {
        arm: per_arm[arm]["invalid_rate"] for arm in arms if per_arm[arm]["n"]
    }
    decision, run_valid = compute_decision(
        per_arm.get("B", {}).get("pass_rate"),
        per_arm.get("C", {}).get("pass_rate"),
        invalid_rates,
    )
    table = {}
    for rec in records:
        table.setdefault(rec["job"], {})[rec["arm"]] = rec.get("outcome")
    return {
        "arms": per_arm,
        "levels": by_level,
        "by_level": by_level,
        "n_calls": len(records),
        "skipped": skipped,
        "budget": budget,
        "budget_stopped": budget_stopped,
        "elapsed_seconds": round(elapsed_s, 3),
        "costs": costs,
        "decision": decision,
        "run_valid": run_valid,
        "table": table,
    }


def _pct(rate):
    return "n/a" if rate is None else f"{100 * rate:.1f}%"


def build_report(summary):
    arms = [a for a in ("A", "B", "C") if a in summary["arms"]]
    lines = ["# First-test report", ""]
    lines.append(f"Decision (PLAN.md section 7): **{summary['decision']}**")
    lines.append(f"Run valid: {summary['run_valid']}")
    lines.append(
        f"Calls: {summary['n_calls']}  "
        f"Skipped by budget guard: {summary['skipped']}  "
        f"(budget ${summary['budget']}, stopped: {summary['budget_stopped']})"
    )
    lines.append("")
    lines.append("## Cost estimate")
    for arm in arms:
        lines.append(f"- Arm {arm}: ${summary['costs'].get(arm, 0):.4f}")
    lines.append(f"- Total: ${summary['costs']['total']:.4f}")
    lines.append("")
    lines.append("## Per arm (PASS / FAIL / INVALID, pass rate, INVALID rate)")
    lines.append("| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |")
    lines.append("|---|---|---|---|---|---|")
    for arm in arms:
        s = summary["arms"][arm]
        lines.append(
            f"| {arm} | {s['PASS']} | {s['FAIL']} | {s['INVALID']} | "
            f"{_pct(s['pass_rate'])} | {_pct(s['invalid_rate'])} |"
        )
    lines.append("")
    for level, per in summary["levels"].items():
        lines.append(f"## Level {level}")
        lines.append("| Arm | PASS | FAIL | INVALID | pass rate | INVALID rate |")
        lines.append("|---|---|---|---|---|---|")
        for arm in arms:
            s = per.get(arm, {"PASS": 0, "FAIL": 0, "INVALID": 0,
                              "pass_rate": None, "invalid_rate": None})
            lines.append(
                f"| {arm} | {s['PASS']} | {s['FAIL']} | {s['INVALID']} | "
                f"{_pct(s['pass_rate'])} | {_pct(s['invalid_rate'])} |"
            )
        lines.append("")
    lines.append("## Per-job outcomes")
    lines.append("| Job | " + " | ".join(arms) + " |")
    lines.append("|---|" + "|".join(["---"] * len(arms)) + "|")
    for job in sorted(summary["table"]):
        lines.append(
            "| " + job + " | "
            + " | ".join(str(summary["table"][job].get(a, "-")) for a in arms)
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI


def load_inputs():
    from jobs import JOBS  # noqa: E402  (frozen file; imported, not modified)

    with open(os.path.join(HERE, "expected.json"), encoding="utf-8") as f:
        expected = json.load(f)
    with open(os.path.join(HERE, "manual.md"), encoding="utf-8") as f:
        manual_text = f.read()
    return JOBS, expected, manual_text


def main(argv=None):
    parser = argparse.ArgumentParser(description="First-test runner.")
    parser.add_argument("--jobs", choices=("dry", "main"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--budget", type=float, default=5.0)
    args = parser.parse_args(argv)

    glimmer_url = os.environ.get("GLIMMER_URL", "")
    glimmer_key = os.environ.get("GLIMMER_KEY", "")
    baseten_key = os.environ.get("BASETEN_KEY", "")
    missing = [
        name
        for name, val in (
            ("GLIMMER_URL", glimmer_url),
            ("GLIMMER_KEY", glimmer_key),
            ("BASETEN_KEY", baseten_key),
        )
        if not val
    ]
    if missing:
        parser.error("missing environment variables: " + ", ".join(missing))

    JOBS, expected, manual_text = load_inputs()
    if args.jobs == "dry":
        jobs = [j for j in JOBS if j.get("level") == "dry"]
    else:
        jobs = [j for j in JOBS if j.get("level") in ("medium", "hard")]
    if not jobs:
        parser.error(f"no jobs for --jobs {args.jobs}")

    arm_cfgs = {
        "A": {"endpoint": arm_endpoint("A", glimmer_url), "model": GLIMMER_MODEL},
        "B": {"endpoint": arm_endpoint("B", glimmer_url), "model": GLIMMER_MODEL},
        "C": {"endpoint": BASETEN_URL, "model": SPARK_MODEL},
    }
    key_map = {"A": glimmer_key, "B": glimmer_key, "C": baseten_key}
    run_suite(
        jobs, expected, manual_text, args.out, arm_cfgs, key_map, args.budget
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())