#!/usr/bin/env python3
"""Build the R5 training mix from Glimmer's own guided solutions.

Inputs: the R5T first-try, self-fix and hint-retry calls.jsonl files
(PASS only) plus the R5T jobs file (for job texts). Row kinds:

- first-try rows: job text -> thinking + code (source glimmer-first);
- self-fix rows: job + wrong code + reference-free feedback -> thinking
  + fixed code (source glimmer-selffix);
- hint-retry PASSes: added as FIRST-TRY rows only (N2: the hint retry
  was prompted as job + hint, i.e. first-try form, so its reasoning
  never saw the wrong code or feedback a self-fix row would show),
  with the hint STRIPPED; dropped when the reasoning says "hint"/"tutor"
  or copies >= 8 words of the hint (source glimmer-hinted).

Rules: rows with reasoning < 200 chars are dropped (no code-only rows);
at most 2 rows per job. Asserts: no row contains "Hint from a tutor", no
dev/exam id or text, no Wonder output. Prints rows per source and token
totals.

Option B (train WITHOUT the card): --drop-card-mentions drops rows
whose reasoning NAMES the card ("rule card", "card says", "per the
card", "cheat sheet", "the card", case-insensitive). Rows that only
quote or follow true rules without naming the card are KEPT. The drop
share is printed per source; more than 20% dropped overall stops the
run (non-zero exit). --first is repeatable (pilot v2 calls.jsonl +
rest-run calls.jsonl). Records from the v1 pilot are refused: any
input file under results/r5-pilot-2026-10-31/ is an error (the v1
pilot used card v1, a prompt mismatch; prompt_tokens ranges overlap,
so paths -- not token counts -- tell v1 from v2, S4).
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_DIR = os.path.join(os.path.dirname(HERE), "final")
if FINAL_DIR not in sys.path:
    sys.path.insert(0, FINAL_DIR)

import runner_final  # noqa: E402 (hint prefix, selffix text)

MIN_REASONING_CHARS = 200
MAX_ROWS_PER_JOB = 2
HINT_MARKER = "Hint from a tutor"

VALID_SOURCES = ("glimmer-first", "glimmer-selffix", "glimmer-hinted")
HINT_COPY_WORDS = 8

# Option B: reasoning that NAMES the card is dropped (rows that only
# quote or follow true rules are kept). Case-insensitive substrings.
CARD_MENTION_PATTERNS = ("rule card", "card says", "per the card",
                         "cheat sheet", "the card")
CARD_DROP_STOP_FRAC = 0.20

# The v1 pilot (card v1, prompt mismatch) is kept as a record and never
# trains: any input file under this dir is refused by path (S4: v1/v2
# prompt_tokens ranges overlap, so token counts cannot tell them apart).
V1_PILOT_DIRNAME = "r5-pilot-2026-10-31"


def reasoning_names_card(reasoning):
    """True when reasoning NAMES the card (option B drop rule).

    Case-insensitive match on CARD_MENTION_PATTERNS. Reasoning that
    only quotes or follows true rules without naming the card returns
    False (kept: that is the point of option B).
    """
    text = (reasoning or "").lower()
    return any(pat in text for pat in CARD_MENTION_PATTERNS)


def refuse_v1_pilot_paths(paths):
    """Refuse v1 pilot inputs by path (S4).

    Raises ValueError naming the file when any input path lives under
    results/r5-pilot-2026-10-31/ (the v1 pilot used card v1: a prompt
    mismatch with the v2-trained rows).
    """
    for path in paths or ():
        if not path:
            continue
        parts = os.path.abspath(str(path)).split(os.sep)
        if V1_PILOT_DIRNAME in parts:
            raise ValueError(
                "refusing v1 pilot input %r: the v1 pilot "
                "results/r5-pilot-2026-10-31/ used rule card v1 (prompt "
                "mismatch); train only on v2 runs (pilot v2 + rest run)"
                % (path,))
    return True


def load_calls(path):
    """Read a calls.jsonl file."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_jobs(path):
    """R5T jobs file -> {id: {text, family}}."""
    with open(path, encoding="utf-8") as f:
        jobs = [json.loads(line) for line in f if line.strip()]
    return {j["id"]: j for j in jobs}


def reasoning_cites_hint(reasoning, hint):
    """True when reasoning mentions the hint or copies >= 8 of its words.

    Case-insensitive; "hint"/"tutor" anywhere rejects, else any 8-gram of
    the hint's words appearing in order in the reasoning rejects.
    """
    text = (reasoning or "").lower()
    if "hint" in text or "tutor" in text:
        return True
    hint_words = (hint or "").lower().split()
    if len(hint_words) < HINT_COPY_WORDS:
        return False
    grams = {" ".join(hint_words[i:i + HINT_COPY_WORDS])
             for i in range(len(hint_words) - HINT_COPY_WORDS + 1)}
    flat = " ".join(text.split())
    return any(g in flat for g in grams)


