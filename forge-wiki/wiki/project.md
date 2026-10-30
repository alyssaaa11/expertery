# Forge: the project on one page

**Summary**: what Forge is, why, what is proven, what happens next, and where everything is. Read this first if you
are new; read [[status]] for today's details.

**Last updated**: 2026-10-30

---

## What Forge is
A factory that turns a company's CAD tool and design rules into a small **private** model. Meta's big model (Muse
Spark Open, the teacher) solves practice jobs, a strict referee keeps only exactly-correct parts, and Muse Glimmer
30B (the student) is trained on them. The trained Glimmer runs on one GPU the company owns, so designs never leave it.
Meta hackathon, Indie track, Push the Frontier. Submit by Nov 4.

## The claim we are testing (decision, user 2026-10-29)
> A trained Glimmer is **as correct** as Glimmer with every fair fix (B-max, 95%), but **many times cheaper and
> faster**, and private.

## Why this claim (verified, [[scoreboard]])
- We looked for an accuracy gap 4 times. Glimmer is already 87-97% correct when the rules are in the prompt, so
  "more accurate" is not where training wins.
- But that accuracy is expensive: B-max needs 21,314 tokens and 295 s of model time per correct part.
- Spark Open is too big to run privately for most firms (816B, ≥ 700 GB GPU memory); Glimmer fits one GPU.

## How it works
![[assets/diagrams/forge-training-exam-plan.png]]
1. Muse Code (Meta's coding agent) writes all the code from our specs.
2. Factory: 200 new practice jobs → Spark writes code → the referee keeps exact answers (~150).
3. Training: a small LoRA patch on Glimmer learns those answers ([[how-training-changes-weights-2026-10-30]]).
4. Dev check on 20 unseen jobs (≥ 80% to continue).
5. Final exam: 30 held-out jobs, compared with B-max and hint-only Glimmer on 4 pre-registered bars.

## Rules we work by (decisions, user)
- All code by Muse Code; no AI-written code runs on the Mac (cloud only: Modal, Baseten).
- Every paid step needs the user's yes; the verifier checks before and after each step.
- Budget $50 (≈ $30.4 spent on Oct 30 morning).
- Every new learning goes into this wiki ([[lessons]]).

## Where we are (Oct 30)
- Prepared, not run: experiments/final/PLAN.md + MUSE_SPEC.md, verifier READY after edits.
- Order (user): factory first, demo last. Muse round 1 (factory) is ready in experiments/final/MUSE_ROUND1.md but NOT
  started: waiting for the user's go. Details: [[status]] "Where we stopped".

## Where things are
| What | Where |
|---|---|
| Today's state, money, next step | [[status]] |
| Every number | [[scoreboard]] |
| All diagrams | [[forge-diagrams]] |
| Lessons (with how learned) | [[lessons]] |
| Submission draft + demo outline | [[submission-draft-2026-10-30]] |
| Code and runs | `~/projects/forge/experiments/`, `results/` |
