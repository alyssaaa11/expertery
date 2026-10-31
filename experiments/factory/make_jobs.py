#!/usr/bin/env python3
"""Write the factory jobs file + dev split, with the self-checks.

Writes experiments/factory/jobs.jsonl (200 jobs: id, family, text,
reference source), split.json (the 20 seed-chosen dev ids) and
jobs_dev.jsonl (the 20 dev jobs as a jobs file for the final-exam
runner's --jobs-file).

Self-check (SPEC section 1): every reference builds one valid solid
in-process (trusted generator code); two "wrong" variants per family
(a moved feature, a wrong size) FAIL at 1e-6; no job text has difflib
ratio >= 0.9 (exact numbers) to any first-test job text; TEXT=REF: for
every job, the numbers in the text are re-parsed and each number the
reference program uses (its literal numbers, after rounding) must
appear in the text (a family passes only at 20/20). Prints a
10-family table.
"""

import ast
import difflib
import hashlib
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import generator

JOBS_NAME = "jobs.jsonl"
SPLIT_NAME = "split.json"
DEV_JOBS_NAME = "jobs_dev.jsonl"
OVERLAP_LIMIT = 0.9

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
# TEXT=REF (round 1d, verifier H2): exempt only 0, +-1 and the /2 of a
# printed size (the radius/half-width idiom (diameter)/2). Any other
# integer, or any arithmetic on printed values used as a size (e.g.
# (5.9 + 1)), is flagged unless it is the +-1 overshoot of a
# through-cut into air.
DIVISOR_RE = re.compile(r"/\s*2(?:\.0)?(?![\d.])")
PLUSMINUS1_RE = re.compile(r"([\)\w.]+)\s*([+-])\s*1(?![\d.])")


def body_of(reference):
    """The reference program without the shared preamble helpers."""
    if reference.startswith(generator.PREAMBLE):
        return reference[len(generator.PREAMBLE):]
    return reference


def _divisor_spans(body):
    """Spans of the `/2` divisor idiom (exempt from TEXT=REF)."""
    return [(m.start(), m.end()) for m in DIVISOR_RE.finditer(body)]


def _cut_vars(body):
    """Variables that are cut: assigned on one line, `.cut(` on another.

    A (printed + 1) overshoot may live on the constructor line of a
    cutter built first and cut later (the F4 slot, the F8 window, the
    F10 rim ring), so those lines count as cutter positions too."""
    assigned = set()
    for line in body.splitlines():
        m = re.match(r"\s*(\w+)\s*=", line)
        if m:
            assigned.add(m.group(1))
    cut = set()
    for line in body.splitlines():
        if ".cut(" in line:
            for name in assigned:
                if re.search(r"\b%s\b" % re.escape(name), line):
                    cut.add(name)
    return cut


def text_ref_ok(text, reference):
    """True when every design number the reference program uses appears
    in the job text (TEXT=REF).

    Each numeric literal in the reference body (after rounding) must
    match a number parsed from the text within 1e-9, except 0, +-1 and
    the /2 divisor. A (printed +- 1) expression is allowed only as the
    overshoot of a through-cut: on a `.cut(` line or on the constructor
    line of a variable that is cut. A text that prints 21.2 while its
    reference uses 21.3 fails, as does a reference box Y -3..3 against
    the text "5.9 wide". (--check-refs grades a reference against
    itself and cannot see this.)
    Returns (ok, missing_literal_or_None)."""
    body = body_of(reference or "")
    texts = [float(m) for m in NUM_RE.findall(text or "")]
    spans = _divisor_spans(body)
    for m in NUM_RE.finditer(body):
        s, e = m.span()
        if s > 0 and (body[s - 1].isalnum() or body[s - 1] == "_"):
            continue  # part of an identifier (atan2), not a literal
        if e < len(body) and (body[e].isalnum() or body[e] == "_"):
            continue
        if any(ds <= s and e <= de for ds, de in spans):
            continue
        v = float(m.group())
        if v == int(v) and abs(int(v)) <= 1:
            continue
        if not any(abs(v - t) <= 1e-9 for t in texts):
            return False, m.group()
    allowed_vars = _cut_vars(body)
    for line in body.splitlines():
        for m in PLUSMINUS1_RE.finditer(line):
            if ".cut(" in line:
                continue
            lhs = re.match(r"\s*(\w+)\s*=", line)
            if lhs and lhs.group(1) in allowed_vars:
                continue
            return False, m.group(0).strip()
    return True, None


