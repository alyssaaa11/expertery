#!/usr/bin/env python3
"""Factory teacher runner: Spark Open on Baseten answers practice jobs.

SPEC section 2. Prompt = system message + the CadQuery manual
(experiments/first-test/manual.md) + job text. Each answer's code runs
in cloud_cq's box and is graded by its grader at 1e-6 (never
runner.run_code on the Mac; reference programs are trusted generator
code and are built inside the grader).

CLI: teacher.py --jobs jobs.jsonl --ids pilot|train|all --out <dir>
  --budget-dollars X [--k 1] [--retry-failed] [--prior <dirs>]
  [--escalate] [--budget-w Y]

Pilot = the 20 non-dev ids that come first per family (2 per family),
never dev ids. --ids train skips every id that already has an answer in
earlier runs' calls.jsonl (pass --prior <dirs>), and train_records.jsonl
holds at most one record per id (the first PASS). Dev ids are never sent
and never trained on. --retry-failed re-asks only FAILed ids (k = 2 at
most) while the budget lasts. --escalate asks Muse Wonder once for
every id Spark FAILED and keeps its answer only if it PASSES at 1e-6.

Budget guard: cost from usage ($1.25/M uncached input, $0.15/M cached,
$4.25/M output); new calls stop when spent + 8 in-flight x $0.075 would
pass the budget (in-flight answers still cost money). --budget-w is the
separate Meta-credit budget for Wonder calls; Wonder spend is tracked
at Meta's rates ($4.00/M uncached input, $0.20/M cached, $20.00/M
output) with an in-flight reserve of 8 x $0.35.

Every calls.jsonl record carries factory_version (the learning loop
reads it) and cached_tokens (the nested Baseten field first).
factory_version is the first 12 hex of the sha256 of generator.py +
teacher.py + teacher_notes.md bytes.
"""

import argparse
import concurrent.futures
import contextlib
import hashlib
import json
import os
import sys
import threading
import time
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

GENERATOR_PATH = os.path.join(HERE, "generator.py")
TEACHER_PATH = os.path.join(HERE, "teacher.py")
NOTES_PATH = os.path.join(HERE, "teacher_notes.md")


def compute_factory_version(gen_path=None, teacher_path=None,
                            notes_path=None):
    """First 12 hex of sha256(generator.py + teacher.py + teacher_notes.md
    bytes, in that order). A missing file counts as empty bytes. Paths
    are injectable so tests can use fake files."""
    digest = hashlib.sha256()
    for path in (gen_path or GENERATOR_PATH,
                 teacher_path or TEACHER_PATH,
                 notes_path or NOTES_PATH):
        try:
            with open(path, "rb") as f:
                digest.update(f.read())
        except OSError:
            digest.update(b"")
    return digest.hexdigest()[:12]


FACTORY_VERSION = compute_factory_version()


