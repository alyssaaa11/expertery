# Keel baseline test: PLAN (draft, not frozen)

Status: **draft** (2026-10-28 ~23:00). Becomes frozen (read-only) only after: blind rebuild 30/30, verifier GO, the
user's yes. Nothing paid runs before that.

## 1. Question
On a private tool no model has seen (Keel, of the fictional Quillon Orbital Works), with only the company manual:
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
- 30 jobs (15 medium, 15 hard) in `jobs.py`, written by Claude, not by a Meta model. Part numbers differ from the
  manual's examples; no exam job may enter practice data later.
- Referee: `referee.py` = first-test `checks.py` unchanged, overlap tolerance 0.01% instead of 0.2%. Reason
  (verified 2026-10-28): correct answers written differently match exactly (0.00000000% on H1, H2); the smallest
  real error (missing 1 mm fillet, M2) is 0.0193%, which 0.2% let pass.
- Self-test 90/90 (30 references pass, 60 wrong versions fail). Blind rebuild: pending.

## 4. Decision rules (ordered, first match wins, whole points)
1. C < 30 → **STOP**: the teacher cannot use an unseen tool from its manual; rethink (e.g. a richer manual).
2. B ≥ 80 → **NO ROOM**: Glimmer + manual is already good; training cannot show much; rethink the tool.
3. C − B ≥ 20 and B ≤ 70 → **GO**: build the factory (practice generator → teacher run → training).
4. Otherwise → **GREY**: report to the user, who decides.
Paired McNemar test on B vs C reported alongside (not part of the rule).

## 5. Cost (estimate) and safety
Modal ~$0.70 (cold start ~7 min + ~15 min), Baseten ~$0.80, runner change by Muse Code ~$0.30 → **~$1.80**.
Spent so far ≈ $4.4 of $30. Budget caps in the runner as before (`--budget`), app stopped with `-y` and checked.

## 6. What changes in the runner (Muse Code, from a spec)
Prompt with the Keel manual; answers are Keel programs; build with `keel` and judge with `referee.py` against
`expected.json`; arms B and C only. Everything else (logging, caps, report) as in the first test.
