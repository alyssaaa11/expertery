"""Exam build / review / lock for one tool (v0: CadQuery).

Past work = one folder per job: request.txt + part.py (CadQuery code
defining `result`). A part.step file means "not supported in v0": the
job is marked SKIPPED.

All cloud contact goes through injected callables so tests run offline:
- box_fn(code) -> {"brep_bytes", "measure", "log", "run_error"}.
- grade_fn(exam, job_id, brep) -> grader dict with at least "verdict".
  The reference (part.py source) travels with the jobs list given to
  cloud.factory_grade_fn, exactly as runner_final.grade_fn_for does, so
  new past-work ids grade against their own reference at the 0.2% rule.
- post_fn(body) -> parsed chat-completions JSON for one reader call.

Money: every model call is costed from its usage tokens with the
teacher's price constants (config fallbacks). Before starting a new
call, spent_estimate + one in-flight reserve must still fit the cap;
otherwise no new calls start. spent_estimate is written to the output.
"""

import concurrent.futures
import datetime
import hashlib
import json
import os
import threading
import time

from . import cloud as _cloud
from . import config as _config

STATUS_READY = "READY"
STATUS_FLAGGED = "FLAGGED"
STATUS_BROKEN = "BROKEN_REFERENCE"
STATUS_SKIPPED = "SKIPPED"
# Extra status (beyond the four above): the cap stopped new calls before
# this job reached a verdict. Documented in report.md; lock refuses
# while any remain.
STATUS_DEFERRED = "DEFERRED"

CANDIDATES_NAME = "candidates.jsonl"
CALLS_NAME = "calls.jsonl"
REPORT_NAME = "report.md"
EXAM_NAME = "exam.jsonl"
FREEZE_NAME = "FREEZE.txt"

FLAGGED_LINE = ("A FLAGGED job is not a model failure: the wording may "
                "be read two ways. A person decides.")
RECHECK_LINE = ("Accepted or edited texts are NOT re-checked automatically; "
                "re-run `exam build` on edited jobs to re-check them.")


class ExamError(Exception):
    """A refusal (bad dir state, bad reply shape, cap misuse)."""


def utcnow():
    """Current UTC time, ISO-8601 seconds."""
    return (datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="seconds"))


def iter_past_work(past_work_dir):
    """List past-work jobs sorted by id.

    Each item: {"id", "request" (text or None), "source" (part.py text or
    None), "step" (True when part.step is present)}.
    """
    jobs = []
    for name in sorted(os.listdir(past_work_dir)):
        job_dir = os.path.join(past_work_dir, name)
        if not os.path.isdir(job_dir):
            continue
        request_path = os.path.join(job_dir, "request.txt")
        part_path = os.path.join(job_dir, "part.py")
        step_path = os.path.join(job_dir, "part.step")
        request = None
        if os.path.isfile(request_path):
            with open(request_path, encoding="utf-8") as f:
                request = f.read()
        source = None
        if os.path.isfile(part_path):
            with open(part_path, encoding="utf-8") as f:
                source = f.read()
        jobs.append({"id": name, "request": request, "source": source,
                     "step": os.path.isfile(step_path)})
    return jobs


def reference_ok(box_result):
    """True when the reference built exactly one valid solid."""
    if not box_result or box_result.get("brep_bytes") is None:
        return False
    measure = box_result.get("measure") or {}
    return measure.get("solids") == 1 and measure.get("valid") is not False


def slim_measurements(measure):
    """bbox / volume / solids kept for the explainer and the record."""
    measure = measure or {}
    return {k: measure.get(k) for k in ("bbox", "volume", "solids")}


def parse_reply(data):
    """(content, usage) from one chat-completions response."""
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
    if not isinstance(content, str):
        content = str(content)
    usage = data.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    return content, usage


