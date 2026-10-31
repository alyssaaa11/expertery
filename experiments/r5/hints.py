#!/usr/bin/env python3
"""Spark tutor hints for Glimmer's failed factory answers (R5 PLAN step 5).

Input: a calls.jsonl of FAILED records (job id, job text, Glimmer's code,
referee failed_checks). For each, Spark Open on Baseten (teacher.py's
client, key handling and budget guard) gets a fixed hint prompt and
returns ONE short hint (max 60 words, no code). A hint with a code fence,
`cq.`, `import`, or more than 60 words is rejected (record hint_rejected).

Order: jobs sorted by family then a seeded shuffle (seed 20261031)
round-robin across families, so every family gets hints. --max-hints 230
is a hard limit; --budget dollars is a hard stop (teacher.py's guard).

Output: hints.jsonl rows {id, hint, hint_words, rejected, usd} plus
summary.json {n, n_rejected, usd, usd_per_hint}.

No network, Modal run, model call or key printing happens before the env
check: with no key the command exits 2 naming the variable. Tests inject
a fake post fn.
"""

import argparse
import json
import os
import random
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY_DIR = os.path.join(os.path.dirname(HERE), "factory")
if FACTORY_DIR not in sys.path:
    sys.path.insert(0, FACTORY_DIR)

import teacher  # noqa: E402 (client, key handling, budget guard)

HINT_ORDER_SEED = 20261031
MAX_HINT_WORDS = 60
DEFAULT_MAX_HINTS = 230
HINT_MAX_TOKENS = 1000
HINT_TEMPERATURE = 0.7

HINT_SYSTEM = "You are a CAD tutor."
FORBIDDEN_SUBSTRINGS = ("```", "cq.", "import")


def build_hint_prompt(job_text, code, failed_checks):
    """The fixed hint prompt (no code is ever requested back)."""
    checks = ", ".join(str(c) for c in (failed_checks or [])) or "(none)"
    return (
        "You are a CAD tutor. A student wrote this CadQuery code for "
        "the job below; the referee says these checks failed: %s. "
        "Give ONE short hint (max 60 words) that points to the mistake. "
        "Do NOT write code.\n\nJob:\n%s\n\nStudent code:\n```python\n%s\n```"
        % (checks, job_text, code or "")
    )


def build_hint_messages(job_text, code, failed_checks):
    """System + hint prompt messages for Spark."""
    return [
        {"role": "system", "content": HINT_SYSTEM},
        {"role": "user",
         "content": build_hint_prompt(job_text, code, failed_checks)},
    ]


def hint_word_count(hint):
    """Word count of a hint (whitespace split)."""
    return len((hint or "").split())


def is_hint_rejected(hint):
    """True when a hint breaks the no-code / 60-word rules."""
    text = hint or ""
    if any(sub in text for sub in FORBIDDEN_SUBSTRINGS):
        return True
    return hint_word_count(text) > MAX_HINT_WORDS


def order_hints(records):
    """Seeded family round-robin order (seed 20261031).

    Jobs sorted by family, each family's ids shuffled with one seeded
    RNG, then round-robin across families so every family gets hints.
    """
    by_family = {}
    for rec in records:
        by_family.setdefault(rec.get("family", 0), []).append(rec)
    rng = random.Random(HINT_ORDER_SEED)
    for fam in by_family:
        by_family[fam] = sorted(
            by_family[fam], key=lambda r: str(r.get("id")))
        rng.shuffle(by_family[fam])
    out = []
    families = sorted(by_family)
    index = 0
    while True:
        progressed = False
        for fam in families:
            if index < len(by_family[fam]):
                out.append(by_family[fam][index])
                progressed = True
        if not progressed:
            break
        index += 1
    return out


def do_hint_call(record, post_fn):
    """One hint call: returns (hint, usage). Never raises for a bad call.

    A failed call returns ("", {}); the caller records it rejected.
    """
    messages = build_hint_messages(
        record.get("text", record.get("job_text", "")),
        record.get("code", record.get("extracted_code", "")),
        record.get("failed_checks", record.get("fails", [])))
    body = dict(teacher.build_body(teacher.SPARK_MODEL, messages))
    body["max_tokens"] = HINT_MAX_TOKENS
    body["temperature"] = HINT_TEMPERATURE
    try:
        data = post_fn(body)
    except Exception:  # noqa: BLE001 -- failed call is a rejected hint
        return "", {}
    try:
        content = ((data.get("choices") or [{}])[0] or {}).get(
            "message", {}).get("content", "")
    except (AttributeError, IndexError, TypeError):
        content = ""
    usage = data.get("usage") if isinstance(data, dict) else {}
    return content or "", usage if isinstance(usage, dict) else {}


def run_hints(records, post_fn, budget, max_hints=DEFAULT_MAX_HINTS):
    """Hint at most max_hints failed records in round-robin order.

    Hard stop: no NEW calls once teacher.over_budget(spent, budget).
    Returns (rows, summary).
    """
    ordered = order_hints(records)[:max(0, int(max_hints))]
    rows, spent, n_rejected = [], 0.0, 0
    for rec in ordered:
        if teacher.over_budget(spent, budget):
            break
        hint, usage = do_hint_call(rec, post_fn)
        usd = teacher.cost_of_usage(usage)
        spent += usd
        rejected = (not (hint or "").strip()) or is_hint_rejected(hint)
        n_rejected += 1 if rejected else 0
        rows.append({
            "id": rec.get("id", rec.get("job")),
            "family": rec.get("family"),
            "hint": hint,
            "hint_words": hint_word_count(hint),
            "rejected": bool(rejected),
            "usd": round(usd, 6),
        })
    summary = {
        "n": len(rows),
        "n_rejected": n_rejected,
        "usd": round(spent, 6),
        "usd_per_hint": round(spent / len(rows), 6) if rows else None,
    }
    return rows, summary


def load_failed_records(path):
    """Read a calls.jsonl file (FAILED records in, order fixed later)."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Spark tutor hints for failed factory answers.")
    parser.add_argument("--calls", required=True,
                        help="calls.jsonl of FAILED records")
    parser.add_argument("--out", required=True,
                        help="output dir for hints.jsonl + summary.json")
    parser.add_argument("--budget", type=float, required=True,
                        help="Baseten dollars (hard stop, like teacher.py)")
    parser.add_argument("--max-hints", type=int, default=DEFAULT_MAX_HINTS,
                        help="hard limit on hint calls (default 230)")
    args = parser.parse_args(argv)
    if args.max_hints is not None and args.max_hints > DEFAULT_MAX_HINTS:
        parser.error("--max-hints is capped at %d" % DEFAULT_MAX_HINTS)
    baseten_key = os.environ.get("BASETEN_KEY", "")
    if not baseten_key:
        parser.error("missing environment variables: BASETEN_KEY")
        return 2
    records = [r for r in load_failed_records(args.calls)
               if (r.get("verdict", r.get("outcome")) == "FAIL")]
    affinity = uuid.uuid4().hex
    post_fn = teacher.real_post_fn(
        teacher.SPARK_URL, baseten_key, affinity)
    rows, summary = run_hints(records, post_fn, args.budget,
                              max_hints=args.max_hints)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "hints.jsonl"), "w",
              encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    with open(os.path.join(args.out, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print("HINTS n=%d rejected=%d usd=%.4f usd_per_hint=%s" % (
        summary["n"], summary["n_rejected"], summary["usd"],
        summary["usd_per_hint"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
