# Spec for Muse Code: B-max arm ("Glimmer + every fair cheap fix") on the first-test runner

Status: approved by the user 2026-10-29 ("YES 1", via hivey). Written by Claude. Build together with
`experiments/b2-hint/SANDBOX_SPEC.DRAFT.md` (the sandbox, read it first; it is part of this job).

## Why
New Forge goal (forge-wiki/wiki/decisions/new-goal-2026-10-29.md): the trained Glimmer must be about as correct as the
strongest fair version of Glimmer without training (B-max), and much cheaper and faster. B-max is that opponent. Every
fix in it is something a real company could do: none of them uses the reference answer.

## Rules for Muse Code
- Work in `~/projects/forge`. Edit only `experiments/first-test/runner.py` and `experiments/first-test/test_runner.py`;
  new files go in `experiments/b2-hint/` (sandbox) and `experiments/bmax/` (nothing else). Never open any `blind/`
  folder, `experiments/option-a/`, or the contents of `expected*.json`. Do not edit `experiments/keel-exam-v2/`.
- Existing arms (A, B, C, BR, B2) must behave exactly as today; all existing tests must still pass.
- No network or model calls, no commit, never print keys.

## 1. The sandbox
Exactly as `experiments/b2-hint/SANDBOX_SPEC.DRAFT.md` (`--sandbox PROFILE`, `sandbox_cq.sb`, `run_one_cq.py`, 60 s
limit, 4 GB RSS kill, `env -i`, scratch dirs under `--out`). Arm BX refuses to run without `--sandbox`.
`run_one_cq.py` additionally prints one JSON line `MEASURE {...}` with the built part's bounding box (xmin..zmax),
volume and number of solids (rounded to 0.01 mm / 0.1 mm³); the runner uses it only for the self-check message.

## 2. New arm `BX` (B-max), Glimmer only
Add `BX` to VALID_ARMS and GLIMMER_ARMS.
- **System message** = the B2 system message (SYSTEM_PROMPT + " " + hint from `experiments/b2-hint/hint.txt`).
- **User message (round 1)** = exactly arm B's user message, except that between the manual and the job text it inserts
  `"\n\nSolved examples (same style as your job):\n\n"` + each example from `experiments/bmax/examples.py`
  (`EXAMPLES`, keys `text`, `code`) formatted as `"Job: <text>\nAnswer:\n```python\n<code>\n```\n\n"`.
- **Request body**: the same as arm B (model, max_tokens 16000, temperature 1.0, top_p 0.95, top_k 64) plus
  `"chat_template_kwargs": {"reasoning_strength": "high"}`. Only BX gets this key.
- **Rounds (at most 3 model calls per job, one conversation):**
  1. Extract the code (same extractor as today) and run it in the sandbox.
  2. If it fails (no code, crash, timeout, no `result`), append the assistant reply and a user message:
     `"Your code failed when it ran:\n<first 2000 chars of the error>\nFix it. Reply with the full corrected program in one Python code block."`
  3. If it builds, append the assistant reply and a user message with its own measurements (never the reference):
     `"Your part was built. Measured: bounding box X <xmin> to <xmax>, Y <ymin> to <ymax>, Z <zmin> to <zmax>; volume <v> mm³; <n> solid(s). Compare this with every number in the job. If the part matches the job, reply with exactly the word DONE. Otherwise reply with the full corrected program in one Python code block."`
  4. Stop when the model replies DONE (no code block), or after the 3rd call.
  - **Final answer** = the most recent program that built. If none built: FAIL with the last error.
  - A reply cut off by the token limit: in round 1 → INVALID (as today); in round 2 or 3 → stop and keep the most
    recent program that built (FAIL if none).
  - The referee scores only the final answer, once, exactly as for the other arms.
- **Logged per job** (in calls.jsonl, one record per round plus a final record): round number, prompt_tokens,
  completion_tokens, reasoning_len, latency (s), what happened (crash / built / DONE / cut off), and the final verdict.

## 3. Cost and speed numbers (all arms)
Per arm in the summary/report: pass rate (as today), mean model calls per job, mean total tokens per job (prompt +
completion, all rounds), mean summed call latency per job, and tokens per correct part plus latency per correct part
(sum ÷ number of PASS). Read token counts from the server's `usage` fields, not an estimate.

## 4. Tests (no network; fake post_fn)
a. BX messages: the system message ends with the hint; the user message contains the manual, then the 3 examples,
   then the job text; the BX body has chat_template_kwargs, while B/B2 bodies are unchanged (byte-for-byte as before).
b. Loop: a fake model that returns crashing code then good code → 2 calls, the error text is in the 2nd user message,
   final = the good program, PASS. A fake that returns good code then "DONE" → 2 calls, stops. A fake that never says
   DONE → exactly 3 calls. Good code, then crashing code → final = the earlier good program.
c. The self-check message is built by a function that receives only the MEASURE values (no reference, no
   expected values in its arguments or closure); test that its text contains exactly those numbers.
d. Token and latency totals sum across rounds.
e. All sandbox tests of SANDBOX_SPEC item 5.
Run `~/projects/forge/.venv/bin/python -m pytest -q experiments/first-test/test_runner.py` until all pass.

## 5. Checks already done by Claude (2026-10-29)
- The B2 hint is general (no job-specific numbers); written before any B2 run (experiments/b2-hint/PLAN.md).
- The 3 B-max examples are new parts from families not in the exam (nameplate with recess, plus-shaped spacer, tube
  with cross hole; the exam families are listed in experiments/first-test/jobs-list.md). They build to the stated
  bounding boxes and volumes (`python experiments/bmax/examples.py` → 3× OK).
