# Forge status: START HERE each day

**Summary**: The one page to read first (the verifier reads it first too). Goal, what is proven, what is open, and the
next step. Each claim links to the page with its evidence. Rewrite (don't append) after every finished step.

**Last updated**: 2026-10-29 ~20:30

---

## Goal
Meta hackathon (Indie track, Push the Frontier), submit by **Nov 4, 18:00 CET**; internal deadline: trained result by
**Nov 1 evening**, otherwise submit the honest finding + pipeline (decision, agreed 2026-10-29).
- decision (user, 2026-10-29): **new goal** = a trained Muse **Glimmer** 30B is **as correct as Glimmer + every fair cheap
  fix (B-max), but many times cheaper and faster, and runs privately** ([[new-goal-2026-10-29]]; method = distillation,
  known; ours = referee-verified training data, strongest fair baseline, end-to-end private tool + proof report).
- decision (user): budget **$30 max** for Forge; every paid step needs the user's yes.
- decision (user, 2026-10-29 ~17:30, clarified): the budget rises to **$40-50 only if Forge becomes the final project
  that is delivered AND has a real chance to win**; if not, rethink (another project) before spending more. Proposed
  check point (to confirm with the user): after the factory pilot + the dev-set result, an honest score against the
  judging rubric (Impact 30 / Meta tooling 25 / Depth 20 / Demo 25) decides "final project + raise" vs "rethink".
- decision (user, 2026-10-29): **all code is written by Muse Code** from Claude's specs (incl. run scripts, training,
  dashboards, checks); Claude writes specs, plans, exams/references, wiki, and checks results.
- decision (user, 2026-10-29): **the Mac is the office, the cloud is the workshop**: no AI-written code runs on the
  Mac; models, answer execution (Modal Sandbox), grading and training run in the cloud ([[where-things-run-2026-10-29]]).
- decision (user, 2026-10-29): **verifier workflow**: after every finished step and before every paid step, ask
  verifier/master (with the user's decision + PLAN/spec + commit), wait for verdict + rubric line, report both.

## Proven so far (verified)
- **Baseline (step 2)** on the 30 held-out CadQuery jobs ([[bmax-baseline-2026-10-29]]): plain Glimmer 87% (k=1),
  hint 1-try **88%** (k=3; medium 100%, hard 76%; 10.7k tokens per correct part), all fair fixes **95%** (75/79 answers;
  hard 91%; 21.3k tokens per correct part). Stop rule (hint ≥ 90%) not triggered. Frozen plan experiments/bmax/PLAN.md
  (cd0716e), results b9c556b. Room is only on the hard jobs.
- **Training smoke test** ([[training-smoke-2026-10-29]]): LoRA trains on one H100 (loss 1.03 → 0.33), an 8,192-token
  step runs out of memory, vLLM LoRA loading crashes (bug 53254), **merging works**; the merged model answered a new job
  in 3 s / 84 tokens and PASSED the strict referee. (Harness written by Claude: record only.)
- **Option A skipped** by the free coverage audit (83% covered by top-5 retrieval ≥ 80%) ([[coverage-audit-2026-10-29]]).
- Earlier: Keel private tool NO ROOM (Glimmer + manual 97.8%) ([[keel-v2-baseline-2026-10-28]]) → difficulty, not
  privacy, drives the gap.

## Money (verified)
| Item | $ | Source |
|---|---|---|
| Spent before Oct 29 | ≈ 9.8 | earlier status |
| Muse Code Oct 29 (sandbox+BX 1.45, fixes 1.15, rebuild 0.51) | ≈ 3.1 | run.usage × $1.25/$0.15/$4.25 per M |
| Modal baseline run | ≈ 4.5 | `modal billing summary` 2.22 → 6.75 |
| Modal smoke test | ≈ 1.06 | 6.76 → 7.82 |
| Muse Code training fix | ≈ 1.11 | run.usage |
| Muse Code Oct 29 evening (build 1.35 + fixes 1.14, 0.61, 0.44, 0.46) | ≈ 4.0 | run.usage |
| **Total** | **≈ 23.9 of 30** (+ cents of Modal CPU checks) | |

## Open questions
1. hypothesis: training on answer-only text (no reasoning) may teach Glimmer to skip reasoning: cheaper, maybe weaker
   on hard jobs. The fixed script logs the rendered example + learned tokens; decide after looking.
2. Final exam must use the same runner + 0.2% referee + 16,000 tokens + k=3 + 8 workers as the baselines (verifier);
   a short-prompt trained arm needs a small runner spec. Finish BX's 11 missing hard answers in that session.
3. Budget: ≈ $9 left under $30; the full plan after the FreeCAD test is ≈ $34-35 → the user's budget answer.

## Next step
1. **FreeCAD gap test** (decision, user 2026-10-29: test FreeCAD before the factory).
   - decision (user, 2026-10-29): **teacher escalation**: Wonder answers only the jobs Spark failed; teacher T = S ∪
     Wonder rescues; the rule is evaluated on T and on S alone (PLAN rule 5), and the report labels a decision that
     rests on Wonder (closed API). Same `--escalate` in the factory, with a teacher tag per record.
   - decision (Claude, following existing accounting): Meta credit for Wonder counts inside Forge's budget.
   - verified (user saw the HerdShot key in their own Meta developer key list, 2026-10-29): Wonder uses
     META_HERDSHOT_API_KEY on the user's own Meta account (verifier A6 closed).
   - verified: modal 1.6.3 + cadquery 2.8.0 in the forge venv (verifier evidence/02, forge-freecad-escalation).
   - Verifier: READY WITH 3 EDITS, rubric 6/7/5 (forge-freecad-escalation-2026-10-29); edits applied f999208 + 7854051.
   - verified: Muse build + 4 fix rounds (6a67525 … 05786b2), pytest 107/107 outside Muse; real-code cloud checks
     (results/freecad-checks-2026-10-29/): FreeCAD 1.1.4 image, HAND OK 5/2 (Mac vs cloud ≤ 6.4e-8; gate 1e-6,
     disclosed), SAFETY OK, REFS 30/30. PLAN rule 6 (harness/INVALID > 5% → RUN INVALID) pre-registered.
   - Verifier pre-run: GO WITH 4 FIXES (forge-freecad-prerun-2026-10-29), all applied (RUN.md 89123ba, round 4).
   - **Next:** the user's "yes run" → experiments/freecad/RUN.md (pilot D1-D3 G,S → main 30 G,S cap $3.50 → W smoke
     $0.50 → W rescues $3 → `runner_fc.py --summarize`).
2. Training pipeline: round 2 done (pytest green; `smoke --cap-dollars 2.0` → CAP REFUSED exit 2).
3. Factory: plan READY (verifier); its target tool (FreeCAD or CadQuery hard jobs) follows from the gap test.

## Where things are
- Project `~/projects/forge` (README routes; "How this was built" table + correction on Claude-written scripts).
- GitHub (PRIVATE, pushed by Muse Code): https://github.com/alyssaaa11/expertery — pushed through f2a1a96 by the user
  (Muse's shell has no ssh login; the hook blocks reading gh credentials).
- Live dashboard of the baseline: [[glimmer-dashboard-2026-10-29]]. Decisions: [[new-goal-2026-10-29]],
  [[night-prep-2026-10-28]]; lessons [[lessons]]; tools [[tools-and-services]].
- Verifier reports: `~/agents/verifier/reports/forge-*-2026-10-29.md`.
