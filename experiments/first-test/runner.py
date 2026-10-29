#!/usr/bin/env python3
"""First-test runner: send each job to each contestant model, run the returned
CadQuery code, score it with checks.py, and log everything.

Built to RUNNER_SPEC.md. Uses only the standard library for HTTP
(urllib.request) plus cadquery. Never prints, logs or writes an API key.

CLI: runner.py --jobs dry|main --out <dir> [--budget 5.0] [--budget-c 3.0] [--gpu-start <unix seconds>] [--arms A,B,C] [--workers N] [--k K] [--sandbox PROFILE]
"""

import argparse
import concurrent.futures
import datetime
import http.client
import json
import os
import re
import shlex
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

MAX_TOKENS = 16000
TEMPERATURE = 1.0
TOP_P = 0.95
TOP_K = 64
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
VALID_ARMS = ("A", "B", "C", "BR", "B2", "BX")
GLIMMER_ARMS = ("A", "B", "BR", "B2", "BX")
DEFAULT_ARMS = ("A", "B", "C")
HINT_PATH = os.path.join(os.path.dirname(HERE), "b2-hint", "hint.txt")
RUN_ONE_CQ = os.path.join(os.path.dirname(HERE), "b2-hint", "run_one_cq.py")
EXAMPLES_PATH = os.path.join(
    os.path.dirname(HERE), "bmax", "examples.py")
_hint_cache = {}

# Sandbox for model answers (experiments/b2-hint/SANDBOX_SPEC.DRAFT.md).
SANDBOX_CPU_LIMIT = 60        # `ulimit -t` inside the sandbox, seconds
SANDBOX_MAX_RSS_MB = 4096   # sandbox memory kill threshold, MB (4 GB)
SANDBOX_RSS_POLL = 0.5      # RSS watchdog interval, seconds

# B-max arm (experiments/bmax/BMAX_SPEC.md, FIX_SPEC.md item 5).
BX_MAX_CALLS = 3
BX_ERROR_HEAD = 2000        # chars of run error sent back to the model
BX_EXAMPLES_HEADER = "\n\nSolved examples (same style as your job):\n\n"
BX_REASONING = "xhigh"      # BX reasoning_strength (Glimmer default is high)


def load_hint_text(path=None):
    """Read the B2 hint file (UTF-8, stripped)."""
    with open(path or HINT_PATH, encoding="utf-8") as f:
        return f.read().strip()


def get_hint_text():
    if "hint" not in _hint_cache:
        _hint_cache["hint"] = load_hint_text()
    return _hint_cache["hint"]


def parse_arms(value):
    """Parse a comma-separated --arms value into a tuple of valid arms."""
    if isinstance(value, (tuple, list)):
        parts = list(value)
    else:
        parts = str(value).split(",")
    arms = tuple(p.strip() for p in parts if p.strip())
    if not arms:
        raise ValueError(
            "no arms requested (expected comma list of A,B,C,BR,B2,BX)")
    for arm in arms:
        if arm not in VALID_ARMS:
            raise ValueError(
                f"unknown arm {arm!r} (expected comma list of A,B,C,BR,B2,BX)"
            )
    return arms


def system_prompt_for_arm(arm, hint_text=None):
    if arm in ("B2", "BX"):
        hint = hint_text if hint_text is not None else get_hint_text()
        return SYSTEM_PROMPT + " " + hint
    return SYSTEM_PROMPT


def load_examples(path=None):
    """Read the B-max solved examples (list of dicts with text/code)."""
    import runpy

    data = runpy.run_path(path or EXAMPLES_PATH)
    return data["EXAMPLES"]


def get_examples():
    if "examples" not in _hint_cache:
        _hint_cache["examples"] = load_examples()
    return _hint_cache["examples"]


def format_bx_examples(examples=None):
    """The solved-examples block inserted between the manual and the job."""
    parts = [BX_EXAMPLES_HEADER]
    for ex in examples if examples is not None else get_examples():
        parts.append(
            "Job: " + ex["text"] + "\nAnswer:\n```python\n"
            + ex["code"] + "\n```\n\n"
        )
    return "".join(parts)

# ---------------------------------------------------------------- arms/messages


def arm_model(arm):
    if arm in GLIMMER_ARMS:
        return GLIMMER_MODEL
    if arm == "C":
        return SPARK_MODEL
    raise ValueError(f"unknown arm {arm!r}")


def arm_endpoint(arm, glimmer_url):
    if arm in GLIMMER_ARMS:
        return glimmer_url.rstrip("/") + "/v1/chat/completions"
    if arm == "C":
        return BASETEN_URL
    raise ValueError(f"unknown arm {arm!r}")


def arm_uses_manual(arm):
    return arm in ("B", "C", "BR", "B2", "BX")


def build_messages(arm, job_text, manual_text, hint_text=None, examples=None):
    """Exactly the spec's messages: system + job text (arm A), or system +
    manual-as-first-user-message + job-text-as-second-user-message (B, C, BR,
    B2). Arm BR is identical to B; arm B2 appends the hint text to the system
    message (SYSTEM text + one space + hint). Arm BX is B2's system message
    with the solved-examples block inserted between the manual message and
    the job-text message."""
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    messages = [
        {"role": "system", "content": system_prompt_for_arm(arm, hint_text)},
    ]
    if arm_uses_manual(arm):
        messages.append({"role": "user", "content": MANUAL_PREFIX + manual_text})
    if arm == "BX":
        messages.append({"role": "user", "content": format_bx_examples(examples)})
    messages.append({"role": "user", "content": job_text})
    return messages


