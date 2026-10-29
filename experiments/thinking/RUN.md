# Thinking exam: exact run commands (pending verifier pre-run check + user yes)

Out dir: `OUT=~/projects/forge/results/thinking-2026-10-29`. Run from ~/projects/forge.

Caps:
- Modal + Baseten: $4.00 for the session.
- Wonder (Meta): $1.50. This is the verifier's fix: worst case $29.0 + $4.3 + $1.5 ≈ $34.8, inside $35. Wonder
  cannot change the decision, because S governs.
- Stop if Forge's total would pass $35.

Keys come from envsave opaque ids inside run_fc_session.sh and are never printed.

0. **Grader references in the cloud** (CPU only, a few cents):
   `.venv/bin/python experiments/freecad/cloud_grade.py --check-refs --exam thinking`
   It must print `REFS 13/13 PASS`. Anything else → STOP.
1. **Session** (Glimmer deploy, pilot, gate, main run):
   `experiments/freecad/run_fc_session.sh $OUT 4.00 --pilot "thinking:dry:pilot:G,S:3" --run "thinking:main:main-GS:G,S:3"`
   - The pilot is D1, D2 and C1-C3, run by G and S at k = 3, which gives 30 answers.
   - The session then waits up to 20 min for `$OUT/GO` or `$OUT/STOP`. Claude writes one of them only after this
     gate (pre-registered in PLAN.md):
     - Harness errors: 0. INVALID answers: 0 or 1. Every answer has a grader verdict at both tolerances.
     - All counts use the 1e-6 record `outcome`, not the 0.2% `verdict`. The gate is decided within 5 min, because
       the GPU keeps running while the session waits.
     - G passes ≥ 8 of its 9 calibration answers (C1-C3) → STOP: the exam is too easy.
     - S passes ≤ 4 of its 9 → STOP: too hard or ambiguous.
     - Otherwise → GO.
2. **Wonder** on S's failed samples only (no GPU):
   `.venv/bin/python experiments/freecad/runner_fc.py --exam thinking --jobs main --out $OUT/main-W --arms W --escalate-from $OUT/main-GS --budget-w 1.50 --budget 10`
3. **Decision** (offline):
   `.venv/bin/python experiments/freecad/runner_fc.py --exam thinking --summarize $OUT/main-GS $OUT/main-W --out $OUT/final`
   Report the S rule, the T rule (and which governs), Wonder's share, the speed and cost table, and Glimmer's
   $ per answer. Glimmer's figure is computed by hand as Modal GPU $ for the session ÷ G answers, because the runner
   prints n/a.
4. Dashboard (live): `experiments/common/dashboard.py --run $OUT --config $OUT/arms.json --out $OUT/dashboard.html --loop --fc --exam thinking --cap 4.00` (arms.json written by Claude: G, S, W labels)
