# Bracket workflow test (2026-11-03)

**Summary**: An impact test on one company workflow ("an employee describes a mounting bracket and gets an editable
CAD part"). Only the trained arm ran: 57% usable. The comparison with the untrained model + rule card was stopped by
the user after seeing the trained result, so no "training beats a card" claim can come from it.

**Sources**: experiments/brackets/PLAN.md (pre-registered, sha freeze at 6a10c79); results/brackets-2026-11-03/REPORT.md;
results/brackets-2026-11-03/FTX/summary.json; Modal billing before/after (session log results/brackets-2026-11-03.session.out).

**Last updated**: 2026-11-04

---

## Goal
- decision (user, 2026-11-03): show "training is better because of X", with X chosen before the run: X = lower cost per
  usable part at the same quality as the easiest alternative (untrained Glimmer + RULE_CARD + the same fix loop).

## Relevant findings
- verified: 20 employee-worded bracket jobs + references, written by Claude; selftest 20/20 (each feature > 0.2% of
  the part, so the referee sees a missing hole). B7 first failed that check (3.4 mm holes were 0.17% of the part) and
  was resized to a 44 mm NEMA 17 face. Check: `.venv/bin/python experiments/brackets/jobs_brackets.py --selftest`.
- verified: arm FTX (trained r5f + loop, no card) 34/60 = **57%** usable, pass@3 16/20, 24,128 tokens per usable part,
  median 476 s per answer, **$3.65** (cap was $3: the runner stops new calls only, running answers finish).
- decision (user, 2026-11-03 ~13:30, after seeing FTX): arm AX **not run**. Claim X is untested. Disclosed in REPORT.md.
- hypothesis (Claude, by reading the 26 failed codes): failures = misread natural wording (~10-12, e.g. "40 tall
  overall" built as 40 above the base), the CadQuery XZ-workplane trap (~6-8), touching-only pieces / small details (~8).
- verified correction (exam agent run c, see [[expertery-installer-2026-11-03]]): Muse Spark Open built B2, B12 and B18
  right from the same text, so those were Glimmer errors, not ambiguous wording. The earlier guess "B2 '80 long' is
  ambiguous" was wrong.

## Open questions
- Would the card arm fall into the same traps? (not run)

## Next step
- Not a headline. Usable only as an honest limitation: "on a new part type in natural wording, 57% (80% within 3
  tries); the fix is to add that job type and wording to the factory and retrain".