def build_body(model, messages, reasoning_strength=None):
    """Exactly the spec's request body keys. Nothing else, except arm BX
    which also carries chat_template_kwargs.reasoning_strength."""
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "top_k": TOP_K,
    }
    if reasoning_strength is not None:
        body["chat_template_kwargs"] = {"reasoning_strength": reasoning_strength}
    return body


def build_bx_body(model, messages):
    """Arm BX request body: arm B's body plus reasoning_strength xhigh."""
    return build_body(model, messages, reasoning_strength=BX_REASONING)


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
    """-D NAME=<path> values for sandbox_cq.sb: the venv root, the base
    Python install it links to, the answer's scratch dir, and run_one_cq.py."""
    exe = sys.executable
    venv = os.path.dirname(os.path.dirname(os.path.abspath(exe)))
    pyhome = os.path.dirname(os.path.dirname(os.path.realpath(exe)))
    return {
        "VENV": venv,
        "PYHOME": pyhome,
        "SCRATCH": scratch,
        "RUNONE": os.path.realpath(RUN_ONE_CQ),
    }


def parse_measure_line(stdout):
    """Parse run_one_cq.py's `MEASURE {...}` line. Returns the dict or None."""
    for line in (stdout or "").splitlines():
        line = line.strip()
        if line.startswith("MEASURE "):
            try:
                data = json.loads(line[len("MEASURE "):])
            except ValueError:
                return None
            return data if isinstance(data, dict) else None
    return None


