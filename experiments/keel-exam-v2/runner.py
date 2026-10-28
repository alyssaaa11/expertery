#!/usr/bin/env python3
"""Keel v2 baseline runner: send each exam job to each arm k times, run the
returned Keel code in the PLAN.md 4c sandbox, score it with referee.py, and
log everything.

Built to RUNNER_SPEC.md from ../first-test/runner.py (copied patterns; that
folder is not modified). Uses only the standard library for HTTP
(urllib.request) plus cadquery (in-process, for the referee only: the
referee never runs untrusted code). Never prints, logs or writes an API key.

CLI: runner.py --mode pilot|main [--arms B,C] [--k 3] --out <dir>
    [--budget 2.50] [--budget-c 4.00] [--max-minutes 60]
    [--gpu-start <unix seconds>] [--parallel 16] [--timeout 120]
    [--max-rss-mb 4096] [--print-hashes]

Offline: no model call is made unless this process runs with real keys and
endpoints; the tests use a fake post_fn and never touch the network.
"""

import argparse
import concurrent.futures
import datetime
import hashlib
import http.client
import json
import os
import random
import re
import shlex
import shutil
import signal
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

import referee  # noqa: E402  (frozen file; imported, not modified)

# referee.py prepends ../first-test to sys.path (it imports checks from
# there). Keep this folder first so `import jobs` always means the v2 exam
# jobs, never the first test's. The runner process also needs the repo's
# `keel` package (to build references for the referee).
COMPANY = os.path.normpath(os.path.join(HERE, "..", "..", "company"))
for _p in (COMPANY, HERE):
    if _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, COMPANY)
sys.path.insert(0, HERE)

# ---------------------------------------------------------------- constants

# PLAN.md 4b, exact.
SYSTEM_PROMPT = (
    "You write programs for Keel, Quillon Orbital Works' private part-description tool. "
    "Units are millimetres. Follow the Keel manual exactly. "
    "The program must start with `import keel`, create the part with `p = keel.part(...)`, "
    "and end with `solid = p.finish()`. "
    "Reply with exactly one Python code block and nothing else."
)
MANUAL_PREFIX = "Here is the Keel manual. Use it.\n\n"

GLIMMER_MODEL = "muse-glimmer"
SPARK_MODEL = "meta-models/muse-spark-open-1026"
BASETEN_URL = "https://inference.baseten.co/v1/chat/completions"

MAX_TOKENS = 16000
TEMPERATURE = 1.0
TOP_P = 0.95
TOP_K = 64
CALL_TIMEOUT = 600.0      # per-call HTTP timeout, seconds
RETRY_DELAY = 20.0        # wait before the single allowed retry, seconds
RUN_TIMEOUT = 120.0       # per-answer sandbox wall-clock limit, seconds (PLAN 4c)
MAX_RSS_MB = 4096         # sandbox memory kill threshold, MB (PLAN 4c: 4 GB)
RSS_POLL = 0.5            # RSS watchdog interval, seconds
MAX_WORKERS = 16
RUN_ERROR_TAIL = 800      # chars of run error kept in calls.jsonl
STREAM_TAIL = 2000        # chars of sandbox stdout/stderr kept in calls.jsonl

# Budget guard pricing (PLAN.md 5).
COST_C_IN_PER_M = 1.25    # $/M input tokens, arm C (Baseten)
COST_C_OUT_PER_M = 4.25   # $/M output tokens, arm C (Baseten)
GPU_DOLLARS_PER_HOUR = 2.50  # Glimmer arm on one A100-80GB, counted once

FENCE_RE = re.compile(r"```(?:python)?[ \t]*\r?\n?(.*?)```", re.DOTALL)

ARMS = ("B", "C")
DEFAULT_ARMS = ("B", "C")
DEFAULT_K = 3
DEFAULT_BUDGET = 2.50        # Modal cap, USD (PLAN.md 5)
DEFAULT_BUDGET_C = 4.00      # Baseten cap, USD (PLAN.md 5)
DEFAULT_MAX_MINUTES = 60     # Glimmer wall-clock limit, minutes (PLAN.md 5)
PILOT_JOBS = ("M1", "M7", "H9")

RUN_ONE_PY = os.path.join(HERE, "run_one.py")
SANDBOX_SB = os.path.join(HERE, "sandbox.sb")

# PLAN.md 7: files frozen by hash, paths relative to this folder.
FROZEN_FILES = (
    "jobs.py",
    "expected.json",
    "referee.py",
    "runner.py",
    "sandbox.sb",
    "run_one.py",
    "../first-test/checks.py",
    "../../company/keel/__init__.py",
    "../../company/manual.md",
)

BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 0


class FreezeError(Exception):
    """The PLAN.md 7 freeze check refused the run."""


# ---------------------------------------------------------------- arms/messages


def parse_arms(value):
    """Parse a comma-separated --arms value into a tuple of valid arms."""
    if isinstance(value, (tuple, list)):
        parts = list(value)
    else:
        parts = str(value).split(",")
    arms = tuple(p.strip() for p in parts if p.strip())
    if not arms:
        raise ValueError("no arms requested (expected comma list of B,C)")
    for arm in arms:
        if arm not in ARMS:
            raise ValueError(
                f"unknown arm {arm!r} (expected comma list of B,C)"
            )
    return arms


def arm_model(arm):
    if arm == "B":
        return GLIMMER_MODEL
    if arm == "C":
        return SPARK_MODEL
    raise ValueError(f"unknown arm {arm!r}")


def arm_endpoint(arm, glimmer_url):
    if arm == "B":
        return glimmer_url.rstrip("/") + "/v1/chat/completions"
    if arm == "C":
        return BASETEN_URL
    raise ValueError(f"unknown arm {arm!r}")