def load_notes(path=None):
    """The teacher notes (added to the prompt after the manual). Empty
    (or missing) means the short prompt."""
    try:
        with open(path or NOTES_PATH, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""

SYSTEM_PROMPT = (
    "You write CadQuery Python code. Units are millimetres. "
    "Assign the final solid to a variable named result. "
    "Reply with exactly one Python code block and nothing else."
)
MANUAL_PREFIX = "Here is the CadQuery manual. Use it.\n\n"
MANUAL_PATH = os.path.join(os.path.dirname(HERE), "first-test",
                           "manual.md")

SPARK_MODEL = "meta-models/muse-spark-open-1026"
SPARK_URL = "https://inference.baseten.co/v1/chat/completions"
WONDER_MODEL = "muse-wonder-1.0"
WONDER_URL = "https://api.meta.ai/v1/chat/completions"

MAX_TOKENS = 16000
TEMPERATURE = 1.0
TOP_P = 0.95
CALL_TIMEOUT = 600.0
MAX_WORKERS = 8  # 8 parallel workers

COST_IN_PER_M = 1.25  # $/M uncached input tokens
COST_CACHED_PER_M = 0.15  # $/M cached input tokens
COST_OUT_PER_M = 4.25  # $/M output tokens

WONDER_COST_IN_PER_M = 4.00  # Meta's rates, not Spark's
WONDER_COST_CACHED_PER_M = 0.20
WONDER_COST_OUT_PER_M = 20.00

IN_FLIGHT_N = 8  # in-flight cost reserve: 8 x $0.075
IN_FLIGHT_COST = 0.075

WONDER_IN_FLIGHT_N = 8  # Wonder reserve: 8 x $0.35 (>= $0.35/call)
WONDER_IN_FLIGHT_COST = 0.35

VALID_IDS = ("pilot", "train", "all")


def load_manual(path=None):
    """Read the CadQuery manual (sent with every teacher prompt)."""
    with open(path or MANUAL_PATH, encoding="utf-8") as f:
        return f.read()


def prompt_user_text(job_text, manual_text, notes_text=None):
    """The user prompt: manual, then the teacher notes (when not empty),
    then the job text. Glimmer's training records keep the short prompt
    (no notes): they store only id/text/code, never this prompt."""
    text = MANUAL_PREFIX + manual_text
    if (notes_text or "").strip():
        text += "\n\nTeacher notes:\n" + notes_text.strip()
    return text + "\n\n" + job_text


def build_messages(job_text, manual_text, notes_text=None):
    """System + manual (+ notes when not empty) + job (the SPEC prompt)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_user_text(
            job_text, manual_text, notes_text)},
    ]


def build_body(model, messages):
    """The SPEC request body keys."""
    return {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
    }


def extract_code(content):
    """First fenced code block; the whole content when there is none."""
    import re as _re

    if not content:
        return content
    m = _re.search(r"```(?:python)?[ \t]*\r?\n?(.*?)```", content,
                   _re.DOTALL)
    if not m:
        return content
    return m.group(1).strip()


def real_post_fn(url, key, affinity, timeout=CALL_TIMEOUT):
    """POST one chat-completions body (stdlib only). Returns parsed JSON."""

    def _post(body):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
                "x-session-affinity": affinity,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)

    return _post


def parse_response(data):
    """Split a chat-completions body into (content, finish_reason, usage)."""
    data = data or {}
    try:
        choice = (data.get("choices") or [{}])[0] or {}
    except (AttributeError, IndexError, TypeError):
        choice = {}
    if not isinstance(choice, dict):
        choice = {}
    msg = choice.get("message") or {}
    if not isinstance(msg, dict):
        msg = {}
    content = msg.get("content") or ""
    usage = data.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    return content, choice.get("finish_reason"), usage


def cached_tokens_of(usage):
    """Baseten cached input tokens: the nested details field first, else
    the flat field, else 0."""
    usage = usage or {}
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict) \
            and details.get("cached_tokens") is not None:
        try:
            return int(details.get("cached_tokens") or 0)
        except (TypeError, ValueError):
            return 0
    try:
        return int(usage.get("cached_tokens", 0) or 0)
    except (TypeError, ValueError):
        return 0


def cost_of_usage(usage, wonder=False):
    """Teacher $ from one usage dict (cached input is not double-charged).

    Wonder is charged at Meta's rates ($4.00 / $0.20 cached / $20.00 per
    M), not Spark's."""
    usage = usage or {}
    try:
        prompt = float(usage.get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt = 0.0
    try:
        completion = float(usage.get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion = 0.0
    cached = float(cached_tokens_of(usage))
    uncached = max(0.0, prompt - cached)
    if wonder:
        return (uncached * WONDER_COST_IN_PER_M
                + cached * WONDER_COST_CACHED_PER_M
                + completion * WONDER_COST_OUT_PER_M) / 1e6
    return (uncached * COST_IN_PER_M + cached * COST_CACHED_PER_M
            + completion * COST_OUT_PER_M) / 1e6


def over_budget(spent, budget, n=None, cost=None):
    """Stop new calls when spent + the in-flight reserve passes budget.

    The default reserve is the Spark one (8 x $0.075); pass the Wonder
    reserve (WONDER_IN_FLIGHT_N, WONDER_IN_FLIGHT_COST) for Wonder."""
    if n is None:
        n = IN_FLIGHT_N
    if cost is None:
        cost = IN_FLIGHT_COST
    return spent + n * cost > budget


def load_jobs(path):
    """Read a jobs file (id, family, text, reference)."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_split(path):
    """Read split.json (the dev ids)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def job_n(job_id):
    """The numeric suffix of F<family>-<n>."""
    return int(str(job_id).rsplit("-", 1)[1])


def select_ids(jobs, which, dev_ids=(), prior_dirs=()):
    """The ids for one mode. Pilot = the 2 non-dev ids that come first
    per family, never dev ids. Train = all non-dev ids minus ids that
    already have an answer in --prior runs' calls.jsonl. All = every
    non-dev id. Dev ids are never selected."""
    dev = set(dev_ids)
    by_family = {}
    for job in jobs:
        if job["id"] in dev:
            continue
        by_family.setdefault(job["family"], []).append(job["id"])
    for ids in by_family.values():
        ids.sort(key=job_n)
    if which == "pilot":
        out = []
        for family in sorted(by_family):
            out.extend(by_family[family][:2])
        return out
    answered = set()
    for d in prior_dirs or ():
        path = os.path.join(d, "calls.jsonl")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    answered.add(json.loads(line).get("id"))
    ids = sorted(
        (j["id"] for j in jobs if j["id"] not in dev),
        key=lambda i: (int(str(i).split("-")[0][1:]), job_n(i)))
    if which == "train":
        ids = [i for i in ids if i not in answered]
    elif which != "all":
        raise ValueError("unknown --ids %r" % (which,))
    return ids


def prior_ids(prior_dirs):
    """Every id answered in earlier runs' calls.jsonl."""
    out = set()
    for d in prior_dirs or ():
        path = os.path.join(d, "calls.jsonl")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.add(json.loads(line).get("id"))
    return out


def default_exec_fn(answer_code):
    """Real box call (needs modal). Tests inject a fake instead."""
    _cq = _cloud_cq()
    return _cq.run_answer_in_box(answer_code)


def default_grade_fn(job_id, brep_bytes):
    """Real grader call (needs modal). Tests inject a fake instead."""
    _cq = _cloud_cq()
    return _cq.grade.remote("factory", job_id, bytes(brep_bytes))


def _cloud_cq():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "final"))
    try:
        import cloud_cq as _mod
    finally:
        try:
            sys.path.remove(os.path.join(os.path.dirname(HERE), "final"))
        except ValueError:
            pass
    return _mod


