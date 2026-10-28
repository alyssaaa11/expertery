---
title: "Final Meta hackathon pick (Forge vs Gatebreaker vs Team Doctor): merged research report"
date: 2026-10-28
type: merged-research
sources: [claude.ai Research (Fable 5.1, High), ChatGPT (GPT-6 Astra, High), arXiv sweep]
claude_chat: https://claude.ai/chat/ec812b0f-d897-4d2a-af04-5834a64d9c0a
chatgpt_chat: "Choose Forge Project"
scores: {claude: 90, chatgpt: 92}
---

# Final Meta hackathon pick: merged research report

Brief: `brief.md` (pick ONE of Forge, Gatebreaker, Team Doctor; PhysLoop removed by the user). Reports: claude.ai
Research **[C]** (claude-fable-5-1, high, 51 sources), ChatGPT GPT-6 Astra High chat **[G]** (33 links), own arXiv
sweep **[A]** (3 searches with alphaXiv, 22 full texts in `arxiv-full/fulltext/`). Both ran on the requested model
and effort (`claude.json`, `chatgpt.log`): no downgrade.

## Report quality

| Criterion | Max | claude.ai (Fable 5.1 High) | ChatGPT (Astra High) | Notes |
|---|---|---|---|---|
| Accuracy (spot checks) | 25 | 21 | 25 | C 6/7 hold; error: "180 configurations" (paper says 260). G 7/7 hold |
| Sources | 20 | 15 | 18 | C 53 links but primary share 0.21 (many blogs/aggregators); G 33 links, primary 0.52; 0 broken markers in both |
| Coverage of the brief | 15 | 15 | 15 | both answer Q1–Q5 with evidence |
| Specificity | 15 | 15 | 10 | C 73 numbers (prices, rate limits, Glimmer HW, cost per rollout); G 17 |
| Calibration | 10 | 9 | 10 | G says outright that Forge "would not fundamentally break" with other models, and gives moderate confidence; C has a good caveats section but overstates Meta-essentiality |
| Usefulness | 15 | 15 | 14 | C: concrete kill test with self-verified checks, folds Gatebreaker into Forge; G: four-arm baseline (incl. skills file), day plan, budget split |
| **Total** | **100** | **90** | **92** | **Winner: ChatGPT by a hair (both excellent; C is the more specific, G the more accurate)** |

| metric | claude | chatgpt |
|---|---|---|
| words | 3484 | 5270 |
| linked_sources | 53 | 33 |
| unique_domains | 36 | 16 |
| primary_share | 0.21 | 0.52 |
| unresolved_citation_markers | 0 | 0 |
| numbers_stated | 73 | 17 |

**Spot checks (full texts in `arxiv-full/fulltext/`, 2026-10-28):**
- [C] Muse Spark 0% cheating on ImpossibleBench (2606.12429) ✔ (table: Spark 0.0, GPT-5.4 0.0, Opus 4.6 2.9, Gemini 3.1 Pro 11.8)
- [C] General Verifier 66.8% false positives on MATH from a blank space (2507.08794) ✔; "GPT-4o fooled up to 35%" not found in text, unverified
- [C] ImpossibleBench "STOP … do NOT carve out the code" prompt (2510.20270) ✔ exists; the 93%→1% and 76% numbers are not in the HTML text (likely figures), unverified
- [C+G] Scaling Agent Systems 2512.08296: −39% to −70% on PlanCraft (sequential), 17.2× vs 4.4× error amplification, 87% architecture prediction on held-out configs ✔; **[C] "180 configurations" ✗: the paper says 260**
- [G] Hacker-Fixer 2606.08960: 1,968 tasks audited, 323 (16%) hackable ✔
- [G] Worse Together 2610.00583: separate agents often worse than a single coordinator ✔ (multi-user setting; direction depends on model and environment)
- [G] Token study 2604.22750: up to 30× token variance on the same task; more tokens don't buy accuracy, which peaks at intermediate cost ✔
- [G] CATS 2610.29292 prunes weak agents/edges into a fixed deployment team ✔; Autonomous Topology Mutation 2607.20488 = "Safe Runtime Restructuring" ✔ (title)

