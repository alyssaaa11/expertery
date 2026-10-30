# Muse Code round 1d: references without hidden extras (blind rebuild 2026-10-30) — verifier PASS WITH ISSUES (forge-factory-r1c-2026-10-30); user yes + H1 = option A, 2026-10-30

Claude's blind rebuild (results/blind-rebuild-2026-10-30, cloud box + grader, 1e-6) passed 8/10. Two misses are factory bugs:
1. **F5-2 (and any reference using overlapping cuts on one axis):** the reference cuts the main bore as two overlapping
   coaxial cylinders (X -1..87.8 and -7..1). Merging them into one cylinder (the same solid) gives volume 35990.856 vs
   35990.680 and FAILs at 1e-6 (probe: results/probe-tight-2026-10-30). Verifier correction (N1): both are the SAME
   solid (precise BRepGProp volume 35987.005411 for both); the cause is the default Volume() noise, which the overlap's
   face structure triggers (F5 up to 6.1e-4, F9 2.7e-6; other families <= 2e-13). A text-faithful answer can fail. Fix: every hole/bore in every family is ONE cut of one primitive
   (no two coincident or overlapping same-radius coaxial cuts; no coincident faces between cutters).
2. **F10-1 (all F10):** the rim's inner cut runs from Z = 34.3 − 1 into the body, so it removes body material below the
   top face that the text never mentions (blind answer volume 33525.1 vs reference 33433.2). Fix: build the rim ring as
   its own ring (outer minus inner, Z 34.3 to 38.7) and fuse it; no cutter may remove material the text does not describe.
Rules: all in experiments/final/MUSE_SPEC.md "Rules". Do not edit checks.py; cloud_cq.py only as in H1 below.

## Build in this round ONLY (experiments/factory/)
- generator.py: fixes 1 and 2 in every family where they apply (search all 10 for overlapping coaxial cuts and for
  overshoot cutters that reach material outside the feature they cut). Seed, ids, numbers and texts stay the same
  unless a text must change to describe the part; report any text change.
- make_jobs.py self-check, new column CUTS: per job, no two cutter primitives in the reference share an axis and radius
  while overlapping (a static scan of the reference source is fine). Keep all other columns.
- Re-run make_jobs.py; report sha256s and whether texts or dev ids changed.
- **H2 (verifier):** TEXT=REF exempts only 0, ±1 and the `/2` of a printed diameter; any other integer or any arithmetic
  on printed values (e.g. `(5.9 + 1)` used as a size) is flagged unless it is an overshoot of a through-cut. Test: a
  reference box Y −3..3 against the text "5.9 wide" fails TEXT=REF.
- **H1 (user choice, filled in before launch):** **option A (user, 2026-10-30)**: the FACTORY grader in experiments/final/cloud_cq.py
  computes every volume used in the mismatch (answer XOR reference, and the reference volume it is divided by) with
  precise BRepGProp (eps 1e-9, e.g. `OCP.BRepGProp.BRepGProp.VolumeProperties_s(shape, props, 1e-9)`), tolerance unchanged
  (1e-6 tight, 0.2% verdict). The **first-test path stays byte-for-byte the same** (it calls checks.score as today):
  this is the only allowed edit to cloud_cq.py; checks.py stays frozen. Tests: F5's one-bore and two-bore solids give
  mismatch < 1e-9 in the factory path; a first-test grade gives the same result as before (fake shapes). Why: the
  default Volume() is noisy up to 6.1e-4 in F5 and 2.7e-6 in F9 (verifier H1), so correct answers failed.
- Tests: an overlapping-coaxial-cut reference fails CUTS; F10's reference does not cut below Z = 34.3 except the recess
  and bore (volume between Z 33.3 and 34.3 equals the text's body there).
## Done when
- pytest (same 5 folders) passes; make_jobs SELF-CHECK OK with TEXT=REF and CUTS 20/20 in all families.
Report: files changed, pytest line, table, sha256s, text changes, anything not followed.