def run_code_sandboxed(code, run_tmp, profile, python=None,
                        timeout=RUN_TIMEOUT,
                        max_rss_mb=SANDBOX_MAX_RSS_MB):
    """Run `code` as answer.py in a fresh scratch dir under `run_tmp`,
    inside the sandbox profile. Imports <scratch>/answer.step here, exactly
    as the unsandboxed path. Returns (shape_or_None, error_or_None,
    measure_or_None). Sandbox denials are plain run failures (FAIL, never
    INVALID); the scratch dir is kept for the replay viewer."""
    import cadquery as cq

    python = python or sys.executable
    scratch = os.path.realpath(tempfile.mkdtemp(prefix="ans_", dir=run_tmp))
    with open(os.path.join(scratch, "answer.py"), "w", encoding="utf-8") as f:
        f.write(code or "")
    shell_cmd = "ulimit -t {}; {} -I {} {}".format(
        SANDBOX_CPU_LIMIT,
        shlex.quote(python),
        shlex.quote(os.path.realpath(RUN_ONE_CQ)),
        shlex.quote(scratch),
    )
    argv = [
        "env",
        "-i",
        "HOME={}".format(scratch),
        "PATH=/usr/bin:/bin",
        "sandbox-exec",
        "-f",
        profile,
    ]
    for name, value in sandbox_params(scratch).items():
        argv += ["-D", "{}={}".format(name, value)]
    argv += ["/bin/sh", "-c", shell_cmd]
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
        return None, f"could not start answer subprocess: {e}", None
    try:
        pgid = os.getpgid(proc.pid)
    except OSError:
        pgid = proc.pid
    timed_out = False
    oom = False
    t0 = time.monotonic()
    last_rss_check = 0.0
    while True:
        rc = proc.poll()
        now = time.monotonic()
        elapsed = now - t0
        if rc is None and elapsed - last_rss_check >= SANDBOX_RSS_POLL:
            last_rss_check = elapsed
            try:
                rss_mb = pgid_rss_kb(pgid) / 1024.0
            except Exception:  # noqa: BLE001 -- a failed poll must not kill
                rss_mb = 0.0
            if rss_mb > max_rss_mb:
                kill_pgid(pgid)
                oom = True
                break
        if rc is not None:
            break
        if elapsed >= timeout:
            kill_pgid(pgid)
            timed_out = True
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
        timed_out = True
    if timed_out:
        return None, f"timeout after {timeout:g}s running answer code", None
    if oom:
        return None, (
            f"answer code failed (exit {proc.returncode}): "
            "memory limit exceeded running answer code"
        ), None
    if proc.returncode is not None and proc.returncode < 0:
        # Killed by a signal (e.g. the sandbox CPU limit): same timeout
        # string as the unsandboxed path.
        return None, f"timeout after {timeout:g}s running answer code", None
    # FIX_SPEC item 4: never trust the answer's stdout. The solid comes
    # only from the fixed path <scratch>/answer.step and the measurements
    # only from <scratch>/measure.json (realpaths must stay inside the
    # scratch dir). Decoy `.step` paths / fake MEASURE lines on stdout, or
    # atexit writers elsewhere, are ignored.
    if proc.returncode != 0:
        err = (err or "").strip() or f"exit {proc.returncode}"
        return None, f"answer code failed (exit {proc.returncode}): {err}", None
    step_path = os.path.realpath(os.path.join(scratch, "answer.step"))
    measure_path = os.path.realpath(os.path.join(scratch, "measure.json"))
    inside = scratch + os.sep
    if not step_path.startswith(inside) or not measure_path.startswith(inside):
        return None, (
            f"answer code failed (exit {proc.returncode}): "
            "answer.step escaped the scratch dir"
        ), None
    if not os.path.isfile(step_path):
        err = (err or "").strip() or f"exit {proc.returncode}"
        return None, f"answer code failed (exit {proc.returncode}): {err}", None
    measure = None
    try:
        with open(measure_path, encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            measure = loaded
    except (OSError, ValueError):
        measure = None
    try:
        shape = cq.importers.importStep(step_path)
        return shape, None, measure
    except Exception as e:  # noqa: BLE001 -- reported as FAIL, not raised
        return None, f"could not import exported STEP: {e!r}", None


def run_code(code, python=None, timeout=RUN_TIMEOUT, sandbox_profile=None,
             sandbox_dir=None):
    """Run `code` in `<python> -I -c <wrapper>` with cwd /tmp and a 60 s
    limit. The wrapper exports `result` as STEP and prints the path; the
    STEP is imported here. Returns (shape_or_None, error_or_None).

    With sandbox_profile (a sandbox_cq.sb path), the answer instead runs
    inside the sandbox (see run_code_sandboxed); without it this behaves
    exactly as before."""
    if sandbox_profile is not None:
        run_tmp = os.path.realpath(sandbox_dir) if sandbox_dir else None
        if run_tmp is None:
            run_tmp = os.path.realpath(tempfile.mkdtemp(prefix="sandbox_"))
        shape, error, _ = run_code_sandboxed(
            code, run_tmp, sandbox_profile, python=python, timeout=timeout)
        return shape, error
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


def bx_error_message(run_error):
    """Follow-up user message after a BX round that failed to build."""
    return (
        "Your code failed when it ran:\n"
        + (run_error or "code error")[:BX_ERROR_HEAD]
        + "\nFix it. Reply with the full corrected program "
        "in one Python code block."
    )


def bx_self_check_message(measure):
    """Follow-up user message after a BX round that built. Takes only the
    part's own MEASURE values (never the reference)."""
    return (
        "Your part was built. Measured: bounding box X "
        f"{measure['xmin']} to {measure['xmax']}, Y "
        f"{measure['ymin']} to {measure['ymax']}, Z "
        f"{measure['zmin']} to {measure['zmax']}; volume "
        f"{measure['volume']} mm³; {measure['solids']} solid(s). "
        "Compare this with every number in the job. If the part matches "
        "the job, reply with exactly the word DONE. Otherwise reply with "
        "the full corrected program in one Python code block."
    )


def score_content(content, finish_reason, build_ref, expected, timeout=RUN_TIMEOUT,
                  sandbox_profile=None, sandbox_dir=None):
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
    answer, run_error = run_code(
        code, timeout=timeout, sandbox_profile=sandbox_profile,
        sandbox_dir=sandbox_dir)
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


def _usage_pair(usage):
    usage = usage or {}
    try:
        prompt = int(usage.get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt = 0
    try:
        completion = int(usage.get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion = 0
    return prompt, completion


def do_bx_call(
    job,
    model,
    endpoint,
    secrets,
    manual_text,
    expected_for_job,
    post_fn,
    sleep_fn,
    exec_timeout=RUN_TIMEOUT,
    call_timeout=CALL_TIMEOUT,
    sandbox_profile=None,
    sandbox_dir=None,
    examples=None,
    hint_text=None,
):
    """Arm BX: up to BX_MAX_CALLS model calls in one conversation. Every
    program runs in the sandbox. Only a reply that contains a Python code
    block is run; a reply with no code block ends the loop whatever its
    text. After ANY build, if calls remain, the self-check follow-up (with
    the part's own measurements) is sent. A cut-off, failed call or empty
    reply after round 1 ends the loop keeping the most recent program that
    built (FAIL if none); only round 1 can make a job INVALID. Returns the
    final record with the per-round records embedded as bx_rounds
    (run_suite writes those as one calls.jsonl record per round plus the
    final record)."""
    if sandbox_profile is None:
        raise ValueError("arm BX requires --sandbox <profile>")
    run_tmp = os.path.realpath(sandbox_dir) if sandbox_dir else None
    if run_tmp is None:
        run_tmp = os.path.realpath(tempfile.mkdtemp(prefix="sandbox_"))
    messages = build_messages("BX", job["text"], manual_text, hint_text,
                              examples)
    start = utcnow_iso()
    t0 = time.monotonic()
    rounds = []
    best = None
    last_code = ""
    last_error = None
    content, finish_reason, usage, reasoning_len = "", None, {}, 0
    outcome = fails = measurements = None
    try:
        n = 0
        while n < BX_MAX_CALLS:
            body = build_bx_body(model, messages)
            try:
                t_call = time.monotonic()
                data = post_with_retry(post_fn, endpoint, body, call_timeout,
                                       sleep_fn)
                latency = time.monotonic() - t_call
            except Exception as e:  # noqa: BLE001 -- failed call
                # Only round 1 can make a job INVALID; later failures end
                # the loop and keep the most recent program that built
                # (FAIL if none), exactly like a cut-off.
                if n == 0:
                    outcome, fails, measurements = "INVALID", [], None
                    last_code = ""
                    last_error = run_error = f"{type(e).__name__}: {e}"
                    content, finish_reason, usage = "", None, {}
                    reasoning_len = 0
                break
            content, finish_reason, usage, reasoning_len = parse_response(data)
            prompt_n, completion_n = _usage_pair(usage)
            n += 1
            rec = {
                "job": job["id"],
                "arm": "BX",
                "bx_final": False,
                "round": n,
                "prompt_tokens": prompt_n,
                "completion_tokens": completion_n,
                "reasoning_len": reasoning_len,
                "latency": round(latency, 3),
                "finish_reason": finish_reason,
            }
            if finish_reason == "length":
                rec["event"] = "cut off"
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if n == 1:
                    outcome, fails, measurements = "INVALID", [], None
                    last_code = ""
                    last_error = run_error = "cut off by the token limit"
                break
            if not content or not (content or "").strip():
                # Empty reply: only round 1 is INVALID; later ones keep
                # the most recent build, exactly like a cut-off.
                rec["event"] = "empty"
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if n == 1:
                    outcome, fails, measurements = "INVALID", [], None
                    last_code = ""
                    last_error = run_error = "empty reply"
                break
            if not FENCE_RE.search(content or ""):
                # No Python code block: the model is satisfied, whatever
                # its text ("DONE", "Looks right", ...). Ends the loop.
                rec["event"] = "DONE"
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if best is None:
                    last_error = "no code in reply"
                break
            code = extract_code(content)
            try:
                shape, run_error, measure = run_code_sandboxed(
                    code, run_tmp, sandbox_profile, timeout=exec_timeout)
            except Exception as e:  # noqa: BLE001 -- harness error is FAIL
                shape, run_error, measure = (
                    None, f"runner error: {e!r}", None)
            if shape is None:
                last_code = code
                last_error = run_error or "code error"
                rec["event"] = "crash"
                rec["run_error"] = scrub(last_error, secrets)[-RUN_ERROR_TAIL:]
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if n >= BX_MAX_CALLS:
                    break
                messages.append({"role": "user",
                                 "content": bx_error_message(run_error)})
                continue
            best = (code, shape)
            last_code = code
            rec["event"] = "built"
            rounds.append(rec)
            messages.append({"role": "assistant", "content": content})
            if n >= BX_MAX_CALLS:
                break
            if measure is None:
                break
            messages.append({"role": "user",
                             "content": bx_self_check_message(measure)})
        if outcome != "INVALID":
            if best is None:
                outcome, fails, measurements = "FAIL", [], None
                run_error = last_error or "code error"
            else:
                try:
                    passed, fails, measurements = checks.score(
                        best[1], job["build"](), expected_for_job)
                except Exception as e:  # noqa: BLE001 -- broken shape is FAIL
                    passed, fails, measurements = (
                        False, ["scoring error"], None)
                    last_error = f"scoring raised: {e!r}"
                if passed:
                    outcome, run_error = "PASS", None
                elif fails == ["scoring error"]:
                    outcome, run_error = "FAIL", last_error
                else:
                    outcome, run_error = "FAIL", None
                last_code = best[0]
    except Exception as e:  # noqa: BLE001 -- unexpected harness error
        # Only round 1 can make a job INVALID; anything later keeps the
        # most recent build (FAIL if none), exactly like a cut-off.
        run_error = f"{type(e).__name__}: {e}"
        if not rounds and best is None and outcome != "INVALID":
            outcome, fails, measurements, last_code = "INVALID", [], None, ""
            content, finish_reason, usage, reasoning_len = "", None, {}, 0
        else:
            last_error = run_error
            if outcome != "INVALID":
                if best is None:
                    outcome, fails, measurements = "FAIL", [], None
                    run_error = last_error or "code error"
                    last_code = last_code or ""
                else:
                    try:
                        passed, fails, measurements = checks.score(
                            best[1], job["build"](), expected_for_job)
                    except Exception:  # noqa: BLE001 -- broken shape FAIL
                        passed, fails, measurements = (
                            False, ["scoring error"], None)
                    if passed:
                        outcome, run_error = "PASS", None
                    else:
                        outcome, run_error = "FAIL", last_error
                    last_code = best[0]
    seconds = time.monotonic() - t0
    end = utcnow_iso()
    run_error = scrub(run_error, secrets)
    if run_error and len(run_error) > RUN_ERROR_TAIL:
        run_error = run_error[-RUN_ERROR_TAIL:]
    prompt_total = sum(r["prompt_tokens"] for r in rounds)
    completion_total = sum(r["completion_tokens"] for r in rounds)
    latency_total = round(sum(r["latency"] for r in rounds), 3)
    reasoning_total = sum(r["reasoning_len"] for r in rounds)
    return {
        "job": job["id"],
        "level": job.get("level"),
        "arm": "BX",
        "model": model,
        "start": start,
        "start_time": start,
        "end": end,
        "end_time": end,
        "seconds": round(seconds, 3),
        "finish_reason": finish_reason,
        "usage": usage,
        "content": content,
        "reasoning_len": reasoning_total,
        "reasoning_length": reasoning_total,
        "code": last_code,
        "extracted_code": last_code,
        "outcome": outcome,
        "fails": fails or [],
        "failed_checks": fails or [],
        "measurements": measurements,
        "run_error": run_error,
        "round": len(rounds),
        "bx_final": True,
        "model_calls": len(rounds),
        "prompt_tokens_total": prompt_total,
        "completion_tokens_total": completion_total,
        "latency_total": latency_total,
        "bx_rounds": rounds,
    }


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
    sandbox_profile=None,
    sandbox_dir=None,
    examples=None,
):
    """Run one (job, arm) pair exactly once: POST, retry once only on a
    network error / HTTP 5xx/429, then score. Never raises for a bad
    answer; network/HTTP failure after the retry is INVALID, never FAIL.
    Arm BX instead runs its multi-round loop (do_bx_call)."""
    if arm == "BX":
        return do_bx_call(
            job, model, endpoint, secrets, manual_text, expected_for_job,
            post_fn, sleep_fn, exec_timeout, call_timeout, sandbox_profile,
            sandbox_dir, examples)
    body = build_body(model, build_messages(arm, job["text"], manual_text))
    start = utcnow_iso()
    t0 = time.monotonic()
    content, finish_reason, usage, reasoning_len = "", None, {}, 0
    outcome = fails = measurements = code = run_error = None
    latency = 0.0
    try:
        t_call = time.monotonic()
        data = post_with_retry(post_fn, endpoint, body, call_timeout, sleep_fn)
        latency = time.monotonic() - t_call
        content, finish_reason, usage, reasoning_len = parse_response(data)
        outcome, fails, measurements, code, run_error = score_content(
            content, finish_reason, job["build"], expected_for_job,
            exec_timeout, sandbox_profile, sandbox_dir
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
        "latency": round(latency, 3),
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


def cost_c_total(c_usages):
    return sum(cost_c_of_usage(u) for u in c_usages)


def over_budget_c(c_usages, budget_c):
    return cost_c_total(c_usages) > budget_c


# ---------------------------------------------------------------- suite


def _run_one_arm(
    arm,
    arm_pairs,
    arm_cfgs,
    secrets,
    manual_text,
    expected,
    post_fn,
    sleep_fn,
    exec_timeout,
    call_timeout,
    sandbox_profile,
    run_tmp,
    pool_size,
    t_start,
    budget,
    budget_c,
    c_usages,
    budget_stopped,
    budget_c_stopped,
):
    """Run one arm's (job, rep) pairs with `pool_size` workers and return
    (records, budget_stopped, budget_c_stopped).

    Called once per arm, arms one after another (FIX_SPEC item 6), so two
    arms are never mixed on the GPU at the same time. Otherwise the
    scheduling is exactly as before: stop sending new calls once the cost
    estimate passes `budget`; stop sending new arm-C calls once arm C's
    own estimate passes `budget_c`.
    """
    n_pairs = len(arm_pairs)
    records = [None] * n_pairs
    next_i = 0
    in_flight = {}
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=pool_size) as pool:
        while next_i < n_pairs or in_flight:
            while next_i < n_pairs and len(in_flight) < pool_size:
                if over_budget(c_usages, time.monotonic() - t_start, budget):
                    budget_stopped = True
                    break
                job, _rep = arm_pairs[next_i]
                if arm == "C" and over_budget_c(c_usages, budget_c):
                    budget_c_stopped = True
                    next_i += 1
                    continue
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
                    sandbox_profile,
                    run_tmp,
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
                job, _rep = arm_pairs[idx]
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
                        job, _rep = arm_pairs[idx]
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
    return records, budget_stopped, budget_c_stopped


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
    budget_c=3.0,
    gpu_start=None,
    sandbox_profile=None,
    k=1,
    workers=None,
):
    """Call every (job, arm) pair `k` times with up to `workers`
    (`max_workers` when None; both default to today's value) concurrent
    calls. The requested arms run one after another, each with that many
    workers, never mixed on the GPU at the same time; each arm's own
    wall-clock start and end are recorded. Stop sending new calls once the
    cost estimate passes `budget`; stop sending new arm-C calls once arm
    C's own estimate passes `budget_c`. When `gpu_start` (unix seconds) is
    given, the GPU estimate uses that start instead of the runner's start.
    Writes calls.jsonl, summary.json and report.md into `out_dir`.

    `arm_cfgs`: {arm: {"endpoint": ..., "model": ...}}.
    `key_map`: {arm: api_key}; keys are only used in the Authorization
    header, never in any record. `post_fn(endpoint, body, timeout)` may be
    a fake for tests; the default posts with urllib.
    `k`: samples per job per arm (default 1 = today's behaviour); each
    sample is a fresh conversation and every answer is saved.
    Returns (records, summary).
    """
    key_map = key_map or {}
    secrets = [k for k in key_map.values() if k]
    if post_fn is None:
        post_fn = _default_post_fn(arm_cfgs, key_map, call_timeout)
    os.makedirs(out_dir, exist_ok=True)
    run_tmp = None
    if sandbox_profile is not None:
        run_tmp = os.path.realpath(
            tempfile.mkdtemp(prefix="sandbox_",
                             dir=os.path.realpath(out_dir)))
    if k is None:
        k = 1
    k = int(k)
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k!r}")
    pool_size = workers if workers is not None else max_workers
    t_start = time.monotonic()
    c_usages = []
    budget_stopped = False
    budget_c_stopped = False
    records = []
    arm_timing = {}
    for arm in arms:
        arm_pairs = [(job, rep) for job in jobs for rep in range(k)]
        arm_start_iso = utcnow_iso()
        arm_t0 = time.monotonic()
        arm_recs, budget_stopped, budget_c_stopped = _run_one_arm(
            arm,
            arm_pairs,
            arm_cfgs,
            secrets,
            manual_text,
            expected,
            post_fn,
            sleep_fn,
            exec_timeout,
            call_timeout,
            sandbox_profile,
            run_tmp,
            pool_size,
            t_start,
            budget,
            budget_c,
            c_usages,
            budget_stopped,
            budget_c_stopped,
        )
        arm_elapsed = time.monotonic() - arm_t0
        arm_end_iso = utcnow_iso()
        for (_job, rep), rec in zip(arm_pairs, arm_recs):
            if rec is not None:
                rec["sample"] = rep
                for rnd in rec.get("bx_rounds", []):
                    rnd["sample"] = rep
            records.append(rec)
        arm_timing[arm] = {
            "start": arm_start_iso,
            "end": arm_end_iso,
            "seconds": round(arm_elapsed, 3),
        }
    elapsed = time.monotonic() - t_start
    if gpu_start is not None:
        try:
            gpu_elapsed = max(0.0, time.time() - float(gpu_start))
        except (TypeError, ValueError):
            gpu_elapsed = elapsed
    else:
        gpu_elapsed = elapsed
    sent = [r for r in records if r is not None]
    skipped = len(records) - len(sent)
    summary = build_summary(
        sent,
        c_usages,
        elapsed,
        budget,
        budget_stopped,
        skipped,
        arms,
        budget_c=budget_c,
        budget_c_stopped=budget_c_stopped,
        gpu_start=gpu_start,
        gpu_elapsed_s=gpu_elapsed,
        k=k,
        arm_timing=arm_timing,
        workers=pool_size,
    )
    calls_path = os.path.join(out_dir, "calls.jsonl")
    with open(calls_path, "w", encoding="utf-8") as f:
        for rec in sent:
            for round_rec in rec.get("bx_rounds", []):
                f.write(json.dumps(round_rec) + "\n")
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