CYL_RE = re.compile(r"_([xyz])cyl\s*\(")


def _split_top(argstr):
    """Split a call argument list on top-level commas."""
    parts, depth, cur = [], 0, []
    for ch in argstr:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _eval_num(expr):
    """Evaluate a numeric-literal expression (+ - * / and parens)."""
    node = ast.parse((expr or "").strip(), mode="eval").body
    return _eval_node(node)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) \
                or not isinstance(node.value, (int, float)):
            raise ValueError("not numeric: %r" % (node.value,))
        return float(node.value)
    if isinstance(node, ast.UnaryOp) \
            and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _eval_node(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) \
            and isinstance(node.op,
                           (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right
    raise ValueError("not a numeric literal expression")


def _cyl_calls(body):
    """Every _xcyl/_ycyl/_zcyl construction: (axis, centre, radius, span).

    axis is "x"/"y"/"z", centre the two fixed coordinates, span the
    (lo, hi) interval along the axis. Fused base solids and cutters alike
    are listed: sharing one axis and radius while overlapping is wrong
    for cutters, and no fused pair in the references shares both either.
    """
    out = []
    for m in CYL_RE.finditer(body):
        i, depth, start = m.end() - 1, 0, m.end() - 1
        while i < len(body):
            ch = body[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth != 0:
            raise ValueError("unbalanced _%scyl call" % m.group(1))
        parts = _split_top(body[start + 1:i])
        if len(parts) != 5:
            raise ValueError("_%scyl takes 5 args" % m.group(1))
        r, a, b, lo, hi = [_eval_num(p) for p in parts]
        out.append({"axis": m.group(1), "c": (round(a, 9), round(b, 9)),
                    "r": round(r, 9),
                    "span": (min(lo, hi), max(lo, hi))})
    return out


def cuts_ok(reference):
    """True when no two cylinder primitives share an axis and radius
    while overlapping or touching (CUTS).

    Two coincident or overlapping same-radius coaxial cuts are the same
    solid but leave a fragmented face structure that makes the default
    Volume() noisy (round 1d: F5 failed 1e-6 on a text-faithful answer).
    A static scan of the reference source is enough: every cutter bound
    is a numeric literal expression. Returns (ok, detail_or_None)."""
    try:
        calls = _cyl_calls(body_of(reference or ""))
    except ValueError as e:
        return False, str(e)
    for i in range(len(calls)):
        for j in range(i + 1, len(calls)):
            a, b = calls[i], calls[j]
            if a["axis"] != b["axis"]:
                continue
            if abs(a["r"] - b["r"]) > 1e-9:
                continue
            if abs(a["c"][0] - b["c"][0]) > 1e-9 \
                    or abs(a["c"][1] - b["c"][1]) > 1e-9:
                continue
            if max(a["span"][0], b["span"][0]) \
                    <= min(a["span"][1], b["span"][1]) + 1e-9:
                return False, ("coaxial cutters share r=%s on %s-axis "
                               "at %s, spans %s and %s"
                               % (a["r"], a["axis"], a["c"], a["span"],
                                  b["span"]))
    return True, None


def exam_texts():
    """First-test job texts (for the overlap self-check)."""
    import importlib.util as _ilu

    path = os.path.join(os.path.dirname(HERE), "first-test", "jobs.py")
    spec = _ilu.spec_from_file_location("factory_exam_jobs", path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [j["text"] for j in mod.JOBS]


def max_overlap(text, texts):
    """Largest difflib ratio of a job text to any exam text."""
    return max(difflib.SequenceMatcher(None, text, e).ratio()
               for e in texts)


def self_check(jobs, texts):
    """Full self-check. Returns per-family rows:
    (family, name, n_valid, n_jobs, wrong_results, max_ratio, n_text_ref,
    n_cuts). n_text_ref is the TEXT=REF count: jobs whose every
    reference number (after rounding) appears in the text. n_cuts is the
    CUTS count: jobs where no two cutter primitives share an axis and
    radius while overlapping."""
    rows = []
    for family in range(1, generator.N_FAMILIES + 1):
        fam = generator.FAMILIES[family]
        sub = [j for j in jobs if j["family"] == family]
        n_valid = 0
        for job in sub:
            shape = generator.build_source(job["reference"])
            n_solids, valid = generator.shape_info(shape)
            if n_solids == 1 and valid:
                n_valid += 1
            else:
                print("INVALID REF %s: solids=%s valid=%s"
                      % (job["id"], n_solids, valid))
        ref = generator.build_source(sub[0]["reference"])
        wrongs = []
        for override in fam["wrong"](generator.first_params(family)):
            wsrc = fam["src"](override)
            passed, fails = generator.score_at_tight(wsrc, ref)
            wrongs.append((passed, fails))
        ratio = max(max_overlap(j["text"], texts) for j in sub)
        n_text_ref = 0
        for job in sub:
            ok, missing = text_ref_ok(job["text"], job["reference"])
            if ok:
                n_text_ref += 1
            else:
                print("TEXT!=REF %s: reference uses %s, not in the text"
                      % (job["id"], missing))
        n_cuts = 0
        for job in sub:
            ok, detail = cuts_ok(job["reference"])
            if ok:
                n_cuts += 1
            else:
                print("CUTS %s: %s" % (job["id"], detail))
        rows.append((family, fam["name"], n_valid, len(sub), wrongs,
                     ratio, n_text_ref, n_cuts))
    return rows


def print_table(rows):
    """Print the 10-family self-check table."""
    print("%-28s %8s %8s %8s %8s %8s %8s" % (
        "FAMILY", "VALID", "WRONG-1", "WRONG-2", "OVERLAP", "TEXT=REF",
        "CUTS"))
    ok = True
    for family, name, n_valid, n_jobs, wrongs, ratio, n_text_ref, \
            n_cuts in rows:
        cells = []
        v_ok = n_valid == n_jobs
        cells.append("%d/%d" % (n_valid, n_jobs))
        for passed, _fails in wrongs:
            cells.append("FAIL" if not passed else "PASS-BAD")
        cells.append("%.3f" % ratio)
        cells.append("%d/%d" % (n_text_ref, n_jobs))
        cells.append("%d/%d" % (n_cuts, n_jobs))
        if not v_ok or any(p for p, _f in wrongs) \
                or ratio >= OVERLAP_LIMIT or n_text_ref != n_jobs \
                or n_cuts != n_jobs:
            ok = False
        print("%-28s %8s %8s %8s %8s %8s %8s" % (
            "%d %s" % (family, name), cells[0], cells[1], cells[2],
            cells[3], cells[4], cells[5]))
    print("SELF-CHECK %s" % ("OK" if ok else "FAIL"))
    return ok


R5_SHUFFLE_SEED = 20261031
CLOUD_CHECK_COST_PER_JOB = 0.005  # $ prior per check (fake paths; real
# boxes are measured, see estimate_job_cost)

# Modal compute prices behind the honest budget (B2): sandbox seconds
# cost cores x $0.142/core-h + GiB x $0.024/GiB-h from the box's actual
# size (sandbox_kwargs); each grader call (cpu-1 function) costs its
# measured seconds x the cpu rate (grader memory is the default slice
# and is excluded, disclosed here).
MODAL_CPU_DOLLARS_PER_CORE_H = 0.142
MODAL_MEM_DOLLARS_PER_GIB_H = 0.024
GRADER_CPU_DOLLARS_PER_H = 0.142
CLOUD_COST_PRINT_AFTER = 20  # honest per-job cost printed + projected
# after this many measured jobs


def sandbox_size():
    """(cores, GiB) of the cloud box from cloud_cq's real kwargs.

    Memory is a (min, max) MiB range: cost uses the max (conservative).
    Falls back to (1, 4.0) when Modal is unavailable (offline)."""
    try:
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "final"))
        import cloud_cq as _cq
        kwargs = _cq.sandbox_kwargs()
        cores = float(kwargs.get("cpu", 1))
        mem = kwargs.get("memory", 4096)
        if isinstance(mem, (tuple, list)):
            mem = max(mem)
        return cores, float(mem) / 1024.0
    except Exception:  # noqa: BLE001 -- offline: documented fallback
        return 1.0, 4.0
    finally:
        try:
            sys.path.remove(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "final"))
        except ValueError:
            pass


def estimate_job_cost(exec_seconds, measure_seconds, cores=None, gib=None):
    """Honest per-job $ from measured seconds (B2).

    Sandbox exec seconds cost cores x $0.142/core-h + GiB x $0.024/GiB-h
    (the box's actual size); grader measure seconds cost the cpu-1 rate.
    """
    if cores is None or gib is None:
        d_cores, d_gib = sandbox_size()
        cores = d_cores if cores is None else cores
        gib = d_gib if gib is None else gib
    sandbox = max(0.0, float(exec_seconds)) / 3600.0 * (
        MODAL_CPU_DOLLARS_PER_CORE_H * float(cores)
        + MODAL_MEM_DOLLARS_PER_GIB_H * float(gib))
    grader = max(0.0, float(measure_seconds)) / 3600.0 * \
        GRADER_CPU_DOLLARS_PER_H
    return sandbox + grader

FORBIDDEN_SEED = generator.SEED


def param_tuple_of_text(text):
    """Rounded parameter tuple of a job text (1-decimal numbers)."""
    return tuple(round(float(m), 1) for m in NUM_RE.findall(text or ""))


def load_text_and_param_sets(paths):
    """(texts, param_tuples) from existing jobs files (id/text only)."""
    texts, params = set(), set()
    for path in paths or ():
        if not path or not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    job = json.loads(line)
                except ValueError:
                    continue
                text = job.get("text", "")
                if text:
                    texts.add(text)
                    params.add(param_tuple_of_text(text))
    return texts, params


def existing_factory_paths(out_dir=None):
    """Default dedup corpus: jobs.jsonl + jobs_dev.jsonl next to make_jobs."""
    base = out_dir or HERE
    return [os.path.join(base, JOBS_NAME),
            os.path.join(base, DEV_JOBS_NAME)]


def generate_prefixed(seed, per_family, prefix):
    """Generate jobs with a new seed and id prefix `P-F<f>-<i>`.

    Refuses a seed equal to generator.SEED (exit 2 via ValueError here;
    main turns it into exit 2). Uses the same 10 families and generator
    code, only the seed and ids differ.
    """
    if int(seed) == int(generator.SEED):
        raise ValueError(
            "refusing seed %s: equal to generator.SEED (%s)"
            % (seed, generator.SEED))
    rng = random.Random(int(seed))
    jobs = []
    for family in range(1, generator.N_FAMILIES + 1):
        fam = generator.FAMILIES[family]
        for n in range(1, int(per_family) + 1):
            params = fam["gen"](rng)
            jobs.append({
                "id": "%s-F%d-%d" % (prefix, family, n),
                "family": family,
                "text": fam["text"](params),
                "reference": fam["src"](params),
            })
    return jobs


def dedup_jobs(jobs, seen_texts, seen_params):
    """Drop jobs whose text or rounded parameter tuple is already seen.

    Returns (kept, n_dropped). Seen sets grow with kept jobs, so
    within-set duplicates are dropped too.
    """
    kept, dropped = [], 0
    for job in jobs:
        text = job.get("text", "")
        tup = param_tuple_of_text(text)
        if text in seen_texts or tup in seen_params:
            dropped += 1
            continue
        seen_texts.add(text)
        seen_params.add(tup)
        kept.append(job)
    return kept, dropped


def sha256_of_file(path):
    """Hex sha256 of a file's bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _terminate_box(box):
    """Best-effort sandbox termination (B3: the one box always dies)."""
    try:
        box.terminate()
    except Exception:  # noqa: BLE001 -- terminate is best-effort
        pass


def cloud_check_jobs(jobs, budget, exec_fn=None, measure_fn=None,
                     sandbox_factory=None, cost_fn=None):
    """Reference self-check + volume/bbox measure in the cloud box.

    Each job's reference runs via exec_fn (default: ONE reused cloud_cq
    box, B3) and its BREP is measured via measure_fn (default: cloud_cq
    measure_brep). All remote calls run inside
    `modal.enable_output()` + `cloud_cq._app.run()` (B1, as
    runner_final does). Returns (results, spent, stopped) where results
    maps id -> {"volume", "bbox", "solids", "valid"} or {"error"}.

    Cost (B2): each job is timed; the real-box charge is
    estimate_job_cost(exec seconds, measure seconds) from the box's
    actual size, `cost_fn(exec_s, measure_s)` when given (tests), else
    the CLOUD_CHECK_COST_PER_JOB prior (injected-fake paths only).
    Stops starting NEW checks once spent + the running per-job average
    passes the budget; after CLOUD_COST_PRINT_AFTER measured jobs the
    honest per-job cost and the projected total are printed, and the run
    stops when the projection exceeds the budget. The one box is
    terminated at the end (also on error, in `finally`); if it dies it
    is rebuilt once, then the run stops. Volume+bbox duplicates are
    found by the caller from results.
    """
    real_exec = exec_fn is None
    _cq = None
    if real_exec or measure_fn is None:
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "final"))
        try:
            import cloud_cq as _cq
        finally:
            try:
                sys.path.remove(os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "..", "final"))
            except ValueError:
                pass
        if _cq.modal is None:
            raise RuntimeError(
                "modal is not installed; cannot run the cloud check")
    state = {"box": None}
    make_box = sandbox_factory or (lambda: _cq.build_sandbox())
    if real_exec:
        # B3: ONE box for the whole batch, reused via sandbox=.
        state["box"] = make_box()

        def exec_fn(code, _state=state, _run=_cq.run_answer_in_box):
            return _run(code, sandbox=_state["box"])
    if measure_fn is None:
        remote = getattr(_cq.measure_brep, "remote",
                         _cq.measure_brep)
        measure_fn = remote
    own_box = real_exec
    if cost_fn is None and own_box:
        cores, gib = sandbox_size()

        def cost_fn(exec_s, measure_s, _c=cores, _g=gib):
            return estimate_job_cost(exec_s, measure_s, _c, _g)
    _need_ctx = _cq is not None
    results, spent, stopped = {}, 0.0, False
    n_charged, rebuilt = 0, False

    def _charge(exec_s, measure_s):
        if cost_fn is not None:
            return float(cost_fn(exec_s, measure_s))
        return CLOUD_CHECK_COST_PER_JOB

    def _check_one(job):
        t0 = time.monotonic()
        boxed = exec_fn(job["reference"])
        exec_s = time.monotonic() - t0
        brep = (boxed or {}).get("brep_bytes")
        if brep is None:
            return ({"error": (boxed or {}).get("run_error")
                     or "the answer wrote no BREP"}, exec_s, 0.0)
        t1 = time.monotonic()
        try:
            meas = measure_fn(bytes(brep))
        except Exception as e:  # noqa: BLE001 -- grader down
            return ({"error": "measure: %r" % (e,)},
                    exec_s, time.monotonic() - t1)
        meas_s = time.monotonic() - t1
        try:
            return ({"volume": float(meas["volume"]),
                     "bbox": [float(v) for v in meas["bbox"]],
                     "solids": int(meas.get("solids", 1)),
                     "valid": meas.get("valid", True)},
                    exec_s, meas_s)
        except (KeyError, TypeError, ValueError):
            return ({"error": "bad measure %r" % (meas,)},
                    exec_s, meas_s)

    def _run_all():
        nonlocal spent, stopped, n_charged, rebuilt
        for job in jobs:
            next_est = (spent / n_charged if n_charged
                        else CLOUD_CHECK_COST_PER_JOB)
            if spent + next_est > float(budget):
                stopped = True
                break
            try:
                outcome, exec_s, meas_s = _check_one(job)
            except Exception as e:  # noqa: BLE001 -- the box may be dead
                if not own_box:
                    results[job["id"]] = {"error": "harness: %r" % (e,)}
                    spent += _charge(0.0, 0.0)
                    n_charged += 1
                    continue
                if rebuilt:
                    # B3: rebuilt once already; stop the run.
                    results[job["id"]] = {"error": "harness: %r" % (e,)}
                    spent += _charge(0.0, 0.0)
                    n_charged += 1
                    print("cloud-check: box died again after one "
                          "rebuild; stopping")
                    stopped = True
                    break
                print("cloud-check: box died; rebuilding once")
                _terminate_box(state["box"])
                try:
                    state["box"] = make_box()
                except Exception as e2:  # noqa: BLE001 -- no box left
                    results[job["id"]] = {
                        "error": "box rebuild failed: %r" % (e2,)}
                    spent += _charge(0.0, 0.0)
                    n_charged += 1
                    stopped = True
                    break
                rebuilt = True
                try:
                    outcome, exec_s, meas_s = _check_one(job)
                except Exception as e3:  # noqa: BLE001 -- still dead
                    results[job["id"]] = {"error": "harness: %r" % (e3,)}
                    spent += _charge(0.0, 0.0)
                    n_charged += 1
                    print("cloud-check: rebuilt box died too; stopping")
                    stopped = True
                    break
            results[job["id"]] = outcome
            spent += _charge(exec_s, meas_s)
            n_charged += 1
            if n_charged == CLOUD_COST_PRINT_AFTER:
                per_job = spent / n_charged
                projected = per_job * len(jobs)
                print("cloud-check cost $%.5f/job over %d jobs; "
                      "projected $%.3f for %d jobs vs budget $%.2f"
                      % (per_job, n_charged, projected, len(jobs),
                         float(budget)))
                if projected > float(budget):
                    print("cloud-check: projection exceeds the budget; "
                          "stopping")
                    stopped = True
                    break

    try:
        if _need_ctx:
            # B1: every remote call happens inside the app context.
            with _cq.modal.enable_output():
                with _cq._app.run():
                    _run_all()
        else:
            _run_all()
    finally:
        if own_box and state["box"] is not None:
            _terminate_box(state["box"])
            state["box"] = None
    return results, spent, stopped


def volume_bbox_duplicates(jobs, measures, tol=1e-6, against=()):
    """Ids whose measured (volume, bbox) duplicates an earlier job's.

    `against` is an iterable of (volume, bbox) pairs measured OUTSIDE
    this set (B4: old factory sets, the exam, --dedup-against measures
    files): a new job duplicating any of them is dropped too. Within-
    set behaviour is unchanged.
    """
    seen = [(float(v), tuple(float(x) for x in b)) for v, b in against]
    dupes = set()
    for job in jobs:
        meas = measures.get(job["id"])
        if not isinstance(meas, dict) or "volume" not in meas:
            continue
        try:
            key = (float(meas["volume"]),
                   tuple(float(x) for x in meas["bbox"]))
        except (TypeError, ValueError):
            continue
        for prev in seen:
            if abs(key[0] - prev[0]) <= tol and all(
                    abs(a - b) <= tol for a, b in zip(key[1], prev[1])):
                dupes.add(job["id"])
                break
        else:
            seen.append(key)
    return sorted(dupes)


def save_measures(path, measures):
    """Save {id: {volume, bbox}} for every measured id (B4).

    Only successful measures are written (errors have no volume).
    Returns the number of ids written.
    """
    out = {}
    for jid, meas in (measures or {}).items():
        if not isinstance(meas, dict) or "volume" not in meas \
                or "bbox" not in meas:
            continue
        try:
            out[jid] = {"volume": float(meas["volume"]),
                        "bbox": [float(v) for v in meas["bbox"]]}
        except (TypeError, ValueError):
            continue
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    return len(out)


def load_measures_file(path):
    """{id: (volume, bbox)} from a <out>.measures.json file (B4).

    Returns None when the file is not a measures file (missing,
    unreadable, or a jobs file instead), so --dedup-against accepts
    both jobs files and measures files.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not data:
        return None
    out = {}
    for jid, meas in data.items():
        if not isinstance(meas, dict):
            return None
        try:
            vol = float(meas["volume"])
            bbox = [float(v) for v in meas["bbox"]]
        except (KeyError, TypeError, ValueError):
            return None
        if len(bbox) != 6:
            return None
        out[jid] = (vol, bbox)
    return out


