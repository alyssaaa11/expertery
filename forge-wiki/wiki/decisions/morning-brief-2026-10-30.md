# Morning brief, Oct 30 (read this first)

**Goal**: a trained Glimmer as correct as B-max (95%), many times cheaper and faster, private. Submit Nov 4.

## Done overnight (free; Forge spend unchanged at ≈ $30.4 of $50)
- verified: final plan + Muse spec ready (experiments/final/PLAN.md, MUSE_SPEC.md). Verifier pre-build: READY WITH 5
  EDITS + 1 decision (rubric 5/7/6); all 5 edits applied (1861990). Your decisions recorded: budget $50, finish B-max
  to 30 jobs (step 6a, a58d416). Verifier re-check of that change: [waiting at time of writing].
- Diagrams: forge-wiki/attachments/final-plan-diagram.html (the plan) and how-training-works.html (how the
  weights change) + page [[how-training-changes-weights-2026-10-30]].
- Submission draft with verified numbers and blanks: [[submission-draft-2026-10-30]].
- Independent direction review (fresh agent, no access to my reasoning): **6/10, keep going but rebalance**. The
  plan is the right technical bet, but Impact (30%) + Demo (25%) get almost no work.

## My recommendation (decision for you)
1. **Add a demo viewer to the Muse build** (reviewer's #1): the same new part request in two lanes, B-max Glimmer
   (~5 min of reasoning and retries, timer running) vs trained Glimmer (seconds), both parts in 3D with the referee's ✓,
   then the scoreboard filling in. It is built from the logs every run already writes. +$1-2 of Muse.
2. **Drop the offline-Mac step 7**: your Mac has 24 GB; the Glimmer MLX copy is ~15 GB and its card recommends ≥ 48 GB
   (verified: model README). Show "private" as a Modal run with no network instead. Saves time and keeps money ≤ $50.
3. **One yes for steps 4-6** (train → dev check → final exam) instead of three, with all stop rules unchanged (dev < 80%
   stops; caps stay). Saves half a day of waiting.
4. **Make the repo public** before submission (rule: public repo), after a secrets scan. Your call; free.
5. Avoid medical examples in the pitch: health/medical ideas are banned by the hackathon rules. Use automotive or
   industrial suppliers.

## Money if you say yes to 1-3
Muse build $4-6 + steps 1-6a caps $13.50 → worst ≈ $48-50; expected ≈ $42-45.

## Timeline
Oct 30 Muse build + fixes, fairness check, factory pilot → Oct 31 factory main + training + dev check → Nov 1 final
exam + B-max finish → Nov 2-3 demo video + README + public repo → Nov 4 submit (internal 18:00 CET).

## Questions for you (3 yes/no)
1. Yes to the Muse build, with the demo viewer added?
2. One yes for steps 4-6 with the stop rules?
3. Make the repo public after a secrets scan (closer to the deadline)?
