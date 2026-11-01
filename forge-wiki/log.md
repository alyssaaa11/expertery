# Forge wiki: log

## [2026-10-28 14:05] create | forge-wiki (user: "why are u using the project herdshot if is forge, u are mixing contexts")
- Moved the Forge pages out of ~/swarms/herdshot/herdshot-wiki: forge-design, forge-questions, forge-diagrams,
  final-pick-research, forge-plan, 6 diagrams, and the 4 final-pick raw reports. Links into HerdShot pages became plain
  path references. Forge lessons collected into wiki/lessons/lessons.md.

## [2026-10-28 14:15] create | glimmer-test-1-2026-10-28 (user: "do a test of glimmer"); Forge deploy script + secret forge-glimmer created

## [2026-10-28 14:40] update | forge-plan-2026-10-28 (first test: 15+15 jobs; Spark Open on Baseten credits)

## [2026-10-28 16:55] update | forge-diagrams (diagram 7 final plan) + forge-questions (Spark Open vs 1.3)

## [2026-10-28 17:45] update | lessons (overlap check, blind rebuild); first test prep: 33 jobs, self-test 33/33, blind 33/33, manual.md, RUNNER_SPEC.md

## [2026-10-28 18:00] update | forge-plan (Baseten $100 credit per user; card on file; check after dry run)

## [2026-10-28 17:25] update | forge-plan (Muse Code built runner, ~$0.51; e2e 33/33)

## [2026-10-28 17:55] update | forge-plan (dry run OK, spend ≈ $1.56) + lesson (modal app stop -y)

## [2026-10-28 18:50] create | first-test-2026-10-28 (main run results; decision = grey zone, waiting for the user)

## [2026-10-28 19:00] decision | first-test → GO (user, from grey zone)

## [2026-10-28 20:30] update | first-test (3 of B's failures are position-only; B2 cheap-fix arm proposed)

## [2026-10-28 21:00] create/update | status (START HERE), tools-and-services, value-and-market, factory-plan; lessons +8; superseded cost estimate and old schedule marked; first-test 'how the exam was built'; index rewritten (user: "put it in the wiki so nothing is forgotten")

## [2026-10-28 21:05] update | status (GitHub repo meta-hackathon, private, published by Muse Code, no leaks) + lesson (rules page)

## [2026-10-28 21:55] update | status (B2 cancelled by the user; private-tool AcmeCAD direction proposed)

## [2026-10-28 22:00] update | factory-plan (day-by-day plan for the AcmeCAD direction, proposed)
- 2026-10-28 22:30 decision: fictional space company Quillon Orbital Works, private tool Keel, company dashboard; draft spec company/SPEC.md (user review pending)
- 2026-10-28 22:20 verified: Muse Code built company/ (Keel, manual, 8 examples, dashboard); SELFTEST 35/35 re-run by Claude; 21 calls, ~$0.40 Meta; dashboard opened in Chrome. Note: request statuses (AI draft / Gauge PASS) are sample data until the assistant really runs.
- 2026-10-28 ~22:20 verified: Keel v2 built by Muse Code (~$0.80, selftest 88/88, spot-checks exact); v2 exam experiments/keel-exam-v2: selftest 90/90, blind rebuild 30/30; v1 exam kept as history. Verifier audit requested.
- 2026-10-28 23:14 verified: Keel v2 pilot (M1, M7, H9, Spark, k=1) 3/3 PASS, $0.03, no harness errors (results/keel-v2-pilot). 23:15 main run started (user yes).
- 2026-10-28 23:30 verified: Keel v2 main run: B Glimmer+manual 97.8%, C Spark 100% → rule 2 NO ROOM. Clean (0 harness/PermissionError). See [[keel-v2-baseline-2026-10-28]].
- 2026-10-28 23:39 filed: findings/quillon-keel-build-2026-10-28 (build method), 8 new lessons, tools-and-services evening facts.
- 2026-10-29 00:15 filed: decisions/night-prep-2026-10-28 (5 free night tasks: Spark context 1M from catalog, training recipe, verifier pre-review READY WITH FIXES, Tern/Skua drafts self-test 90/90, B2 sandbox spec), raw/training-recipe-research-2026-10-28.
- 2026-10-29 verified: coverage audit 83% (k=5) → Option A skipped by the user's noon rule. Page findings/coverage-audit-2026-10-29.
- 2026-10-29 decision (user): new goal = same quality, many times cheaper and faster, private. Page decisions/new-goal-2026-10-29.

## [2026-10-29] research | learning guide: training weights + verifiers
- Added raw: raw/knowledge/research-training-from-verified-data-2026-10-29.md, research-verifier-design-2026-10-29.md, research-cad-code-papers-2026-10-29.md (subagent reports, unedited)
- Created: wiki/findings/learn-training-and-verifiers-2026-10-29.md (3 key papers re-read in full: 2505.19713, 2605.07807, 2610.25812)
- Updated: wiki/status.md open questions 2 and 5; index.md
- 2026-10-29 12:32 verified: step-2 baseline: BR 87%, B2 88%, BX 95% (79/90 ran); Modal ≈ $4.5. Page findings/bmax-baseline-2026-10-29.
- 2026-10-29 13:49 verified: training smoke test (≈$1.06): train OK, 8k OOM, vLLM LoRA crash, merge OK, strict PASS. Page findings/training-smoke-2026-10-29.