def do_teacher_call(job, teacher, model, post_fn, exec_fn, grade_fn,
                    manual_text, call_timeout=CALL_TIMEOUT,
                    notes_text=None):
    """Run one (job, teacher) pair once: POST, extract, box, grade at
    1e-6. Never raises for a bad answer; a failed call is INVALID, never
    FAIL. A box/grader exception is a harness INVALID; an answer that
    writes no BREP is the answer's FAIL. The teacher notes (when not
    empty) go into the prompt after the manual."""
    body = build_body(
        model, build_messages(job["text"], manual_text, notes_text))
    t0 = time.monotonic()
    content, finish_reason, usage = "", None, {}
    code, verdict, fails, run_error = "", "INVALID", [], None
    try:
        data = post_fn(body)
        content, finish_reason, usage = parse_response(data)
        code = extract_code(content)
        if finish_reason == "length" or not (code or "").strip():
            verdict, fails = "INVALID", []
            run_error = "cut off by the token limit" \
                if finish_reason == "length" else "empty reply"
        else:
            try:
                boxed = exec_fn(code)
            except Exception as e:  # noqa: BLE001 -- box down: harness
                verdict, fails = "INVALID", []
                run_error = "harness: %s: %s" % (type(e).__name__, e)
            else:
                if boxed is None or boxed.get("brep_bytes") is None:
                    verdict, fails = "FAIL", []
                    run_error = (boxed or {}).get("run_error") or \
                        "the answer wrote no BREP"
                else:
                    try:
                        graded = grade_fn(job["id"], boxed["brep_bytes"])
                    except Exception as e:  # noqa: BLE001 -- grader down
                        verdict, fails = "INVALID", []
                        run_error = "harness: %s: %s" % (
                            type(e).__name__, e)
                    else:
                        if graded.get("tight",
                                      graded.get("verdict")) == "PASS":
                            verdict, fails = "PASS", []
                        else:
                            verdict = "FAIL"
                            fails = list(graded.get("fails_tight")
                                         or graded.get("fails") or [])
    except Exception as e:  # noqa: BLE001 -- failed call => INVALID
        verdict, fails = "INVALID", []
        run_error = "%s: %s" % (type(e).__name__, e)
        usage = {}
    latency = round(time.monotonic() - t0, 3)
    return {
        "id": job["id"],
        "family": job["family"],
        "teacher": teacher,
        "attempt": 1,
        "code": code,
        "verdict": verdict,
        "fails": fails,
        "usage": usage,
        "cached_tokens": cached_tokens_of(usage),
        "latency": latency,
        "finish_reason": finish_reason,
        "run_error": run_error,
        "factory_version": FACTORY_VERSION,
    }