def _rec_calls_tokens_latency(rec):
    """(model calls, total tokens, summed model-call latency) for one final
    record. Latency is model call time only, the same definition for every
    arm (FIX_SPEC item 6)."""
    if "model_calls" in rec:
        tokens = (rec.get("prompt_tokens_total", 0) or 0) + \
            (rec.get("completion_tokens_total", 0) or 0)
        return (rec.get("model_calls", 1) or 0, tokens,
                rec.get("latency_total", rec.get("latency", 0) or 0) or 0)
    prompt_n, completion_n = _usage_pair(rec.get("usage"))
    latency = rec.get("latency", None)
    if latency is None:
        latency = rec.get("seconds", 0) or 0
    return 1, prompt_n + completion_n, latency or 0


def _rec_token_split(rec):
    """(input tokens, output tokens) for one final record."""
    if "prompt_tokens_total" in rec or "completion_tokens_total" in rec:
        try:
            prompt = int(rec.get("prompt_tokens_total", 0) or 0)
        except (TypeError, ValueError):
            prompt = 0
        try:
            completion = int(rec.get("completion_tokens_total", 0) or 0)
        except (TypeError, ValueError):
            completion = 0
        return prompt, completion
    return _usage_pair(rec.get("usage"))


def arm_stats(records, arm, extra=False, k=1, wall_seconds=None):
    arm_recs = [r for r in records if r.get("arm") == arm]
    n_pass = sum(1 for r in arm_recs if r.get("outcome") == "PASS")
    n_fail = sum(1 for r in arm_recs if r.get("outcome") == "FAIL")
    n_inv = sum(1 for r in arm_recs if r.get("outcome") == "INVALID")
    scored = n_pass + n_fail
    by_job = {}
    for r in arm_recs:
        by_job.setdefault(r.get("job"), []).append(r)
    n_jobs = len(by_job)
    jobs_with_pass = sum(
        1 for rs in by_job.values()
        if any(x.get("outcome") == "PASS" for x in rs)
    )
    splits = [_rec_token_split(r) for r in arm_recs]
    sum_in = sum(p for p, _ in splits)
    sum_out = sum(c for _, c in splits)
    sum_tokens = sum_in + sum_out
    sum_calls = sum(_rec_calls_tokens_latency(r)[0] for r in arm_recs)
    stats = {
        "n": len(arm_recs),
        "PASS": n_pass,
        "FAIL": n_fail,
        "INVALID": n_inv,
        "pass_rate": (n_pass / scored) if scored else None,
        "invalid_rate": (n_inv / len(arm_recs)) if arm_recs else None,
        # FIX_SPEC items 6-7: per-arm cost/usage numbers over all answers.
        "calls": sum_calls,
        "input_tokens": sum_in,
        "output_tokens": sum_out,
        "total_tokens": sum_tokens,
        "k": k,
        "pass_at_k": (jobs_with_pass / n_jobs) if n_jobs else None,
    }
    if wall_seconds is not None:
        stats["wall_seconds"] = wall_seconds
        stats["dollars_per_pass"] = (
            (wall_seconds / 3600.0 * GPU_DOLLARS_PER_HOUR / n_pass)
            if n_pass else None
        )
    if extra:
        totals = [_rec_calls_tokens_latency(r) for r in arm_recs]
        n = len(arm_recs)
        sum_latency = sum(s for _, _, s in totals)
        denom = n_jobs or n
        stats.update({
            "mean_calls_per_job": (sum_calls / denom) if denom else None,
            "mean_tokens_per_job": (sum_tokens / denom) if denom else None,
            "mean_latency_per_job": (sum_latency / denom) if denom else None,
            "tokens_per_pass": (sum_tokens / n_pass) if n_pass else None,
            "latency_per_pass": (sum_latency / n_pass) if n_pass else None,
        })
    return stats


