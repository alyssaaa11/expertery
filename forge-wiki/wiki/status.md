# Forge status: START HERE each day

**Summary**: The one page to read first (the verifier reads it first too). Goal, what is proven, what is open, and the
next step. Each claim links to the page with its evidence. Rewrite (don't append) after every finished step.

**Last updated**: 2026-10-29 ~17:21

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
| **Total** | **≈ 18.6 of 30** | |

## Open questions
1. Training script (Muse Code, experiments/train/forge_train.py, c8f5d55): **verifier NO-GO** (loop uses 1/8 of the data,
   data never reaches Modal, no exam guard, cap timeouts not applied, trap/kill gaps). Fix spec
   experiments/train/FIX_SPEC.md (8851957) — **waiting for the user's "yes fix"** (~$0.5-0.8) and the verifier's spec check.
2. Training on answer-only text (no reasoning) may teach Glimmer to skip reasoning: cheaper, maybe weaker on hard jobs.
   The fixed script logs the rendered example + learned tokens; decide after looking.
3. Factory spec (hard-style practice jobs, new families, strict 1e-6 referee, ~20 dev jobs) not written yet.
4. Final exam must use the same runner + 0.2% referee + 16,000 tokens + k=3 + 8 workers as the baselines (verifier);
   a short-prompt trained arm needs a small runner spec. Finish BX's 11 missing hard answers in that session.
5. Budget: ≈ $11 left for factory (~$3) + training (~$3) + final (~$1.5) + fixes; no money for a training retry.

## Next step
1. Verifier checks experiments/train/FIX_SPEC.md (requested 2026-10-29); then the user's yes → Muse Code fix session.
2. Then: factory spec → verifier → user yes → Muse Code builds the generator → teacher run (Spark Open, Baseten).

## Where things are
- Project `~/projects/forge` (README routes; "How this was built" table + correction on Claude-written scripts).
- GitHub (PRIVATE, pushed by Muse Code): https://github.com/alyssaaa11/expertery — local commits since d23b21a are
  not pushed yet (Muse Code pushes at the next publish step).
- Live dashboard of the baseline: [[glimmer-dashboard-2026-10-29]]. Decisions: [[new-goal-2026-10-29]],
  [[night-prep-2026-10-28]]; lessons [[lessons]]; tools [[tools-and-services]].
- Verifier reports: `~/agents/verifier/reports/forge-*-2026-10-29.md`.