def app_context():
    """The Modal context real box/grader calls need: enable_output plus
    the cloud_cq grader app's run (a different App from forge_train's
    own app.run). Outside it `.remote` raises "Function has not been
    hydrated" and every paid answer would come back harness INVALID.
    Offline (no modal or no grader app) this is a nullcontext so unit
    tests can run without Modal."""
    cq = _cloud_cq()
    modal_mod = getattr(cq, "modal", None)
    if modal_mod is None:
        try:
            import modal as modal_mod
        except ImportError:
            modal_mod = None
    app = getattr(cq, "_app", None)
    if modal_mod is None or app is None:
        return contextlib.nullcontext()
    return _app_stack(modal_mod, app)


@contextlib.contextmanager
def _app_stack(modal_mod, app):
    with modal_mod.enable_output():
        with app.run():
            yield


def run_suite(jobs_by_id, ids, out_dir, spark_post_fn, wonder_post_fn,
              manual_text, budget, budget_w=None, retry_failed=False,
              escalate=False, exec_fn=None, grade_fn=None, k=1,
              notes_text=None):
    """Ask the teacher for each id (8 workers), with the budget guard.

    First pass: one call per id (Spark). --retry-failed: a second pass
    over FAILed ids (k = 2 at most). --escalate: one Wonder call per
    id Spark never PASSED (kept only on PASS at 1e-6). Every call is
    appended live to calls.jsonl. Returns (records, summary)."""
    if exec_fn is None:
        exec_fn = default_exec_fn
    if grade_fn is None:
        grade_fn = default_grade_fn
    os.makedirs(out_dir, exist_ok=True)
    calls_path = os.path.join(out_dir, "calls.jsonl")
    lock = threading.Lock()
    records = []
    spent = [0.0]
    spent_w = [0.0]
    budget_stopped = [False]

    def _submit(pool, futures, job_id, teacher, model, post_fn,
                attempt, wonder):
        job = jobs_by_id[job_id]
        fut = pool.submit(do_teacher_call, job, teacher, model, post_fn,
                          exec_fn, grade_fn, manual_text,
                          CALL_TIMEOUT, notes_text)
        futures[fut] = (job_id, teacher, attempt, wonder)

    def _charge(rec, wonder):
        cost = cost_of_usage(rec.get("usage"), wonder=wonder)
        if wonder:
            spent_w[0] += cost
        else:
            spent[0] += cost
        return cost

    def _passes(pool, ids_attempts, teacher, model, post_fn, wonder,
                budget_cap):
        if wonder:
            reserve_n, reserve_cost = (WONDER_IN_FLIGHT_N,
                                      WONDER_IN_FLIGHT_COST)
        else:
            reserve_n, reserve_cost = IN_FLIGHT_N, IN_FLIGHT_COST
        futures = {}
        queue = list(ids_attempts)
        while queue or futures:
            while queue and len(futures) < MAX_WORKERS:
                with lock:
                    cur = spent_w[0] if wonder else spent[0]
                if over_budget(cur, budget_cap, n=reserve_n,
                               cost=reserve_cost):
                    budget_stopped[0] = True
                    queue.clear()
                    break
                job_id, attempt = queue.pop(0)
                _submit(pool, futures, job_id, teacher, model, post_fn,
                        attempt, wonder)
            if not futures:
                break
            done, _ = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_COMPLETED)
            for fut in done:
                job_id, _t, attempt, _w = futures.pop(fut)
                rec = fut.result()
                rec["attempt"] = attempt
                cost = _charge(rec, wonder)
                rec["cost"] = cost
                with lock:
                    records.append(rec)
                    with open(calls_path, "a",
                              encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_WORKERS) as pool:
        _passes(pool, [(i, 1) for i in ids], "spark", SPARK_MODEL,
                spark_post_fn, False, budget)
        if retry_failed and int(k) > 1:
            failed = [r["id"] for r in records
                      if r["teacher"] == "spark" and r["verdict"] == "FAIL"
                      and r["attempt"] == 1]
            seen = {r["id"] for r in records if r["attempt"] > 1}
            _passes(pool, [(i, 2) for i in failed if i not in seen],
                    "spark", SPARK_MODEL, spark_post_fn, False, budget)
        if escalate:
            passed = {r["id"] for r in records if r["verdict"] == "PASS"}
            need = [i for i in ids if i not in passed]
            _passes(pool, [(i, 1) for i in need], "wonder",
                    WONDER_MODEL, wonder_post_fn, True,
                    budget_w if budget_w is not None else budget)
    summary = build_summary(records, ids, spent[0], spent_w[0],
                            budget_stopped[0])
    with open(os.path.join(out_dir, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    train_records = build_train_records(records, jobs_by_id)
    with open(os.path.join(out_dir, "train_records.jsonl"), "w",
              encoding="utf-8") as f:
        for rec in train_records:
            f.write(json.dumps(rec) + "\n")
    return records, summary


def build_summary(records, ids, spent, spent_w, budget_stopped):
    """Pass rate per family, tokens, cost, the Wonder share."""
    by_family = {}
    for rec in records:
        by_family.setdefault(rec["family"], []).append(rec)
    families = {}
    for fam, recs in sorted(by_family.items()):
        passed = sum(1 for r in recs if r["verdict"] == "PASS")
        families[str(fam)] = {
            "n_calls": len(recs),
            "n_pass": passed,
            "pass_rate": round(passed / len(recs), 4) if recs else 0.0,
        }
    prompt = sum((r.get("usage") or {}).get("prompt_tokens", 0) or 0
                 for r in records)
    completion = sum(
        (r.get("usage") or {}).get("completion_tokens", 0) or 0
        for r in records)
    cached = sum(r.get("cached_tokens", 0) or 0 for r in records)
    n_pass = sum(1 for r in records if r["verdict"] == "PASS")
    kept = {r["id"] for r in records if r["verdict"] == "PASS"}
    wonder_kept = sum(1 for r in build_train_records_from(
        records) if r.get("teacher") == "wonder")
    return {
        "factory_version": FACTORY_VERSION,
        "n_ids": len(ids),
        "n_calls": len(records),
        "n_pass": n_pass,
        "n_kept_ids": len(kept),
        "families": families,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "cached_tokens": cached,
        "cost_dollars": round(spent, 4),
        "cost_w_dollars": round(spent_w, 4),
        "wonder_share": (round(wonder_kept / len(kept), 4)
                         if kept else 0.0),
        "budget_stopped": budget_stopped,
    }


def build_train_records_from(records):
    """First PASS per id (the kept answers), with their teacher tag."""
    best = {}
    for rec in records:
        if rec["verdict"] != "PASS" or rec["id"] in best:
            continue
        best[rec["id"]] = rec
    return [best[i] for i in sorted(best)]


def build_train_records(records, jobs_by_id):
    """train_records.jsonl = {"id", "text", "code"} for the first PASS
    at 1e-6 of each id (the teacher's extracted code, not the
    reference)."""
    out = []
    for rec in build_train_records_from(records):
        job = jobs_by_id[rec["id"]]
        out.append({"id": rec["id"], "text": job["text"],
                    "code": rec["code"]})
    return out


def main(argv=None):
    """CLI (keys from env; missing keys exit 2 with the variable name,
    before any network)."""
    parser = argparse.ArgumentParser(description="Factory teacher runner.")
    parser.add_argument("--jobs", default=os.path.join(HERE, "jobs.jsonl"))
    parser.add_argument("--split", default=None,
                        help="split.json holding the dev ids "
                             "(default: <jobs-dir>/split.json)")
    parser.add_argument("--ids", choices=VALID_IDS, default="pilot")
    parser.add_argument("--out", required=True)
    parser.add_argument("--budget-dollars", type=float, required=True)
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--prior", action="append", default=[],
                        help="earlier run dirs whose calls.jsonl ids "
                             "--ids train skips")
    parser.add_argument("--escalate", action="store_true")
    parser.add_argument("--budget-w", type=float, default=None,
                        help="separate Meta-credit budget for Wonder calls")
    args = parser.parse_args(argv)
    baseten_key = os.environ.get("BASETEN_KEY", "")
    if not baseten_key:
        parser.error("missing environment variables: BASETEN_KEY")
        return 2
    meta_key = os.environ.get("META_HERDSHOT_API_KEY", "")
    if args.escalate and not meta_key:
        parser.error(
            "missing environment variables: META_HERDSHOT_API_KEY")
        return 2
    jobs = load_jobs(args.jobs)
    split_path = args.split or os.path.join(
        os.path.dirname(os.path.abspath(args.jobs)), "split.json")
    dev_ids = load_split(split_path)["dev"] \
        if os.path.isfile(split_path) else []
    ids = select_ids(jobs, args.ids, dev_ids, args.prior)
    jobs_by_id = {j["id"]: j for j in jobs}
    manual_text = load_manual()
    notes_text = load_notes()
    affinity = uuid.uuid4().hex  # one value per run (prompt caching)
    spark_post_fn = real_post_fn(SPARK_URL, baseten_key, affinity)
    wonder_post_fn = real_post_fn(WONDER_URL, meta_key, affinity) \
        if args.escalate else None
    # Real box/grader calls need the grader app's run context (F1);
    # outside it `.remote` raises "Function has not been hydrated".
    with app_context():
        _records, summary = run_suite(
            jobs_by_id, ids, args.out, spark_post_fn, wonder_post_fn,
            manual_text, args.budget_dollars, budget_w=args.budget_w,
            retry_failed=args.retry_failed, escalate=args.escalate,
            k=args.k, notes_text=notes_text)
    print("TEACHER ids=%d calls=%d kept=%d cost=$%.4f wonder=%.2f" % (
        summary["n_ids"], summary["n_calls"], summary["n_kept_ids"],
        summary["cost_dollars"], summary["wonder_share"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
