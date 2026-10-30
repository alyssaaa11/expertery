# Forge status: START HERE each day

**Summary**: The one page to read first (the verifier reads it first too). Goal, what is proven, what is open, and the
next step. Each claim links to the page with its evidence. Rewrite (don't append) after every finished step.

**Last updated**: 2026-10-30 ~21:40 (after the base control + superintel diagnosis)

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
- decision (user, 2026-10-30 evening): **Claude may make small code fixes** (a few lines, each disclosed in the README);
  Muse still builds the big parts; **never Claude inside the product** (Glimmer's answers are never fixed by Claude).
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
| Training (Modal) | 0.89 | billing before/after |
| Dashboard (Muse) | 0.43 | run.usage |
| Muse round 2b | 0.87 | run.usage |
| Dev check (Modal) | 0.32 | billing 10.78 → 11.10 |
| Oct 30 evening: Muse 3 + 3b + 3c (2.44+0.38+0.26), factory R3 (0.59+4.39), training R3 (1.99), dev R3 (2.22) | ≈ 12.3 | run.usage, summary.json, billing |
| Base control (Modal, incl. aborted attempt) | 2.33 | billing 15.31 → 17.64 |
| **Total** | **≈ 61.2 of 80** | earlier rows recounted by the verifier (T2) |

Rest of the plan (verifier, forge-factory-pilot-2026-10-30): expected ≈ $48-49 total; worst case at every cap ≈ $54
(main 4.70 + training 4 + Muse round 2 ≈ 4 + dev 1 + BX finish 1 + exam 2 + demo 0.3) > $50. decision (user, 2026-10-30 evening, "total" to the $80 proposal): **budget $80 total**; extra room is for Modal + Baseten,
Muse (Meta) kept tight. Earlier: budget raised to $65, covering
everything together, credits included (Baseten, Modal, Meta). Every paid step still needs the user's yes + verifier.

## Open questions
1. hypothesis: training on answer-only text (no reasoning) may teach Glimmer to skip reasoning: cheaper, maybe weaker
   on hard jobs. The fixed script logs the rendered example + learned tokens; decide after looking.
2. Final exam must use the same runner + 0.2% referee + 16,000 tokens + k=3 + 8 workers as the baselines (verifier);
   a short-prompt trained arm needs a small runner spec. BX's 11 missing answers are run in step 6a (user decision).
3. Budget: ≈ $9 left under $30; the full plan after the FreeCAD test is ≈ $34-35 → the user's budget answer.

## Where we stopped (2026-10-30 afternoon, factory ready for the pilot pending verifier)
- **NOW (2026-10-30 ~22:40, before the user cleared the chat):** the **rule-card check** is RUNNING (user yes, verifier GO
  forge-rulecard-check-go-2026-10-30): (1) R3 + card → results/check-r3card-2026-10-30 (FORGE_MODEL_NAME=r3,
  FORGE_RULE_CARD=~/projects/forge/experiments/final/RULE_CARD.md, cap $4.50, deploy 22:30), then (2) A + card
  → results/check-acard-2026-10-30 (cap $3.00); one shell chain under caffeinate, ends ≈ 00:15, ≈ $3.3.
  - verified (C2 done, 22:38): served root /vol/r3/merged; first records prompt_tokens 838/830 (≈ 240 without the card)
    → the card IS in the prompt; first two answers PASS.
  - Reading pre-registered in experiments/final/PLAN.md "Rule-card check": R3+card crashes (non-empty run_error) ≤ 8 →
    manual-gap diagnosis holds; 9-14 unclear; ≥ 15 wrong; pass rates within ±10 points = no clear difference.
  - After it: report to Alyssa in Slack (hivey msg send human --from hivey/hivey), commit results, verifier review, then
    (if confirmed) card-conditioned self-distillation per raw/superintel-answer-training-diagnosis-2026-10-30.md
    (≈ $15-23, 120 fresh dev jobs, needs user yes + verifier + Muse spec). D3 (served sampling + digest) still open.
  - Results so far on dev: untrained 51.7%, R1 38.3%, R3 48.3% ([[training-experiments-2026-10-30]]).
  - Money ≈ $61.2 of $80 before the check (Modal billing 17.53 at the start of the check).
  - Working rules (user): Slack via hivey; verifier before every paid step; Muse writes big code, Claude only small
    disclosed fixes (README "Small fixes by Claude"), never Claude inside the product; no Wonder data in training; budget
    $80 total incl. credits; keep the git history; never use `tr` in the shell (aliased to Trash).
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
- verified: **training done** (step 4, user yes + verifier GO, --out final): 167 examples, 0 dropped; exam guard 167
  kept / 0 refused; 42 optimizer steps; loss 0.42 → 0.15-0.26; train 231 s, peak 64.3 GB of 85; merged to
  /vol/final/merged (174 s); Modal ≈ $0.89 (billing 9.89 → 10.78). No serve test (no prompt given).
  Note: the training prompt rendered "Reasoning strength: high." from the chat template while answers have no reasoning
  (open question 1).
- verified (verifier forge-round2b-prebuild): training OK for the dev check; 'Reasoning strength: high.' is the template
  default at train AND serve (match), answers trained without a reasoning turn. **B3: dev session starts with a pilot on
  first-test D1-D3** (served format end to end). N1: before the exam, served generation_config.json = base's.
- verified: **dev check (step 5) = STOP** (results/dev-2026-10-30, COMPLETE 60/60, not budget-stopped): trained Glimmer
  23/60 = **38.3%** at 0.2% (31.7% at 1e-6), pass@3 75%; per family F1 5/6 … F8 0/6, F5 1/6, F10 1/6; failures mostly
  wrong volume (18) and separate solids (6), 8 no-BREP tracebacks; ~390 completion tokens, 21.5 s per answer. Pilot on
  first-test D1-D3: 0/3 (base Glimmer passes them), errors like the centred-box trap. Pre-registered rule: STOP, report,
  one retry only with a new user yes, exam untouched. Session note: first start aborted (budget double count, verifier
  D1), restart with cap $2.50; Modal ≈ $0.32.
- verified correction (second opinion 2026-10-30, checked in findings/first-test-2026-10-28.md:31): base Glimmer with the
  short prompt and NO manual = **16/30 = 53%** on the exam; 87% (BR) is Glimmer + manual. So training had to replace the
  manual and keep the reasoning from a 53% start. Claude had told the user "Glimmer alone 87%": wrong, corrected.
- Second opinion (forge-wiki/raw/second-opinion-answer-2026-10-30.md, independent Claude, read-only): diagnosis confirmed
  (first loss tokens ` to` `=user` taught "skip the thinking turn"); recommends one base-Glimmer check (A and B2 on the 20
  dev jobs, ≈ $0.5-0.8) then self-distillation: generate WITH manual (+hint), train WITHOUT it, on reasoning + code.
- hypothesis: training on answer-only code (no reasoning turn, no manual) taught the short format but not the care;
  open question 1 answered in the bad direction. Missing baseline: base Glimmer on the same 20 dev jobs.
- verified: **R3 dev re-check = STOP** (40420ed; verifier forge-r3-dev-result-2026-10-30): trained-on-Spark-thinking Glimmer
  29/60 = 48.3% at 0.2% (tight 48.3%), COMPLETE, served /vol/r3/merged; pass@3 85%; ≈ 7.1k tokens/answer, 14.8k per
  correct; F8 0/6. 15 of 31 fails = crashes from invented API arguments. Disclosure (E5): the pilot's reasoning gate was
  passed on reasoning_len (frozen field) because the new reasoning_chars reads only reasoning_content (shows 0).
- hypothesis (verifier lead): Spark's reasoning names real CadQuery args (yDir in 61/159, inPlane in 62/159 records) that
  Glimmer then attaches to the wrong calls.
- verified: **base control** (results/dev-base-2026-10-30, COMPLETE): untrained Glimmer, short prompt: 31/60 = **51.7%**
  (tight 50%), pass@3 85%, 9.2k tokens/correct, 7 crashes. FT R3 48.3% < A 51.7% → pre-registered reading (PLAN R3 item
  10): **training did not help**; the trained model invents more API args (15 vs 7 crashes).
- (superseded) Next: base control (running) → R4 idea = rule card (experiments/final/RULE_CARD.md) in the prompt + more data + 3
  epochs, with the verifier's E1-E4 (A+card control; pre-register; bar (d) token form cannot pass at ≈ 7.1k/answer).
- Next: Muse round 2b (E2 test, E3 calls.jsonl cross-check) + verifier review of round 2 + 2b → **dev check** (step 5,
  cap $1, gate ≥ 80% at 0.2%).
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
