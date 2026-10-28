# Spec: first-test runner (for Muse Code to build)

Build one Python 3.12 program, `runner.py`, in this folder. It runs the first test described in `PLAN.md`: it sends each
job to each contestant model, runs the returned CadQuery code, scores it with the existing `checks.py`, and logs
everything. Do not change `jobs.py`, `checks.py`, `expected.json`, `manual.md` or `PLAN.md`: they are frozen.

## Inputs (already in this folder)
- `jobs.py`: `JOBS`, a list of dicts with `id`, `level` (`medium`, `hard`, `dry`), `text` and `build()` (the reference part).
- `checks.py`: `score(answer, reference, expected) -> (passed, fails, measurements)`.
- `expected.json`: measurements of each reference part, keyed by job id.
- `manual.md`: the CadQuery manual given to arms B and C.

## Contestants (arms)
| Arm | Endpoint | Model | Manual |
|---|---|---|---|
| A | env `GLIMMER_URL` + `/v1/chat/completions`, bearer key from env `GLIMMER_KEY` | `muse-glimmer` | no |
| B | same as A | `muse-glimmer` | yes |
| C | `https://inference.baseten.co/v1/chat/completions`, bearer key from env `BASETEN_KEY` | `meta-models/muse-spark-open-1026` | yes |
- Keys come only from environment variables. Never print, log or write a key to any file.
- Use only the standard library for HTTP (`urllib.request`), plus `cadquery` from the venv.

## Messages (exactly these, no other words)
- System: `You write CadQuery Python code. Units are millimetres. Assign the final solid to a variable named result. Reply with exactly one Python code block and nothing else.`
- Arms B and C: first user message `Here is the CadQuery manual. Use it.\n\n` + contents of `manual.md`, then the job text
  as a second user message. Arm A: only the job text as the user message.
- Request body: `{"model": ..., "messages": ..., "max_tokens": 8000, "temperature": 0.6}`. Nothing else.

## Running
- CLI: `runner.py --jobs dry|main --out <dir>`. `dry` = the 3 jobs with level `dry`; `main` = the 30 medium + hard jobs.
- Each (job, arm) pair is called exactly once, in a fresh conversation. No retries on a bad answer. One retry is allowed
  only for a network error or HTTP 5xx/429, after 20 s.
- Run up to 16 calls at the same time in total (thread pool). Per-call timeout 600 s.
- Budget guard: keep a running cost estimate. Arm C: input tokens × $1.25/M + output tokens × $4.25/M (from `usage`).
  Arms A and B: wall-clock time of the whole run × $2.50/h (A100-80GB), counted once. Stop sending new calls if the
  estimate passes $5 (`--budget`, default 5.0) and record it.

## Scoring each answer
1. Take the first fenced code block (```python or ```) from `message.content`. No block → use the whole content.
2. Run it in a separate process: `<venv python> -I -c <wrapper>` with cwd `/tmp`, time limit 60 s. The wrapper runs the
   code, then pickles nothing: it exports `result` as a STEP file to a temp path and prints that path.
3. In the runner, import the STEP (`cadquery.importers.importStep`), then `checks.score(answer, job['build'](),
   expected[id])`.
- Outcomes: **PASS** (score passed), **FAIL** (wrong shape, code error, timeout, no `result`), **INVALID**
  (`finish_reason == "length"`, empty content, or a network/HTTP error after the retry). INVALID is never FAIL.

## Output (in `--out`)
- `calls.jsonl`: one line per call: job, level, arm, model, start/end time, seconds, finish_reason, usage, content,
  reasoning length (not the reasoning text), extracted code, outcome, failed checks, measurements, run error (last
  800 chars).
- `summary.json` and `report.md`: per arm and per level: PASS / FAIL / INVALID counts and pass rate (PASS ÷ (PASS +
  FAIL)); INVALID rate; the PLAN.md section 7 decision computed from the numbers (GO / STOP / Spark can't teach /
  grey zone, and "run not valid" if INVALID > 5% in any arm); estimated cost per arm and total; a per-job table
  (rows = jobs, columns = A/B/C outcome).

## Tests to include (`test_runner.py`, run with the venv's pytest, no network)
- Code extraction: fenced python block, plain fence, no fence.
- A fake model answer containing a reference-like correct CadQuery program for job D2 scores PASS; a wrong one scores
  FAIL; `finish_reason == "length"` scores INVALID.
- The budget guard stops new calls once the estimate passes the budget.
- No key ever appears in `calls.jsonl` (check with a fake key string).