class Budget:
    """Cap guard: each call reserves its estimate before it starts.

    may_start is true only when spent + reserved_in_flight + one more
    reserve still fits inside the cap. On finish, the reserve is
    released and the real cost is charged, so with N workers the
    realised spend can never pass the cap (real costs are bounded by
    the reserve estimate).
    """

    def __init__(self, cap_dollars):
        if not cap_dollars > 0:
            raise ExamError("--cap-dollars must be > 0")
        self.cap = float(cap_dollars)
        self.spent = 0.0
        self.in_flight = 0
        self.reserve = _cloud.in_flight_cost()
        self.lock = threading.Lock()

    def _fits_locked(self):
        return (self.spent
                + self.in_flight * self.reserve
                + self.reserve <= self.cap)

    def may_start(self):
        """True when one more call still fits inside the cap."""
        with self.lock:
            return self._fits_locked()

    def try_reserve(self):
        """Atomically reserve one call; False when it would pass cap."""
        with self.lock:
            if not self._fits_locked():
                return False
            self.in_flight += 1
            return True

    def release_and_charge(self, cost):
        """Release one reserve and add the realised cost."""
        with self.lock:
            self.in_flight = max(0, self.in_flight - 1)
            self.spent += max(0.0, float(cost))

    def charge(self, cost):
        """Add the realised cost of a finished call."""
        with self.lock:
            self.spent += max(0.0, float(cost))


def call_reader(post_fn, url, model, key, messages, timeout=600.0):
    """One reader call. Returns (content, usage, seconds)."""
    body = _cloud.reader_body(model, messages)
    t0 = time.monotonic()
    data = post_fn(url, key, body, timeout)
    seconds = time.monotonic() - t0
    content, usage = parse_reply(data)
    return content, usage, seconds


def explainer_messages(request_text, reference_measurements,
                       failures, passes=0):
    """Messages for the explainer call.

    Sees the request text, the reference part's measurements, each
    failed reader's measurements or run error, and the passing tries'
    count. NEVER the reference code (only measurements cross this
    boundary).
    """
    lines = [
        "You read CAD requests for wording problems. Reply with exactly "
        'one JSON object {"kind", "phrase", "why", "suggested_request"} '
        "and nothing else.",
        'kind is "wording" when the text can be read two ways by a '
        "careful engineer; kind is \"reader_mistake\" when a careful "
        "engineer would read the text one way only (for example the "
        "failure is a code or API error, or a misread of a clear "
        "number).",
        '"why" is at most 20 words. "suggested_request" is the full '
        "request with the smallest wording change.",
        "",
        "Request text:",
        request_text,
        "",
        "Reference part measurements (from the correct part; "
        "you do not see its code): %s"
        % json.dumps(reference_measurements, sort_keys=True),
        "",
        "Failed reader attempts (their measurements or run error):",
    ]
    for i, fail in enumerate(failures):
        lines.append("- attempt %d: %s"
                     % (i + 1, json.dumps(fail, sort_keys=True)))
    lines += ["",
              "Passing attempts: %d." % passes]
    return [
        {"role": "system",
         "content": ("You spot ambiguous wording in CAD requests. Reply "
                     "with exactly one JSON object and nothing else.")},
        {"role": "user", "content": "\n".join(lines)},
    ]


def truncate_words(text, limit=20):
    """First `limit` words of text (for the 20-word `why` rule)."""
    words = (text or "").split()
    return " ".join(words[:limit])


def parse_explainer(content):
    """(suggestion|None, raw). Invalid JSON or kind -> (None, content)."""
    try:
        data = json.loads(content)
    except (ValueError, TypeError):
        return None, content
    if not isinstance(data, dict):
        return None, content
    if data.get("kind") not in ("wording", "reader_mistake"):
        return None, content
    why = data.get("why")
    why = truncate_words(why) if isinstance(why, str) else why
    return {"kind": data.get("kind"), "phrase": data.get("phrase"),
            "why": why,
            "suggested_request": data.get("suggested_request")}, None


