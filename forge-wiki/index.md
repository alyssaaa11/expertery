# Forge wiki: index

Project folder: `~/projects/forge` (README routes to code, results and everything else).

- [status](wiki/status.md): **START HERE each day**: goal, what is proven, money, open questions, next step

## findings
- [learn-training-and-verifiers-2026-10-29](wiki/findings/learn-training-and-verifiers-2026-10-29.md): learning guide: 5 levels (prompting → SFT on verified teacher → data tricks → DPO → GRPO), what research says on data, LoRA, RL cost, referee design (mutants, spec-based CADTests), reward hacking, SAM 3.1 verdict, Forge checklist, reading list, exercises
- [quillon-keel-build-2026-10-28](wiki/findings/quillon-keel-build-2026-10-28.md): how the private-tool experiment was built: company, Keel v1→2.1, dashboard, exam method, tolerance 1e-6, sandbox, freeze by hash, verifier rounds, user plan rules
- [keel-v2-baseline-2026-10-28](wiki/findings/keel-v2-baseline-2026-10-28.md): private tool Keel v2: Glimmer + manual 97.8%, Spark 100% → NO ROOM; a short complete manual is enough
- [first-test-2026-10-28](wiki/findings/first-test-2026-10-28.md): the main experiment: how the exam was built; Spark Open 30/30, Glimmer+manual 20/30, Glimmer 16/30 → grey zone → user GO; 3 of 10 failures position-only; B2 proposed
- [value-and-market-2026-10-28](wiki/findings/value-and-market-2026-10-28.md): why Forge instead of the big model, cost per job, who would use it, space-company example, honest downside, how to demo a background run
- [tools-and-services](wiki/findings/tools-and-services.md): checked facts: Modal, Baseten, Meta API + Muse Code, CadQuery, Glimmer, Spark Open
- [glimmer-test-1-2026-10-28](wiki/findings/glimmer-test-1-2026-10-28.md): first live Glimmer run: cube ✅, L-bracket ❌ (wall off the base); $0.57
- [forge-design-2026-10-28](wiki/findings/forge-design-2026-10-28.md): what Forge is, the design, why, demo idea
- [forge-questions-2026-10-28](wiki/findings/forge-questions-2026-10-28.md): privacy per company, why CadQuery, why test Glimmer first, selling without credits, Spark Open vs 1.3
- [forge-diagrams](wiki/findings/forge-diagrams.md): all 7 Archify diagrams (what it is, design, use cases, checklist, plan, factory, final plan)
- [final-pick-research-2026-10-28](wiki/findings/final-pick-research-2026-10-28.md): why Forge was picked: claude.ai 90 + GPT-6 92 merged, prior art, risk paper 2607.08938

## decisions
- [option-a-plan-2026-10-29](wiki/decisions/option-a-plan-2026-10-29.md): plan for Oct 29: hidden standards in ~300 past designs, arms B / B-search / C, Spark context check, blind rule check, B2 CadQuery test in parallel
- [night-prep-2026-10-28](wiki/decisions/night-prep-2026-10-28.md): night prep for Oct 29: Spark context, training recipe, verifier pre-review, drafts, risks and second plans, morning decisions
- [coverage-audit-2026-10-29](wiki/findings/coverage-audit-2026-10-29.md): free retrieval-coverage audit: 83% of exam jobs covered by top-5 → Option A skipped
- [new-goal-2026-10-29](wiki/decisions/new-goal-2026-10-29.md): new goal: same quality, many times cheaper and faster, private; B-max baseline; kill rule
- [glimmer-dashboard-2026-10-29](wiki/findings/glimmer-dashboard-2026-10-29.md): live Chrome dashboard of the baseline run (how Glimmer is doing)
- [bmax-baseline-2026-10-29](wiki/findings/bmax-baseline-2026-10-29.md): step-2 baseline: plain 87%, hint 1-try 88%, all fixes 95%; bar for the trained Glimmer
- [factory-plan-2026-10-29](wiki/decisions/factory-plan-2026-10-29.md): next stage: B2 → recipe research → generator → teacher run → training → final exam; rules; ~$13–16
- [forge-plan-2026-10-28](wiki/decisions/forge-plan-2026-10-28.md): history of Oct 28 decisions: $30 budget, CadQuery, Spark Open on Baseten, own folder/app, spend log

## lessons
- [lessons](wiki/lessons/lessons.md): 34 lessons with how they were learned: cheap baseline first, referee self-test + overlap check, blind rebuild, verifier before paid runs, ordered decision rules, look at how a model fails, modal app stop -y, Muse Code costs, one project per context