def pass_records(calls):
    """PASS-only records (verdict or outcome)."""
    return [r for r in calls
            if (r.get("verdict", r.get("outcome")) == "PASS")]


def build_rows(first_calls, selffix_calls, hint_calls, jobs_by_id,
               drop_card_mentions=False):
    """Build mix rows; returns (rows, counts) with drop counters.

    With drop_card_mentions=True (option B) rows whose reasoning NAMES
    the card are dropped and counted per source in
    counts["card_dropped_by_source"]; rows that only quote or follow
    true rules are kept.
    """
    rows, counts = [], {"glimmer-first": 0, "glimmer-selffix": 0,
                        "glimmer-hinted": 0, "dropped_short": 0,
                        "dropped_hint_cite": 0, "dropped_card_mention": 0,
                        "card_dropped_by_source": {}}
    per_job = {}

    def _add(job_id, text, code, reasoning, source):
        if not isinstance(reasoning, str) \
                or len(reasoning) < MIN_REASONING_CHARS:
            counts["dropped_short"] += 1
            return
        if drop_card_mentions and reasoning_names_card(reasoning):
            counts["dropped_card_mention"] += 1
            by_src = counts["card_dropped_by_source"]
            by_src[source] = by_src.get(source, 0) + 1
            return
        if per_job.get(job_id, 0) >= MAX_ROWS_PER_JOB:
            return
        rows.append({"id": job_id, "text": text, "code": code,
                     "reasoning": reasoning, "source": source})
        per_job[job_id] = per_job.get(job_id, 0) + 1
        counts[source] += 1

    for rec in pass_records(first_calls):
        job = jobs_by_id.get(rec.get("job"))
        if job is None:
            continue
        _add(rec["job"], job["text"], rec.get("code") or "",
              rec.get("reasoning") or "", "glimmer-first")
    for rec in pass_records(selffix_calls):
        job = jobs_by_id.get(rec.get("job"))
        if job is None:
            continue
        wrong = rec.get("selffix_wrong_code", "")
        feedback = rec.get("selffix_feedback") or \
            "The code ran but the shape was wrong. Fix the code."
        text = runner_final.build_selffix_user_text(
            job["text"], wrong, feedback)
        _add(rec["job"], text, rec.get("code") or "",
              rec.get("reasoning") or "", "glimmer-selffix")
    for rec in pass_records(hint_calls):
        job = jobs_by_id.get(rec.get("job"))
        if job is None:
            continue
        hint = rec.get("hint") or ""
        reasoning = rec.get("reasoning") or ""
        if hint and reasoning_cites_hint(reasoning, hint):
            counts["dropped_hint_cite"] += 1
            continue
        # N2: FIRST-TRY kind only, hint STRIPPED (plain job text). Never
        # a self-fix row: the hint retry never saw wrong code/feedback.
        _add(rec["job"], job["text"], rec.get("code") or "",
              reasoning, "glimmer-hinted")
    return rows, counts


def card_drop_shares(counts):
    """Card-mention drop share per source and overall (option B).

    Per source: dropped_s / (kept_s + dropped_s); overall:
    dropped / (kept + dropped), where kept counts rows that passed
    every other filter. A source (or the run) with no candidate rows
    has share 0.0.
    """
    by_src = (counts or {}).get("card_dropped_by_source") or {}
    per_source = {}
    for src in VALID_SOURCES:
        dropped = by_src.get(src, 0)
        denom = (counts or {}).get(src, 0) + dropped
        per_source[src] = (dropped / denom) if denom else 0.0
    total_dropped = (counts or {}).get("dropped_card_mention", 0)
    total_kept = sum((counts or {}).get(src, 0) for src in VALID_SOURCES)
    denom = total_kept + total_dropped
    return per_source, (total_dropped / denom) if denom else 0.0


def assert_mix(rows, dev_ids=(), exam_texts=(), dev_texts=()):
    """Fire on hint text, dev/exam ids or texts, or Wonder output."""
    dev_id_set = set(dev_ids or ())
    banned_texts = set(exam_texts or ()) | set(dev_texts or ())
    for row in rows:
        if HINT_MARKER in (row.get("text") or ""):
            raise ValueError(
                "mix row %r contains hint text" % (row.get("id"),))
        if row.get("id") in dev_id_set:
            raise ValueError(
                "mix row %r is a dev id" % (row.get("id"),))
        if not str(row.get("id", "")).startswith("R5T-"):
            raise ValueError(
                "mix row %r is not an R5T id" % (row.get("id"),))
        if row.get("text") in banned_texts:
            raise ValueError(
                "mix row %r matches a dev/exam text" % (row.get("id"),))
        if row.get("teacher") == "wonder" or row.get("teacher") == "spark":
            raise ValueError(
                "mix row %r carries teacher output" % (row.get("id"),))
        if "wonder" in str(row.get("source", "")).lower():
            raise ValueError(
                "mix row %r has a Wonder source" % (row.get("id"),))
    return True