> [!summary] Bottom line
> 1. **Both reports independently pick Forge** ([C] 8.25/10, [G] 81/100): Muse Spark writes tasks for one unfamiliar tool with checks that run, then Glimmer is fine-tuned (LoRA/QLoRA SFT on one H100) into a private local agent for that tool. The story matches Meta's own recipe: Glimmer was distilled from Spark [C]. [C+G]
> 2. **It is not a new research method** (NVIDIA CLI training, Nemotron-Terminal 2602.21193 [A, verified], ToolACE, Tool-R0, AutoPlay, ToolForge, OpenPipe ART). The pitch is a working per-tool "teacher → private local specialist" capability, with honest baselines. [C+G]
> 3. **Main risk = the HerdShot trap again:** base Glimmer with the docs, or with a short skills file or adapted harness, may already do the tool. CMU's 2607.08938 [A, verified] got small models to 89.7% of a large model's performance at 4% of the cost by adapting the harness alone, with no fine-tuning. Day 1 must prove a real, learnable gap. [C+G+A]
> 4. **Gatebreaker alone is a poor bet:** a near-exact predecessor exists (Hacker-Fixer 2606.08960, verified) and Muse Spark cheats 0% on ImpossibleBench (verified), so the demo is weak with Meta's model. Its best use is inside Forge, attacking every task check before training. [C+G]
> 5. **Team Doctor's problem is the best documented** (260 configs, −39–70% on sequential tasks, token waste; verified), but the fix is crowded (AgentDropout, CATS, topology mutation, Magentic-One, LangSmith Engine) and Meta's models aren't essential. Fallback if Forge's day-1 gate fails ([G]), and a good later business ([G] sellability 4.2/5). [C+G]
> 6. **Meta-essential? Honestly, partly.** Forge would *run* with Qwen; the Meta case is Apache-2.0 Glimmer + Spark as teacher + Meta's documented single-H100 post-training, i.e. Meta-native, not Meta-only. [G, the more accurate view; C overstates]

## 1. Is each problem real and growing? (with evidence against)

- **Forge:** labs pay heavily for verifiable agent tasks: Epoch AI reports $200–$2,000 per RL task and contracts of six to seven figures per quarter (interview-based), and Anthropic leaders reportedly *discussed* >$1B on RL environments [C]. Small RL-trained models beat frontier ones on narrow tasks: OpenPipe ART·E (Qwen 2.5 14B) 96% vs o3 90% on email search, about $80 to train [C, not checked]. Nemotron-Terminal: SFT on synthetic terminal tasks lifts Qwen3-32B from 3.4% to 27.4% on Terminal-Bench 2.0 [A, verified]. **Against:** strong models with the docs in context often already work; much of the workflow is reproducible with existing tools (NVIDIA tutorial) [C+G]; harness adaptation alone closes most of the gap in 7/21 task-model pairs (2607.08938) [A, verified].
- **Gatebreaker:** verifiers are hackable: 16% of 1,968 benchmark tasks (2606.08960) [G, verified]; a blank space fools a general verifier 66.8% of the time on MATH (2507.08794) [C, verified]. **Against:** the loop is published with code (2606.08960) [G]; Spark cheats 0% on ImpossibleBench (2606.12429) [C, verified]; Master-RM shows the judge weakness can be trained away [C].
- **Team Doctor:** multi-agent teams lose 39–70% on sequential planning; independent agents amplify errors 17.2× (2512.08296) [C+G, verified]; agent token use varies up to 30× with no accuracy gain (2604.22750) [G, verified]; Anthropic says multi-agent systems use about 15× the tokens of chats [C]. **Against:** the scaling paper's model already picks the best architecture for 87% of held-out configs, so a static rule may match a live doctor [C+G, verified].

## 2. Prior art and "would a strong model + verifier already do it?"

| | Closest prior art | Strong model + verifier already does it? |
|---|---|---|
| Forge | NVIDIA CLI training (synthetic + GRPO) [G]; Nemotron-Terminal 2602.21193 [A]; ToolACE, Tool-R0 2602.21320, AutoPlay, ScaleEnv, SPADE 2608.19197, ToolForge (EMNLP 2026; name clash) [G]; Agent World Model, CodeGym, OpenPipe ART/RULER (acquired by CoreWeave) [C] | **At runtime, often yes** (Spark + docs + checker). **Not locally, privately, offline, at zero marginal cost**: the value is distilling that into weights [C+G] |
| Gatebreaker | Hacker-Fixer 2606.08960 (near-exact spec, code released) [G]; ImpossibleBench, EvilGenie, Reward Hacking Benchmark, BaitBench, Master-RM [C]; weak-to-strong verifier hardening 2610.15924 [A] | Already implemented in prior work [G]; Spark doesn't cheat when told not to [C] |
| Team Doctor | AgentDropout (−21.6% prompt / −18.4% completion tokens) [C+G]; AgentPrune, G-Designer, MaAS, ARG-Designer [C]; Topology Mutation 2607.20488, DATS 2609.13890, CATS 2610.29292, Magentic-One, LangSmith Engine [G]; Dream2Discern 2610.16071 (runtime failure prediction >90%), AgentConductor 2602.17100, DoVer 2512.06749 [A] | Largely yes: a supervisor plus a "try one agent" baseline captures most of the gain [C+G] |

