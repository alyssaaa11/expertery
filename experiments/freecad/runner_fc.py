#!/usr/bin/env python3
"""FreeCAD gap-test runner (arms G and S, W escalation): SPEC sections 3-4.

Reuses the frozen first-test runner (experiments/first-test/runner.py):
Glimmer/Baseten request code and retry, code extraction, the budget
guard, k and workers handling are imported, never copy-pasted. Only the
FreeCAD specifics live here: the Part system prompt, the frozen manual
(refused when its sha256 changes), the manual+job messages, cloud
execution (cloud_exec Modal Sandbox -> STEP bytes -> cloud_grade Modal
Function), the G/S/W arms, failure tags, and the PLAN decision rules.

0.2% is the verdict (the baseline's yardstick); 1e-6 is also recorded.
Nothing from the model runs on the Mac; the Mac only coordinates and
writes logs. Up to 8 sandboxes run in parallel.

CLI: runner_fc.py --jobs main --out <dir> --arms G,S --k 1 --workers 8
  --budget <$> --budget-c <$> [--budget-w <$>] [--escalate-from <S run dir>]
  [--w-smoke] [--w-endpoint <url>]
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
_FT = os.path.join(os.path.dirname(HERE), "first-test")
if _FT not in sys.path:
    sys.path.insert(0, _FT)
import runner  # noqa: E402  (frozen file; imported, not modified)

from cloud_exec import run_answer_in_box  # noqa: E402
from cloud_grade import grade_result  # noqa: E402

FC_SYSTEM_PROMPT = (
    "You write FreeCAD Python code using the Part module "
    "(import FreeCAD as App, Part). Units are millimetres. "
    "Assign the final solid (a Part.Shape) to a variable named result. "
    "Reply with exactly one Python code block and nothing else."
)
FC_MANUAL_PREFIX = "Here is the FreeCAD manual. Use it.\n\n"
FROZEN_MANUAL_SHA256 = (
    "865ab9af45eb2fb554f97155fa8f3cf44f92d54973437a1f94c78d67cdc89bb6"
)
MANUAL_PATH = os.path.join(HERE, "manual.md")

# Arms. G = Glimmer (same body as first-test arm B); S = Spark Open on
# Baseten (same sampling, x-session-affinity header, cached_tokens
# logged); W = Muse Wonder, run only on jobs S failed.
VALID_ARMS = ("G", "S", "W")
GLIMMER_ARMS = ("G",)
SPARK_MODEL = runner.SPARK_MODEL  # meta-models/muse-spark-open-1026
WONDER_MODEL = "muse-wonder-1.0"
WONDER_URL = "https://api.meta.ai/v1/chat/completions"
WONDER_RESPONSES_PATH = "/v1/responses"

# Same sampling for every arm (SPEC: same body as arm B).
FC_MAX_TOKENS = runner.MAX_TOKENS  # 16000
FC_TEMPERATURE = runner.TEMPERATURE  # 1.0
FC_TOP_P = runner.TOP_P  # 0.95
FC_TOP_K = runner.TOP_K  # 64

CALL_TIMEOUT = runner.CALL_TIMEOUT
MAX_WORKERS = 8  # up to 8 sandboxes in parallel

# Wonder pricing: $20/M output, $4/M input, $0.20/M cached.
COST_W_OUT_PER_M = 20.0
COST_W_IN_PER_M = 4.0
COST_W_CACHED_PER_M = 0.20


class ManualChanged(RuntimeError):
    """Raised when the manual's sha256 differs from the frozen value."""


def load_manual(path=None):
    """Read the FreeCAD manual; refuse it when its sha256 changed.

    A changed manual changes the result, so the run stops instead.
    """
    with open(path or MANUAL_PATH, encoding="utf-8") as f:
        text = f.read()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != FROZEN_MANUAL_SHA256:
        raise ManualChanged(
            "manual sha256 %s != frozen %s; refusing to run"
            % (digest, FROZEN_MANUAL_SHA256))
    return text


def build_messages(job_text, manual_text):
    """System + manual-as-first-user-message + job-as-second-user-message
    (the arm-B layout, tool swapped to FreeCAD)."""
    return [
        {"role": "system", "content": FC_SYSTEM_PROMPT},
        {"role": "user", "content": FC_MANUAL_PREFIX + manual_text},
        {"role": "user", "content": job_text},
    ]


def build_body_fc(model, messages):
    """The arm-B request body (imported, not reimplemented)."""
    return runner.build_body(model, messages)


# ------------------------------------------------------------ HTTP per arm


def real_post_fn_fc(endpoint, key, extra_headers=None, timeout=CALL_TIMEOUT):
    """POST one chat-completions body (stdlib only) with extra headers."""
    headers = dict(extra_headers or {})

    def _post(endpoint_arg, body_arg, timeout_arg):
        req = urllib.request.Request(
            endpoint_arg,
            data=json.dumps(body_arg).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
                **headers,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_arg) as resp:
            return json.load(resp)

    return _post


