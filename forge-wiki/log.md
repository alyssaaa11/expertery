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
- Created: experiments/final/PLAN.md, MUSE_SPEC.md; attachments/final-plan-diagram.html, how-training-works.html;
  findings/how-training-changes-weights-2026-10-30; decisions/submission-draft-2026-10-30, morning-brief-2026-10-30
- decision (user): budget $50; finish BX to 30 jobs (step 6a). Verifier: pre-build READY WITH 5 EDITS (applied 1861990),
  delta READY WITH 3 EDITS (applied 9602647).
- verified: Spark Open 816B/42B active, ≥ 700 GB VRAM (HF card); Mac 24 GB vs MLX Glimmer ≥ 48 GB recommended.
- Fresh direction review: 6/10, rebalance toward Impact + Demo. Lessons +8. README status refreshed.