## 3. Are Meta's models essential? What could surprise Meta?

- **Forge:** the strongest Meta story of the three [C+G]. Glimmer is 30B dense, Apache 2.0, distilled from Spark, built for local agents [C]; LoRA SFT fits on one 80 GB H100, and Meta's own post-training guide reports about 27 GB peak for a QLoRA run and recommends several hundred good examples [C+G]. Possible surprise: "Glimmer learned a tool released after its cutoff, in one evening on one H100, and now beats its teacher-without-docs, offline" [C]. But it is Meta-native engineering, not Meta-only: it would run with another open model [G].
- **Gatebreaker:** moderate. An RL-trained Glimmer attacker uses open weights, but any open model could attack [C+G].
- **Team Doctor:** weak. Detection could be deterministic telemetry plus scheduler rules [G]; any model works [C].
- **Not worth forcing in:** SAM 3.1 for a CLI project [G]. Exception: a fabrication CLI (OpenSCAD/CadQuery/slicer) where SAM masks the rendered part as an extra check [C].

## 4. Feasibility, day-1 kill test and demo

**Merged day-1 test for Forge (Oct 29; about $5 in Contributor mode for a public tool, plus about 2 H100-hours) [C+G+A]:**
1. Shortlist 2–3 sandboxable tools with checkable outputs and low pretraining exposure (released or changed after Aug 2026, or niche; hivey CLI is a candidate) [C+G].
2. Spark writes ~60 tasks per tool; for each, a reference solution and 2 deliberately wrong ones. Keep only checks that pass the reference and fail both wrong ones (checks verified, Gatebreaker-style) [C]. Freeze 40–60 held-out tasks from a *different* generator prompt plus 10–15 hand-written ones [C+G].
3. Arms: Glimmer no docs; **Glimmer + full docs**; **Glimmer + short generated skills file / adapted harness** [G+A]; Spark + docs + verifier.
4. Proceed if the best cheap Glimmer arm ≤ 60%, Spark ≥ 75% and ≥ 20 points above it, check false-pass rate < 5%, and Glimmer load → one QLoRA step → adapter reload works on Modal [C+G]. Kill the tool if Glimmer + docs ≥ 80% [C]. Kill Forge if every tool fails; then fall back.
5. Final claim target: +15–20 points on unseen tasks over the strongest cheap local baseline, with paired outcomes and uncertainty, not "broad generalization" [G].

**Build:** day 2 ~300+ tasks and verified Spark traces (aim for 500–800 accepted demonstrations [G]); day 3 LoRA SFT on Modal and first eval; day 4 attack/harden checks, GRPO only as a stretch [C+G]; day 5 second tool + UI; day 6 video with buffer.

**Budget:** about 2,400 Spark rollouts ≈ $141 uncached, ≈ $61 cached, ≈ $10 in Contributor mode (public tool only) [C]. Contributor mode lets Meta train on the data, so use it only for public tools [C+G]. Modal H100 ≈ $3.95/h [G]; Fireworks reportedly offers free Glimmer SFT to Nov 30 [G, unverified].

**3-minute demo [C+G]:** base Glimmer fails a live task on a tool it has never seen → Forge runs (Spark swarm writes tasks; wrong answers attack the checks; traces fill up) → training curve on one H100 (pre-trained, labelled as such) → the same unseen task passes with Wi-Fi off, next to a scoreboard of base / +docs / +skills / Spark+docs / Forge-Glimmer for accuracy, latency and cost → point Forge at a second tool.

## 5. Scores and pick

| | [C] weighted /10 | [G] /100 | Sellability |
|---|---|---|---|
| **Forge** | **8.25** | **81** | C high; G 3.8/5 (pilot $2–5k per integration, a pricing experiment) |
| Gatebreaker | 6.95 | 73 | C medium; G 3.3/5 |
| Team Doctor | 6.50 | 76 | C low–medium; G 4.2/5 (recurring savings; competes with LangSmith $39/seat, Langfuse $29–199, Braintrust $249) |

**Pick: Forge, scoped to one hero tool + a quick second tool** [C+G]. **Runner-up:** split verdict, see below. **Main risk:** no learnable gap over Glimmer + docs/skills/harness [C+G+A].

## Where the reports disagree