def arm_endpoint(arm, glimmer_url, w_endpoint=WONDER_URL):
    if arm == "G":
        return glimmer_url.rstrip("/") + "/v1/chat/completions"
    if arm == "S":
        return runner.BASETEN_URL
    if arm == "W":
        return w_endpoint
    raise ValueError("unknown arm %r" % (arm,))


def arm_model(arm):
    if arm == "G":
        return runner.GLIMMER_MODEL
    if arm == "S":
        return SPARK_MODEL
    if arm == "W":
        return WONDER_MODEL
    raise ValueError("unknown arm %r" % (arm,))


def default_post_fns(arm_cfgs, key_map, affinity):
    """Per-arm post functions: S carries x-session-affinity; W falls back
    from /v1/chat/completions to /v1/responses when refused."""

    def _post(endpoint_arg, body_arg, timeout_arg):
        arm = None
        for name, cfg in arm_cfgs.items():
            if cfg["endpoint"] == endpoint_arg:
                arm = name
                break
        key = key_map.get(arm, "")
        if arm == "S":
            return real_post_fn_fc(
                endpoint_arg, key,
                {"x-session-affinity": affinity})(endpoint_arg, body_arg,
                                                  timeout_arg)
        if arm == "W":
            try:
                return real_post_fn_fc(endpoint_arg, key)(
                    endpoint_arg, body_arg, timeout_arg)
            except urllib.error.HTTPError as e:
                if e.code in (404, 405) and endpoint_arg.endswith(
                        "/v1/chat/completions"):
                    fallback = endpoint_arg[: -len("/v1/chat/completions")] \
                        + WONDER_RESPONSES_PATH
                    return real_post_fn_fc(fallback, key)(
                        fallback, body_arg, timeout_arg)
                raise
        return runner.real_post_fn(endpoint_arg, key)(
            endpoint_arg, body_arg, timeout_arg)

    return _post


# ------------------------------------------------------- failure tags


def tag_failure(finish_reason, content, run_error, built, fails):
    """One of api_error / wrong_geometry / INVALID (PLAN failure tags).

    api_error: the answer raised during the run (AttributeError,
    TypeError, NameError, Part errors, timeout, memory limit,
    PermissionError, refused import, no network in the box) or never
    assigned `result` (a missing variable is an API-knowledge miss, not
    a built-but-wrong shape).
    wrong_geometry: it built but failed the checker, or `result` was not
    a Part solid. A reply cut off by the token limit is INVALID.
    """
    if finish_reason == "length":
        return "INVALID"
    if not content or not content.strip():
        return "INVALID"
    err = run_error or ""
    if "no variable named 'result'" in err:
        return "api_error"
    if "not a Part solid" in err:
        return "wrong_geometry"
    if built and fails:
        return "wrong_geometry"
    if built and not fails:
        return ""
    if err:
        return "api_error"
    return "wrong_geometry"


def outcome_of(finish_reason, content, call_error):
    """INVALID for cut-offs, empty replies, and failed calls after the
    retry (as in the baseline); else None (the box + grader decide)."""
    if call_error is not None:
        return "INVALID"
    if finish_reason == "length":
        return "INVALID"
    if not content or not content.strip():
        return "INVALID"
    return None


# ------------------------------------------------------- Wonder money


