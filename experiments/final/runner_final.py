#!/usr/bin/env python3
"""Trained arm FT (+ base control arm A, round 3) + the BX finisher on the
cloud CadQuery box (MUSE_SPEC sections 3, 3b).

Arm FT = arm A's messages (system + job text, no manual, no hint) and arm
A's body (max_tokens 16000, temperature 1.0, top_p 0.95, top_k 64), with
model "forge" served from FORGE_URL/FORGE_KEY. Every answer's code runs in
the cloud box (experiments/final/cloud_cq.py) and is graded by the cloud
grader; nothing a model writes runs on the Mac. Each calls.jsonl record
carries ``grader: first-test|factory`` (N1): the exam (first-test) uses
checks.score exactly as the baselines, factory dev jobs use the factory
grader (precise volumes). Do not mix them.

The BX finisher (``--arms BX --fill-missing <baseline dir>``) runs only
the (job, rep) pairs with no BX final record, with the frozen BX prompt,
settings and loop and base Glimmer (GLIMMER_URL/GLIMMER_KEY). Fewer final
records than missing pairs at the end exits 3 with "INCOMPLETE: ask the
user" and writes a summary compare.py refuses.

CLI: runner_final.py --jobs dry|main [--jobs-file <factory dev file>]
  --out <dir> [--arms FT|BX] [--fill-missing <dir>] [--k 3] [--workers 8]
  [--budget 5.0] [--gpu-start <unix seconds>]

No network, Modal run, model call or key printing happens before the env
check: with no keys the command exits 2 naming the variable. Tests are
offline; exec/grade/server-info steps are injected fakes.
"""