def build_one_job(job, readers, budget, box_fn, grade_fn, post_fn,
                  reader_url, reader_model, reader_key, calls,
                  stop):
    """Build one candidate record, appending call records to `calls`.

    `stop` is a threading.Event set once the cap stops new calls.
    """
    job_id = job["id"]
    if job["step"]:
        return {"id": job_id, "text": job["request"],
                "reference": job["source"], "status": STATUS_SKIPPED,
                "readers": [], "reference_measurements": None,
                "suggestion": None, "explainer_raw": None,
                "decision": None}
    ref_run = _cloud.run_box(job["source"] or "", box_fn=box_fn)
    if not reference_ok(ref_run):
        return {"id": job_id, "text": job["request"],
                "reference": job["source"],
                "status": STATUS_BROKEN,
                "readers": [],
                "reference_measurements": slim_measurements(
                    (ref_run or {}).get("measure")),
                "suggestion": None, "explainer_raw": None,
                "run_error": (ref_run or {}).get("run_error"),
                "decision": None}
    ref_meas = slim_measurements(ref_run.get("measure"))
    verdicts = []
    failures = []

    def run_reader_try(attempt_no, kind="reader"):
        """One reserved reader call; None when the cap blocks it."""
        if stop.is_set() or not budget.try_reserve():
            stop.set()
            return None
        try:
            content, usage, seconds = call_reader(
                post_fn, reader_url, reader_model, reader_key,
                _cloud.reader_messages(job["request"]))
        except Exception:
            budget.release_and_charge(0.0)
            raise
        cost = _cloud.cost_of_usage(usage)
        budget.release_and_charge(cost)
        calls.append({"job": job_id, "kind": kind,
                      "attempt": attempt_no, "model": reader_model,
                      "prompt_tokens": usage.get("prompt_tokens", 0),
                      "completion_tokens": usage.get("completion_tokens", 0),
                      "seconds": round(seconds, 3),
                      "cost_estimate": round(cost, 6)})
        code = _cloud.extract_code(content)
        run = _cloud.run_box(code, box_fn=box_fn)
        if run.get("brep_bytes") is None:
            graded = {"verdict": "FAIL", "fails": [run.get("run_error")],
                      "measurements": None}
            failures.append({"run_error": run.get("run_error")})
        else:
            graded = grade_fn("factory", job_id, run["brep_bytes"])
            failures.append({"verdict": graded.get("verdict"),
                             "fails": graded.get("fails"),
                             "measurements": graded.get("measurements")})
        verdicts.append({
            "verdict": graded.get("verdict"),
            "fails": graded.get("fails"),
            "measurements": graded.get("measurements"),
            "run_error": run.get("run_error")})
        if graded.get("verdict") == "PASS":
            failures.pop()
        return graded.get("verdict")

    for attempt in range(readers):
        if run_reader_try(attempt + 1) is None:
            break
    if verdicts and all(v["verdict"] == "PASS" for v in verdicts):
        return {"id": job_id, "text": job["request"],
                "reference": job["source"], "status": STATUS_READY,
                "readers": verdicts, "reference_measurements": ref_meas,
                "suggestion": None, "explainer_raw": None,
                "decision": None, "note": None}
    if not verdicts:
        return {"id": job_id, "text": job["request"],
                "reference": job["source"], "status": STATUS_DEFERRED,
                "readers": [], "reference_measurements": ref_meas,
                "suggestion": None, "explainer_raw": None,
                "decision": None, "note": None}
    passes = sum(1 for v in verdicts if v["verdict"] == "PASS")
    fails = len(verdicts) - passes
    if fails > passes:
        pass
    elif passes > 0:
        # Mixed but no FAIL majority (tie or PASS majority short of
        # unanimous): one tie-break reader decides the majority.
        tied = run_reader_try(len(verdicts) + 1, kind="tie-break")
        if tied is None:
            return {"id": job_id, "text": job["request"],
                    "reference": job["source"], "status": STATUS_DEFERRED,
                    "readers": verdicts,
                    "reference_measurements": ref_meas,
                    "suggestion": None, "explainer_raw": None,
                    "decision": None, "note": None}
        passes = sum(1 for v in verdicts if v["verdict"] == "PASS")
        if passes > len(verdicts) / 2:
            return {"id": job_id, "text": job["request"],
                    "reference": job["source"], "status": STATUS_READY,
                    "readers": verdicts,
                    "reference_measurements": ref_meas,
                    "suggestion": None, "explainer_raw": None,
                    "decision": None, "note": None}
    if stop.is_set() or not budget.try_reserve():
        stop.set()
        return {"id": job_id, "text": job["request"],
                "reference": job["source"], "status": STATUS_DEFERRED,
                "readers": verdicts, "reference_measurements": ref_meas,
                "suggestion": None, "explainer_raw": None,
                "decision": None, "note": None}
    try:
        content, usage, seconds = call_reader(
            post_fn, reader_url, reader_model, reader_key,
            explainer_messages(job["request"], ref_meas, failures,
                               passes=passes))
    except Exception:
        budget.release_and_charge(0.0)
        raise
    cost = _cloud.cost_of_usage(usage)
    budget.release_and_charge(cost)
    calls.append({"job": job_id, "kind": "explainer", "attempt": 1,
                  "model": reader_model,
                  "prompt_tokens": usage.get("prompt_tokens", 0),
                  "completion_tokens": usage.get("completion_tokens", 0),
                  "seconds": round(seconds, 3),
                  "cost_estimate": round(cost, 6)})
    suggestion, raw = parse_explainer(content)
    if suggestion is not None and suggestion.get("kind") == "reader_mistake":
        note = "reader mistake: %s" % truncate_words(
            suggestion.get("why") or "")
        return {"id": job_id, "text": job["request"],
                "reference": job["source"], "status": STATUS_READY,
                "readers": verdicts, "reference_measurements": ref_meas,
                "suggestion": suggestion, "explainer_raw": None,
                "decision": None, "note": note}
    return {"id": job_id, "text": job["request"],
            "reference": job["source"], "status": STATUS_FLAGGED,
            "readers": verdicts, "reference_measurements": ref_meas,
            "suggestion": suggestion, "explainer_raw": raw,
            "decision": None, "note": None}