def compute_decision(rate_b, rate_c, invalid_rates):
    """PLAN.md section 7 from the numbers. Returns (decision, run_valid).

    Rates are compared in whole percentage points (round(rate*100)).
    Rules apply in order; the first match wins. run_valid is False
    ("run not valid") if INVALID > 5% in any arm.
    """
    run_valid = all(
        (r is None or r <= 0.05) for r in (invalid_rates or {}).values()
    )
    if rate_b is None or rate_c is None:
        decision = "grey zone (too few scored calls)"
    else:
        b_pts = round(rate_b * 100)
        c_pts = round(rate_c * 100)
        gap = c_pts - b_pts
        if b_pts >= 80:
            decision = "STOP (manual is enough)"
        elif c_pts < 20:
            decision = "Spark can't teach"
        elif b_pts <= 60 and c_pts >= 30 and gap >= 25:
            decision = "GO to training"
        else:
            decision = "grey zone"
    if not run_valid:
        decision = "run not valid (INVALID > 5% in an arm); " + decision
    return decision, run_valid


def build_summary(records, c_usages, elapsed_s, budget, budget_stopped,
                  skipped, arms, budget_c=3.0, budget_c_stopped=False,
                  gpu_start=None, gpu_elapsed_s=None, k=1,
                  arm_timing=None, workers=None):
    arm_timing = arm_timing or {}
    wall = {
        arm: (arm_timing.get(arm) or {}).get("seconds") for arm in arms
    }
    per_arm = {
        arm: arm_stats(records, arm, extra=True, k=k,
                       wall_seconds=wall[arm])
        for arm in arms
    }
    levels = sorted({r.get("level") for r in records if r.get("level")})
    by_level = {}
    for level in levels:
        by_level[level] = {}
        for arm in arms:
            sub = [r for r in records if r.get("level") == level]
            by_level[level][arm] = arm_stats(sub, arm, k=k)
    cost_c = sum(cost_c_of_usage(u) for u in c_usages)
    gpu_elapsed = gpu_elapsed_s if gpu_elapsed_s is not None else elapsed_s
    gpu_total = gpu_cost_of_elapsed(gpu_elapsed)
    costs = {}
    for arm in arms:
        if wall[arm] is not None:
            costs[arm] = round(
                wall[arm] / 3600.0 * GPU_DOLLARS_PER_HOUR, 4)
    if "C" in arms:
        costs["C_tokens"] = round(cost_c, 4)
    costs.update({
        "gpu_total": round(gpu_total, 4),
        "total": round(gpu_total + cost_c, 4),
        "note": "Each arm ran alone on the GPU: that arm's cost is its "
        "own wall-clock at $2.50/h (A100-80GB Modal rate). Arm C token "
        "cost is input $1.25/M + output $4.25/M tokens from usage. "
        "The estimate covers only the runner's own wall-clock; the real "
        "Modal cost (incl. cold start) comes from `modal billing report`.",
    })
    invalid_rates = {
        arm: per_arm[arm]["invalid_rate"] for arm in arms if per_arm[arm]["n"]
    }
    if "B" in per_arm and "C" in per_arm:
        decision, run_valid = compute_decision(
            per_arm.get("B", {}).get("pass_rate"),
            per_arm.get("C", {}).get("pass_rate"),
            invalid_rates,
        )
    else:
        run_valid = all(
            (r is None or r <= 0.05) for r in invalid_rates.values()
        )
        decision = "decision: see experiments/bmax/PLAN.md"
    table = {}
    for rec in records:
        cell = table.setdefault(rec["job"], {}).get(rec["arm"])
        if k is not None and int(k) > 1:
            if cell is None:
                table[rec["job"]][rec["arm"]] = [rec.get("outcome")]
            else:
                cell.append(rec.get("outcome"))
        else:
            table[rec["job"]][rec["arm"]] = rec.get("outcome")
    return {
        "arms": per_arm,
        "levels": by_level,
        "by_level": by_level,
        "n_calls": len(records),
        "skipped": skipped,
        "budget": budget,
        "budget_stopped": budget_stopped,
        "budget_c": budget_c,
        "budget_c_stopped": budget_c_stopped,
        "elapsed_seconds": round(elapsed_s, 3),
        "gpu_start": gpu_start,
        "gpu_elapsed_seconds": round(gpu_elapsed, 3),
        "costs": costs,
        "decision": decision,
        "run_valid": run_valid,
        "table": table,
        "k": k,
        "workers": workers,
        "arm_timing": {
            arm: arm_timing.get(arm) or {"seconds": wall[arm]}
            for arm in arms
        },
    }