def build_messages(job_text, manual_text):
    """Exactly PLAN.md 4b: system + manual-as-first-user-message +
    request-text-as-second-user-message. Same for both arms."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": MANUAL_PREFIX + manual_text},
        {"role": "user", "content": job_text},
    ]


def build_body(model, messages):
    """Exactly the spec's request body keys. Nothing else."""
    return {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
    }


def prompt_hash(messages):
    return hashlib.sha256(
        json.dumps(messages, sort_keys=True).encode("utf-8")
    ).hexdigest()


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


# ---------------------------------------------------------------- freeze check (PLAN.md 7)


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def print_hashes(folder=HERE):
    """Block lines `<sha256>  <path>` for the files listed in PLAN.md 7."""
    return [
        f"{file_sha256(os.path.normpath(os.path.join(folder, rel)))}  {rel}"
        for rel in FROZEN_FILES
    ]


def parse_freeze_block(plan_text):
    """Parse the ```text block under "## 7." in PLAN.md into
    [(sha256, path), ...]. Empty block -> []."""
    lines = plan_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## 7."):
            start = i
            break
    if start is None:
        return []
    fence = None
    for i in range(start, len(lines)):
        if lines[i].strip() in ("```text", "```"):
            fence = i
            break
    if fence is None:
        return []
    entries = []
    for i in range(fence + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            break
        if not stripped:
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+(.+?)\s*$", stripped)
        if m:
            entries.append((m.group(1).lower(), m.group(2)))
    return entries


def freeze_check(folder=HERE, plan_name="PLAN.md"):
    """Recompute the PLAN.md 7 hashes; raise FreezeError if a file is
    missing, a hash differs, a frozen file is absent from the block, or the
    block is empty (not frozen: the runner refuses)."""
    plan_path = os.path.join(folder, plan_name)
    try:
        with open(plan_path, encoding="utf-8") as f:
            plan_text = f.read()
    except OSError as e:
        raise FreezeError(f"cannot read {plan_path}: {e}")
    entries = parse_freeze_block(plan_text)
    if not entries:
        raise FreezeError(
            f"{plan_path} section 7 freeze block is empty: not frozen, "
            "refusing to run (fill it with runner.py --print-hashes "
            "and commit before the run)"
        )
    for sha, rel in entries:
        full = os.path.normpath(os.path.join(folder, rel))
        if not os.path.isfile(full):
            raise FreezeError(f"frozen file missing: {rel}")
        actual = file_sha256(full)
        if actual != sha:
            raise FreezeError(
                f"frozen file changed: {rel}\n"
                f"  PLAN.md 7: {sha}\n"
                f"  actual:    {actual}"
            )
    listed = {rel for _, rel in entries}
    for rel in FROZEN_FILES:
        if rel not in listed:
            raise FreezeError(
                f"frozen file {rel} is not listed in {plan_path} section 7"
            )
    return entries


# ---------------------------------------------------------------- sandbox execution (PLAN.md 4c)


def pgid_rss_kb(pgid):
    """Sum RSS (KiB) of all processes in process group `pgid`, via ps."""
    try:
        proc = subprocess.run(
            ["ps", "ax", "-o", "pgid,rss"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    if proc.returncode != 0:
        return 0
    total = 0
    for line in (proc.stdout or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            g, rss = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if g == pgid:
            total += rss
    return total


def kill_pgid(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass


def sandbox_params(scratch):
    """-D NAME=<path> values for sandbox.sb. The venv root, the base
    Python install it links to, and company/ are read-allowed; the
    scratch dir is read/write-allowed; run_one.py is read-allowed."""
    exe = sys.executable
    venv = os.path.dirname(os.path.dirname(os.path.abspath(exe)))
    pyhome = os.path.dirname(
        os.path.dirname(os.path.realpath(exe)))
    return {
        "VENV": venv,
        "PYHOME": pyhome,
        "COMPANY": COMPANY,
        "SCRATCH": scratch,
        "RUNONE": RUN_ONE_PY,
    }


def run_sandboxed(code, run_tmp, timeout=RUN_TIMEOUT, max_rss_mb=MAX_RSS_MB):
    """Run `code` as answer.py in a fresh scratch dir under `run_tmp`,
    inside the PLAN.md 4c sandbox. Returns a dict with the outcome flags
    (timed_out / oom / harness_error), the sandbox stdout/stderr tails, the
    parsed result.json (or None), and whether solid.brep was written."""
    # Fully resolved: sandbox subpath matching is literal, so an
    # unresolved scratch (/tmp/..., /var/...) would be denied its own
    # writes.
    scratch = os.path.realpath(tempfile.mkdtemp(prefix="ans_", dir=run_tmp))
    with open(os.path.join(scratch, "answer.py"), "w", encoding="utf-8") as f:
        f.write(code or "")
    shell_cmd = "ulimit -t 120; {} {} {}".format(
        shlex.quote(sys.executable),
        shlex.quote(RUN_ONE_PY),
        shlex.quote(scratch),
    )
    argv = [
        "env",
        "-i",
        f"HOME={scratch}",
        "PATH=/usr/bin:/bin",
        "sandbox-exec",
        "-f",
        SANDBOX_SB,
    ]
    for name, value in sandbox_params(scratch).items():
        argv += ["-D", f"{name}={value}"]
    argv += ["/bin/sh", "-c", shell_cmd]
    res = {
        "scratch": scratch,
        "timed_out": False,
        "oom": False,
        "harness_error": None,
        "returncode": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "result": None,
        "brep_path": None,
        "seconds": 0.0,
    }
    t0 = time.monotonic()
    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            cwd=scratch,
        )
    except OSError as e:
        res["harness_error"] = f"harness: could not start sandbox: {e}"
        return res
    try:
        pgid = os.getpgid(proc.pid)
    except OSError:
        pgid = proc.pid
    last_rss_check = 0.0
    while True:
        rc = proc.poll()
        now = time.monotonic()
        elapsed = now - t0
        if rc is None and elapsed - last_rss_check >= RSS_POLL:
            last_rss_check = elapsed
            try:
                rss_mb = pgid_rss_kb(pgid) / 1024.0
            except Exception:  # noqa: BLE001 -- a failed poll must not kill
                rss_mb = 0.0
            if rss_mb > max_rss_mb:
                kill_pgid(pgid)
                res["oom"] = True
                break
        if rc is not None:
            break
        if elapsed >= timeout:
            kill_pgid(pgid)
            res["timed_out"] = True
            break
        time.sleep(0.05)
    try:
        out, err = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        kill_pgid(pgid)
        try:
            out, err = proc.communicate(timeout=30)
        except Exception:  # noqa: BLE001
            out, err = "", ""
        res["timed_out"] = True
    res["returncode"] = proc.returncode
    res["seconds"] = round(time.monotonic() - t0, 3)
    res["stdout_tail"] = (out or "")[-STREAM_TAIL:]
    res["stderr_tail"] = (err or "")[-STREAM_TAIL:]
    result_path = os.path.join(scratch, "result.json")
    try:
        with open(result_path, encoding="utf-8") as f:
            loaded = json.load(f)
        res["result"] = loaded if isinstance(loaded, dict) else None
    except (OSError, ValueError):
        res["result"] = None
    brep_path = os.path.join(scratch, "solid.brep")
    if os.path.isfile(brep_path):
        res["brep_path"] = brep_path
    return res


# ---------------------------------------------------------------- scoring one answer


def import_brep_shape(brep_path):
    import cadquery as cq

    return cq.importers.importBrep(brep_path)


def score_sandboxed(job_id, code, sb, build_ref_fn, expected_for_job,
                     keep_dir=None, arm=None, sample=None):
    """Classify one extracted answer run through the sandbox. Returns
    (outcome, reason, failed_checks, measurements).

    INVALID: cut off by the token limit (handled by the caller via
    finish_reason), empty reply. Everything here is PASS or FAIL:
    timeout, memory, harness errors, answer exceptions (incl. KeelError),
    a missing `solid`, or the referee checks.
    """
    if sb.get("harness_error"):
        return ("FAIL", sb["harness_error"], ["harness"], None)
    if sb.get("timed_out"):
        return ("FAIL", "timeout in sandbox", ["timeout"], None)
    if sb.get("oom"):
        return ("FAIL", "memory", ["memory"], None)
    result = sb.get("result") or {}
    if not result.get("ok"):
        err = result.get("error") or (
            sb.get("stderr_tail") or ""
        ).strip() or f"answer failed (exit {sb.get('returncode')})"
        return ("FAIL", str(err)[-RUN_ERROR_TAIL:], [], None)
    brep_path = sb.get("brep_path")
    if not brep_path:
        return ("FAIL", "no solid.brep written by answer", [], None)
    try:
        answer = import_brep_shape(brep_path)
    except Exception as e:  # noqa: BLE001 -- a broken BREP is FAIL
        return ("FAIL", f"could not import solid.brep: {e!r}"[-RUN_ERROR_TAIL:],
                ["brep"], None)
    try:
        reference = build_ref_fn(job_id)
    except Exception as e:  # noqa: BLE001 -- broken reference is a harness bug
        return ("FAIL", f"harness: cannot build reference for {job_id}: {e!r}",
                ["harness"], None)
    try:
        passed, fails, measurements = referee.score(
            answer, reference, expected_for_job)
    except Exception as e:  # noqa: BLE001 -- a broken shape is FAIL
        return ("FAIL", f"scoring raised: {e!r}"[-RUN_ERROR_TAIL:],
                ["scoring error"], None)
    if keep_dir is not None and os.path.isfile(brep_path):
        try:
            os.makedirs(keep_dir, exist_ok=True)
            dest = os.path.join(keep_dir, f"{arm}_{job_id}_s{sample}.brep")
            shutil.copyfile(brep_path, dest)
        except OSError:
            pass
    if passed:
        return ("PASS", None, [], measurements)
    return ("FAIL", "; ".join(fails)[:RUN_ERROR_TAIL], list(fails),
            measurements)


# ---------------------------------------------------------------- one (job, arm, sample) call


def utcnow_iso():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def scrub(text, secrets):
    if not isinstance(text, str):
        return text
    for secret in secrets:
        if secret and isinstance(secret, str) and secret in text:
            text = text.replace(secret, "***")
    return text


def do_call(
    job,
    arm,
    sample,
    model,
    endpoint,
    secrets,
    manual_text,
    expected_for_job,
    build_ref_fn,
    post_fn,
    sleep_fn,
    run_tmp,
    keep_dir,
    exec_timeout=RUN_TIMEOUT,
    call_timeout=CALL_TIMEOUT,
    max_rss_mb=MAX_RSS_MB,
):
    """Run one (job, arm, sample) triple exactly once: POST, retry once
    only on a network error / HTTP 5xx/429, then run the answer in the
    sandbox and score it. Never raises for a bad answer; network/HTTP
    failure after the retry is INVALID, never FAIL."""
    messages = build_messages(job["text"], manual_text)
    body = build_body(model, messages)
    phash = prompt_hash(messages)
    start = utcnow_iso()
    t0 = time.monotonic()
    content, finish_reason, usage, reasoning_len = "", None, {}, 0
    outcome = reason = failed_checks = measurements = code = None
    sandbox_info = {}
    try:
        data = post_with_retry(post_fn, endpoint, body, call_timeout, sleep_fn)
        content, finish_reason, usage, reasoning_len = parse_response(data)
        if finish_reason == "length":
            outcome = "INVALID"
            reason = "cut off by the token limit"
            code = ""
        elif not content or not content.strip():
            outcome = "INVALID"
            reason = "empty reply"
            code = ""
        else:
            code = extract_code(content)
            if not code or not code.strip():
                outcome = "INVALID"
                reason = "empty reply"
            else:
                sb = run_sandboxed(code, run_tmp, exec_timeout, max_rss_mb)
                sandbox_info = {
                    "stdout_tail": sb.get("stdout_tail", ""),
                    "stderr_tail": sb.get("stderr_tail", ""),
                    "returncode": sb.get("returncode"),
                    "timed_out": sb.get("timed_out"),
                    "oom": sb.get("oom"),
                    "sandbox_seconds": sb.get("seconds"),
                }
                outcome, reason, failed_checks, measurements = score_sandboxed(
                    job["id"], code, sb, build_ref_fn, expected_for_job,
                    keep_dir, arm, sample)
    except Exception as e:  # noqa: BLE001 -- failed call => INVALID record
        outcome = "INVALID"
        reason = f"{type(e).__name__}: {e}"
        failed_checks = []
        measurements = None
        code = ""
    seconds = time.monotonic() - t0
    end = utcnow_iso()
    content = scrub(content, secrets)
    code = scrub(code, secrets) or ""
    reason = scrub(reason, secrets)
    if reason and len(reason) > RUN_ERROR_TAIL:
        reason = reason[-RUN_ERROR_TAIL:]
    try:
        prompt_tokens = float((usage or {}).get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt_tokens = 0.0
    try:
        completion_tokens = float((usage or {}).get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion_tokens = 0.0
    return {
        "job": job["id"],
        "arm": arm,
        "sample": sample,
        "model": model,
        "start": start,
        "end": end,
        "seconds": round(seconds, 3),
        "prompt_hash": phash,
        "finish_reason": finish_reason,
        "usage": usage,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "content": content,
        "reasoning_len": reasoning_len,
        "code": code,
        "extracted_code": code,
        "sandbox": sandbox_info,
        "outcome": outcome,
        "reason": reason,
        "run_error": reason,
        "failed_checks": failed_checks or [],
        "fails": failed_checks or [],
        "measurements": measurements,
        "cost_usd": cost_c_of_usage(usage) if arm == "C" else 0.0,
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


def modal_cost_of_elapsed(elapsed_s):
    return max(0.0, elapsed_s) * GPU_DOLLARS_PER_HOUR / 3600.0


def not_run_record(job, arm, sample, model, cap, cap_value):
    """A calls.jsonl record for a slot never sent because a PLAN.md 5 cap
    stopped the arm. Outcome NOT_RUN: never FAIL, never INVALID, and
    never counted as an answer. `cap` is one of "modal-budget",
    "baseten-budget" or "glimmer-time" (the same names as the summary's
    `caps.stopped_by`)."""
    return {
        "job": job["id"],
        "arm": arm,
        "sample": sample,
        "model": model,
        "start": None,
        "end": None,
        "seconds": 0.0,
        "prompt_hash": None,
        "finish_reason": None,
        "usage": {},
        "prompt_tokens": 0.0,
        "completion_tokens": 0.0,
        "content": "",
        "reasoning_len": 0,
        "code": "",
        "extracted_code": "",
        "sandbox": {},
        "outcome": "NOT_RUN",
        "reason": (
            f"NOT RUN: {cap} cap ({cap_value}) stopped arm {arm}; "
            "call never sent"
        ),
        "run_error": None,
        "failed_checks": [],
        "fails": [],
        "measurements": None,
        "cost_usd": 0.0,
        "stopped_by": cap,
    }


# ---------------------------------------------------------------- suite


def run_suite(
    jobs,
    expected,
    manual_text,
    out_dir,
    arm_cfgs,
    key_map=None,
    budget=DEFAULT_BUDGET,
    post_fn=None,
    sleep_fn=time.sleep,
    max_workers=MAX_WORKERS,
    exec_timeout=RUN_TIMEOUT,
    call_timeout=CALL_TIMEOUT,
    arms=ARMS,
    budget_c=DEFAULT_BUDGET_C,
    gpu_start=None,
    max_minutes=DEFAULT_MAX_MINUTES,
    k=DEFAULT_K,
    max_rss_mb=MAX_RSS_MB,
    mode="main",
    build_ref_fn=None,
):
    """Call every (job, arm, sample) triple once with up to `max_workers`
    concurrent calls, scheduled sample-major (PLAN.md 5): for sample in
    1..k, for arm in `arms`, for job in `jobs` (fixed exam order), so a
    cap hit leaves complete samples behind it.
    Before every new call, check the PLAN.md 5 caps. The Modal estimate
    (wall-clock since `gpu_start` x $2.50/h) at `budget` and the Glimmer
    wall clock at `max_minutes` stop only new arm-B calls; the Baseten
    token total at `budget_c` stops only new arm-C calls. Arm C keeps
    running until its own Baseten cap even after arm B stopped. Calls in
    flight finish and are logged. Slots never sent are logged with
    outcome NOT_RUN (PLAN.md 5: never FAIL, never INVALID).
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
    if build_ref_fn is None:
        build_ref_fn = default_build_ref_fn()
    os.makedirs(out_dir, exist_ok=True)
    run_tmp = os.path.join(out_dir, "tmp")
    os.makedirs(run_tmp, exist_ok=True)
    keep_dir = os.path.join(out_dir, "breps")
    # PLAN.md 5, sample-major: all jobs of sample 1 (both arms), then
    # sample 2, then sample 3; jobs in the fixed exam order.
    pairs = [
        (job, arm, sample)
        for sample in range(1, k + 1)
        for arm in arms
        for job in jobs
    ]
    try:
        t0_modal = float(gpu_start) if gpu_start is not None else time.time()
    except (TypeError, ValueError):
        t0_modal = time.time()

    def modal_usd_now():
        return modal_cost_of_elapsed(time.time() - t0_modal)

    def baseten_usd_now(c_usages):
        return sum(cost_c_of_usage(u) for u in c_usages)

    records = [None] * len(pairs)
    t_start = time.monotonic()
    c_usages = []
    modal_stopped = False
    baseten_stopped = False
    time_stopped = False
    next_i = 0
    in_flight = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        while next_i < len(pairs) or in_flight:
            while next_i < len(pairs) and len(in_flight) < max_workers:
                job, arm, sample = pairs[next_i]
                # PLAN.md 5: the Modal cap and the Glimmer wall clock stop
                # only arm-B calls; arm C keeps running until its own
                # Baseten cap. A skipped slot is logged as NOT_RUN.
                if arm == "B" and modal_usd_now() >= budget:
                    modal_stopped = True
                    records[next_i] = not_run_record(
                        job, arm, sample, arm_cfgs[arm]["model"],
                        "modal-budget", budget)
                    next_i += 1
                    continue
                if arm == "B" and (time.time() - t0_modal) / 60.0 >= max_minutes:
                    time_stopped = True
                    records[next_i] = not_run_record(
                        job, arm, sample, arm_cfgs[arm]["model"],
                        "glimmer-time", max_minutes)
                    next_i += 1
                    continue
                if arm == "C" and baseten_usd_now(c_usages) >= budget_c:
                    baseten_stopped = True
                    records[next_i] = not_run_record(
                        job, arm, sample, arm_cfgs[arm]["model"],
                        "baseten-budget", budget_c)
                    next_i += 1
                    continue
                cfg = arm_cfgs[arm]
                fut = pool.submit(
                    do_call,
                    job,
                    arm,
                    sample,
                    cfg["model"],
                    cfg["endpoint"],
                    secrets,
                    manual_text,
                    expected.get(job["id"]),
                    build_ref_fn,
                    post_fn,
                    sleep_fn,
                    run_tmp,
                    keep_dir,
                    exec_timeout,
                    call_timeout,
                    max_rss_mb,
                )
                in_flight[fut] = next_i
                next_i += 1
            if not in_flight:
                break
            done, _ = concurrent.futures.wait(
                in_flight, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for fut in done:
                idx = in_flight.pop(fut)
                job, arm, sample = pairs[idx]
                try:
                    rec = fut.result()
                except Exception as e:  # noqa: BLE001 -- never lose a slot
                    rec = {
                        "job": job["id"],
                        "arm": arm,
                        "sample": sample,
                        "model": arm_cfgs[arm]["model"],
                        "outcome": "INVALID",
                        "reason": scrub(
                            f"runner error: {e!r}", secrets
                        )[-RUN_ERROR_TAIL:],
                        "failed_checks": [],
                        "fails": [],
                        "measurements": None,
                    }
                    rec["run_error"] = rec["reason"]
                records[idx] = rec
                if arm == "C" and isinstance(rec.get("usage"), dict):
                    c_usages.append(rec["usage"])
    elapsed = time.monotonic() - t_start
    modal_usd = modal_usd_now()
    baseten_usd = baseten_usd_now(c_usages)
    # Every slot has a record now: sent answers plus NOT_RUN slots.
    sent = [r for r in records if r is not None]
    skipped = sum(1 for r in sent if r.get("outcome") == "NOT_RUN")
    n_calls = len(sent) - skipped
    stopped_by = []
    if modal_stopped:
        stopped_by.append("modal-budget")
    if baseten_stopped:
        stopped_by.append("baseten-budget")
    if time_stopped:
        stopped_by.append("glimmer-time")
    summary = build_summary(
        sent,
        job_ids=[j["id"] for j in jobs],
        arms=list(arms),
        k=k,
        mode=mode,
        modal_usd=modal_usd,
        baseten_usd=baseten_usd,
        budget=budget,
        budget_c=budget_c,
        max_minutes=max_minutes,
        stopped_by=stopped_by,
        skipped=skipped,
        elapsed_s=elapsed,
        gpu_start=gpu_start,
        n_calls=n_calls,
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


def default_build_ref_fn():
    from jobs import JOBS, build

    def _build(job_id):
        return build(job_id, JOBS[job_id]["ref"])

    return _build


# ---------------------------------------------------------------- scores, bootstrap, McNemar, decision


SCORED_OUTCOMES = ("PASS", "FAIL", "INVALID")


def tally(records, job_ids, arms, k):
    """Per-arm counts plus per-job passes over scored answers only
    (PLAN.md 5). A sample is complete for an arm when every job has an
    answer with outcome PASS, FAIL or INVALID; anything else (NOT_RUN,
    missing) makes it incomplete. Only complete samples are scored; an
    incomplete sample is reported (pass@1, calls.jsonl) but not scored.
    NOT_RUN slots are counted separately and are never PASS, FAIL or
    INVALID. Returns (per_arm, per_job); per_job counts passes in
    complete samples only."""
    by_slot = {}
    for r in records:
        by_slot[(r.get("job"), r.get("arm"), r.get("sample"))] = r.get(
            "outcome")
    complete = {}
    for arm in arms:
        complete[arm] = [
            s for s in range(1, k + 1)
            if all(
                by_slot.get((jid, arm, s)) in SCORED_OUTCOMES
                for jid in job_ids
            )
        ]
    per_job = {}
    for jid in job_ids:
        per_job[jid] = {}
        for arm in arms:
            per_job[jid][arm] = sum(
                1
                for s in complete[arm]
                if by_slot.get((jid, arm, s)) == "PASS"
            )
    per_arm = {}
    for arm in arms:
        arm_recs = [r for r in records if r.get("arm") == arm]
        comp_set = set(complete[arm])
        scored = [
            r for r in arm_recs
            if r.get("sample") in comp_set
            and r.get("outcome") in SCORED_OUTCOMES
        ]
        n_pass = sum(1 for r in scored if r.get("outcome") == "PASS")
        n_fail = sum(1 for r in scored if r.get("outcome") == "FAIL")
        n_inv = sum(1 for r in scored if r.get("outcome") == "INVALID")
        n_not_run = sum(
            1 for r in arm_recs if r.get("outcome") == "NOT_RUN")
        n_comp = len(complete[arm])
        # PLAN.md 4 score, restricted to complete samples (PLAN.md 5):
        # mean over jobs of passes/n_complete, in percent.
        score = (
            sum(per_job[jid][arm] / n_comp for jid in job_ids)
            / len(job_ids)
            if job_ids and n_comp
            else None
        )
        per_arm[arm] = {
            "n_sent": sum(
                1 for r in arm_recs
                if r.get("outcome") in SCORED_OUTCOMES),
            "PASS": n_pass,
            "FAIL": n_fail,
            "INVALID": n_inv,
            "NOT_RUN": n_not_run,
            "complete_samples": complete[arm],
            "n_complete_samples": n_comp,
            "score_pct": None if score is None else round(score * 100, 1),
            "score_frac": score,
            # PLAN.md 5: the INVALID gate counts over scored answers.
            "invalid_rate": (n_inv / len(scored)) if scored else None,
            "stopped_by": None,
        }
    return per_arm, per_job


def pass_at_1(records, job_ids, arms, k):
    """Pass rate (%) of each sample index separately, per arm."""
    by_slot = {}
    for r in records:
        by_slot[(r.get("job"), r.get("arm"), r.get("sample"))] = r.get(
            "outcome")
    table = {}
    for arm in arms:
        table[arm] = {}
        for s in range(1, k + 1):
            if not job_ids:
                table[arm][s] = None
                continue
            rate = sum(
                1 for jid in job_ids if by_slot.get((jid, arm, s)) == "PASS"
            ) / len(job_ids)
            table[arm][s] = round(rate * 100, 1)
    return table


def bootstrap_ci(diffs, resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """Paired bootstrap 95% CI of the mean of `diffs` (fractions).
    Resamples jobs with replacement; deterministic for a fixed seed.
    Returns (lo, hi) in percentage points."""
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        means.append(
            sum(diffs[rng.randrange(n)] for _ in range(n)) / n
        )
    means.sort()
    lo = means[int(0.025 * resamples)] * 100.0
    hi = means[int(0.975 * resamples)] * 100.0
    return (round(lo, 1), round(hi, 1))


def mcnemar_p_value(b, c):
    """Two-sided exact binomial McNemar p-value for the off-diagonal
    counts b (C pass, B not) and c (B pass, C not)."""
    from math import comb

    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, round(2 * tail, 4))


def compute_mcnemar(records, job_ids):
    """McNemar on sample 1 (informational): paired pass/not-pass outcomes
    for jobs with a sample-1 answer in both arms B and C."""
    outcome = {}
    for r in records:
        if r.get("sample") == 1:
            outcome[(r.get("job"), r.get("arm"))] = r.get("outcome")
    b = c = both = neither = n = 0
    for jid in job_ids:
        ob, oc = outcome.get((jid, "B")), outcome.get((jid, "C"))
        if ob is None or oc is None:
            continue
        n += 1
        pb, pc = ob == "PASS", oc == "PASS"
        if pb and pc:
            both += 1
        elif not pb and not pc:
            neither += 1
        elif pc and not pb:
            b += 1
        else:
            c += 1
    return {
        "n_paired": n,
        "b_c_pass_b_fail": b,
        "c_b_pass_c_fail": c,
        "both_pass": both,
        "neither_pass": neither,
        "p_value": mcnemar_p_value(b, c),
    }


def compute_decision(rate_b, rate_c, invalid_rates):
    """PLAN.md 4 decision rules in order; first match wins. Rates are
    fractions compared in whole points (round(rate*100)).
    Returns (decision, run_valid)."""
    run_valid = all(
        (r is None or r <= 0.05) for r in (invalid_rates or {}).values()
    )
    if not run_valid:
        return (
            "RUN INVALID: INVALID answers exceed 5% in an arm; "
            "fix the cause and rerun that arm (no decision from this run)",
            False,
        )
    if rate_b is None or rate_c is None:
        return ("GREY: too few scored answers for a decision", True)
    b_pts = round(rate_b * 100)
    c_pts = round(rate_c * 100)
    gap = c_pts - b_pts
    if c_pts < 30:
        return (
            f"STOP: arm C scores {c_pts}% (< 30%): the teacher cannot use "
            "an unseen tool from its manual",
            True,
        )
    if b_pts >= 80:
        return (
            f"NO ROOM: arm B scores {b_pts}% (>= 80%): Glimmer + manual "
            "is already good",
            True,
        )
    if gap >= 25 and b_pts <= 70:
        return (
            f"GO: C - B = {gap} points (>= 25) and B = {b_pts}% (<= 70%): "
            "build the factory",
            True,
        )
    return ("GREY: no rule fired; report to the user, who decides", True)


def build_summary(sent, job_ids, arms, k, mode, modal_usd, baseten_usd,
                  budget, budget_c, max_minutes, stopped_by, skipped,
                  elapsed_s, gpu_start=None, n_calls=None):
    per_arm, per_job = tally(sent, job_ids, arms, k)
    # Which cap stopped each arm: the cap named by its first NOT_RUN
    # record in call order (None when the arm ran everything).
    for r in sent:
        if r.get("outcome") == "NOT_RUN" and r.get("stopped_by"):
            arm = r.get("arm")
            if arm in per_arm and per_arm[arm]["stopped_by"] is None:
                per_arm[arm]["stopped_by"] = r["stopped_by"]
    pat1 = pass_at_1(sent, job_ids, arms, k)
    diffs = []
    if ("B" in arms and "C" in arms
            and per_arm["B"]["n_complete_samples"]
            and per_arm["C"]["n_complete_samples"]):
        n_b = per_arm["B"]["n_complete_samples"]
        n_c = per_arm["C"]["n_complete_samples"]
        diffs = [
            per_job[jid]["C"] / n_c - per_job[jid]["B"] / n_b
            for jid in job_ids
        ] if k else []
    if diffs:
        ci_lo, ci_hi = bootstrap_ci(diffs)
        observed = round(sum(diffs) / len(diffs) * 100, 1)
    else:  # single-arm run (e.g. pilot), or an arm with no complete
        # sample: no C-B difference exists
        ci_lo, ci_hi, observed = None, None, None
    mcnemar = compute_mcnemar(sent, job_ids)
    # PLAN.md 5: the INVALID gate (rule 0) counts over scored answers;
    # per_arm invalid_rate is already scored-only (see tally).
    invalid_rates = {
        arm: per_arm[arm]["invalid_rate"] for arm in arms
        if per_arm[arm]["n_sent"]
    }
    # PLAN.md 5: if either arm has no complete sample, the run is
    # INCOMPLETE and no decision is made (checked before rule 0).
    incomplete = [a for a in arms if not per_arm[a]["complete_samples"]]
    if incomplete:
        decision = (
            "INCOMPLETE: arm(s) " + ",".join(incomplete)
            + " have no complete sample; no decision from this run"
        )
        run_valid = False
    elif "B" in per_arm and "C" in per_arm:
        decision, run_valid = compute_decision(
            per_arm["B"]["score_frac"],
            per_arm["C"]["score_frac"],
            invalid_rates,
        )
    else:
        run_valid = all(
            (r is None or r <= 0.05) for r in invalid_rates.values()
        )
        decision = "GREY: pilot run, no decision (see PLAN.md 4d)"
    pilot_ok = None
    if mode == "pilot":
        pilot_ok = bool(sent) and all(
            r.get("outcome") != "INVALID"
            and "harness" not in (r.get("reason") or "")
            for r in sent
        )
    return {
        "mode": mode,
        "arms": per_arm,
        "pass_at_1_pct": pat1,
        "k": k,
        "per_job_passes": per_job,
        "bootstrap_c_minus_b": {
            "observed_points": observed,
            "ci95_points": [ci_lo, ci_hi],
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
        },
        "mcnemar_sample1": mcnemar,
        "decision": decision,
        "run_valid": run_valid,
        "pilot_ok": pilot_ok,
        "n_calls": len(sent) - skipped if n_calls is None else n_calls,
        "skipped": skipped,
        "costs": {
            "modal_usd": round(modal_usd, 4),
            "baseten_usd": round(baseten_usd, 4),
            "total_usd": round(modal_usd + baseten_usd, 4),
            "note": "Modal: wall-clock since deploy start x $2.50/h "
            "(incl. cold start). Baseten: usage tokens x $1.25/M in, "
            "$4.25/M out.",
        },
        "caps": {
            "budget_modal": budget,
            "budget_baseten": budget_c,
            "max_minutes_glimmer": max_minutes,
            "stopped_by": stopped_by,
            "cap_hit": bool(stopped_by),
        },
        "elapsed_seconds": round(elapsed_s, 3),
        "gpu_start": gpu_start,
    }


def _pct(rate):
    return "n/a" if rate is None else f"{100 * rate:.1f}%"


def build_report(summary):
    arms = [a for a in summary["arms"]]
    lines = ["# Keel v2 baseline report", ""]
    lines.append(f"Mode: {summary['mode']}")
    lines.append(f"Decision (PLAN.md 4): **{summary['decision']}**")
    lines.append(f"Run valid: {summary['run_valid']}")
    if summary.get("pilot_ok") is not None:
        lines.append(f"Pilot passed: {summary['pilot_ok']}")
    caps = summary["caps"]
    lines.append(
        f"Calls: {summary['n_calls']}  "
        f"Skipped by caps: {summary['skipped']}  "
        f"(modal budget ${caps['budget_modal']}, "
        f"baseten budget ${caps['budget_baseten']}, "
        f"glimmer limit {caps['max_minutes_glimmer']} min; "
        f"stopped by: {', '.join(caps['stopped_by']) or 'none'})"
    )
    lines.append("")
    lines.append("## Cost estimate")
    lines.append(f"- Modal (Glimmer arm): ${summary['costs']['modal_usd']:.4f}")
    lines.append(f"- Baseten (arm C): ${summary['costs']['baseten_usd']:.4f}")
    lines.append(f"- Total: ${summary['costs']['total_usd']:.4f}")
    lines.append(
        "Modal estimate covers wall-clock since deploy start (incl. cold "
        "start); confirm with `modal billing summary`."
    )
    lines.append("")
    lines.append("## Per arm (score = mean pass rate over complete "
                 "samples %, PLAN.md 4/5)")
    lines.append("| Arm | Score % | complete samples | PASS | FAIL | "
                 "INVALID | NOT RUN | INVALID rate | stopped by |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for arm in arms:
        s = summary["arms"][arm]
        score = "n/a" if s["score_pct"] is None else f"{s['score_pct']:.1f}%"
        comp = ",".join(str(x) for x in s.get("complete_samples", []))
        lines.append(
            f"| {arm} | {score} | {comp or 'none'} | {s['PASS']} | "
            f"{s['FAIL']} | {s['INVALID']} | {s.get('NOT_RUN', 0)} | "
            f"{_pct(s['invalid_rate'])} | {s.get('stopped_by') or 'none'} |"
        )
    partial = {
        arm: [s for s in range(1, summary["k"] + 1)
              if s not in set(summary["arms"][arm].get(
                  "complete_samples", []))]
        for arm in arms
    }
    if any(partial.values()):
        lines.append("")
        lines.append("Incomplete samples (reported, not scored): "
                     + "; ".join(
                         f"{arm}: {','.join(str(x) for x in partial[arm])}"
                         for arm in arms if partial[arm]))
    lines.append("")
    lines.append("## pass@1 per sample (%)")
    lines.append("| Arm | " + " | ".join(
        f"sample {s}" for s in range(1, summary["k"] + 1)) + " |")
    lines.append("|---|" + "|".join(["---"] * summary["k"]) + "|")
    for arm in arms:
        lines.append("| " + arm + " | " + " | ".join(
            f"{summary['pass_at_1_pct'][arm][s]:.1f}%"
            for s in range(1, summary["k"] + 1)) + " |")
    lines.append("")
    lines.append("## Per-job passes in complete samples "
                 "(passes/scored samples)")
    lines.append("| Job | " + " | ".join(arms) + " |")
    lines.append("|---|" + "|".join(["---"] * len(arms)) + "|")
    for job in sorted(summary["per_job_passes"]):
        lines.append(
            "| " + job + " | "
            + " | ".join(
                f"{summary['per_job_passes'][job][a]}/"
                f"{summary['arms'][a].get('n_complete_samples', 0)}"
                for a in arms)
            + " |"
        )
    lines.append("")
    bs = summary["bootstrap_c_minus_b"]
    lines.append("## C − B (paired bootstrap over jobs, "
                 f"{bs['resamples']} resamples, seed {bs['seed']})")
    if bs["observed_points"] is None:
        lines.append("- n/a (needs both arms B and C)")
    else:
        lines.append(f"- Observed C − B: {bs['observed_points']:.1f} points")
        lines.append(
            f"- 95% CI: [{bs['ci95_points'][0]:.1f}, "
            f"{bs['ci95_points'][1]:.1f}]")
    mc = summary["mcnemar_sample1"]
    lines.append("")
    lines.append("## McNemar on sample 1 (informational)")
    lines.append(
        f"- Paired jobs: {mc['n_paired']}; C-only passes: "
        f"{mc['b_c_pass_b_fail']}; B-only passes: {mc['c_b_pass_c_fail']}; "
        f"both pass: {mc['both_pass']}; neither: {mc['neither_pass']}")
    lines.append(f"- Exact two-sided p-value: {mc['p_value']}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI


def load_inputs(folder=HERE):
    from jobs import JOBS  # noqa: E402  (frozen file; imported, not modified)

    with open(os.path.join(folder, "expected.json"), encoding="utf-8") as f:
        expected = json.load(f)
    company_manual = os.path.normpath(
        os.path.join(folder, "..", "..", "company", "manual.md"))
    with open(company_manual, encoding="utf-8") as f:
        manual_text = f.read()
    return JOBS, expected, manual_text


def build_parser():
    parser = argparse.ArgumentParser(description="Keel v2 baseline runner.")
    parser.add_argument("--mode", choices=("pilot", "main"), default=None)
    parser.add_argument("--arms", default=",".join(DEFAULT_ARMS),
                        help="comma list of arms (default B,C)")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--out", default=None)
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    parser.add_argument("--budget-c", type=float, default=DEFAULT_BUDGET_C)
    parser.add_argument("--max-minutes", type=float,
                        default=DEFAULT_MAX_MINUTES)
    parser.add_argument("--gpu-start", type=float, default=None)
    parser.add_argument("--parallel", type=int, default=MAX_WORKERS)
    parser.add_argument("--timeout", type=float, default=RUN_TIMEOUT)
    parser.add_argument("--max-rss-mb", type=float, default=MAX_RSS_MB)
    parser.add_argument("--print-hashes", action="store_true")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.print_hashes:
        for line in print_hashes():
            print(line)
        return 0
    if args.mode is None:
        parser.error("--mode pilot|main is required")
    if args.out is None:
        parser.error("--out <dir> is required")
    try:
        freeze_check()
    except FreezeError as e:
        print(f"FREEZE CHECK FAILED: {e}", file=sys.stderr)
        return 3
    if args.mode == "pilot":
        if args.arms != "C" or args.k != 1:
            print("pilot mode: using jobs M1,M7,H9, arm C, k=1 (PLAN.md 4d)")
        arms = ("C",)
        k = 1
    else:
        try:
            arms = parse_arms(args.arms)
        except ValueError as e:
            parser.error(str(e))
        k = args.k
        if k < 1:
            parser.error("--k must be >= 1")

    glimmer_url = os.environ.get("GLIMMER_URL", "")
    glimmer_key = os.environ.get("GLIMMER_KEY", "")
    baseten_key = os.environ.get("BASETEN_KEY", "")
    need = []
    if "B" in arms:
        need += [("GLIMMER_URL", glimmer_url), ("GLIMMER_KEY", glimmer_key)]
    if "C" in arms:
        need += [("BASETEN_KEY", baseten_key)]
    missing = [name for name, val in need if not val]
    if missing:
        parser.error("missing environment variables: " + ", ".join(missing))

    JOBS, expected, manual_text = load_inputs()
    if args.mode == "pilot":
        job_ids = list(PILOT_JOBS)
    else:
        job_ids = list(JOBS)
    jobs = [{"id": jid, "text": JOBS[jid]["text"]} for jid in job_ids]

    arm_cfgs = {}
    key_map = {}
    for arm in arms:
        if arm == "C":
            arm_cfgs[arm] = {"endpoint": BASETEN_URL, "model": SPARK_MODEL}
            key_map[arm] = baseten_key
        else:
            arm_cfgs[arm] = {
                "endpoint": arm_endpoint(arm, glimmer_url),
                "model": arm_model(arm),
            }
            key_map[arm] = glimmer_key
    t0 = time.time()
    run_suite(
        jobs, expected, manual_text, args.out, arm_cfgs, key_map,
        args.budget, budget_c=args.budget_c, gpu_start=args.gpu_start,
        max_minutes=args.max_minutes, k=k, arms=arms,
        max_workers=args.parallel, exec_timeout=args.timeout,
        max_rss_mb=args.max_rss_mb, mode=args.mode,
    )
    print(f"done in {time.time() - t0:.1f}s: {args.out}/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