## [2026-10-29 night] plan | training + final exam prepared, not run
- Created: experiments/final/PLAN.md, MUSE_SPEC.md; forge-wiki/wiki/assets/diagrams/forge-training-exam-plan.png, forge-how-training.png (assets/diagrams);
  findings/how-training-changes-weights-2026-10-30; decisions/submission-draft-2026-10-30, morning-brief-2026-10-30
- decision (user): budget $50; finish BX to 30 jobs (step 6a). Verifier: pre-build READY WITH 5 EDITS (applied 1861990),
  delta READY WITH 3 EDITS (applied 9602647).
- verified: Spark Open 816B/42B active, ≥ 700 GB VRAM (HF card); Mac 24 GB vs MLX Glimmer ≥ 48 GB recommended.
- Fresh direction review: 6/10, rebalance toward Impact + Demo. Lessons +8. README status refreshed.

## [2026-10-30] fix | diagrams visible in Obsidian + project page
- Moved the 2 new diagrams from attachments/ (HTML only, not shown in Obsidian) to wiki/assets/diagrams/ with PNGs (8, 9 in forge-diagrams); embedded in the training page; created wiki/project.md (one-page overview).

## [2026-10-30] explain | simple words
- Created wiki/forge-in-simple-words.md (story, word list) + 2 simple diagrams (10, 11 in forge-diagrams). Lesson added.

## [2026-10-30 ~09:30] save | before the user cleared the chat
- forge-in-simple-words: added the user's questions + answers (LoRA, the notebook, why freeze, one notebook vs pages, what is built).
- status: "Where we stopped" (factory first, demo last; Muse round 1 ready, NOT started; launch recipe; open recommendations).
- project: where we are. experiments/final/MUSE_ROUND1.md committed (not run).


## [2026-10-30] build | factory (Muse round 1) + learning loop + verifier
- verified: Muse round 1 (e24a9a7): cloud_cq box + grader, generator/make_jobs (200 jobs), teacher, patterns.py v0,
  exam guard on box, cached_tokens fix; ≈ $2.4. Claude re-checks all pass.
- decision (user): learning loop, suggest-and-approve (SPEC §4, 27e8800 missed the file; written in e24a9a7, verifier items dac893d).
- verified: verifier FAIL for pilot / GO for fix round (forge-factory-build-2026-10-30, 4/7/5); round 1b prompt ready, not launched.
- 2026-10-30 verified: Muse r1b (d304368, ≈ $0.96) fixed F1/F2/F4 + gallery; verifier FAIL for pilot (G1 text≠reference in
  4 families), GO for cheap Modal checks with filtered inputs. Round 1c prompt ready (00394af), not launched.

## [2026-10-30 afternoon] factory ready (pending verifier) + repo readiness
- verified: Muse r1c (5edd84a) + r1d (ff7f3a4); cloud checks: REFS 200/200 + 30/30, regrade 199 same, blind rebuilds 10/10 + 10/10.
- decision (user): precise volumes in factory grader; no Wonder output in training; updates via hivey/Slack.
- Repo readiness 1-7 (f692227, 3f392d6), verifier reviewing.
- 2026-10-30 verified: factory pilot 19/20 (95%), $0.52, 0 patterns (6274420); main run proposed (160 jobs).
- 2026-10-30 verified: factory main 148/157 (94%) $4.38; training set 167 records; Muse round 2 built $2.40 (fd1d32c). Money ≈ $43.6.
- 2026-10-30 17:00 verified: dev check STOP: trained Glimmer 38.3% (23/60) at 0.2%; pilot D1-D3 0/3. Exam untouched.

## [2026-10-30 21:40] ingest | training experiments + diagnosis
- raw: second-opinion brief/answer, superintel task/answer (training diagnosis).
- Created: wiki/findings/training-experiments-2026-10-30.md. Updated: status (now), scoreboard §4, lessons (+6), index.
- verified: R1 38.3%, R3 48.3%, untrained 51.7% on dev; decision pending: cheap check, then self-distillation.

## [2026-10-30 22:40] save | before the user cleared the chat
- status NOW: rule-card check running (R3+card, then A+card), reading pre-registered, next steps, working rules.
- Claude small fix bb5e080 (FORGE_RULE_CARD) disclosed in README.

## [2026-11-01 16:45] update | R5 round (Oct 31 – Nov 1)
- new: findings/r5-own-answers-training-2026-11-01, decisions/r5-decisions-2026-10-31; indexed the 10-31 findings pages.
- status NOW rewritten: trained model ready, baselines 62/96 on R5D, next = FT test (user OK), Spark hints, final training.
- lessons +10 (card beats training, held-out check, own answers, filter dry-run, token caps, billing month, prompt ranges, announce runs, stand-in agents).
- scoreboard §4 (R5 held-out baselines).

## 2026-11-01 18:30
- r5 dev 94/100 (no card); Spark hints 54/76 usable, retries solved 52/54; r5f mix 1,742 (46 tutoring); r5f training started.
- new: findings/r5-final-spark-guided-2026-11-01; status NOW rewritten.