def _pct(rate):
    return "n/a" if rate is None else f"{100 * rate:.1f}%"


def _num(value):
    return "n/a" if value is None else f"{value:.2f}"


def build_report(summary):
    arms = [a for a in summary["arms"]]
    lines = ["# First-test report", ""]
    lines.append(f"Decision (PLAN.md section 7): **{summary['decision']}**")
    lines.append(f"Run valid: {summary['run_valid']}")
    lines.append(
        f"Calls: {summary['n_calls']}  "
        f"Skipped by budget guard: {summary['skipped']}  "
        f"(budget ${summary['budget']}, stopped: {summary['budget_stopped']}; "
        f"arm-C budget ${summary.get('budget_c', 3.0)}, "
        f"stopped: {summary.get('budget_c_stopped', False)})"
    )
    lines.append("")
    lines.append("## Cost estimate")
    for arm in arms:
        lines.append(f"- Arm {arm}: ${summary['costs'].get(arm, 0):.4f}")
    if "C_tokens" in summary["costs"]:
        lines.append(
            f"- Arm C tokens: ${summary['costs']['C_tokens']:.4f}")
    lines.append(f"- Total: ${summary['costs']['total']:.4f}")
    lines.append(
        "Each arm ran alone on the GPU; per-arm cost is its own wall-clock "
        "at $2.50/h (A100-80GB Modal rate). The estimate covers only the "
        "runner's own wall-clock; the real Modal cost (incl. cold start) "
        "comes from `modal billing report`."
    )
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
    if any("mean_calls_per_job" in summary["arms"][a] for a in arms):
        lines.append("## Cost and speed (all arms)")
        lines.append("| Arm | mean calls/job | mean tokens/job | "
                     "mean latency/job (s) | tokens/correct | "
                     "latency/correct (s) | in tokens | out tokens | "
                     "calls | wall (s) | $/correct | "
                     f"pass@{summary.get('k', 1)} |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for arm in arms:
            s = summary["arms"][arm]
            lines.append(
                f"| {arm} | {_num(s.get('mean_calls_per_job'))} | "
                f"{_num(s.get('mean_tokens_per_job'))} | "
                f"{_num(s.get('mean_latency_per_job'))} | "
                f"{_num(s.get('tokens_per_pass'))} | "
                f"{_num(s.get('latency_per_pass'))} | "
                f"{s.get('input_tokens', 'n/a')} | "
                f"{s.get('output_tokens', 'n/a')} | "
                f"{s.get('calls', 'n/a')} | "
                f"{_num(s.get('wall_seconds'))} | "
                f"{_num(s.get('dollars_per_pass'))} | "
                f"{_pct(s.get('pass_at_k'))} |"
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
    if summary.get("k", 1) is not None and int(summary.get("k", 1)) > 1:
        lines.append(f"(k = {summary.get('k')}: one outcome per sample)")
    lines.append("| Job | " + " | ".join(arms) + " |")
    lines.append("|---|" + "|".join(["---"] * len(arms)) + "|")

    def _cell(value):
        if isinstance(value, list):
            return ",".join(str(v) for v in value)
        return str(value if value is not None else "-")

    for job in sorted(summary["table"]):
        lines.append(
            "| " + job + " | "
            + " | ".join(_cell(summary["table"][job].get(a)) for a in arms)
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
    parser.add_argument("--budget-c", type=float, default=3.0)
    parser.add_argument("--gpu-start", type=float, default=None)
    parser.add_argument("--arms", default=",".join(DEFAULT_ARMS),
                        help="comma list of arms (default A,B,C)")
    parser.add_argument("--sandbox", default=None,
                        help="sandbox profile (.sb file) for model answers")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help="workers per arm; arms run one after another, "
                        f"never mixed (default {MAX_WORKERS})")
    parser.add_argument("--k", type=int, default=1,
                        help="samples per job per arm in fresh conversations "
                        "(default 1)")
    args = parser.parse_args(argv)
    if args.workers is not None and args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.k is not None and args.k < 1:
        parser.error("--k must be >= 1")
    try:
        arms = parse_arms(args.arms)
    except ValueError as e:
        parser.error(str(e))
    if args.sandbox is not None and not os.path.isfile(args.sandbox):
        parser.error(f"sandbox profile not found: {args.sandbox}")
    if "BX" in arms and args.sandbox is None:
        parser.error("arm BX requires --sandbox <profile>")

    glimmer_url = os.environ.get("GLIMMER_URL", "")
    glimmer_key = os.environ.get("GLIMMER_KEY", "")
    baseten_key = os.environ.get("BASETEN_KEY", "")
    need = []
    if any(a in GLIMMER_ARMS for a in arms):
        need += [("GLIMMER_URL", glimmer_url), ("GLIMMER_KEY", glimmer_key)]
    if "C" in arms:
        need += [("BASETEN_KEY", baseten_key)]
    missing = [name for name, val in need if not val]
    if missing:
        parser.error("missing environment variables: " + ", ".join(missing))
    if {"B2", "BX"} & set(arms):
        try:
            load_hint_text()
        except OSError as e:
            parser.error(f"cannot read hint file {HINT_PATH}: {e}")

    JOBS, expected, manual_text = load_inputs()
    if args.jobs == "dry":
        jobs = [j for j in JOBS if j.get("level") == "dry"]
    else:
        jobs = [j for j in JOBS if j.get("level") in ("medium", "hard")]
    if not jobs:
        parser.error(f"no jobs for --jobs {args.jobs}")

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
    run_suite(
        jobs, expected, manual_text, args.out, arm_cfgs, key_map, args.budget,
        budget_c=args.budget_c, gpu_start=args.gpu_start, arms=arms,
        sandbox_profile=args.sandbox, k=args.k, workers=args.workers,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())