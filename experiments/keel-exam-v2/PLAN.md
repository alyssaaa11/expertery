# Keel v2 baseline test: PLAN (draft, not frozen)

Supersedes `experiments/keel-exam/` (v1 exam, kept as history: the user asked for a more realistic tool, 2026-10-28).

Status: **draft** (2026-10-29 ~00:10, verifier fixes applied). Becomes frozen (read-only) only after: blind rebuild 30/30, verifier GO, the
user's yes. Nothing paid runs before that.

## 1. Question
On a private tool no model has seen (Keel 2.0, of the fictional Quillon Orbital Works), with only the company manual:
1. Can the teacher (Spark Open) do the work? If not, it cannot teach, and the factory stops here cheaply.
2. Is the small model (Glimmer) clearly worse? If Glimmer + manual is already good, training has nothing to add.

## 2. Arms (30 held-out exam jobs each, one answer per job, no retries)
| Arm | Model | Gets |
|---|---|---|
| B | Muse Glimmer 30B on Modal (A100-80GB, vLLM, as in the first test) | Keel manual + request |
| C | Muse Spark Open on Baseten | Keel manual + request |
No arm A (Glimmer without the manual): it cannot know Keel's names, so it would score ~0 and cost money for nothing.
Same prompt for both, same sampling as the first test (temperature 1.0, top_p 0.95, top_k 64, max_tokens 16000).

## 3. Exam and referee (verified before the run)
- 30 jobs (15 medium, 15 hard) in `jobs.py`, written by Claude, not by a Meta model; realistic requests (materials, flight class, company mounts, FRM centre dimensions, wall holes, mirror) that need the manual v2. Part numbers differ from the
  manual's examples; no exam job may enter practice data later.
- Referee: `referee.py` (this folder) = first-test `checks.py` unchanged, overlap tolerance **1e-6** (0.0001%).
  Reason (verifier audit 2026-10-28): correct answers written differently and a STEP round trip match to ~2e-14;
  0.01% let a missing standard fillet PASS on large parts (0.006–0.009%). The runner must import `referee.py`.
- Keel 2.1 (verifier fix): cuts are applied after all walls and bosses whatever the call order, and no cut removes
  material above its local top. Exam references must be unchanged by this (checked by re-running the self-test).
- Self-test 90/90 (30 references pass, 60 wrong versions fail; smallest wrong-version mismatch 0.0133%, alternative correct programs 0.00000000%). Blind rebuild 30/30 (fresh helper, manual v2 + texts only; it hit and solved the mirror/pattern trap in H2, H15; notes in blind/NOTES.md, no text changes needed).

## 4. Decision rules (ordered, first match wins, whole points)
0. INVALID > 5% in either arm (more than 1 of 30 answers cut off, empty, or a network/HTTP failure after one retry)
   → **RUN INVALID**: fix the cause, rerun that arm; no decision from this run.
1. C < 30 → **STOP**: the teacher cannot use an unseen tool from its manual; rethink (e.g. a richer manual).
2. B ≥ 80 → **NO ROOM**: Glimmer + manual is already good; training cannot show much; rethink the tool.
3. C − B ≥ 25 and B ≤ 70 → **GO**: build the factory (practice generator → teacher run → training). Bar 25, the
   same as the first test.
4. Otherwise → **GREY**: report to the user, who decides.
Paired McNemar test on B vs C reported alongside (not part of the rule). Scores = PASS / 30 (INVALID counts as not
PASS in the score, and is reported separately).

## 4b. Prompt and answer format (fixed)
- Messages: system = "You write programs for Keel, Quillon Orbital Works' private part-description tool. Units are
  millimetres. Follow the Keel manual exactly. The program must start with `import keel`, create the part with
  `p = keel.part(...)`, and end with `solid = p.finish()`. Reply with exactly one Python code block and nothing
  else."; user 1 = "Here is the Keel manual. Use it.\n\n" + `company/manual.md`; user 2 = the request text.
- Answer: the first fenced code block (```python or ```), else the whole reply. Run in a fresh subprocess with
  `company/` on the path and a 120 s timeout; the part is the variable `solid`. FAIL = it raises (incl. KeelError),
  `solid` is missing, or the referee fails it. INVALID = cut off by the token limit, empty reply, or network failure.

## 5. Cost (estimate) and safety
Modal ~$0.70 (cold start ~7 min + ~15 min), Baseten ~$0.80, runner change by Muse Code ~$0.30 → **~$1.80**.
Spent so far ≈ $5.2 of $30 (incl. Keel v2 build ~$0.80). Budget caps in the runner as before (`--budget`), app stopped with `-y` and checked.

## 6. What changes in the runner (Muse Code, from a spec)
Prompt with the Keel manual; answers are Keel programs; build with `keel` and judge with `referee.py` against
`expected.json`; arms B and C only. Everything else (logging, caps, report) as in the first test.