def cost_w_of_usage(usage):
    """Wonder $: reasoning tokens are billed as output (same completion
    count); cached input at $0.20/M."""
    usage = usage or {}
    try:
        prompt = float(usage.get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt = 0.0
    try:
        completion = float(usage.get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion = 0.0
    try:
        cached = float(usage.get("cached_tokens", 0) or 0)
    except (TypeError, ValueError):
        cached = 0.0
    return (prompt * COST_W_IN_PER_M + completion * COST_W_OUT_PER_M
            + cached * COST_W_CACHED_PER_M) / 1e6


def cost_w_total(w_usages):
    return sum(cost_w_of_usage(u) for u in w_usages)


def over_budget_w(w_usages, budget_w):
    return cost_w_total(w_usages) > budget_w


def cached_tokens_of(usage):
    try:
        return int((usage or {}).get("cached_tokens", 0) or 0)
    except (TypeError, ValueError):
        return 0


# ------------------------------------------------------- PLAN decision


def pass_job_ids(records, arm):
    return {r["job"] for r in records
            if r.get("arm") == arm and r.get("outcome") == "PASS"}


def fail_records(records, arm):
    return [r for r in records
            if r.get("arm") == arm and r.get("outcome") == "FAIL"]


def api_error_share(records, arm):
    """Share of arm's FAILs tagged api_error (PLAN rule 4 needs >= 60%)."""
    fails = fail_records(records, arm)
    if not fails:
        return 0.0
    n_api = sum(1 for r in fails if r.get("failure_tag") == "api_error")
    return n_api / len(fails)


HARNESS_GATE = 0.05  # PLAN rule 6: harness/INVALID over 5% → RUN INVALID


def harness_invalid_share(records, arm):
    """Share of an arm's answers tagged harness or outcome INVALID."""
    arm_recs = [r for r in records if r.get("arm") == arm]
    if not arm_recs:
        return 0.0
    bad = sum(1 for r in arm_recs
              if r.get("failure_tag") == "harness"
              or r.get("outcome") == "INVALID")
    return bad / len(arm_recs)


def run_invalid_arms(records):
    """{arm: share} for arms over the PLAN rule 6 gate (empty when clean)."""
    arms = sorted({r.get("arm") for r in records})
    return {arm: harness_invalid_share(records, arm) for arm in arms
            if harness_invalid_share(records, arm) > HARNESS_GATE}


def decide_one(rate_g, rate_x, wins_x_not_g, api_share_g):
    """PLAN rules 1-4 for one teacher rate (T or S alone).

    1. X < 70% -> RUN INVALID for FreeCAD: stay on CadQuery.
    2. G <= 60% AND X >= 75% AND X-G >= 20pts AND >= 8 wins ->
       FreeCAD target. 3. G >= 75% -> stay on hard CadQuery jobs.
    4. Grey: default stay on CadQuery; FreeCAD only if api_error >= 60%
       of G's FAILs AND >= 6 wins.
    """
    if rate_x is None:
        return "INVALID (no scored calls)"
    if rate_x < 0.70:
        return "stay on CadQuery (RUN INVALID for FreeCAD: teacher < 70%)"
    if rate_g is not None:
        if (rate_g <= 0.60 and rate_x >= 0.75
                and round(rate_x * 100) - round(rate_g * 100) >= 20
                and wins_x_not_g >= 8):
            return "FreeCAD target"
        if rate_g >= 0.75:
            return "stay on hard CadQuery jobs"
    if api_share_g >= 0.60 and wins_x_not_g >= 6:
        return "FreeCAD target"
    return "stay on CadQuery (grey zone)"


def teacher_pass_ids(records):
    """T = S ∪ W-rescues per job (S INVALID jobs are never escalated, so
    a W PASS only counts where S ran and failed)."""
    t = set(pass_job_ids(records, "S"))
    s_failed = {r["job"] for r in records
                if r.get("arm") == "S" and r.get("outcome") == "FAIL"}
    for r in records:
        if (r.get("arm") == "W" and r.get("outcome") == "PASS"
                and r.get("job") in s_failed):
            t.add(r["job"])
    return t


def wonder_share(records):
    """Share of T's passes that needed a Wonder rescue."""
    t = teacher_pass_ids(records)
    if not t:
        return 0.0
    s_pass = pass_job_ids(records, "S")
    return (len(t - s_pass) / len(t)) if t else 0.0


def evaluate_fc_decision(records):
    """PLAN rules 5+6: rules 1-4 evaluated on BOTH T and S alone, then
    the harness gate.

    Returns {"decision_t", "decision_s", "agree", "decision",
    "wonder_share", "run_invalid", "run_invalid_arms"}. On disagreement
    the report says "FreeCAD target only with Wonder escalation (closed
    API)" and the user decides. When harness errors or INVALID answers
    exceed 5% of any arm's answers (rule 6), the decision is RUN INVALID
    no matter what rules 1-4 say: a broken box must not read as a model
    gap. The rule-5 disagreement label is unchanged (user, 2026-10-29).
    """
    g_ids = pass_job_ids(records, "G")
    s_ids = pass_job_ids(records, "S")
    t_ids = teacher_pass_ids(records)
    jobs = set()
    for arm in ("G", "S"):
        jobs.update(r["job"] for r in records if r.get("arm") == arm)
    # n = 30 jobs at k = 1: every rate is the share of jobs with a pass,
    # so T-vs-G gaps are comparable (pass@1 for G and S, S-plus-rescues
    # for T; S INVALID jobs stay INVALID and are never escalated).
    n = len(jobs) or 1
    rate_g = (len(g_ids) / n) if n else None
    rate_t = (len(t_ids) / n) if n else None
    rate_s = (len(s_ids) / n) if n else None
    api_g = api_error_share(records, "G")
    decision_t = decide_one(rate_g, rate_t, len(t_ids - g_ids), api_g)
    decision_s = decide_one(rate_g, rate_s, len(s_ids - g_ids), api_g)
    agree = ((decision_t == "FreeCAD target") ==
             (decision_s == "FreeCAD target"))
    if agree:
        decision = decision_t
    else:
        decision = ("FreeCAD target only with Wonder escalation "
                    "(closed API)")
    bad_arms = run_invalid_arms(records)
    if bad_arms:
        decision = "RUN INVALID"
    return {
        "decision_t": decision_t,
        "decision_s": decision_s,
        "agree": agree,
        "decision": decision,
        "wonder_share": round(wonder_share(records), 3),
        "rate_g": rate_g,
        "rate_t": rate_t,
        "rate_s": rate_s,
        "run_invalid": bool(bad_arms),
        "run_invalid_arms": {a: round(s, 3)
                             for a, s in sorted(bad_arms.items())},
    }


# ------------------------------------------------------- one (job, arm)


def default_exec_fn(answer_code):
    """Real box call (needs modal). Tests inject a fake instead."""
    return run_answer_in_box(answer_code)


def default_grade_fn(job_id, step_bytes):
    """Real grader call (needs modal). Tests inject a fake instead."""
    from cloud_grade import grade as _grade  # noqa: E402

    return _grade.remote(job_id, bytes(step_bytes))


def do_fc_call(job, arm, model, endpoint, secrets, manual_text, post_fn,
               sleep_fn, exec_fn, grade_fn,
               call_timeout=CALL_TIMEOUT, affinity=None):
    """Run one (job, arm) pair exactly once: POST (one retry on network /
    HTTP 5xx/429, imported), extract the code, run it in the cloud box,
    grade the STEP. Never raises for a bad answer; a failed call after
    the retry is INVALID, never FAIL. Any exception from the box (Sandbox
    create / exec / filesystem) or the grader is a harness failure:
    outcome INVALID, tag `harness`, error text kept. The one exception is
    an answer that writes no STEP: that is the answer's failure (FAIL),
    with run_one_fc's ERROR line as run_error."""
    import datetime as _dt

    body = build_body_fc(model, build_messages(job["text"], manual_text))
    start = (_dt.datetime.now(_dt.timezone.utc)
             .isoformat(timespec="milliseconds").replace("+00:00", "Z"))
    t0 = time.monotonic()
    content, finish_reason, usage = "", None, {}
    reasoning_len, cached = 0, 0
    outcome = fails = measurements = code = run_error = None
    failure_tag, grade_tight = "", None
    call_error, built = None, False
    latency = 0.0
    try:
        t_call = time.monotonic()
        data = runner.post_with_retry(post_fn, endpoint, body, call_timeout,
                                      sleep_fn)
        latency = time.monotonic() - t_call
        content, finish_reason, usage, reasoning_len = runner.parse_response(
            data)
        cached = cached_tokens_of(usage)
        invalid = outcome_of(finish_reason, content, None)
        if invalid is not None:
            outcome, fails = invalid, []
            code, run_error = "", "cut off by the token limit" \
                if finish_reason == "length" else "empty reply"
            failure_tag = "INVALID"
        else:
            code = runner.extract_code(content)
            if not code or not code.strip():
                outcome, fails = "INVALID", []
                run_error, failure_tag = "empty reply", "INVALID"
            else:
                try:
                    boxed = exec_fn(code)
                except Exception as e:  # noqa: BLE001 -- box down: harness
                    outcome, fails = "INVALID", []
                    run_error = "harness: %s: %s" % (type(e).__name__, e)
                    failure_tag, built = "harness", False
                else:
                    if boxed is None or boxed.get("step_bytes") is None:
                        # The answer wrote no STEP: its own failure, with
                        # run_one_fc's ERROR line as run_error.
                        outcome, fails = "FAIL", []
                        built = False
                        run_error = (boxed or {}).get("run_error") or \
                            "the answer wrote no STEP"
                        failure_tag = tag_failure(finish_reason, content,
                                                  run_error, built, fails)
                    else:
                        try:
                            graded = grade_fn(job["id"], boxed["step_bytes"])
                        except Exception as e:  # noqa: BLE001 -- grader down
                            outcome, fails = "INVALID", []
                            run_error = "harness: %s: %s" % (
                                type(e).__name__, e)
                            failure_tag, built = "harness", False
                        else:
                            built = True
                            measurements = graded.get("measurements")
                            grade_tight = graded.get("tight")
                            if graded.get("verdict") == "PASS":
                                outcome, fails = "PASS", []
                                failure_tag = ""
                            else:
                                outcome = "FAIL"
                                fails = list(graded.get("fails") or [])
                                failure_tag = tag_failure(
                                    finish_reason, content, run_error,
                                    built, fails)
    except Exception as e:  # noqa: BLE001 -- failed call => INVALID record
        call_error = "%s: %s" % (type(e).__name__, e)
        outcome, fails, measurements, code = "INVALID", [], None, ""
        run_error, failure_tag = call_error, "INVALID"
    seconds = time.monotonic() - t0
    end = runner.utcnow_iso()
    run_error = runner.scrub(run_error, secrets)
    if run_error and len(run_error) > runner.RUN_ERROR_TAIL:
        run_error = run_error[-runner.RUN_ERROR_TAIL:]
    return {
        "job": job["id"],
        "level": job.get("level"),
        "arm": arm,
        "model": model,
        "start": start,
        "end": end,
        "seconds": round(seconds, 3),
        "latency": round(latency, 3),
        "finish_reason": finish_reason,
        "usage": usage,
        "cached_tokens": cached,
        "content": content,
        "reasoning_len": reasoning_len,
        "code": code,
        "extracted_code": code,
        "outcome": outcome,
        "fails": fails or [],
        "failed_checks": fails or [],
        "measurements": measurements,
        "tight": grade_tight,
        "run_error": run_error,
        "failure_tag": failure_tag,
    }


# ------------------------------------------------------- suite + outputs


def gpu_elapsed_s(t_start_mono, gpu_start):
    """GPU seconds for the money estimate: since the session's GPU start
    when given (the whole-session cap covers deploy + ready waits), else
    the runner's own wall clock."""
    if gpu_start is None:
        return time.monotonic() - t_start_mono
    try:
        return max(0.0, time.time() - float(gpu_start))
    except (TypeError, ValueError):
        return time.monotonic() - t_start_mono


def estimate_total_fc(s_usages, w_usages, elapsed_s):
    """Running estimate: S tokens (Baseten rate) + W tokens (Meta rate) +
    one shared GPU cost for the run's wall-clock time."""
    return (sum(runner.cost_c_of_usage(u) for u in s_usages)
            + cost_w_total(w_usages)
            + runner.gpu_cost_of_elapsed(elapsed_s))


def over_budget_fc(s_usages, w_usages, elapsed_s, budget):
    return estimate_total_fc(s_usages, w_usages, elapsed_s) > budget


def s_failed_job_ids(s_run_dir):
    """Job ids that FAILED in S's calls.jsonl (INVALID is not escalated)."""
    ids = []
    with open(os.path.join(s_run_dir, "calls.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("arm") == "S" and rec.get("outcome") == "FAIL":
                ids.append(rec.get("job"))
    return ids


def run_suite_fc(jobs, manual_text, out_dir, arm_cfgs, key_map,
                 budget=3.5, budget_c=3.0, budget_w=3.0,
                 arms=("G", "S"), k=1, workers=MAX_WORKERS,
                 post_fn=None, sleep_fn=time.sleep,
                 exec_fn=None, grade_fn=None, w_job_ids=None,
                 call_timeout=CALL_TIMEOUT, affinity=None, gpu_start=None):
    """Call every (job, arm) pair `k` times with `workers` threads.

    Arms run one after another with that many workers (up to 8 sandboxes
    in parallel), never mixed. New calls stop once the cost estimate
    passes `budget`; new S calls stop at `budget_c`, new W calls at
    `budget_w`. W runs only on `w_job_ids` (S's failed jobs). Writes
    calls.jsonl, summary.json and report.md into `out_dir`.
    """
    key_map = key_map or {}
    secrets = [v for v in key_map.values() if v]
    affinity = affinity or uuid.uuid4().hex[:8]
    if post_fn is None:
        post_fn = default_post_fns(arm_cfgs, key_map, affinity)
    exec_fn = exec_fn or default_exec_fn
    grade_fn = grade_fn or default_grade_fn
    os.makedirs(out_dir, exist_ok=True)
    pool_size = workers or MAX_WORKERS
    t_start = time.monotonic()
    s_usages, w_usages = [], []
    budget_stopped = budget_c_stopped = budget_w_stopped = False
    records = []
    arm_timing = {}
    for arm in arms:
        if arm == "W":
            arm_jobs = [j for j in jobs if j["id"] in set(w_job_ids or [])]
        else:
            arm_jobs = list(jobs)
        pairs = [(job, rep) for job in arm_jobs for rep in range(k)]
        arm_start = runner.utcnow_iso()
        arm_t0 = time.monotonic()
        arm_recs = [None] * len(pairs)
        next_i, in_flight = 0, {}
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=pool_size) as pool:
            while next_i < len(pairs) or in_flight:
                while next_i < len(pairs) and len(in_flight) < pool_size:
                    if over_budget_fc(s_usages, w_usages,
                                      gpu_elapsed_s(t_start, gpu_start),
                                      budget):
                        budget_stopped = True
                        break
                    if arm == "S" and runner.over_budget_c(s_usages, budget_c):
                        budget_c_stopped = True
                        next_i += 1
                        continue
                    if arm == "W" and over_budget_w(w_usages, budget_w):
                        budget_w_stopped = True
                        next_i += 1
                        continue
                    job, _rep = pairs[next_i]
                    cfg = arm_cfgs[arm]
                    fut = pool.submit(
                        do_fc_call, job, arm, cfg["model"],
                        cfg["endpoint"], secrets, manual_text, post_fn,
                        sleep_fn, exec_fn, grade_fn, call_timeout, affinity)
                    in_flight[fut] = next_i
                    next_i += 1
                if budget_stopped and not in_flight:
                    break
                if not in_flight:
                    break
                done, _ = concurrent.futures.wait(
                    in_flight,
                    return_when=concurrent.futures.FIRST_COMPLETED)
                for fut in done:
                    idx = in_flight.pop(fut)
                    job, _rep = pairs[idx]
                    try:
                        rec = fut.result()
                    except Exception as e:  # noqa: BLE001 -- never lose a slot
                        rec = {"job": job["id"], "level": job.get("level"),
                               "arm": arm, "model": arm_cfgs[arm]["model"],
                               "outcome": "INVALID", "fails": [],
                               "failed_checks": [], "measurements": None,
                               "run_error": runner.scrub(
                                   "runner error: %r" % (e,), secrets),
                               "failure_tag": "INVALID"}
                    arm_recs[idx] = rec
                    if arm == "S" and isinstance(rec.get("usage"), dict):
                        s_usages.append(rec["usage"])
                    if arm == "W" and isinstance(rec.get("usage"), dict):
                        w_usages.append(rec["usage"])
                if budget_stopped:
                    while in_flight:
                        done, _ = concurrent.futures.wait(
                            in_flight,
                            return_when=concurrent.futures.FIRST_COMPLETED)
                        for fut in done:
                            idx = in_flight.pop(fut)
                            try:
                                arm_recs[idx] = fut.result()
                            except Exception as e:  # noqa: BLE001
                                arm_recs[idx] = {
                                    "job": pairs[idx][0]["id"], "arm": arm,
                                    "outcome": "INVALID", "fails": [],
                                    "failure_tag": "INVALID",
                                    "run_error": "runner error: %r" % (e,)}
                    break
        arm_elapsed = time.monotonic() - arm_t0
        for (job, rep), rec in zip(pairs, arm_recs):
            if rec is not None:
                rec["sample"] = rep
            records.append(rec)
        arm_timing[arm] = {"start": arm_start, "end": runner.utcnow_iso(),
                           "seconds": round(arm_elapsed, 3)}
    elapsed = time.monotonic() - t_start
    sent = [r for r in records if r is not None]
    summary = build_fc_summary(sent, s_usages, w_usages, elapsed, budget,
                               budget_c, budget_w, budget_stopped,
                               budget_c_stopped, budget_w_stopped, arms, k,
                               pool_size, arm_timing)
    with open(os.path.join(out_dir, "calls.jsonl"), "w",
              encoding="utf-8") as f:
        for rec in sent:
            f.write(json.dumps(rec) + "\n")
    with open(os.path.join(out_dir, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(out_dir, "report.md"), "w",
              encoding="utf-8") as f:
        f.write(build_fc_report(summary))
    return sent, summary


def build_fc_summary(records, s_usages, w_usages, elapsed_s, budget,
                     budget_c, budget_w, budget_stopped, budget_c_stopped,
                     budget_w_stopped, arms, k=1, workers=None,
                     arm_timing=None):
    arm_timing = arm_timing or {}
    per_arm = {arm: runner.arm_stats(records, arm, extra=True, k=k)
               for arm in arms}
    levels = sorted({r.get("level") for r in records if r.get("level")})
    by_level = {}
    for level in levels:
        by_level[level] = {}
        for arm in arms:
            sub = [r for r in records if r.get("level") == level]
            by_level[level][arm] = runner.arm_stats(sub, arm, k=k)
    tags = {}
    for arm in arms:
        tags[arm] = {
            "api_error": sum(1 for r in records
                             if r.get("arm") == arm
                             and r.get("failure_tag") == "api_error"),
            "wrong_geometry": sum(1 for r in records
                                  if r.get("arm") == arm
                                  and r.get("failure_tag") == "wrong_geometry"),
            # Harness and INVALID are counted, never folded into the
            # pass rate (PLAN: PASS / (PASS + FAIL); rule 6 gates on
            # their share).
            "harness": sum(1 for r in records
                           if r.get("arm") == arm
                           and r.get("failure_tag") == "harness"),
            "INVALID": sum(1 for r in records
                           if r.get("arm") == arm
                           and r.get("outcome") == "INVALID"),
        }
    s_pass, g_pass = pass_job_ids(records, "S"), pass_job_ids(records, "G")
    cost_s = round(sum(runner.cost_c_of_usage(u) for u in s_usages), 4)
    cost_w = round(cost_w_total(w_usages), 4)
    gpu = round(runner.gpu_cost_of_elapsed(elapsed_s), 4)
    decision = evaluate_fc_decision(records)
    table = {}
    for rec in records:
        table.setdefault(rec["job"], {})[rec["arm"]] = rec.get("outcome")
    return {
        "arms": per_arm,
        "levels": by_level,
        "by_level": by_level,
        "failure_tags": tags,
        "jobs_passed_by_S_not_G": sorted(s_pass - g_pass),
        "n_calls": len(records),
        "budget": budget,
        "budget_stopped": budget_stopped,
        "budget_c": budget_c,
        "budget_c_stopped": budget_c_stopped,
        "budget_w": budget_w,
        "budget_w_stopped": budget_w_stopped,
        "elapsed_seconds": round(elapsed_s, 3),
        "costs": {"S_tokens": cost_s, "W_tokens": cost_w, "gpu": gpu,
                  "total": round(cost_s + cost_w + gpu, 4)},
        "tokens": {
            arm: {"input": per_arm[arm]["input_tokens"],
                  "output": per_arm[arm]["output_tokens"],
                  "total": per_arm[arm]["total_tokens"]}
            for arm in arms
        },
        "teacher_T_pass": sorted(teacher_pass_ids(records)),
        "wonder_share": decision["wonder_share"],
        "decision_t": decision["decision_t"],
        "decision_s": decision["decision_s"],
        "decision": decision["decision"],
        "agree_T_S": decision["agree"],
        "run_invalid": decision["run_invalid"],
        "run_invalid_arms": decision["run_invalid_arms"],
        "rate_g": decision["rate_g"],
        "rate_t": decision["rate_t"],
        "rate_s": decision["rate_s"],
        "table": table,
        "k": k,
        "workers": workers,
        "arm_timing": arm_timing,
    }


def build_fc_report(summary):
    arms = [a for a in summary["arms"]]
    lines = ["# FreeCAD gap-test report", ""]
    lines.append("Teacher T = S ∪ W-rescues per job "
                 "(S INVALID jobs are never escalated).")
    lines.append("Decision on T: **%s**" % summary["decision_t"])
    lines.append("Decision on S alone: **%s**" % summary["decision_s"])
    lines.append("Report decision: **%s**" % summary["decision"])
    lines.append("Wonder's share of T's passes: %.1f%%"
                 % (100.0 * summary["wonder_share"]))
    lines.append("Rates: G %.1f%%, T %.1f%%, S %.1f%%"
                 % (100 * (summary["rate_g"] or 0),
                    100 * (summary["rate_t"] or 0),
                    100 * (summary["rate_s"] or 0)))
    lines.append("")
    lines.append("## Per arm (PASS / FAIL / INVALID, pass rate)")
    lines.append("Pass rates are PASS / (PASS + FAIL); INVALID and harness "
                 "are counted, never folded in.")
    if summary.get("run_invalid"):
        lines.append("RUN INVALID: harness/INVALID over 5%% in %s"
                     % ", ".join(
                         "%s (%.1f%%)" % (a, 100 * shr)
                         for a, shr in sorted(
                             summary["run_invalid_arms"].items())))
    lines.append("| Arm | PASS | FAIL | INVALID | pass rate | "
                 "api_error | wrong_geometry | harness |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for arm in arms:
        s = summary["arms"][arm]
        t = summary["failure_tags"][arm]
        pr = "n/a" if s["pass_rate"] is None else "%.1f%%" % (100 * s["pass_rate"])
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s |"
            % (arm, s["PASS"], s["FAIL"], s["INVALID"], pr,
               t["api_error"], t["wrong_geometry"], t.get("harness", 0)))
    lines.append("")
    lines.append("Jobs passed by S but not G: %s"
                 % (", ".join(summary["jobs_passed_by_S_not_G"]) or "-"))
    lines.append("Tokens/cost: %s" % json.dumps(summary["costs"]))
    lines.append("")
    lines.append("Honest caveat: FreeCAD's Part API has no "
                 "counterbore/slot/polar-pattern helpers (CadQuery has "
                 "them), so part of a G-vs-S gap measures that the tool is "
                 "harder to use, which is exactly the kind of difficulty a "
                 "company tool has.")
    lines.append("")
    lines.append("## Per-job outcomes")
    lines.append("| Job | " + " | ".join(arms) + " |")
    lines.append("|---|" + "|".join(["---"] * len(arms)) + "|")
    for job in sorted(summary["table"]):
        lines.append(
            "| " + job + " | "
            + " | ".join(str(summary["table"][job].get(a, "-")) for a in arms)
            + " |")
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------- CLI


def load_inputs_fc():
    """Job texts (neutral, from the frozen first-test jobs) + the frozen
    FreeCAD manual. The Mac never loads expected.json (the grader holds
    the references)."""
    from jobs import JOBS  # noqa: E402  (frozen file; imported, not modified)

    return JOBS, load_manual()


def parse_fc_arms(value):
    arms = tuple(p.strip() for p in str(value).split(",") if p.strip())
    if not arms:
        raise ValueError("no arms requested (expected comma list of G,S,W)")
    for arm in arms:
        if arm not in VALID_ARMS:
            raise ValueError("unknown arm %r (expected comma list of G,S,W)"
                             % (arm,))
    return arms


def main(argv=None):
    parser = argparse.ArgumentParser(description="FreeCAD gap-test runner.")
    parser.add_argument("--jobs", choices=("dry", "main"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--arms", default="G,S")
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--budget", type=float, default=3.5)
    parser.add_argument("--gpu-start", default=None,
                        help="unix seconds of the session's GPU start: the "
                             "money estimate counts GPU time since then "
                             "(the whole-session cap)")
    parser.add_argument("--budget-c", type=float, default=3.0)
    parser.add_argument("--budget-w", type=float, default=3.0,
                        help="Wonder's own cap ($20/M output, $4/M input, "
                             "$0.20/M cached)")
    parser.add_argument("--escalate-from", default=None,
                        help="S run dir: W runs only on its FAILED job ids")
    parser.add_argument("--w-endpoint", default=WONDER_URL,
                        help="Wonder chat-completions endpoint "
                             "(falls back to /v1/responses when refused)")
    parser.add_argument("--w-smoke", action="store_true",
                        help="send ONE Wonder call (a dry job), log the "
                             "endpoint and usage fields, and stop")
    args = parser.parse_args(argv)
    if args.workers is not None and args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.k is not None and args.k < 1:
        parser.error("--k must be >= 1")
    try:
        arms = parse_fc_arms(args.arms)
    except ValueError as e:
        parser.error(str(e))

    glimmer_url = os.environ.get("GLIMMER_URL", "")
    glimmer_key = os.environ.get("GLIMMER_KEY", "")
    baseten_key = os.environ.get("BASETEN_KEY", "")
    meta_key = os.environ.get("META_HERDSHOT_API_KEY", "")
    need = []
    if "G" in arms:
        need += [("GLIMMER_URL", glimmer_url), ("GLIMMER_KEY", glimmer_key)]
    if "S" in arms:
        need += [("BASETEN_KEY", baseten_key)]
    if "W" in arms or args.w_smoke:
        need += [("META_HERDSHOT_API_KEY", meta_key)]
    missing = [name for name, val in need if not val]
    if missing:
        parser.error("missing environment variables: " + ", ".join(missing))

    try:
        from cloud_exec import modal as _modal  # noqa: E402
    except ImportError:
        _modal = None
    if _modal is None:
        print("modal is not installed in the forge venv; "
              "runner_fc.py needs it to create sandboxes and call the "
              "grader (CPU-only consistency check first).",
              file=sys.stderr)
        return 2

    JOBS, manual_text = load_inputs_fc()
    if args.jobs == "dry":
        jobs = [j for j in JOBS if j.get("level") == "dry"]
    else:
        jobs = [j for j in JOBS if j.get("level") in ("medium", "hard")]
    if not jobs:
        parser.error("no jobs for --jobs %s" % args.jobs)

    arm_cfgs, key_map = {}, {}
    for arm in arms:
        if arm == "G":
            arm_cfgs[arm] = {"endpoint": arm_endpoint(arm, glimmer_url),
                             "model": arm_model(arm)}
            key_map[arm] = glimmer_key
        elif arm == "S":
            arm_cfgs[arm] = {"endpoint": arm_endpoint(arm, glimmer_url),
                             "model": arm_model(arm)}
            key_map[arm] = baseten_key
        else:
            arm_cfgs[arm] = {"endpoint": arm_endpoint(arm, glimmer_url,
                                                      args.w_endpoint),
                             "model": arm_model(arm)}
            key_map[arm] = meta_key

    if args.w_smoke:
        # One cheap call before money is spent: settles the endpoint path
        # and whether reasoning tokens are billed as output.
        dry = [j for j in JOBS if j.get("level") == "dry"][:1]
        if not dry:
            parser.error("no dry jobs for --w-smoke")
        post_fn = default_post_fns(
            {"W": {"endpoint": args.w_endpoint, "model": WONDER_MODEL}},
            {"W": meta_key}, uuid.uuid4().hex[:8])
        body = build_body_fc(WONDER_MODEL,
                             build_messages(dry[0]["text"], manual_text))
        data = runner.post_with_retry(post_fn, args.w_endpoint, body,
                                      CALL_TIMEOUT, time.sleep)
        _content, finish, usage, reasoning = runner.parse_response(data)
        print("W_SMOKE endpoint=%s finish=%s usage=%s reasoning_len=%s"
              % (args.w_endpoint, finish, json.dumps(usage), reasoning))
        return 0

    w_job_ids = None
    if "W" in arms:
        if not args.escalate_from:
            parser.error("arm W needs --escalate-from <S run dir>")
        w_job_ids = s_failed_job_ids(args.escalate_from)
        if not w_job_ids:
            print("no S failures to escalate; W has nothing to run")

    import cloud_grade as _cloud_grade  # noqa: E402

    # The runner's remote work (grader calls) needs an app context, so
    # cloud_grade.grade.remote() runs inside it.
    with _modal.enable_output():
        with _cloud_grade.lookup_grader_app().run():
            run_suite_fc(jobs, manual_text, args.out, arm_cfgs, key_map,
                         budget=args.budget, budget_c=args.budget_c,
                         budget_w=args.budget_w, arms=arms, k=args.k,
                         workers=args.workers, w_job_ids=w_job_ids,
                         gpu_start=args.gpu_start)
    return 0


if __name__ == "__main__":
    sys.exit(main())