def load_old_reference_items(paths):
    """[{"id", "reference"}] from existing factory jobs files (B4).

    Entries without both are skipped. Callers filter out ids they
    already measure themselves.
    """
    items = []
    for path in paths or ():
        if not path or not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    job = json.loads(line)
                except ValueError:
                    continue
                if isinstance(job, dict) and job.get("id") \
                        and job.get("reference"):
                    items.append({"id": job["id"],
                                  "reference": job["reference"]})
    return items


def exam_cloud_items():
    """Trusted exam builds as cloud exec items (B4).

    first-test/jobs.py is trusted frozen code, but it imports cadquery,
    which the Mac lacks: each exam reference is measured by exec'ing the
    whole jobs.py source plus a `result = JOBS[i]["build"]()` driver in
    the same cloud batch as the old factory refs. Ids are EXAM-<exam id>.
    Returns (items, exam_ids).
    """
    path = os.path.join(os.path.dirname(HERE), "first-test", "jobs.py")
    with open(path, encoding="utf-8") as f:
        source = f.read()
    ids = re.findall(r'dict\(id="([^"]+)"', source)
    items = [{"id": "EXAM-%s" % jid,
              "reference": source + '\nresult = JOBS[%d]["build"]()\n' % i}
             for i, jid in enumerate(ids)]
    return items, ["EXAM-%s" % jid for jid in ids]


