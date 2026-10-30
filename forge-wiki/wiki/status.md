# Forge status: START HERE each day

**Summary**: The one page to read first (the verifier reads it first too). Goal, what is proven, what is open, and the
next step. Each claim links to the page with its evidence. Rewrite (don't append) after every finished step.

**Last updated**: 2026-10-30 (after Muse round 1 + verifier)

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
| **Total** | **≈ 30.4 of 35** (incl. FreeCAD run ≈ $1.6, thinking exam + Muse rounds ≈ $4.9) | |

## Open questions
1. hypothesis: training on answer-only text (no reasoning) may teach Glimmer to skip reasoning: cheaper, maybe weaker
   on hard jobs. The fixed script logs the rendered example + learned tokens; decide after looking.
2. Final exam must use the same runner + 0.2% referee + 16,000 tokens + k=3 + 8 workers as the baselines (verifier);
   a short-prompt trained arm needs a small runner spec. BX's 11 missing answers are run in step 6a (user decision).
3. Budget: ≈ $9 left under $30; the full plan after the FreeCAD test is ≈ $34-35 → the user's budget answer.

## Where we stopped (2026-10-30 afternoon, factory ready for the pilot pending verifier)
- verified: factory built by Muse in 4 rounds (r1 e24a9a7 ≈ $2.4, r1b d304368 ≈ $0.96, r1c 5edd84a ≈ $1.62, r1d ff7f3a4
  ≈ $1.26). Claude re-ran: pytest 259 passed; make_jobs SELF-CHECK OK with TEXT=REF and CUTS 20/20 in all 10 families.
- verified (results/cloud-checks-2-2026-10-30.log, Modal credits, $0 billed): check-refs factory 200/200, first-test 30/30;
  regrade of the 199 baseline answers in the cloud box: 30 + 169 same verdicts, measures equal (exam path unchanged
  after 1d); **blind rebuild 2 (10 new jobs, one per family, from text only) 10/10 at 1e-6**; blind rebuild 1 now 10/10.
- What the checks found on the way (each fixed by Muse before any teacher money): cloud grader outside its app (F1),
  job text ≠ reference in F3/F4/F7/F8/F10, overlapping coaxial cuts in F5, hidden rim cut in F10, default-volume noise
  (F5/F9; fixed by user option A: precise volumes in the factory grader only).
- decision (user, Oct 30): learning loop = suggest-and-approve; precise volumes (option A); **no Wonder output in training
  data** (Meta API terms §10.1); talk to the user via hivey/Slack (`hivey msg send human --from hivey/hivey`).
- Repo readiness list 1-7 done (f692227): README for judges, LICENSE Apache-2.0, defence/medical removed, licence check,
  history secret scan clean. Verifier review pending (m…219). Repo stays PRIVATE until the user decides.
- Next: verifier on the factory → the user's yes for the **pilot** (20 jobs, Spark Open on Baseten, cap $1.20) → learning
  loop report → main run. Muse round 2 (exam runner, BX finisher, deploy, compare) still to build.
- Money: ≈ $36.7 of $50.

## Training + final exam: PREPARED, NOT RUN
- Plan experiments/final/PLAN.md, Muse spec experiments/final/MUSE_SPEC.md, diagrams [[forge-diagrams]] 8-11.
- verified: the CadQuery path (factory spec, exam guard, first-test runner) still runs answer code on the Mac
  (sandbox-exec, experiments/first-test/runner.py:423, forge_train.py run_train_code); round 1 moves it to a Modal box.
- verified: Spark Open = 816B (42B active), needs >= 700 GB VRAM (https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B);
  Glimmer 30B 4-bit < 20 GB (https://huggingface.co/meta-models/Muse-Glimmer-30B).

## Next step
1. **FreeCAD gap test: DONE** ([[freecad-gap-2026-10-29]]). verified: Glimmer 28/30 (93%), Spark 30/30 (100%), Wonder 0
   rescues (share 0%) → pre-registered rule 3: **stay on hard CadQuery jobs**. Both Glimmer misses = one API mistake
   (makeCylinder keyword args). Run ≈ $1.6. Verifier: PASS WITH ISSUES, result and decision stand (rubric 7/6/4, 0 WRONG).
   Next Muse round (small): runner adds its own folder to sys.path (the -I launch failure), dashboard live for runner_fc,
   report's rule-5 label only on disagreement.
2. **Thinking exam in FreeCAD: pilot STOP, too easy** ([[thinking-exam-pilot-2026-10-29]]).
   - verified: Glimmer 8/9 and Spark 9/9 on calibration at 1e-6, with a 40-rule NDS-1 in the prompt. The
     pre-registered gate (G ≥ 8/9) stopped the main run.
   - Glimmer is 9× slower (167 s against 18 s) and about 1.4-1.9× dearer per answer (Spark ≈ $0.017, 91% cached).
   - Verifier: PASS WITH ISSUES, STOP stands (rubric 7/6/4).
   - Pending code fix before the next paid Spark run: cached_tokens_of must read usage.prompt_tokens_details.cached_tokens.
   - hypothesis: the gap is in knowing the standard without it in the prompt (what training adds), not in applying
     written rules. Next is the user's choice.
3. Training pipeline: round 2 done (pytest green; `smoke --cap-dollars 2.0` → CAP REFUSED exit 2).
4. Factory: plan READY (verifier); its target tool (FreeCAD or CadQuery hard jobs) follows from the gap test.

## Where things are
- Project `~/projects/forge` (README routes; "How this was built" table + correction on Claude-written scripts).
- GitHub (PRIVATE, pushed by Muse Code): https://github.com/alyssaaa11/expertery — pushed through f2a1a96 by the user
  (Muse's shell has no ssh login; the hook blocks reading gh credentials).
- Live dashboard of the baseline: [[glimmer-dashboard-2026-10-29]]. Decisions: [[new-goal-2026-10-29]],
  [[night-prep-2026-10-28]]; lessons [[lessons]]; tools [[tools-and-services]].
- Verifier reports: `~/agents/verifier/reports/forge-*-2026-10-29.md`.
