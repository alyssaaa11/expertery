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
- Pilot first: 20 jobs (2 per family). Gate: teacher pass rate ≥ 50% at 1e-6 and 0 harness errors → main run;
  otherwise report and fix the family that fails (decided with the user).

## Money and caps
Spark Open ≈ $0.015-0.02 per call (≈ 6k prompt, mostly cached after the first call, + ≈ 3k output; $1.25 / $0.15 /
$4.25 per M). Pilot ≈ $0.4; main 180 jobs ≈ $3; second tries ≈ $1 if used. Hard cap $5 on Baseten for the factory
(runner token guard counts cached tokens at $0.15/M). Muse Code build ≈ $0.5-1.

## Report
Pass rate per family (pilot and main), tokens per answer, kept records (count, token lengths: must be ≤ 4,096 with
the short prompt), the exam-guard report, the dev split, and cost (Baseten usage).

## Freeze
SPEC, generator code + seed + generated jobs file, referee, sandbox, teacher runner, prompt — sha256 recorded here before
the pilot.