def ref_status(job_id, measures):
    """(ok, reason): does the reference build exactly one valid solid?

    ok is True only for a measured volume with solids == 1 and valid
    not False (B2). Otherwise reason names the failure ("reference
    failed: ..." / "reference built N solids" / "reference invalid") or
    "not checked (stopped early)" when the id was never measured.
    """
    meas = (measures or {}).get(job_id)
    if not isinstance(meas, dict) or "volume" not in meas:
        if isinstance(meas, dict) and meas.get("error"):
            return False, "reference failed: %s" % (meas["error"],)
        return False, "not checked (stopped early)"
    if meas.get("solids") != 1:
        return False, "reference built %s solids" % (meas.get("solids"),)
    if meas.get("valid") is False:
        return False, "reference invalid"
    return True, None


def finalize_seed_jobs(jobs, measures):
    """Split new jobs into kept + dropped (B2).

    Jobs whose reference was not checked, or failed to build exactly
    one valid solid, are dropped with reasons. Returns
    (kept, dropped, failed_any) where failed_any is True when any
    reference failed (stopped-early ids do not count: the caller
    reports `stopped` separately and exits non-zero for it too).
    """
    kept, dropped, failed_any = [], [], False
    for job in jobs:
        ok, reason = ref_status(job["id"], measures)
        if ok:
            kept.append(job)
            continue
        dropped.append({"id": job["id"], "reason": reason})
        if reason != "not checked (stopped early)":
            failed_any = True
    return kept, dropped, failed_any


