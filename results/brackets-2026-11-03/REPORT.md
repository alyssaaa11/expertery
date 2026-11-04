# Bracket workflow test: result (FTX only; AX not run)

Plan: experiments/brackets/PLAN.md (pre-registered, frozen at eadaf89 / 6a10c79). Session log: ../brackets-2026-11-03.session.out.

## What happened
- verified: arm FTX (trained r5f + self-check loop, no card) ran on the 20 bracket jobs, k = 3, COMPLETE 60/60
  (FTX/summary.json). Served model /vol/r5f/merged.
- verified: **34/60 = 57% usable** at 0.2% (medium 18/30, hard 16/30); pass@3 16/20 = 80%; 9 jobs 3/3, 4 jobs 0/3
  (B2, B12, B16, B18); 24,128 tokens per usable part; median 476 s per answer; 2.2 rounds per part.
- verified: Modal cost **$3.65** (billing 36.90 → 40.55), over the $3 per-arm cap: the runner stops new calls at the
  cap but lets running ones finish, and answers took ~9 min.
- **decision (user, 2026-11-03 ~13:30): arm AX (untrained Glimmer + rule card + same loop) NOT run.** The user asked
  to see FTX first and decided after seeing it (disclosed: the decision was made after seeing FTX results). The
  chain was stopped before AX (no AX call made). Reasons: cost (~$4 more) and time before the deadline.
- So the pre-registered claim X (same quality as the card, cheaper per usable part) is **untested**. No claim about
  training vs card may be made from this test.

## Why FTX scored lower than the exam (92%): Claude's reading of the 26 failed answers (hypothesis, by code reading)
1. Employee wording misread (~10-12): "40 tall overall" built as 40 above the base (B18), "stands on the back edge,
   flush" built behind the base (B1), "arm 80 long" measured from the wall's inside face (B2: NOT ambiguous after all,
   Muse Spark Open read it right 2/2 in the exam-agent run c; a model error).
2. CadQuery trap (~6-8): Workplane("XZ").extrude(t) grows toward -Y (verified: Y from -4 to 0 for extrude(4), forge
   .venv cadquery 2.8.0), so triangular gussets/webs land off-centre (B12 3/3, B10, B2).
3. Pieces only touching / small details (~8): B16 sides start on top of the feet → 3 solids (start Z not stated in
   the job, partly Claude's wording); keyhole, notch, slot off by 1-5% (B14, B20, B5).
The exam gave every coordinate; these jobs use natural wording and a part type absent from training.

## Use
- Not a headline and not a comparison. Usable as a limitation: "on a new part type in natural wording, 57% (80%
  within 3 tries); the fix is to add that job type and wording to the factory and retrain."