def token_totals(rows):
    """Whitespace-token totals per source (offline estimate)."""
    totals = {}
    for row in rows:
        totals[row["source"]] = totals.get(row["source"], 0) + len(
            (row.get("text", "") + " " + row.get("reasoning", "")
             + " " + row.get("code", "")).split())
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the R5 training mix.")
    parser.add_argument("--first", required=True, action="append",
                        help="first-try calls.jsonl (PASS only kept); "
                             "repeatable: pilot v2 + rest-run files "
                             "concatenate (S1)")
    parser.add_argument("--selffix", default=None,
                        help="self-fix calls.jsonl")
    parser.add_argument("--hinted", default=None,
                        help="hint-retry calls.jsonl")
    parser.add_argument("--jobs", required=True,
                        help="R5T jobs file (job texts)")
    parser.add_argument("--dev-ids", default=None,
                        help="split/dev ids JSON (asserted absent)")
    parser.add_argument("--dev-jobs", default=None,
                        help="R5D jobs file: dev TEXTS are loaded from "
                             "here (N2; the R5T jobs file cannot hold "
                             "R5D texts)")
    parser.add_argument("--exam-texts", default=None,
                        help="exam texts JSON list (asserted absent)")
    parser.add_argument("--drop-card-mentions", action="store_true",
                        help="option B: drop rows whose reasoning NAMES "
                             "the card (rows quoting true rules kept); "
                             "stops non-zero when over 20%% are dropped")
    parser.add_argument("--out", required=True,
                        help="output train_records.jsonl")
    args = parser.parse_args(argv)
    refuse_v1_pilot_paths(
        list(args.first or []) + [args.selffix, args.hinted, args.jobs,
                                  args.dev_ids, args.dev_jobs,
                                  args.exam_texts])
    jobs_by_id = load_jobs(args.jobs)
    first_calls = []
    for path in args.first:
        first_calls.extend(load_calls(path))
    selffix_calls = load_calls(args.selffix) if args.selffix else []
    hint_calls = load_calls(args.hinted) if args.hinted else []
    rows, counts = build_rows(first_calls, selffix_calls, hint_calls,
                              jobs_by_id,
                              drop_card_mentions=args.drop_card_mentions)
    if args.drop_card_mentions:
        per_source, overall = card_drop_shares(counts)
        print("CARD_MENTION_DROP overall=%.3f %s" % (
            overall, json.dumps(
                {src: round(per_source[src], 3) for src in VALID_SOURCES},
                sort_keys=True)))
        if overall > CARD_DROP_STOP_FRAC:
            print("CARD_MENTION_STOP dropped %.1f%% of rows (over %.0f%%); "
                  "refusing to write the mix" % (
                      100.0 * overall, 100.0 * CARD_DROP_STOP_FRAC))
            return 1
    dev_ids, exam_texts = [], []
    if args.dev_ids and os.path.isfile(args.dev_ids):
        with open(args.dev_ids, encoding="utf-8") as f:
            data = json.load(f)
        dev_ids = data.get("dev", data) if isinstance(data, dict) \
            else data
    if args.exam_texts and os.path.isfile(args.exam_texts):
        with open(args.exam_texts, encoding="utf-8") as f:
            exam_texts = json.load(f)
    if args.dev_jobs and os.path.isfile(args.dev_jobs):
        # N2: R5D texts come from the R5D file (the R5T jobs file never
        # holds them, so the old lookup never fired).
        dev_texts = [j["text"] for j in load_jobs(args.dev_jobs).values()
                     if isinstance(j.get("text"), str)]
    else:
        dev_texts = [jobs_by_id[i]["text"] for i in dev_ids
                     if i in jobs_by_id]
    assert_mix(rows, dev_ids, exam_texts, dev_texts)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    totals = token_totals(rows)
    print("MIX rows=%d first=%d selffix=%d hinted=%d "
          "dropped_short=%d dropped_hint_cite=%d dropped_card_mention=%d"
          % (len(rows), counts["glimmer-first"],
             counts["glimmer-selffix"], counts["glimmer-hinted"],
             counts["dropped_short"], counts["dropped_hint_cite"],
             counts["dropped_card_mention"]))
    print("MIX tokens %s" % json.dumps(totals, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
