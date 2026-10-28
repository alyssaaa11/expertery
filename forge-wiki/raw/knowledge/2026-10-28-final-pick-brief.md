# Validate and pick ONE final Meta hackathon project (Oct 28, 2026)

**Goal:** a solo developer must commit by Oct 29 to one project for the Meta Global AI Developer Hackathon (Indie track, "Push the Frontier": use Meta's models on challenges in software, robotics and beyond; "give a machine a new capability"). Build window: Oct 29 – Nov 4, 9pm ET. The 3-minute demo video is judged on **Impact 30%** (real-world potential, who benefits, must fit the problem statement), **Use of Meta AI tooling 25%** (creative, beyond basic integration, "surprised even us"), **Technical depth & execution 20%** (sound, refined engineering), and **Demo 25%** (works live, cool to watch). The developer also wants something they can sell afterwards.

**Context:** Meta tools: Muse Spark (API), Muse Wonder, SAM 3.1, Muse Code (coding agent, which will build the code), and open weights Muse Glimmer (fine-tunable on the developer's Modal H100s) and Muse Spark Open. Budget: about $65 of API spend. The developer builds multi-agent systems daily. A previous project died because the problem didn't occur: agents that read the project files already rejected planted false facts in 70/70 runs. So any problem must provably occur, and "a strong model plus a verifier agent" must not already solve it.

**Candidates:**
- **Forge:** point it at an unseen tool/CLI/API; a Muse Spark swarm writes ~300 tasks with executable checks; Glimmer is fine-tuned (LoRA SFT, maybe GRPO) on verified traces → a private local agent that masters the tool.
- **Gatebreaker:** an agent swarm (Glimmer RL-trained as attacker) finds wrong-but-passing outputs against tests and LLM judges, then hardens the verifier and proves valid work still passes.
- **Team Doctor:** detects when a multi-agent team is badly composed (wasting tokens, confusing itself, doing worse than one agent) while it runs, and restructures it live (fewer agents, an orchestrator, or a single agent), with before/after accuracy, tokens and time.

**Questions (most important first):**
1. For each: is the underlying problem real and growing in 2025–2026? Evidence of pain, money or time already spent, current workarounds, and evidence AGAINST it.
2. Closest prior art (papers, products, open-source; 2025–2026) and how new each one really is. Would "a strong model + verifier/judge agent" already deliver it?
3. Are Meta's models essential (would it break with another model?), and what could surprise Meta?
4. Feasibility for one person in 6 days, a day-1 kill test that shows the problem actually occurs, and the 3-minute demo story.
5. Score each on the 30/25/20/25 rubric and on sellability (who pays, comparable prices). Pick one, with a runner-up, and give the main risk of the pick.

**Scope:** primary sources (arXiv, official docs, company pages, repos), 2025–2026; cite inline with links. **Output:** executive summary first, comparison tables, ranked recommendation.

Assume sensible defaults rather than asking me clarifying questions.