def write_jsonl(path, rows):
    """Write rows as JSONL (one JSON object per line)."""
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path):
    """Read a JSONL file into a list of dicts."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def split_sentences(text):
    """Split text into sentences (keeps short lines short)."""
    import re
    parts = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def changed_sentence(original, suggested):
    """The changed sentence only: suggested sentences missing upstream."""
    orig = split_sentences(original)
    sugg = split_sentences(suggested)
    if not sugg:
        return (suggested or "").strip()
    changed = [s for s in sugg if s not in orig]
    if changed:
        return " ".join(changed)
    if sugg != orig:
        return sugg[-1] if len(sugg) > 1 else sugg[0]
    return sugg[0]


def write_report(path, candidates, spent_estimate, cap_dollars,
                 extra_lines=(), reader_model=None, num_calls=None):
    """Write report.md, readable first: headline, decision, ready."""
    if reader_model is None:
        try:
            reader_model = _cloud.reader_config()[1]
        except Exception:  # noqa: BLE001
            reader_model = "unknown"
    if num_calls is None:
        try:
            calls_path = os.path.join(os.path.dirname(path), CALLS_NAME)
            num_calls = len(read_jsonl(calls_path))
        except (OSError, ValueError):
            num_calls = 0
    ready = sorted(c.get("id") for c in candidates
                   if c.get("status") == STATUS_READY)
    flagged = sorted((c for c in candidates
                      if c.get("status") == STATUS_FLAGGED),
                     key=lambda c: c.get("id"))
    deferred = sorted(c.get("id") for c in candidates
                      if c.get("status") == STATUS_DEFERRED)
    mistakes = [c for c in candidates
                if c.get("status") == STATUS_READY and c.get("note")]
    lines = ["**%d ready · %d need your decision · %d not checked "
             "(money cap)**" % (len(ready), len(flagged), len(deferred)),
             "",
             "## Need your decision",
             ""]
    if not flagged:
        lines.append("None.")
    for cand in flagged:
        suggestion = cand.get("suggestion") or {}
        phrase = suggestion.get("phrase") or "?"
        why = truncate_words(suggestion.get("why") or "")
        lines.append("- %s: \"%s\" — %s" % (cand.get("id"), phrase, why))
        changed = changed_sentence(cand.get("text") or "",
                                   suggestion.get("suggested_request") or "")
        lines.append("  Suggested: %s" % changed)
        lines.append("  Run `expertery exam review <dir>` to accept, "
                     "keep, edit or drop.")
    lines += ["",
              "## Ready",
              ""]
    lines.append(", ".join(ready) + "." if ready else "None.")
    for cand in sorted(mistakes, key=lambda c: c.get("id")):
        lines.append("- %s: %s" % (cand.get("id"), cand.get("note")))
    lines += ["",
              "## Not checked",
              ""]
    lines.append(", ".join(deferred) + "." if deferred else "None.")
    if deferred:
        lines.append("Re-run with a higher --cap-dollars.")
    lines += ["",
              "spent_estimate: $%.4f (cap $%.2f)." % (spent_estimate,
                                                      cap_dollars),
              "Reader model: %s." % reader_model,
              "Model calls: %d." % num_calls]
    lines.extend(extra_lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_exam(past_work_dir, exam_dir, cap_dollars, readers=2,
               workers=4, dry_run=False, box_fn=None, grade_fn=None,
               post_fn=None, print_fn=print):
    """Run the exam build. Returns {"candidates", "spent_estimate"}.

    With dry_run, prints the plan and the estimated spend and makes
    zero calls (box, grader or reader) and writes no files.
    """
    jobs = iter_past_work(past_work_dir)
    exam_path = os.path.join(exam_dir, EXAM_NAME)
    if os.path.exists(exam_path):
        raise ExamError("refusing to overwrite %s (exam is locked)"
                        % exam_path)
    reader_url, reader_model, _ = _cloud.reader_config()
    if dry_run:
        calls = sum(readers + 2 for j in jobs if not j["step"])
        print_fn("dry-run: %d jobs x up to %d reader calls + explainer"
                 % (len(jobs), readers + 1))
        print_fn("dry-run: estimated spend <= $%.4f (cap $%.2f)"
                 % (calls * _cloud.in_flight_cost(), cap_dollars))
        print_fn("dry-run: would write %s, %s, %s in %s"
                 % (CANDIDATES_NAME, CALLS_NAME, REPORT_NAME, exam_dir))
        return {"candidates": [], "spent_estimate": 0.0}
    if post_fn is None:
        key = _cloud.reader_key()
        if not key:
            raise ExamError("no reader key: set %s (or %s)"
                            % (_config.READER_KEY_ENV,
                               _config.READER_KEY_FALLBACK_ENV))

        def post_fn(url, key_arg, body, timeout=600.0,
                    _key=key):  # noqa: B023
            return _cloud.post_reader(url, _key, body, timeout)
    budget = Budget(cap_dollars)
    calls = []
    calls_lock = threading.Lock()
    stop = threading.Event()

    def run_job(job):
        grade = grade_fn
        if grade is None:
            grade = _cloud.factory_grade_fn(
                [{"id": job["id"], "reference": job["source"]}])
        return build_one_job(job, readers, budget, box_fn, grade,
                             post_fn, reader_url, reader_model,
                             _cloud.reader_key(), _ThreadSafeCalls(
                                 calls, calls_lock), stop)

    os.makedirs(exam_dir, exist_ok=True)

    def run_all():
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max(1, workers)) as pool:
            return list(pool.map(run_job, jobs))

    # Real runs (no injected fakes) grade in the cloud: the ephemeral
    # grader app runs for the whole build, then stops. With fakes or
    # dry-run there is no cloud contact at all.
    if box_fn is None and grade_fn is None:
        with _cloud.cloud_session():
            candidates = run_all()
    else:
        candidates = run_all()
    candidates.sort(key=lambda c: c["id"])
    ordered_calls = sorted(calls, key=lambda c: (c["job"], c["attempt"]))
    write_jsonl(os.path.join(exam_dir, CANDIDATES_NAME), candidates)
    write_jsonl(os.path.join(exam_dir, CALLS_NAME), ordered_calls)
    write_report(os.path.join(exam_dir, REPORT_NAME), candidates,
                 budget.spent, budget.cap, reader_model=reader_model,
                 num_calls=len(ordered_calls))
    return {"candidates": candidates, "spent_estimate": budget.spent}


class _ThreadSafeCalls:
    """list.append wrapper safe to share across job threads."""

    def __init__(self, calls, lock):
        self._calls = calls
        self._lock = lock

    def append(self, item):
        with self._lock:
            self._calls.append(item)


def load_candidates(exam_dir):
    """Read candidates.jsonl from an exam dir."""
    return read_jsonl(os.path.join(exam_dir, CANDIDATES_NAME))


def save_candidates(exam_dir, candidates):
    """Write candidates.jsonl back to an exam dir."""
    write_jsonl(os.path.join(exam_dir, CANDIDATES_NAME), candidates)


def decide_candidate(cand, choice, edit_text=None):
    """Apply one review decision; returns the updated candidate."""
    suggestion = cand.get("suggestion") or {}
    if choice == "accepted":
        cand["text"] = suggestion.get("suggested_request")
    elif choice == "edited":
        cand["text"] = edit_text
    cand["decision"] = {"choice": choice, "reviewer": "human",
                        "at": utcnow()}
    return cand


def review_exam(exam_dir, accept_all=False, keep_all=False,
                choices=None, input_fn=None, print_fn=print):
    """Review every undecided FLAGGED job in an exam dir.

    choices maps job id -> (choice, edit_text) for scripts and tests
    ("accepted" | "kept" | "dropped" | "edited"). Without choices, each
    job is asked interactively: [a]ccept / [k]eep / [d]rop / [e]dit.
    --accept-all / --keep-all record reviewer "flag" (non-interactive).
    """
    candidates = load_candidates(exam_dir)
    flagged = [c for c in candidates
               if c.get("status") == STATUS_FLAGGED
               and not c.get("decision")]
    if accept_all and keep_all:
        raise ExamError("--accept-all and --keep-all are exclusive")
    if accept_all:
        auto = "accepted"
    elif keep_all:
        auto = "kept"
    else:
        auto = None
    input_fn = input_fn or input
    for cand in flagged:
        suggestion = cand.get("suggestion") or {}
        if choices is not None and cand["id"] in choices:
            choice, edit_text = choices[cand["id"]]
        elif auto is not None:
            choice, edit_text = auto, None
        else:
            print_fn("job %s" % cand["id"])
            print_fn("original: %s" % (cand.get("text") or ""))
            print_fn("phrase: %s" % (suggestion.get("phrase") or ""))
            print_fn("why: %s" % (suggestion.get("why") or ""))
            print_fn("suggestion: %s"
                     % (suggestion.get("suggested_request") or ""))
            answer = input_fn(
                "[a]ccept suggestion / [k]eep original / "
                "[d]rop job / [e]dit text: ").strip().lower()
            mapping = {"a": "accepted", "k": "kept", "d": "dropped",
                       "e": "edited"}
            if answer not in mapping:
                raise ExamError("unknown choice %r" % answer)
            choice = mapping[answer]
            edit_text = None
            if choice == "edited":
                edit_text = input_fn("new text (one line): ")
        if choice not in ("accepted", "kept", "dropped", "edited"):
            raise ExamError("unknown choice %r" % (choice,))
        if choice == "accepted" and not suggestion.get(
                "suggested_request"):
            raise ExamError("job %s has no suggestion to accept"
                            % cand["id"])
        if choice == "edited" and not (edit_text or "").strip():
            raise ExamError("job %s: edited text is empty" % cand["id"])
        decide_candidate(cand, choice,
                         (edit_text or "").strip()
                         if choice == "edited" else None)
        if auto is not None:
            cand["decision"]["reviewer"] = "flag"
    save_candidates(exam_dir, candidates)
    call_rows = read_jsonl(os.path.join(exam_dir, CALLS_NAME))
    spent = sum(c.get("cost_estimate", 0.0) for c in call_rows)
    model = call_rows[0].get("model") if call_rows else None
    write_report(os.path.join(exam_dir, REPORT_NAME), candidates,
                 spent, spent, extra_lines=["", RECHECK_LINE],
                 reader_model=model, num_calls=len(call_rows))
    return candidates


def lock_exam(exam_dir):
    """Write exam.jsonl + FREEZE.txt. Returns the locked rows."""
    if os.path.exists(os.path.join(exam_dir, EXAM_NAME)):
        raise ExamError("refusing to overwrite %s"
                        % os.path.join(exam_dir, EXAM_NAME))
    candidates = load_candidates(exam_dir)
    undecided = [c["id"] for c in candidates
                 if c.get("status") == STATUS_FLAGGED
                 and not c.get("decision")]
    if undecided:
        raise ExamError("undecided FLAGGED jobs: %s (run `exam review`)"
                        % ", ".join(sorted(undecided)))
    unfinished = [c["id"] for c in candidates
                  if c.get("status") == STATUS_DEFERRED]
    if unfinished:
        raise ExamError("unfinished DEFERRED jobs: %s (re-run `exam build` "
                        "with a higher cap)" % ", ".join(sorted(unfinished)))
    rows = []
    for cand in candidates:
        status = cand.get("status")
        if status == STATUS_READY:
            rows.append({"id": cand["id"], "family": "past-work",
                         "level": "unknown", "text": cand["text"],
                         "reference": cand.get("reference")})
        elif status == STATUS_FLAGGED:
            choice = (cand.get("decision") or {}).get("choice")
            if choice in ("accepted", "kept", "edited"):
                rows.append({"id": cand["id"], "family": "past-work",
                             "level": "unknown", "text": cand["text"],
                             "reference": cand.get("reference")})
    rows.sort(key=lambda r: r["id"])
    exam_path = os.path.join(exam_dir, EXAM_NAME)
    write_jsonl(exam_path, rows)
    with open(exam_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(exam_dir, FREEZE_NAME), "w",
              encoding="utf-8") as f:
        f.write("sha256: %s\ndate: %s\n"
                % (digest,
                   datetime.datetime.now(
                       datetime.timezone.utc).date().isoformat()))
    return rows

