"""The 92%-second-look loop (FTX rules) with an injected model and box.

Messages start from ``runner_final.ft_messages(job)``. Then up to 3 model
calls: after a crash the assistant reply plus ``runner.bx_error_message``
are appended; after a build the reply plus ``runner.bx_self_check_message``
are appended; a reply without a code fence ("DONE") ends the loop. Every
request body is built exactly as the FTX arm builds it
(``runner.build_bx_body``: 16,000 max tokens, same temperature/top_p/top_k
and the same reasoning setting), except the reasoning strength comes from
the ONE ``REASONING_STRENGTH`` setting (env, "high"|"xhigh", default
"xhigh"). With the default the body is byte-identical to
``runner.build_bx_body``.

``model_call(messages, body)`` returns ``(content, gpu_seconds)``.
``box_run(code)`` returns a ``cloud_cq.run_answer_in_box``-style dict
``{"brep_bytes", "measure", "run_error"}``. Both are faked in tests; no
Modal, no network here.
"""

import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_FINAL_DIR = os.path.normpath(os.path.join(
    _HERE, "..", "..", "experiments", "final"))
_FIRST_DIR = os.path.normpath(os.path.join(
    _HERE, "..", "..", "experiments", "first-test"))
for _p in (_FINAL_DIR, _FIRST_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import runner  # noqa: E402 (frozen; imported, never modified)
import runner_final  # noqa: E402 (frozen; imported, never modified)

from . import config  # noqa: E402
from . import selfcheck  # noqa: E402

MODEL_NAME = "forge"
MAX_CALLS = 3


def initial_messages(job_text):
    """Round-1 messages, exactly the FTX arm's."""
    return runner_final.ft_messages(job_text)


def build_body(model, messages):
    """Exactly the FTX arm's body, with the configured reasoning strength.

    With the default setting ("xhigh") this equals
    ``runner.build_bx_body(model, messages)``.
    """
    return runner.build_body(
        model, messages,
        reasoning_strength=config.reasoning_strength())


def has_code(content):
    """A reply only counts as code when it holds a fenced block (FTX rule)."""
    return bool(runner.FENCE_RE.search(content or ""))


def _cap(text):
    text = str(text or "")
    if len(text) > config.OUTPUT_CAP:
        return text[:config.OUTPUT_CAP]
    return text


def _measure_line(measure):
    """One short human line for a built part's own measurements."""
    try:
        return ("Measured bbox X %s to %s, Y %s to %s, Z %s to %s; "
                "volume %s mm3; %s solid(s)."
                % (measure["xmin"], measure["xmax"], measure["ymin"],
                   measure["ymax"], measure["zmin"], measure["zmax"],
                   measure["volume"], measure["solids"]))
    except (TypeError, KeyError):
        return "Measured the built part."


def _past_deadline(now, deadline):
    """True when a deadline was passed and no new work may start."""
    return deadline is not None and now() >= deadline


def run_job(job_text, model_call, box_run, model=MODEL_NAME,
            clock=None, deadline=None):
    """Yield SSE-style event dicts for one visitor job.

    Event steps: write, build, fix, measure, done (or error). The first
    event is yielded before the first model call. The final done event
    carries verdict/reasons/measurements/code/rounds/seconds/gpu_seconds;
    the web layer adds the file URLs.

    ``deadline`` (same clock as ``clock``) is the wall-clock limit for the
    whole build (verifier W4): no new model call and no new box run starts
    once it has passed. The caller also sizes each model call's own timeout
    from the time left until the deadline.
    """
    now = clock or time.monotonic
    t0 = now()
    messages = initial_messages(job_text)
    best_code = ""
    best_raw = None
    last_error = None
    gpu_total = 0.0
    rounds = 0
    while rounds < MAX_CALLS:
        rounds += 1
        yield {"step": "write", "round": rounds,
               "detail": "Writing the part script (round %d of %d)."
                         % (rounds, MAX_CALLS)}
        if _past_deadline(now, deadline):
            break
        body = build_body(model, messages)
        try:
            content, gpu_s = model_call(messages, body)
        except Exception as e:  # noqa: BLE001 -- failed call ends the loop
            if best_raw is None and not best_code:
                last_error = "%s: %s" % (type(e).__name__, e)
            break
        try:
            gpu_total += float(gpu_s or 0.0)
        except (TypeError, ValueError):
            pass
        messages.append({"role": "assistant", "content": content})
        if not has_code(content):
            if not best_code:
                last_error = "the model sent no code"
            break
        code = runner.extract_code(content)
        if _past_deadline(now, deadline):
            break
        try:
            boxed = box_run(code)
        except Exception as e:  # noqa: BLE001 -- harness error is a crash
            boxed = {"brep_bytes": None, "measure": None,
                     "run_error": "runner error: %r" % (e,)}
        if boxed is None or boxed.get("brep_bytes") is None:
            err = (boxed or {}).get("run_error") or \
                "the answer wrote no BREP"
            last_error = err
            yield {"step": "build", "round": rounds,
                   "detail": "Building in the locked box."}
            yield {"step": "fix", "round": rounds,
                   "detail": _cap(err)}
            messages.append({"role": "user",
                             "content": runner.bx_error_message(err)})
            continue
        measure_raw = boxed.get("measure")
        measure = runner_final.box_measure_to_selfcheck(measure_raw)
        yield {"step": "build", "round": rounds,
               "detail": "Building in the locked box."}
        best_code = code
        best_raw = measure_raw
        last_error = None
        if measure is None:
            break
        yield {"step": "measure", "round": rounds,
               "detail": _measure_line(measure),
               "measurements": measure_raw}
        # FTX rule (Claude fix 2026-11-02, disclosed): after a build the
        # model sees its own measurements and either fixes the part or says
        # DONE (no code fence), up to MAX_CALLS. The last built part counts.
        messages.append({"role": "user",
                         "content": runner.bx_self_check_message(measure)})
        if rounds < MAX_CALLS:
            yield {"step": "fix", "round": rounds,
                   "detail": "Checking its own measurements."}
    seconds = now() - t0
    if best_code:
        verdict, reasons = selfcheck.self_check(job_text, best_raw)
    else:
        verdict, reasons = ("CHECK FAILED",
                            [last_error or "the part did not build"])
    yield {"step": "done", "round": rounds, "verdict": verdict,
           "reason": "; ".join(reasons),
           "measurements": best_raw, "code": best_code,
           "rounds": rounds, "seconds": round(seconds, 3),
           "gpu_seconds": round(gpu_total, 3)}