import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FIRST_TEST_DIR = os.path.join(os.path.dirname(HERE), "first-test")
COMMON_DIR = os.path.join(os.path.dirname(HERE), "..", "common")
for _p in (HERE, FIRST_TEST_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
if os.path.isdir(COMMON_DIR) and COMMON_DIR not in sys.path:
    sys.path.insert(0, COMMON_DIR)

import runner  # noqa: E402 (frozen; imported, never modified)

try:
    import cloud_cq  # noqa: E402 (lazy Modal inside; tests inject fakes)
except ImportError:
    cloud_cq = None

try:
    import budget_left as _budget_left  # noqa: E402 (reserve constant)
    RESERVE = float(_budget_left.RESERVE)
except (ImportError, AttributeError):
    RESERVE = 0.30  # experiments/common/budget_left.py RESERVE

FT_MODEL = "forge"
FT_ARM = "FT"
A_MODEL = "muse-glimmer"
A_ARM = "A"
BX_ARM = "BX"
VALID_FINAL_ARMS = (FT_ARM, A_ARM, BX_ARM)
GPU_DOLLARS_PER_HOUR = runner.GPU_DOLLARS_PER_HOUR  # 2.50, same yardstick
CALL_TIMEOUT = runner.CALL_TIMEOUT
DEV_GATE_RATE = 0.80  # PLAN step 5: dev >= 80% at 0.2% -> GO, else STOP


# ------------------------------------------------------- FT messages / body


def ft_messages(job_text, manual_text=""):
    """Arm FT messages = arm A's messages (system + job text).

    Claude small fix (2026-10-30, disclosed): if env FORGE_RULE_CARD names a
    file, its text is appended to the system message (the rule-card check).
    Unset (the default), the messages are unchanged."""
    messages = runner.build_messages("A", job_text, manual_text)
    card_path = os.environ.get("FORGE_RULE_CARD", "")
    if card_path:
        with open(card_path, encoding="utf-8") as f:
            card = f.read().strip()
        messages[0] = dict(messages[0],
                           content=messages[0]["content"] + "\n\n" + card)
    return messages


def ft_body(messages, model=FT_MODEL):
    """Arm FT body = arm A's body, with model "forge"."""
    return runner.build_body(model, messages)


def a_messages(job_text, manual_text=""):
    """Arm A messages = arm FT messages (system + job text)."""
    return ft_messages(job_text, manual_text)


def a_body(messages, model=A_MODEL):
    """Arm A body = arm FT body, with model "muse-glimmer"."""
    return runner.build_body(model, messages)


def reasoning_chars_of(data):
    """Length of message.reasoning_content (round 3 serving check)."""
    try:
        choice = (data.get("choices") or [{}])[0] or {}
    except (AttributeError, IndexError, TypeError):
        return 0
    if not isinstance(choice, dict):
        return 0
    msg = choice.get("message") or {}
    if not isinstance(msg, dict):
        return 0
    val = msg.get("reasoning_content")
    return len(val) if isinstance(val, str) else 0


def _usage_pair(usage):
    """(prompt_tokens, completion_tokens) as ints (same rule as runner)."""
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


def box_measure_to_selfcheck(measure):
    """Cloud box measure.json -> the run_one_cq field format that
    bx_self_check_message needs (xmin..zmax, volume, solids).

    Returns None when the box wrote no usable measurement (the BX loop
    then ends after the build, exactly like run_code_sandboxed's
    measure-None path).
    """
    try:
        bbox = (measure or {}).get("bbox")
        return {
            "xmin": bbox[0],
            "ymin": bbox[1],
            "zmin": bbox[2],
            "xmax": bbox[3],
            "ymax": bbox[4],
            "zmax": bbox[5],
            "volume": (measure or {})["volume"],
            "solids": (measure or {})["solids"],
        }
    except (TypeError, IndexError, KeyError):
        return None


def run_box_code(exec_fn, code):
    """One answer string through the cloud box.

    Returns (brep_bytes|None, run_error|None, selfcheck_measure|None).
    A box harness exception is the answer's FAIL (never raised), like
    the frozen runner's harness-error path.
    """
    try:
        boxed = exec_fn(code)
    except Exception as e:  # noqa: BLE001 -- harness error is FAIL
        return None, "runner error: %r" % (e,), None
    if boxed is None or boxed.get("brep_bytes") is None:
        return None, (boxed or {}).get("run_error") or \
            "the answer wrote no BREP", None
    return (boxed["brep_bytes"], None,
            box_measure_to_selfcheck((boxed or {}).get("measure")))


# ------------------------------------------------------- vLLM server info


def fetch_server_info(endpoint, key, urlopen=None):
    """Best-effort vLLM server info for summary.json (never raises).

    GETs <base>/v1/models with the bearer key and records the served
    model ids plus the vLLM image digest when the server reports one
    (body fields image_digest/digest, or an x-image-digest header).
    Offline or on any error returns models [] and image_digest None.
    """
    info = {"models": [], "image_digest": None}
    try:
        base = (endpoint or "").split("/v1/")[0].rstrip("/")
        if not base:
            return info
        req = urllib.request.Request(
            base + "/v1/models",
            headers={"Authorization": "Bearer " + (key or "")},
        )
        opener = urlopen or (lambda r, timeout: urllib.request.urlopen(
            r, timeout=timeout))
        resp = opener(req, 30)
        try:
            data = json.load(resp)
        except Exception:  # noqa: BLE001 -- unreadable body: no info
            return info
        try:
            names = [m.get("id") for m in data.get("data", [])
                     if isinstance(m, dict)]
            info["models"] = [n for n in names if n]
        except (AttributeError, TypeError):
            pass
        for field in ("image_digest", "digest", "digest_sha"):
            try:
                val = data.get(field)
            except (AttributeError, TypeError):
                val = None
            if val:
                info["image_digest"] = str(val)
                break
        if info["image_digest"] is None:
            try:
                headers = resp.headers or {}
            except AttributeError:
                headers = {}
            get = getattr(headers, "get", None)
            if callable(get):
                for header in ("x-image-digest", "docker-content-digest"):
                    val = get(header)
                    if val:
                        info["image_digest"] = str(val)
                        break
    except Exception:  # noqa: BLE001 -- best effort only
        pass
    return info


# ------------------------------------------------------- money guard


def money_left(cap_dollars, gpu_start, now=None):
    """Money left = cap - GPU time since gpu-start x $2.50/h.

    Without --gpu-start the runner's own start counts as the GPU start.
    """
    t_now = time.time() if now is None else now
    try:
        start = float(gpu_start) if gpu_start is not None else t_now
    except (TypeError, ValueError):
        start = t_now
    return float(cap_dollars) - max(0.0, t_now - start) * \
        GPU_DOLLARS_PER_HOUR / 3600.0


def out_of_money(cap_dollars, gpu_start, reserve=RESERVE, now=None):
    """Stop sending NEW calls once the money left is at/below the reserve
    (in-flight answers still cost money, as in budget_left.py)."""
    return money_left(cap_dollars, gpu_start, now) <= reserve


# ------------------------------------------------------- one FT answer


def _invalid_ft(job, rep, model, start, end, seconds, run_error, exam,
                arm=FT_ARM, reasoning_chars=0):
    """An INVALID FT record (cut off, empty reply, or a failed call)."""
    return {
        "job": job["id"],
        "rep": rep,
        "sample": rep,
        "level": job.get("level"),
        "arm": arm,
        "model": model,
        "grader": exam,
        "start": start,
        "start_time": start,
        "end": end,
        "end_time": end,
        "seconds": round(seconds, 3),
        "t_call_s": 0.0,
        "finish_reason": "length" if "cut off" in (run_error or "")
        else None,
        "usage": {},
        "content": "",
        "reasoning_len": 0,
        "reasoning_length": 0,
        "reasoning_chars": reasoning_chars,
        "code": "",
        "extracted_code": "",
        "verdict": "INVALID",
        "tight": "INVALID",
        "outcome": "INVALID",
        "fails": [],
        "fails_tight": [],
        "failed_checks": [],
        "measurements": None,
        "run_error": (run_error or "")[-runner.RUN_ERROR_TAIL:],
    }


def do_ft_call(job, model, endpoint, secrets, exam, post_fn, sleep_fn,
               exec_fn, grade_fn, call_timeout=CALL_TIMEOUT, rep=0,
               arm=FT_ARM):
    """Run one (job, rep) pair once: POST the FT prompt, extract the code,
    run it in the cloud box, grade the BREP in the cloud grader.

    Never raises for a bad answer; a failed model call is INVALID, an
    answer that writes no BREP is FAIL, the grader's 0.2% verdict is the
    outcome (tight at 1e-6 is recorded alongside). Arm A runs the same
    call with the base Glimmer model (round 3 control arm).
    """
    body = ft_body(ft_messages(job["text"]), model=model)
    start = runner.utcnow_iso()
    t0 = time.monotonic()
    try:
        t_call = time.monotonic()
        data = runner.post_with_retry(post_fn, endpoint, body,
                                      call_timeout, sleep_fn)
        latency = time.monotonic() - t_call
    except Exception as e:  # noqa: BLE001 -- failed call => INVALID
        seconds = time.monotonic() - t0
        end = runner.utcnow_iso()
        return _invalid_ft(job, rep, model, start, end, seconds,
                           "%s: %s" % (type(e).__name__, e), exam,
                           arm=arm)
    content, finish_reason, usage, reasoning_len = \
        runner.parse_response(data)
    reasoning_chars = reasoning_chars_of(data)
    if finish_reason == "length" or not (content or "").strip():
        seconds = time.monotonic() - t0
        end = runner.utcnow_iso()
        err = "cut off by the token limit" if finish_reason == "length" \
            else "empty reply"
        return _invalid_ft(job, rep, model, start, end, seconds, err, exam,
                           arm=arm, reasoning_chars=reasoning_chars)
    code = runner.extract_code(content)
    if not (code or "").strip():
        seconds = time.monotonic() - t0
        end = runner.utcnow_iso()
        return _invalid_ft(job, rep, model, start, end, seconds,
                           "empty reply", exam,
                           arm=arm, reasoning_chars=reasoning_chars)
    brep, run_error, _sc = run_box_code(exec_fn, code)
    if brep is None:
        outcome, tight, fails, fails_tight, measurements = \
            "FAIL", "FAIL", [], [], None
    else:
        try:
            graded = grade_fn(exam, job["id"], brep)
        except Exception as e:  # noqa: BLE001 -- grader down is FAIL
            graded = {"verdict": "FAIL", "tight": "FAIL",
                      "fails": ["grader error: %s: %s"
                                % (type(e).__name__, e)],
                      "fails_tight": ["grader error"], "measurements": None}
        verdict = graded.get("verdict", "FAIL")
        outcome = "PASS" if verdict == "PASS" else "FAIL"
        tight = graded.get("tight", outcome)
        fails = list(graded.get("fails") or [])
        fails_tight = list(graded.get("fails_tight")
                           or graded.get("fails") or [])
        measurements = graded.get("measurements")
        run_error = None if outcome == "PASS" else run_error
    seconds = time.monotonic() - t0
    end = runner.utcnow_iso()
    run_error = runner.scrub(run_error, secrets)
    if run_error and len(run_error) > runner.RUN_ERROR_TAIL:
        run_error = run_error[-runner.RUN_ERROR_TAIL:]
    prompt_n, completion_n = _usage_pair(usage)
    return {
        "job": job["id"],
        "rep": rep,
        "sample": rep,
        "level": job.get("level"),
        "arm": arm,
        "model": model,
        "grader": exam,
        "start": start,
        "start_time": start,
        "end": end,
        "end_time": end,
        "seconds": round(seconds, 3),
        "t_call_s": round(latency, 3),
        "latency": round(latency, 3),
        "finish_reason": finish_reason,
        "usage": usage if isinstance(usage, dict) else {},
        "prompt_tokens": prompt_n,
        "completion_tokens": completion_n,
        "content": content,
        "reasoning_len": reasoning_len,
        "reasoning_length": reasoning_len,
        "reasoning_chars": reasoning_chars,
        "code": code,
        "extracted_code": code,
        "verdict": outcome,
        "tight": tight,
        "outcome": outcome,
        "fails": fails,
        "fails_tight": fails_tight,
        "failed_checks": fails,
        "measurements": measurements,
        "run_error": run_error,
    }


# ------------------------------------------------------- one BX answer (cloud)


def do_bx_cloud_call(job, model, endpoint, secrets, manual_text, post_fn,
                     sleep_fn, exec_fn, grade_fn, exam="first-test",
                     call_timeout=CALL_TIMEOUT, hint_text=None,
                     examples=None, rep=0):
    """Arm BX on the cloud box: the frozen runner.do_bx_call loop, except
    each program runs in the cloud box (which returns run_error + measure
    in the run_code_sandboxed field format) and the verdict comes from the
    cloud grader. Sends exactly the same message list, round by round, as
    runner.do_bx_call with the same replies (covered by test)."""
    messages = runner.build_messages("BX", job["text"], manual_text,
                                     hint_text, examples)
    start = runner.utcnow_iso()
    t0 = time.monotonic()
    rounds = []
    best = None
    last_code = ""
    last_error = None
    content, finish_reason, usage, reasoning_len = "", None, {}, 0
    outcome = fails = measurements = None
    tight = None
    fails_tight = None
    try:
        n = 0
        while n < runner.BX_MAX_CALLS:
            body = runner.build_bx_body(model, messages)
            try:
                t_call = time.monotonic()
                data = runner.post_with_retry(post_fn, endpoint, body,
                                              call_timeout, sleep_fn)
                latency = time.monotonic() - t_call
            except Exception as e:  # noqa: BLE001 -- failed call
                if n == 0:
                    outcome, fails, measurements = "INVALID", [], None
                    tight = "INVALID"
                    last_code = ""
                    last_error = run_error = "%s: %s" % (
                        type(e).__name__, e)
                    content, finish_reason, usage = "", None, {}
                    reasoning_len = 0
                break
            content, finish_reason, usage, reasoning_len = \
                runner.parse_response(data)
            prompt_n, completion_n = _usage_pair(usage)
            n += 1
            rec = {
                "job": job["id"],
                "arm": BX_ARM,
                "bx_final": False,
                "round": n,
                "rep": rep,
                "sample": rep,
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
                    tight = "INVALID"
                    last_code = ""
                    last_error = run_error = "cut off by the token limit"
                break
            if not content or not (content or "").strip():
                rec["event"] = "empty"
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if n == 1:
                    outcome, fails, measurements = "INVALID", [], None
                    tight = "INVALID"
                    last_code = ""
                    last_error = run_error = "empty reply"
                break
            if not runner.FENCE_RE.search(content or ""):
                rec["event"] = "DONE"
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if best is None:
                    last_error = "no code in reply"
                break
            code = runner.extract_code(content)
            brep, run_error, sc_measure = run_box_code(exec_fn, code)
            if brep is None:
                last_code = code
                last_error = run_error or "code error"
                rec["event"] = "crash"
                rec["run_error"] = runner.scrub(
                    last_error, secrets)[-runner.RUN_ERROR_TAIL:]
                rounds.append(rec)
                messages.append({"role": "assistant", "content": content})
                if n >= runner.BX_MAX_CALLS:
                    break
                messages.append({"role": "user", "content":
                                 runner.bx_error_message(run_error)})
                continue
            best = (code, brep)
            last_code = code
            rec["event"] = "built"
            rounds.append(rec)
            messages.append({"role": "assistant", "content": content})
            if n >= runner.BX_MAX_CALLS:
                break
            if sc_measure is None:
                break
            messages.append({"role": "user", "content":
                             runner.bx_self_check_message(sc_measure)})
        if outcome != "INVALID":
            if best is None:
                outcome, fails, measurements = "FAIL", [], None
                tight = "FAIL"
                run_error = last_error or "code error"
            else:
                try:
                    graded = grade_fn(exam, job["id"], best[1])
                    verdict = graded.get("verdict", "FAIL")
                    tight = graded.get("tight", verdict)
                    fails = list(graded.get("fails") or [])
                    fails_tight = list(graded.get("fails_tight")
                                       or graded.get("fails") or [])
                    measurements = graded.get("measurements")
                    passed = (verdict == "PASS")
                except Exception as e:  # noqa: BLE001 -- broken is FAIL
                    passed, fails, measurements = (
                        False, ["scoring error"], None)
                    fails_tight = ["scoring error"]
                    tight = "FAIL"
                    last_error = "scoring raised: %r" % (e,)
                if passed:
                    outcome, run_error = "PASS", None
                elif fails == ["scoring error"]:
                    outcome, run_error = "FAIL", last_error
                else:
                    outcome, run_error = "FAIL", None
                last_code = best[0]
    except Exception as e:  # noqa: BLE001 -- unexpected harness error
        run_error = "%s: %s" % (type(e).__name__, e)
        if not rounds and best is None and outcome != "INVALID":
            outcome, fails, measurements, last_code = "INVALID", [], None, ""
            tight = "INVALID"
            content, finish_reason, usage, reasoning_len = "", None, {}, 0
        else:
            last_error = run_error
            if outcome != "INVALID":
                if best is None:
                    outcome, fails, measurements = "FAIL", [], None
                    tight = "FAIL"
                    run_error = last_error or "code error"
                    last_code = last_code or ""
                else:
                    try:
                        graded = grade_fn(exam, job["id"], best[1])
                        verdict = graded.get("verdict", "FAIL")
                        tight = graded.get("tight", verdict)
                        fails = list(graded.get("fails") or [])
                        measurements = graded.get("measurements")
                        passed = (verdict == "PASS")
                    except Exception:  # noqa: BLE001 -- broken shape FAIL
                        passed, fails, measurements = (
                            False, ["scoring error"], None)
                        tight = "FAIL"
                    if passed:
                        outcome, run_error = "PASS", None
                    else:
                        outcome, run_error = "FAIL", last_error
                    last_code = best[0]
    seconds = time.monotonic() - t0
    end = runner.utcnow_iso()
    run_error = runner.scrub(run_error, secrets)
    if run_error and len(run_error) > runner.RUN_ERROR_TAIL:
        run_error = run_error[-runner.RUN_ERROR_TAIL:]
    prompt_total = sum(r["prompt_tokens"] for r in rounds)
    completion_total = sum(r["completion_tokens"] for r in rounds)
    latency_total = round(sum(r["latency"] for r in rounds), 3)
    reasoning_total = sum(r["reasoning_len"] for r in rounds)
    for rnd in rounds:
        rnd["grader"] = exam
    return {
        "job": job["id"],
        "rep": rep,
        "sample": rep,
        "level": job.get("level"),
        "arm": BX_ARM,
        "grader": exam,
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
        "verdict": outcome,
        "tight": tight if tight is not None else outcome,
        "outcome": outcome,
        "fails": fails or [],
        "fails_tight": (fails_tight or fails) or [],
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


# ------------------------------------------------------- summaries


def _passed(rec):
    return (rec.get("verdict", rec.get("outcome"))) == "PASS"


def _tight_passed(rec):
    return rec.get("tight", rec.get("verdict")) == "PASS"


def _split_tokens(rec):
    """(prompt, completion) tokens for one final record (either arm)."""
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


def summarize_arm(records, arm, exam, wall_seconds, cold_start_s,
                  server_info, k, workers, budget, budget_stopped,
                  skipped, status="COMPLETE", extra=None):
    """summary.json for one FT or BX session: pass rates at 0.2% (the
    decision) and at 1e-6 (reference), pass@k, tokens per correct part
    split into prompt/completion, seconds per answer (median, mean), arm
    wall-clock, $ per correct part = wall-clock h x $2.50 / PASS."""
    arm_recs = [r for r in records if r.get("arm") == arm]
    n_pass = sum(1 for r in arm_recs if _passed(r))
    n_tight = sum(1 for r in arm_recs if _tight_passed(r))
    n_fail = sum(1 for r in arm_recs
                 if (r.get("verdict", r.get("outcome"))) == "FAIL")
    n_inv = sum(1 for r in arm_recs
                if (r.get("verdict", r.get("outcome"))) == "INVALID")
    scored = n_pass + n_fail
    by_job = {}
    for r in arm_recs:
        by_job.setdefault(r.get("job"), []).append(r)
    jobs_with_pass = sum(
        1 for rs in by_job.values() if any(_passed(x) for x in rs))
    splits = [_split_tokens(r) for r in arm_recs]
    sum_in = sum(p for p, _ in splits)
    sum_out = sum(c for _, c in splits)
    per_answer = [float(r.get("seconds", 0) or 0) for r in arm_recs]
    dollars = (wall_seconds / 3600.0 * GPU_DOLLARS_PER_HOUR / n_pass) \
        if n_pass else None
    by_level = {}
    for level in sorted({r.get("level") for r in arm_recs
                         if r.get("level")}):
        sub = [r for r in arm_recs if r.get("level") == level]
        sp = sum(1 for r in sub if _passed(r))
        st = sum(1 for r in sub if _tight_passed(r))
        sc = sum(1 for r in sub if _passed(r) or
                 (r.get("verdict", r.get("outcome"))) == "FAIL")
        by_job_l = {}
        for r in sub:
            by_job_l.setdefault(r.get("job"), []).append(r)
        by_level[level] = {
            "n": len(sub),
            "PASS": sp,
            "pass_rate": (sp / sc) if sc else None,
            "pass_rate_tight": (st / sc) if sc else None,
            "pass_at_k": (sum(1 for rs in by_job_l.values()
                              if any(_passed(x) for x in rs))
                          / len(by_job_l)) if by_job_l else None,
        }
    summary = {
        "arm": arm,
        "grader": exam,
        "status": status,
        "n": len(arm_recs),
        "PASS": n_pass,
        "FAIL": n_fail,
        "INVALID": n_inv,
        "pass_rate": (n_pass / scored) if scored else None,
        "pass_rate_tight": (n_tight / scored) if scored else None,
        "pass_at_k": (jobs_with_pass / len(by_job)) if by_job else None,
        "by_level": by_level,
        "prompt_tokens": sum_in,
        "completion_tokens": sum_out,
        "total_tokens": sum_in + sum_out,
        "tokens_per_correct": ((sum_in + sum_out) / n_pass)
        if n_pass else None,
        "prompt_per_correct": (sum_in / n_pass) if n_pass else None,
        "completion_per_correct": (sum_out / n_pass) if n_pass else None,
        "seconds_per_answer": {
            "median": statistics.median(per_answer) if per_answer else None,
            "mean": (sum(per_answer) / len(per_answer))
            if per_answer else None,
        },
        "wall_seconds": wall_seconds,
        "cold_start_s": cold_start_s,
        "dollars_per_correct": dollars,
        "server": server_info or {},
        "k": k,
        "workers": workers,
        "budget": budget,
        "budget_stopped": budget_stopped,
        "skipped": skipped,
    }
    if extra:
        summary.update(extra)
    if exam == "factory":
        rate = summary["pass_rate"] or 0.0
        summary["dev_gate"] = "GO" if rate >= DEV_GATE_RATE else "STOP"
    return summary


def dev_gate_line(summary):
    """The PLAN step-5 gate line for a dev (factory) summary."""
    rate = summary.get("pass_rate")
    pct = "n/a" if rate is None else "%.1f%%" % (100.0 * rate)
    gate = summary.get("dev_gate", "GO" if (rate or 0.0) >= DEV_GATE_RATE
                       else "STOP")
    return "DEV GATE (PLAN step 5): dev %s at 0.2%% -> %s" % (pct, gate)


def build_report(summary):
    """report.md for one FT or BX session."""
    arm = summary.get("arm", "?")
    lines = ["# Final-exam report: arm %s" % arm, ""]
    lines.append("Grader: %s" % summary.get("grader", "?"))
    lines.append("Status: %s" % summary.get("status", "?"))

    def _pct(rate):
        return "n/a" if rate is None else "%.1f%%" % (100.0 * rate)

    lines.append("Pass rate at 0.2%% (decision): %s (%d/%d)" % (
        _pct(summary.get("pass_rate")), summary.get("PASS", 0),
        summary.get("PASS", 0) + summary.get("FAIL", 0)))
    lines.append("Pass rate at 1e-6 (reference): %s" % _pct(
        summary.get("pass_rate_tight")))
    lines.append("pass@%s: %s" % (summary.get("k", "?"),
                                   _pct(summary.get("pass_at_k"))))
    for level, sub in (summary.get("by_level") or {}).items():
        lines.append("Level %s: %s at 0.2%%, %s at 1e-6 (n=%d)" % (
            level, _pct(sub.get("pass_rate")),
            _pct(sub.get("pass_rate_tight")), sub.get("n", 0)))
    lines.append("Tokens per correct part: %s (prompt %s + completion %s)"
                 % (summary.get("tokens_per_correct"),
                    summary.get("prompt_per_correct"),
                    summary.get("completion_per_correct")))
    secs = summary.get("seconds_per_answer") or {}
    lines.append("Seconds per answer: median %s, mean %s" % (
        secs.get("median"), secs.get("mean")))
    lines.append("Arm wall-clock: %ss; $ per correct part: %s" % (
        summary.get("wall_seconds"), summary.get("dollars_per_correct")))
    digest = (summary.get("server") or {}).get("image_digest")
    lines.append("vLLM image digest: %s" % (digest or "unknown"))
    if summary.get("grader") == "factory":
        lines.append("")
        lines.append(dev_gate_line(summary))
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------- suites


def _cold_start_s(wall_start, gpu_start):
    """Session cold start: runner start minus the session GPU start (the
    deploy + ready wait). 0 without --gpu-start."""
    if gpu_start is None:
        return 0.0
    try:
        return round(max(0.0, wall_start - float(gpu_start)), 3)
    except (TypeError, ValueError):
        return 0.0


def run_pairs(pairs, call_one, out_dir, arm, exam, budget, gpu_start,
              workers, server_info, k, extra=None):
    """Run (job, rep) pairs with `workers` threads, appending each answer
    to calls.jsonl live under a lock. Stops sending NEW calls once the
    money left is at/below the reserve; in-flight answers drain.

    `call_one(job, rep)` returns (final_record, extra_round_records).
    Returns (finals, summary)."""
    os.makedirs(out_dir, exist_ok=True)
    wall_start = time.time()
    t_start = time.monotonic()
    cold = _cold_start_s(wall_start, gpu_start)
    calls_path = os.path.join(out_dir, "calls.jsonl")
    lock = threading.Lock()
    finals = [None] * len(pairs)
    budget_stopped = False

    def _write(rec):
        with lock:
            with open(calls_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")

    def _one(idx):
        job, rep = pairs[idx]
        try:
            final, rounds = call_one(job, rep)
        except Exception as e:  # noqa: BLE001 -- never lose a slot
            final = {
                "job": job["id"],
                "rep": rep,
                "sample": rep,
                "level": job.get("level"),
                "arm": arm,
                "grader": exam,
                "verdict": "INVALID",
                "tight": "INVALID",
                "outcome": "INVALID",
                "fails": [],
                "measurements": None,
                "run_error": "runner error: %r" % (e,),
            }
            rounds = []
        for rnd in rounds:
            _write(rnd)
        _write(final)
        return final

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=workers) as pool:
        in_flight = {}
        next_i = 0
        while next_i < len(pairs) or in_flight:
            while next_i < len(pairs) and len(in_flight) < workers:
                if out_of_money(budget, gpu_start or wall_start):
                    budget_stopped = True
                    break
                in_flight[pool.submit(_one, next_i)] = next_i
                next_i += 1
            if budget_stopped and not in_flight:
                break
            if not in_flight:
                break
            done, _ = concurrent.futures.wait(
                in_flight, return_when=concurrent.futures.FIRST_COMPLETED)
            for fut in done:
                finals[in_flight.pop(fut)] = fut.result()
            if budget_stopped:
                while in_flight:
                    done, _ = concurrent.futures.wait(
                        in_flight,
                        return_when=concurrent.futures.FIRST_COMPLETED)
                    for fut in done:
                        finals[in_flight.pop(fut)] = fut.result()
                break
    sent = [r for r in finals if r is not None]
    skipped = len(finals) - len(sent)
    wall_seconds = round(time.monotonic() - t_start, 3)
    summary = summarize_arm(sent, arm, exam, wall_seconds, cold,
                            server_info, k, workers, budget,
                            budget_stopped, skipped, extra=extra)
    with open(os.path.join(out_dir, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(out_dir, "report.md"), "w",
              encoding="utf-8") as f:
        f.write(build_report(summary))
    return sent, summary


def run_ft_suite(jobs, out_dir, endpoint, model, key, exam, post_fn,
                 sleep_fn, exec_fn, grade_fn, server_info_fn=None,
                 k=3, workers=8, budget=5.0, gpu_start=None, arm=FT_ARM):
    """Arm FT (or the base control arm A) over jobs x k reps. Returns
    (records, summary)."""
    secrets = [key] if key else []
    server_info = (server_info_fn or
                   (lambda: fetch_server_info(endpoint, key)))()
    pairs = [(job, rep) for job in jobs for rep in range(k)]

    def _call(job, rep):
        rec = do_ft_call(job, model, endpoint, secrets, exam, post_fn,
                         sleep_fn, exec_fn, grade_fn, rep=rep, arm=arm)
        return rec, []

    return run_pairs(pairs, _call, out_dir, arm, exam, budget,
                     gpu_start, workers, server_info, k)


def bx_finals_in(records):
    """BX final records only (per-round records have bx_final False;
    other arms' records have no bx_final key)."""
    return [r for r in records
            if r.get("arm") == BX_ARM and r.get("bx_final") is True]


def rep_of(rec):
    """The rep index of a record (baseline calls it sample)."""
    try:
        return int(rec.get("sample", rec.get("rep", 0)))
    except (TypeError, ValueError):
        return 0


def missing_bx_pairs(baseline_dir, exam_jobs, k=3):
    """(job, rep) pairs with no BX final record in the baseline dir.

    `exam_jobs`: the exam job dicts (id/text/level) by id. Returns
    ([(job, rep)], present) where present maps (job_id, rep) -> record.
    """
    with open(os.path.join(baseline_dir, "calls.jsonl"),
              encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    present = {}
    for rec in bx_finals_in(records):
        present[(rec.get("job"), rep_of(rec))] = rec
    by_id = {j["id"]: j for j in exam_jobs}
    missing = []
    for job_id in sorted(by_id):
        for rep in range(k):
            if (job_id, rep) not in present:
                missing.append((by_id[job_id], rep))
    return missing, present


def run_bx_fill(baseline_dir, exam_jobs, out_dir, endpoint, model, key,
                manual_text, post_fn, sleep_fn, exec_fn, grade_fn,
                server_info_fn=None, workers=12, k=3, budget=1.0,
                gpu_start=None, hint_text=None, examples=None):
    """Run only the missing BX (job, rep) pairs. Returns
    (finals, summary, missing). Fewer finals than missing pairs means
    the session ended INCOMPLETE (exit 3 in main)."""
    secrets = [key] if key else []
    server_info = (server_info_fn or
                   (lambda: fetch_server_info(endpoint, key)))()
    missing, _present = missing_bx_pairs(baseline_dir, exam_jobs, k)

    def _call(job, rep):
        rec = do_bx_cloud_call(job, model, endpoint, secrets, manual_text,
                               post_fn, sleep_fn, exec_fn, grade_fn,
                               exam="first-test", hint_text=hint_text,
                               examples=examples, rep=rep)
        return rec, list(rec.get("bx_rounds") or [])

    extra = {"fill_missing_from": os.path.abspath(baseline_dir),
             "n_missing": len(missing)}
    if not missing:
        sent, summary = [], summarize_arm(
            [], BX_ARM, "first-test", 0.0,
            _cold_start_s(time.time(), gpu_start), server_info, k,
            workers, budget, False, 0, extra=extra)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "summary.json"), "w",
                  encoding="utf-8") as f:
            json.dump(summary, f, indent=1)
        with open(os.path.join(out_dir, "report.md"), "w",
                  encoding="utf-8") as f:
            f.write(build_report(summary))
        return sent, summary, missing
    sent, summary = run_pairs([(j, r) for j, r in missing], _call,
                              out_dir, BX_ARM, "first-test", budget,
                              gpu_start, workers, server_info, k,
                              extra=extra)
    finals = [r for r in sent if r.get("bx_final") is True]
    if len(finals) < len(missing):
        missing_ids = sorted({j["id"] for j, _r in missing})
        have = {(r.get("job"), rep_of(r)) for r in finals}
        still = sorted("%s rep %d" % (j["id"], r)
                       for j, r in missing
                       if (j["id"], r) not in have)
        summary["status"] = "INCOMPLETE"
        summary["still_missing"] = still
        summary["missing_jobs"] = missing_ids
        with open(os.path.join(out_dir, "summary.json"), "w",
                  encoding="utf-8") as f:
            json.dump(summary, f, indent=1)
        with open(os.path.join(out_dir, "report.md"), "w",
                  encoding="utf-8") as f:
            f.write(build_report(summary) +
                    "\nINCOMPLETE: ask the user\n")
    return sent, summary, missing


# ------------------------------------------------------- CLI


def load_factory_jobs_file(path):
    """Dev jobs file (id, family, text, reference): {id, text, family}."""
    with open(path, encoding="utf-8") as f:
        jobs = [json.loads(line) for line in f if line.strip()]
    out = []
    for job in jobs:
        if not job.get("id") or not job.get("text"):
            raise ValueError("jobs file %r has a record without id/text"
                             % (path,))
        out.append({"id": job["id"], "text": job["text"],
                    "family": job.get("family")})
    return out


def _real_post_fn(endpoint_to_key):
    """POST one chat-completions body with urllib (stdlib only)."""
    def _post(endpoint_arg, body_arg, timeout_arg):
        endpoint_url, key = endpoint_to_key(endpoint_arg)
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trained arm FT + "
                                     "BX finisher on the cloud box.")
    parser.add_argument("--jobs", choices=("dry", "main"), default=None)
    parser.add_argument("--jobs-file", default=None,
                        help="factory dev jobs file (exam factory)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--arms", default=FT_ARM,
                        help="comma list of FT,A,BX (default FT; exactly "
                             "one serving arm (FT|A) per run, or --arms BX "
                             "with --fill-missing)")
    parser.add_argument("--fill-missing", default=None, metavar="DIR",
                        help="baseline dir whose missing BX (job, rep) "
                             "pairs to run (needs --arms BX)")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--workers", type=int, default=None,
                        help="workers (default 8; 12 for --fill-missing)")
    parser.add_argument("--budget", type=float, default=5.0)
    parser.add_argument("--gpu-start", type=float, default=None)
    args = parser.parse_args(argv)
    if args.workers is not None and args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.k is not None and args.k < 1:
        parser.error("--k must be >= 1")
    arms = tuple(p.strip() for p in str(args.arms).split(",") if p.strip())
    if not arms:
        parser.error("no arms requested (expected comma list of FT,BX)")
    for arm in arms:
        if arm not in VALID_FINAL_ARMS:
            parser.error("unknown arm %r (this runner runs FT,BX)" % (arm,))
    if args.fill_missing is not None:
        if arms != (BX_ARM,):
            parser.error("--fill-missing needs --arms BX")
        if args.workers is None:
            args.workers = 12
    if args.workers is None:
        args.workers = 8
    if args.fill_missing is None and args.jobs is None \
            and args.jobs_file is None:
        parser.error("need --jobs dry|main or --jobs-file <file> "
                     "(or --fill-missing <dir> with --arms BX)")

    # Keys first: missing keys exit 2 naming the variable, before any
    # network, Modal run or model call.
    forge_url = os.environ.get("FORGE_URL", "")
    forge_key = os.environ.get("FORGE_KEY", "")
    glimmer_url = os.environ.get("GLIMMER_URL", "")
    glimmer_key = os.environ.get("GLIMMER_KEY", "")
    need = []
    if FT_ARM in arms and args.fill_missing is None:
        need += [("FORGE_URL", forge_url), ("FORGE_KEY", forge_key)]
    if A_ARM in arms:
        need += [("GLIMMER_URL", glimmer_url),
                 ("GLIMMER_KEY", glimmer_key)]
    if BX_ARM in arms:
        need += [("GLIMMER_URL", glimmer_url),
                 ("GLIMMER_KEY", glimmer_key)]
    missing = [name for name, val in need if not val]
    if missing:
        parser.error("missing environment variables: " + ", ".join(missing))

    if cloud_cq is None or getattr(cloud_cq, "modal", None) is None:
        print("modal is not installed in the forge venv; "
              "runner_final.py needs it to reach the cloud box and "
              "grader.", file=sys.stderr)
        return 2

    if args.fill_missing is not None:
        jobs, _expected, manual_text = runner.load_inputs()
        endpoint = runner.arm_endpoint(BX_ARM, glimmer_url)
        model = runner.arm_model(BX_ARM)
        post_fn = _real_post_fn(lambda _e: (endpoint, glimmer_key))
        with cloud_cq.modal.enable_output():
            with cloud_cq._app.run():
                _sent, _summary, missing_pairs = run_bx_fill(
                    args.fill_missing, jobs, args.out, endpoint, model,
                    glimmer_key, manual_text,
                    post_fn=post_fn, sleep_fn=time.sleep,
                    exec_fn=lambda code: cloud_cq.run_answer_in_box(code),
                    grade_fn=lambda exam, jid, brep: cloud_cq.grade.remote(
                        exam, jid, brep),
                    workers=args.workers, k=args.k, budget=args.budget,
                    gpu_start=args.gpu_start)
        finals = [r for r in _sent if r.get("bx_final") is True]
        if len(finals) < len(missing_pairs):
            print("INCOMPLETE: ask the user")
            return 3
        print("BX FILL complete: %d/%d final records" % (
            len(finals), len(missing_pairs)))
        return 0

    if args.jobs_file is not None:
        jobs = load_factory_jobs_file(args.jobs_file)
        exam = "factory"
    else:
        all_jobs, _expected, _manual = runner.load_inputs()
        if args.jobs == "dry":
            jobs = [j for j in all_jobs if j.get("level") == "dry"]
        else:
            jobs = [j for j in all_jobs
                    if j.get("level") in ("medium", "hard")]
        exam = "first-test"
        if not jobs:
            parser.error("no jobs for --jobs %s" % args.jobs)
    # One serving arm per run: FT (trained model) or A (base Glimmer
    # control, round 3: same short prompt and body as FT, served by
    # deploy/modal_glimmer.py with the same vLLM flags).
    serving = [a for a in arms if a in (FT_ARM, A_ARM)]
    if len(serving) != 1:
        parser.error("need exactly one serving arm (FT|A), got %r "
                     "(--arms BX needs --fill-missing)" % (arms,))
    if serving == [A_ARM]:
        endpoint = glimmer_url.rstrip("/") + "/v1/chat/completions"
        run_key, run_model, run_arm = glimmer_key, A_MODEL, A_ARM
    else:
        endpoint = forge_url.rstrip("/") + "/v1/chat/completions"
        run_key, run_model, run_arm = forge_key, FT_MODEL, FT_ARM
    post_fn = _real_post_fn(lambda _e: (endpoint, run_key))
    with cloud_cq.modal.enable_output():
        with cloud_cq._app.run():
            _records, summary = run_ft_suite(
                jobs, args.out, endpoint, run_model, run_key, exam,
                post_fn=post_fn, sleep_fn=time.sleep,
                exec_fn=lambda code: cloud_cq.run_answer_in_box(code),
                grade_fn=lambda exam_arg, jid, brep: cloud_cq.grade.remote(
                    exam_arg, jid, brep),
                k=args.k, workers=args.workers, budget=args.budget,
                gpu_start=args.gpu_start, arm=run_arm)
    print("%s %s: %d answers, pass rate at 0.2%%: %s" % (
        run_arm, exam, summary.get("n", 0), summary.get("pass_rate")))
    if exam == "factory":
        print(dev_gate_line(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
