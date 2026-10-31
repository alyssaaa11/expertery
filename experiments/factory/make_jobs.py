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
CLOUD_CHECK_COST_PER_JOB = 0.005  # $ budget accounting per cloud check

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


def cloud_check_jobs(jobs, budget, exec_fn=None, measure_fn=None):
    """Reference self-check + volume/bbox measure in the cloud box.

    Each job's reference runs via exec_fn (default: cloud_cq box) and its
    BREP is measured via measure_fn (default: cloud_cq measure_brep).
    Returns (results, spent) where results maps id -> {"volume", "bbox",
    "solids"} or {"error"}. Stops starting NEW checks once spent +
    CLOUD_CHECK_COST_PER_JOB passes the budget (in-flight checks still
    count). Volume+bbox duplicates are found by the caller from results.
    """
    if exec_fn is None or measure_fn is None:
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
        if exec_fn is None:
            exec_fn = _cq.run_answer_in_box
        if measure_fn is None:
            remote = getattr(_cq.measure_brep, "remote",
                             _cq.measure_brep)
            measure_fn = remote
    results, spent, stopped = {}, 0.0, False
    for job in jobs:
        if spent + CLOUD_CHECK_COST_PER_JOB > float(budget):
            stopped = True
            break
        try:
            boxed = exec_fn(job["reference"])
        except Exception as e:  # noqa: BLE001 -- harness error is FAIL
            results[job["id"]] = {"error": "harness: %r" % (e,)}
            continue
        finally:
            spent += CLOUD_CHECK_COST_PER_JOB
        brep = (boxed or {}).get("brep_bytes")
        if brep is None:
            results[job["id"]] = {
                "error": (boxed or {}).get("run_error")
                or "the answer wrote no BREP"}
            continue
        try:
            meas = measure_fn(bytes(brep))
        except Exception as e:  # noqa: BLE001 -- grader down
            results[job["id"]] = {"error": "measure: %r" % (e,)}
            continue
        try:
            results[job["id"]] = {
                "volume": float(meas["volume"]),
                "bbox": [float(v) for v in meas["bbox"]],
                "solids": int(meas.get("solids", 1)),
            }
        except (KeyError, TypeError, ValueError):
            results[job["id"]] = {"error": "bad measure %r" % (meas,)}
    return results, spent, stopped


def volume_bbox_duplicates(jobs, measures, tol=1e-6):
    """Ids whose measured (volume, bbox) duplicates an earlier job's."""
    seen, dupes = [], set()
    for job in jobs:
        meas = measures.get(job["id"])
        if not isinstance(meas, dict) or "volume" not in meas:
            continue
        key = (meas["volume"], tuple(meas["bbox"]))
        for prev in seen:
            if abs(key[0] - prev[0]) <= tol and all(
                    abs(a - b) <= tol for a, b in zip(key[1], prev[1])):
                dupes.add(job["id"])
                break
        else:
            seen.append(key)
    return sorted(dupes)


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
            measures, spent, stopped = cloud_check_jobs(
                jobs, args.budget)
            dupes = volume_bbox_duplicates(jobs, measures)
            n_ok = sum(1 for j in jobs
                       if isinstance(measures.get(j["id"]), dict)
                       and "volume" in measures.get(j["id"]))
            print("cloud-check %d/%d refs ok, spent $%.3f%s"
                  % (n_ok, len(jobs), spent,
                     " (budget stopped)" if stopped else ""))
            if dupes:
                print("cloud-check volume+bbox dupes dropped %d: %s"
                      % (len(dupes), ", ".join(dupes)))
                jobs = [j for j in jobs if j["id"] not in set(dupes)]
        with open(args.out, "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(json.dumps(job) + "\n")
        print("wrote %d jobs to %s" % (len(jobs), args.out))
        print("sha256 %s %s" % (sha256_of_file(args.out),
                                os.path.basename(args.out)))
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