def main(argv=None):
    import argparse as _ap

    parser = _ap.ArgumentParser(description="Write factory jobs + split.")
    parser.add_argument("--out-dir", default=HERE)
    parser.add_argument("--seed", type=int, default=None,
                        help="new job-set seed (refused when == SEED)")
    parser.add_argument("--per-family", type=int, default=None)
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--out", default=None,
                        help="output jobs file for --seed mode")
    parser.add_argument("--dedup-against", action="append", default=[],
                        help="extra jobs file to dedup against "
                             "(repeatable; covers R5T vs R5D)")
    parser.add_argument("--cloud-check", action="store_true",
                        help="run the reference self-check + volume/bbox "
                             "measure in the cloud box")
    parser.add_argument("--budget", type=float, default=1.0,
                        help="cloud-check budget in dollars (hard stop)")
    args = parser.parse_args(argv)
    if args.seed is not None:
        if args.per_family is None or not args.prefix or not args.out:
            parser.error("--seed needs --per-family, --prefix and --out")
        try:
            jobs = generate_prefixed(args.seed, args.per_family,
                                     args.prefix)
        except ValueError as e:
            parser.error(str(e))
        n_before = len(jobs)
        seen_texts, seen_params = load_text_and_param_sets(
            existing_factory_paths(args.out_dir) + list(
                args.dedup_against or ()))
        for exam_text in exam_texts():
            seen_texts.add(exam_text)
            seen_params.add(param_tuple_of_text(exam_text))
        jobs, n_dedup = dedup_jobs(jobs, seen_texts, seen_params)
        print("dedup dropped %d of %d (text or rounded params)"
              % (n_dedup, n_before))
        if args.cloud_check:
            # B4: the old sets are measured in the SAME cloud run (one
            # batch): jobs.jsonl (+dev), every --dedup-against jobs
            # file, and the exam (trusted builds via a driver). The new
            # set is also compared against --dedup-against measures
            # files from earlier runs.
            new_ids = set(j["id"] for j in jobs)
            old_items = load_old_reference_items(
                existing_factory_paths(args.out_dir) + list(
                    args.dedup_against or ()))
            old_items = [it for it in old_items
                         if it["id"] not in new_ids]
            seen_old = set()
            old_items = [it for it in old_items
                         if it["id"] not in seen_old
                         and not seen_old.add(it["id"])]
            exam_items, exam_ids = exam_cloud_items()
            batch = ([{"id": j["id"], "reference": j["reference"]}
                      for j in jobs] + old_items + exam_items)
            against = []
            for path in list(args.dedup_against or ()):
                loaded = load_measures_file(path)
                if loaded is not None:
                    against.extend(loaded.values())
            measures, spent, stopped = cloud_check_jobs(
                batch, args.budget)
            new_measures = {jid: measures[jid] for jid in new_ids
                            if jid in measures}
            n_old = sum(1 for it in old_items if it["id"] in measures
                        and isinstance(measures[it["id"]], dict)
                        and "volume" in measures[it["id"]])
            n_exam = sum(1 for jid in exam_ids if jid in measures
                         and isinstance(measures[jid], dict)
                         and "volume" in measures[jid])
            old_failed = (
                len(old_items) - n_old, len(exam_items) - n_exam)
            print("cloud-check measured %d old refs (%d factory, %d "
                  "exam)%s" % (n_old + n_exam, n_old, n_exam,
                                "" if old_failed == (0, 0) else
                                " (unmeasured old refs are skipped for "
                                "dedup: %d factory, %d exam)"
                                % old_failed))
            for it in old_items:
                meas = measures.get(it["id"])
                if isinstance(meas, dict) and "volume" in meas:
                    against.append(
                        (meas["volume"], meas["bbox"]))
            for jid in exam_ids:
                meas = measures.get(jid)
                if isinstance(meas, dict) and "volume" in meas:
                    against.append(
                        (meas["volume"], meas["bbox"]))
            n_meas = save_measures(args.out + ".measures.json",
                                   new_measures)
            print("cloud-check saved %d measures to %s" % (
                n_meas, args.out + ".measures.json"))
            kept, dropped, failed_any = finalize_seed_jobs(
                jobs, new_measures)
            dupes = volume_bbox_duplicates(kept, new_measures,
                                           against=against)
            if dupes:
                print("cloud-check volume+bbox dupes dropped %d: %s"
                      % (len(dupes), ", ".join(dupes)))
                dupe_set = set(dupes)
                dropped.extend({"id": j["id"],
                                "reason": "volume+bbox duplicate"}
                               for j in kept if j["id"] in dupe_set)
                kept = [j for j in kept if j["id"] not in dupe_set]
            n_ok = len(kept)
            print("cloud-check %d/%d refs ok, spent $%.3f%s"
                  % (n_ok, len(jobs), spent,
                     " (stopped early)" if stopped else ""))
            jobs = kept
            with open(args.out + ".dropped.json", "w",
                      encoding="utf-8") as f:
                json.dump(dropped, f, indent=1)
            print("cloud-check dropped %d (see %s)"
                  % (len(dropped), args.out + ".dropped.json"))
        with open(args.out, "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(json.dumps(job) + "\n")
        print("wrote %d jobs to %s" % (len(jobs), args.out))
        print("sha256 %s %s" % (sha256_of_file(args.out),
                                os.path.basename(args.out)))
        if args.cloud_check and (failed_any or stopped):
            print("cloud-check FAILED: %s"
                  % ("some references failed" if failed_any else
                     "the run stopped before every job was checked"))
            return 1
        return 0
    jobs = generator.generate_all()
    dev_ids = generator.choose_dev_ids(jobs)
    dev_set = set(dev_ids)
    with open(os.path.join(args.out_dir, JOBS_NAME), "w",
              encoding="utf-8") as f:
        for job in jobs:
            f.write(json.dumps(job) + "\n")
    with open(os.path.join(args.out_dir, SPLIT_NAME), "w",
              encoding="utf-8") as f:
        json.dump({"seed": generator.SEED, "dev": dev_ids}, f, indent=1)
    with open(os.path.join(args.out_dir, DEV_JOBS_NAME), "w",
              encoding="utf-8") as f:
        for job in jobs:
            if job["id"] in dev_set:
                f.write(json.dumps(job) + "\n")
    print("wrote %d jobs, %d dev ids" % (len(jobs), len(dev_ids)))
    rows = self_check(jobs, exam_texts())
    ok = print_table(rows)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
