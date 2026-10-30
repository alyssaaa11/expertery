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

## Money (verified, updated 2026-10-30 after the pilot)
| Item | $ | Source |
|---|---|---|
| Spent through Oct 29 | ≈ 30.4 | earlier table; **unreconciled** (verifier: its rows sum to ≈ 23.6; the 30.4 also counted FreeCAD ≈ 1.6 + thinking ≈ 4.9 in a footnote). Upper estimate kept on purpose |
| Muse Code Oct 30: r1 2.40 + r1b 0.96 + r1c 1.62 + r1d 1.26 | ≈ 6.24 | run.usage of each round |
| Modal Oct 30 (cloud checks, pilot box + grader) | ≈ 0.12 | `modal billing summary` (paid from Modal credit, $0 billed) |
| Factory pilot (Baseten, Spark Open) | 0.52 | summary.json |
| Muse round 2 | 2.40 | run.usage |
| Factory main run (Baseten) | 4.38 | summary.json |
| **Total** | **≈ 44.1 of 65** (verifier T2 recount: 44.06; + Modal cents) | |

Rest of the plan (verifier, forge-factory-pilot-2026-10-30): expected ≈ $48-49 total; worst case at every cap ≈ $54
(main 4.70 + training 4 + Muse round 2 ≈ 4 + dev 1 + BX finish 1 + exam 2 + demo 0.3) > $50. decision (user, 2026-10-30): **budget raised to $65**, covering
everything together, credits included (Baseten, Modal, Meta). Every paid step still needs the user's yes + verifier.

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
- decision (user, Oct 30, "keep"): keep the full git history (timeline proof); README states the removed defence/medical
  market examples openly.
- Repo readiness list 1-7 done (f692227): README for judges, LICENSE Apache-2.0, defence/medical removed, licence check,
  history secret scan clean. Verifier review pending (m…219). Repo stays PRIVATE until the user decides.
- verified: **factory pilot** (6274420, user yes + verifier GO): 19/20 PASS at 1e-6 (95%), 0 harness errors, $0.52,
  113 s; F8-2 one teacher error (invalid shape); patterns.py 0 repeated patterns; 19 train records; cached tokens work
  after the first calls. Yield rule p ≥ 0.83 → main run of the 160 remaining non-dev jobs (≈ $4.17; cap A $4.60 or B
  $4.48, user to choose; verifier asked m…240).
- verified: **factory main run** (e152895): 148/157 PASS at 1e-6 (94%), $4.38, budget stop 3 short ($0.0279/call vs pilot
  $0.0261); F8 bezel 13/18 (separate solids), F5 15/18. patterns.py: 0 patterns (hypothesis: the loop's exact-fail-list
  signature is too strict; F8's 'solids=N' cluster was missed). **Training set: 167 records** (19 + 148), 0 dev, 0 Wonder,
  results/factory-train-2026-10-30/train_records.jsonl sha256 7181e73b…9217.
- verified: **Muse round 2** (fd1d32c, $2.40): runner_final (FT + BX finisher), modal_forge + session, compare.py,
  no-Wonder loader filter; pytest 286. Round 2b todo: E2 test + E3 calls.jsonl cross-check.
- Next: verifier on main run + round 2 (m…265) → user's yes for **training** (step 4, cap $4).
- (done) Next: verifier on the factory → the user's yes for the **pilot** (20 jobs, Spark Open on Baseten, cap $1.20) → learning
  loop report → main run. Muse round 2 (exam runner, BX finisher, deploy, compare) still to build.
- Money: ≈ $37.2 of $50.

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