| Topic | claude.ai says | ChatGPT says | Verdict (and how decided) |
|---|---|---|---|
| Runner-up | Gatebreaker (6.95) | Team Doctor (76) | **Team Doctor as the standalone fallback; Gatebreaker as a component inside Forge.** Gatebreaker's near-exact predecessor (2606.08960) and Spark's 0% ImpossibleBench cheating are both verified, which kills it alone. C's own idea of attacking Forge's checks is the best use of it |
| Are Meta models essential to Forge? | "Essential by design" | "Would not fundamentally break if replaced" | **G is right on substance; C's version is the pitch.** Nothing in the method needs Glimmer specifically; the Meta case is licence, teacher pairing, and documented single-H100 training |
| Team Doctor sellability | Low–medium | 4.2/5, the best of the three | Both cite the same observability prices; G adds the recurring-savings argument. Unresolved: no buyer evidence either way |
| Kill threshold | Glimmer+docs ≤ 60%, Spark ≥ +20 pts, kill at ≥ 80% | Glimmer+docs ≤ 60%, teacher ≥ 75%, final +15–20 pts | Compatible; merged into § 4 |

## Errors found

- [C] "Towards a Science of Scaling Agent Systems … 180 configurations": the paper says 260 (2512.08296 full text).
- Unverified (kept with a label, not dropped): [C] GPT-4o fooled up to 35%; [C] ImpossibleBench 76% and 93%→1%; [G] Fireworks free Glimmer SFT; [G] ToolForge EMNLP 2026 name clash.

## Papers neither report cited

- **2607.08938** Better Harnesses, Smaller Models (CMU): automated harness adaptation lets small models recover 89.7% of LLM performance at 4% cost, with no fine-tuning. **The strongest cheap baseline Forge must beat.**
- **2602.21193** Nemotron-Terminal (NVIDIA): Terminal-Task-Gen synthetic tasks + SFT, Qwen3-32B 3.4% → 27.4% on Terminal-Bench 2.0. Shows the Forge recipe works for general terminal skill; Forge's gap is the per-tool private specialist.
- **2606.24855** OpenThoughts-Agent: open data recipes for agentic models (training-data reference for Forge).
- **2610.15924** Weak-to-strong verifier hardening (Stanford/CMU): hacker-fixer loop on Terminal Bench, KernelBench, SETA; a second Gatebreaker predecessor.
- **2610.16071** Dream2Discern: runtime auditor predicting multi-agent failure from execution prefixes, >90% accuracy; Team Doctor prior art.
- **2602.17100** AgentConductor and **2512.06749** DoVer (Microsoft): RL-adapted topology and intervention-driven multi-agent debugging; Team Doctor prior art.
- **2610.28679** VerifierBench: generated verifiers both falsely accept and falsely reject; supports verifying Forge's checks.

## What each report added that the other missed

- **claude.ai only:** Spark 0% ImpossibleBench (kills Gatebreaker's demo); Glimmer is distilled from Spark (the narrative); Glimmer hardware matrix (LoRA SFT 1×H100, GRPO tight, Unsloth 24 GB); Spark rate limits and prices; cost per 2,400 rollouts; self-verified checks (reference + 2 wrong solutions); fabrication-CLI + SAM option; Glimmer AA index 35 vs 17 uncertainty.
- **ChatGPT only:** Hacker-Fixer 2606.08960 (verified, decisive against Gatebreaker); the skills-file baseline arm; honest "Meta-native not Meta-only"; ToolForge name clash; Worse Together, token study, CATS, Topology Mutation, DATS; Modal price; budget split; day-by-day plan; Team Doctor's best business case.

## Sources

[C] = claude.ai report sources (see `claude.md` § Sources, 51 items); [G] = ChatGPT report sources (see `chatgpt.md` § Sources, 33 items). Key ones:
1. [C+G] Towards a Science of Scaling Agent Systems, arXiv 2512.08296
2. [C+G] Meta Model API docs: models, pricing, Muse Glimmer post-training (dev.meta.ai/docs)
3. [C+G] Cerebral Valley / Meta hackathon event page
4. [C] Muse Spark Safety & Preparedness Report, arXiv 2606.12429
5. [C] One Token to Fool LLM-as-a-Judge, arXiv 2507.08794
6. [C] ImpossibleBench, arXiv 2510.20270
7. [C] Epoch AI, An FAQ on reinforcement learning environments
8. [C] Hugging Face blog, Muse Glimmer; Unsloth Glimmer docs
9. [G] Hardening Agent Benchmarks with Adversarial Hacker-Fixer Loops, arXiv 2606.08960
10. [G] Worse Together, arXiv 2610.00583
11. [G] How Do AI Agents Spend Your Money?, arXiv 2604.22750
12. [G] CATS, arXiv 2610.29292; Autonomous Topology Mutation, arXiv 2607.20488; DATS, arXiv 2609.13890
13. [G] NVIDIA, Training an AI agent for command-line tasks with synthetic data and RL
14. [G] Tool-R0 2602.21320; SPADE 2608.19197; ToolACE (ICLR 2025); ToolForge (EMNLP 2026)
15. [A] 2607.08938, 2602.21193, 2606.24855, 2610.15924, 2610.16071, 2602.17100, 2512.06749, 2610.28679
