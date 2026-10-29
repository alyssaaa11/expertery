# Factory plan: hard-style practice jobs → teacher answers → strict referee → training data (DRAFT)

Status: DRAFT by Claude, 2026-10-29. Needs: verifier check (plan + spec), the user's yes, then Muse Code builds the
generator and the teacher runner (spec: experiments/factory/SPEC.md). Goal link: forge-wiki/wiki/decisions/new-goal-2026-10-29.md.

## Question
Can the teacher (Muse Spark Open on Baseten) produce ~150+ referee-verified solutions to **hard-style** CadQuery jobs
from part families that are **not** in the 30-job exam, cheaply enough to train Glimmer on?

## Data rules (decisions)
- Practice families are new (list in SPEC §1); none of the exam families in experiments/first-test/jobs-list.md.
  The training pipeline's exam guard (FIX_SPEC item 3) re-checks every kept answer before training.
- Every job is generated with exact coordinates in the same text style as the exam ("X from a to b ..."), and a
  reference program built by the generator (deterministic, seeded). The reference is used ONLY by the referee.
- Strict referee: experiments/first-test/checks.py at TOL_DIFF = 1e-6 (user rule), run in the sandbox.
- Training records = the teacher's code (not the generator's reference), only when it PASSES at 1e-6.
- Split: ~180 training jobs + 20 dev jobs (seed-chosen before any teacher call; dev jobs are never trained on and are
  used only to pick training settings).

## Teacher run
- Spark Open (`meta-models/muse-spark-open-1026`, Baseten), prompt = system message + the CadQuery manual
  (experiments/first-test/manual.md) + job text, max_tokens 16,000, temperature 1.0, top_p 0.95, k = 1, a second try
  (k = 2) only for jobs that failed, if money allows. The teacher may use the manual; Glimmer's training records use the
  short prompt (no manual).
- Pilot first: 20 jobs (2 per family). Gate: 0 harness errors, then the yield rule below decides the main-run size.

## Money and caps (corrected after the verifier: WRONG output-length assumption)
Measured: Spark Open's answers to hard first-test jobs average **5,212 output tokens** (first-test arm C) → ≈ $0.023 per
call ($1.25 / $0.15 cached / $4.25 per M; output dominates). Pilot 20 ≈ $0.46; main 180 ≈ $4.2; retries extra.
**Cap $5 on Baseten** (Forge's $30 budget; more only if the user raises it under the "final, winnable project" rule).
Within $5: the guard keeps 8 × $0.075 = $0.60 for in-flight answers, so ≈ $4.40 is usable → pilot + about 170 first
tries (expected records ≈ 170 × p), retries only with what is left. Muse Code build ≈ $0.5-1.
## Yield rule (verifier A1)
Target ≥ 150 kept records needs a first-try pass rate p ≥ 83% (150/180). At the pilot gate: if p ≥ 0.83, run 180 jobs;
if 0.5 ≤ p < 0.83, either accept fewer records (expected 180 × p, e.g. ≈ 110 at 60%) or ask the user to raise the
cap to run ceil(150/p) jobs (max 300); if p < 0.5, stop and fix the families. Why: too few records may train too weakly;
too many jobs at a low pass rate burns the budget without the retry money.
## Blind rebuild before the pilot (verifier A4)
Claude rebuilds 1 job per family from its text alone (no reference) and must PASS at 1e-6 (10/10). Why: otherwise a
teacher FAIL could mean our wording is ambiguous, not that the teacher is wrong.
## Dev jobs
Scored with the final-exam runner and the 0.2% referee (like the exam), with 1e-6 also reported. Why: training settings
must be chosen with the same yardstick as the final exam.

## Report
Pass rate per family (pilot and main), tokens per answer, kept records (count, token lengths: must be ≤ 4,096 with
the short prompt), the exam-guard report, the dev split, and cost (Baseten usage).

## Freeze
SPEC, generator code + seed + generated jobs file, referee, sandbox, teacher runner, prompt — sha256 recorded here before
the pilot.

## Privacy headline (decision, user 2026-10-29)
Headline: "a private teacher; Wonder only helps on the hardest jobs (X% of the data)", X = share of kept records
tagged `teacher: wonder`, printed next to the headline in the factory summary. Large X is stated openly. See
forge-wiki/wiki/decisions/new-goal-2026-10-29.md.
