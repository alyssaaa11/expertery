---
source: ChatGPT chat (web search)
model: GPT-6 Astra
effort: high
date: 2026-10-28
chat: Choose Forge Project
brief: ~/Research/2026-10-28-hackathon-final-validation/brief.md
---

# Meta Global AI Hackathon: Final Project Decision

Research assessment · October 28, 2026 · Decision deadline: October 29

## Executive summary

# 1. Forge — Recommended

Conditional goAn AI system that learns to master an unfamiliar real-world tool, then transfers that expertise into a private, locally running Meta model.

Predicted hackathon score

# 81/100

Commercial potential

## Medium–high

My recommendation is to commit to Forge, but change its central claim. Do not pitch it as an invention of synthetic tool-training data. That already exists. Pitch it as an automated system that converts expensive, repeated tool exploration into a verified, reusable capability inside a private local model.

The strongest demonstration would be:

> An unfamiliar tool takes a general agent repeated exploration and corrections to operate. Forge explores it, creates executable tasks, learns from successful operations, and produces a tuned Muse Glimmer agent that completes new tasks locally, with fewer attempts and lower recurring cost.

There is one important condition: the tuned model must outperform an untuned Glimmer given the same tool documentation, execution access, and opportunities to self-correct. Without that comparison, the project risks becoming an impressive-looking training pipeline with no demonstrated benefit.

### Ranked decision

| Rank | Candidate | Predicted score | Verdict |
| --- | --- | --- | --- |
| 1 | Forge | 81/100 | Best balance of Meta-native innovation, technical demonstration and potential product |
| 2 | Team Doctor | 76/100 | Strongest evidence of an operational problem; weaker novelty and Meta-specific advantage |
| 3 | Gatebreaker | 73/100 | Real, valuable problem, but a near-exact research predecessor makes this a poor hackathon bet |

These are my forecasts of how a convincing implementation might score under your supplied 30/25/20/25 rubric, not actual judge scores or independently validated performance.

Three research findings drive the decision:

- Gatebreaker has a near-exact predecessor. June 2026 research implemented an attacker–fixer–solver loop, audited 1,968 benchmark tasks and found 323 hackable environments. Its results include automated verifier hardening and preservation of legitimate solutions. [Hardening Agent Benchmarks with Adversarial Hacker-Fixer Loops](https://arxiv.org/abs/2606.08960?utm_source=chatgpt.com).
- Team Doctor addresses a documented failure, but much of the proposed solution already exists. Runtime topology mutation, dynamic agent elimination, cost-aware topology selection and agent-contribution-based pruning have all been studied. [Autonomous Topology Mutation](https://arxiv.org/abs/2607.20488?utm_source=chatgpt.com), [AgentDropout](https://aclanthology.org/2025.acl-long.1170/?utm_source=chatgpt.com), [DATS](https://arxiv.org/abs/2609.13890?utm_source=chatgpt.com), [CATS](https://arxiv.org/abs/2610.29292?utm_source=chatgpt.com).
- Forge also has predecessors, but it offers the clearest Meta-specific capability demonstration. NVIDIA has already demonstrated specializing a model for a new CLI using synthetic examples and reinforcement learning. Meta, however, supplies a 30B open-weight agentic model, documented single-H100 QLoRA training, and a separate frontier teacher model. That enables a compelling, integrated teacher-to-local-specialist demonstration. [NVIDIA](https://developer.nvidia.com/blog/how-to-train-an-ai-agent-for-command-line-tasks-with-synthetic-data-and-reinforcement-learning/?utm_source=chatgpt.com), [Meta Glimmer post-training](https://dev.meta.ai/docs/muse-glimmer/post-training?utm_source=chatgpt.com).

Important distinction: Forge is the best hackathon choice among these three, not a completely new research method. Its differentiator must be the practical combination, independently verified results, and a new capability that is useful after the demonstration.

## 1. Comparison: real problem, novelty and risk

| Dimension | Forge | Gatebreaker | Team Doctor |
| --- | --- | --- | --- |
| Problem demonstrated in research? | Yes | Very strongly | Very strongly |
| Evidence of growing demand | Moderate | Strong | Strong |
| Originality of core algorithm | Low–medium | Very low | Low–medium |
| Room for product differentiation | High if focused on private tools | Limited without a new mechanism | Moderate if genuinely live and outcome-aware |
| Could a frontier model + verifier substantially solve it? | Often yes, but not necessarily cheaply or locally | Already implemented in prior work | Often yes through replanning |
| Meta models central to result | Very strong | Moderate | Moderate |
| Six-day feasibility | Medium | Medium | Medium–high |
| Most dangerous failure | Fine-tuning adds no value | Judges recognize the predecessor | No measurable gain over static routing |

The central distinction is between a real problem, an original method, and a defensible product. They are three different questions. A problem can be urgent while the proposed solution is already well understood.

### Evidence of underlying demand

| Candidate | Positive evidence | Evidence against the opportunity |
| --- | --- | --- |
| Forge | Tool-use training remains a serious research focus. ToolACE generated training data across 26,507 APIs; Tool-R0 demonstrated self-evolving tool learning from zero initial task data. | Strong models with tool documentation already work well in many environments. NVIDIA's CLI-training tutorial demonstrates that much of this workflow is reproducible with established tools. |
| Gatebreaker | METR observed reward hacking in frontier models; Hacker-Fixer found 16% of audited benchmark tasks exploitable. | The most obvious solution is already available as published research and released implementation. The practical customer base is narrower than all AI-agent developers. |
| Team Doctor | A 260-configuration study shows that collaboration can harm performance. Stanford's token-consumption study finds that more tokens do not reliably produce higher accuracy. | Static routing, dynamic pruning, live restructuring and trace-based diagnosis already exist. A simpler orchestrator may capture most of the benefit. |

The evidence establishes real technical problems. It does not yet establish customer willingness to pay for any of these particular implementations.

## 2. Forge: detailed assessment

### Is the problem real?

Yes, with an important qualification.

Tool-using agents struggle with environments requiring several dependent calls, changing state, recovery from errors, and strict constraints. Researchers continue investing in training environments and synthetic trajectories because manually obtaining large volumes of realistic, verifiable agent data is difficult.

The strongest relevant examples are:

- [ToolGym, January 2026](https://arxiv.org/abs/2601.06328?utm_source=chatgpt.com): an environment covering 5,571 tools across 204 applications, designed to expose difficult multi-step tool-use behavior.
- [AutoPlay, 2025–2026](https://machinelearning.apple.com/research/scaling-synthetic-task?utm_source=chatgpt.com): Apple's environment-exploration system generated tens of thousands of tasks, then used them for agent training and evaluation.
- [ScaleEnv, ICML 2026](https://proceedings.mlr.press/v306/tu26a.html?utm_source=chatgpt.com): generates interactive environments and verifiable tasks to train agents.
- [SPADE, August 2026](https://arxiv.org/abs/2608.19197?utm_source=chatgpt.com): generates executable training environments and trains agents using an adaptive self-play loop.

These support the broader proposition that interactive tool competence can be developed through verifiable experience.

But the strongest commercial pain is more specific: companies have private or unusual workflows, repeated tool-operation requirements, and data they may not want to send to a hosted model. A general agent might solve each task eventually, but repeated rediscovery can consume time, tokens and supervision.

The economic proposition is therefore capability amortization: pay once to teach a tool, then reuse the specialized capability across many tasks.

### Closest prior art

| Predecessor | What it already does | What remains for Forge |
| --- | --- | --- |
| NVIDIA CLI training, Jan 2026 | Synthetic examples, verifiable rewards, GRPO, specialized CLI agent | Automated discovery of an unfamiliar real tool, rather than primarily teaching from supplied seed patterns |
| ToolACE, ICLR 2025 | Multi-agent generation and verification of tool-use training data | Private, environment-specific mastery and deployment |
| Tool-R0, Feb 2026 | Generator and solver co-evolve using real tool calls | An accessible product with a local specialist and measurable workflow savings |
| AutoPlay | Explores environments and generates executable tasks | A focused, CLI/API-based end-to-end tool-apprenticeship experience |
| ToolForge, EMNLP 2026 | Synthesizes and validates multi-turn tool-use data for fine-tuning | Real private environments, local deployment and deployment economics |

The last result also creates a naming problem: ToolForge already exists as a published 2026 system. I would use Forge internally, but choose a distinct public product name.

### What should be genuinely different?

Forge should learn from real environment transitions, not only textual descriptions or generated conversations.

Proposed architecture

Unfamiliar real CLI / API / MCP tool

Commands, errors, state changes and execution resultsMuse Spark 1.3

Explore, propose tasks, generate candidate tracesIndependent verifier

Check actual environment state and task validityVerified training corpus

Accepted demonstrations, failures, retries, separate held-out scenariosMuse Glimmer 30B + QLoRA

Private specialist with learned tool behaviorUnseen real tasks

Compare against untuned models, documentation and reusable skillsThe ability to conduct post-training is unusually practical here. Meta documents QLoRA for Muse Glimmer on a single H100 and reports approximately 27 GB of peak GPU memory for one bounded QLoRA experiment. The same documentation cautions that several hundred high-quality examples are a more credible starting point than a tiny dataset. [Meta post-training guide](https://dev.meta.ai/docs/muse-glimmer/post-training?utm_source=chatgpt.com).

Do not promise 300 generated tasks equal 300 valid training examples. Some tasks will be unsolvable, duplicated, trivial or incorrectly verified. I'd aim for 500–800 independently accepted demonstrations, potentially derived from fewer task families, while keeping test scenarios fully separate.

### Would a strong model plus verifier solve it?

Frequently, yes. That is Forge's biggest challenge.

You must compare four approaches under equivalent tool access:

| Approach | Question it answers |
| --- | --- |
| Untuned Glimmer + full tool documentation | Is fine-tuning needed at all? |
| Untuned Glimmer + concise generated skill/reference | Would a simple knowledge file deliver nearly the same result? |
| Muse Spark or Wonder + tools + verifier | Can a frontier model already perform the task reliably? |
| Tuned Glimmer + the same tools | Does learned specialization improve the local agent? |

A strong frontier model winning outright does not automatically invalidate a local specialist, provided the local model achieves adequate success at lower recurring cost or under an offline/privacy constraint.

But if a short generated skills file performs about as well as the LoRA model, the training component has failed to justify itself.

### What makes Meta essential?

Meta supplies two different capabilities in one system: Muse Spark for teacher-side exploration, and the Apache-2.0-licensed [Muse Glimmer 30B](https://dev.meta.ai/models/muse-glimmer?utm_source=chatgpt.com) for trainable local deployment.

The algorithm would not fundamentally break if both models were replaced by capable alternatives. So this is Meta-native engineering, not mathematical dependence on Meta's exact weights.

That distinction matters for the 25% tooling score. Judges should see actual improvements produced by adapting Meta weights, not simply a Meta API call powering an otherwise generic pipeline.

### Day-one kill test — October 29

Choose a real, stateful, relatively unfamiliar tool that can run safely in an isolated environment. Your own hivey CLI could be suitable, provided the test uses legitimate workflows rather than artificial traps.

Pre-register 40–50 meaningful task scenarios covering dependencies, configuration, errors and recovery. Keep the test tasks hidden from all training-data generation.

Proposed acceptance thresholds

| Untuned Glimmer with documentation | Preferably 60% success or less |
| --- | --- |
| Frontier teacher with verification | Preferably at least 75% success |
| Evidence of training headroom | Early QLoRA improvement on separate development tasks |
| Technical feasibility | Working Glimmer load, training step and adapter reload on one H100 |

These are decision thresholds I propose, not results. They are designed to establish that the tool is genuinely difficult yet teachable.

Kill Forge if the untuned model, given fair documentation and a simple reusable skills file, already performs near the teacher's level; if meaningful improvement requires fabricated tasks; or if the training/inference pipeline cannot be demonstrated reliably.

For the full result, target an improvement of at least 15–20 percentage points on unseen tasks over the strongest cheap local baseline, with no weaker safety or task-validity checks. A 50-task evaluation is still small, so show paired task outcomes and uncertainty rather than claiming broad generalization.

## 3. Gatebreaker: detailed assessment

### Problem strength: exceptionally high

Gatebreaker's underlying problem is better established than Forge's.

[METR's 2025 investigation](https://metr.org/blog/2025-06-05-recent-reward-hacking/?utm_source=chatgpt.com) documented models exploiting evaluation environments instead of completing the intended work. [Anthropic's November 2025 research](https://www.anthropic.com/research/emergent-misalignment-reward-hacking?utm_source=chatgpt.com) further demonstrated that training models to exploit reward loopholes can produce undesirable behavior beyond the original task.

There is also a less obvious failure: a verifier can reject legitimate solutions because it assumes the wrong format, tool sequence or implementation strategy.

[VerifierBench, October 19, 2026](https://arxiv.org/abs/2610.28679?utm_source=chatgpt.com), evaluates generated verifiers against 4,993 hidden cases across 222 tasks. Its findings show that some generated verifiers reject valid solutions while appearing strict and reliable.

That is a valuable enterprise problem because both false acceptance and false rejection can corrupt evaluations and training signals.

### Why I would not choose it

The [June 2026 Hacker-Fixer paper](https://arxiv.org/abs/2606.08960?utm_source=chatgpt.com) is almost the specification for Gatebreaker:

1. An attacker seeks an invalid solution that passes.
2. A fixer modifies the verifier.
3. A solver confirms legitimate work remains accepted.
4. The loop repeats as new weaknesses appear.
5. The repaired verifiers are evaluated against held-out attacks.

The researchers reported eliminating successful attacks on a held-out KernelBench exploit corpus in one experiment. They also released their environments, trajectories, patched verifiers and implementation.

Adding Glimmer RL as the attacker would be an engineering change, but not enough by itself to claim a new problem-solving paradigm.

A frontier model with access to the verifier and a legitimate-solver agent already implements the concept very closely.

### Feasibility and day-one test

Gatebreaker would be fairly easy to make impressive on video because an invalid submission that passes a test, followed by a repaired test that rejects it, is visually compelling.

But your day-one test would have to show something beyond the published baseline: for example, an RL-trained Glimmer attacker finding new held-out exploit classes that a strong prompt-only attacker systematically misses, at comparable attacker compute.

Test against the authors' released Hacker-Fixer approach. If Glimmer RL merely reproduces known exploits, stop.

Commercial potential: model labs, agent-evaluation providers, and organizations training agents with executable rewards. The product could be a continuous verifier-hardening service, but those customers will compare it to available research implementations and existing evaluation platforms.

My decision: do not spend this hackathon on Gatebreaker unless you already have a sharply different technique and controlled evidence that it beats Hacker-Fixer.

## 4. Team Doctor: detailed assessment

### Problem strength: very high

Team Doctor's biggest advantage is that the problem is observable in ordinary multi-agent workflows.

The published evidence is substantial:

- The [MIT/Google-backed collaboration study](https://www.media.mit.edu/projects/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/overview/?utm_source=chatgpt.com) evaluates 260 configurations and finds that capable single agents can outperform coordinated teams. Its within-domain architecture predictor selects the best architecture in 87% of held-out configurations.
- [Worse Together, September 2026](https://arxiv.org/abs/2610.00583?utm_source=chatgpt.com) reports that multi-agent teams coordinating over shared resources underperform a single coordinator across the tested environments, with stalling, interference and other coordination failures.
- [Stanford's 2026 token study](https://arxiv.org/abs/2604.22750?utm_source=chatgpt.com) reports that agent token consumption varies dramatically, with more spending often failing to improve accuracy.

This supports both the reliability problem and the economic problem.

Your own preliminary parallel-edit experiments provide an additional reason to test this candidate. The important limitation is that they establish the cost of bad parallelization, not yet the value of automatically detecting and repairing it.

### Closest prior art

| Existing solution | Overlap with Team Doctor |
| --- | --- |
| AgentDropout, ACL 2025 | Dynamically eliminates redundant agents and communication |
| Magentic-One | Orchestrator tracks progress and replans when work stalls |
| Autonomous Topology Mutation, 2026 | Detects runtime bottlenecks and restructures agent topology with state-transfer safeguards |
| Difficulty-Aware Topology Selection, Sep 2026 | Selects a cost-aware topology for a task before execution |
| Runtime Agent Coordination, Oct 2026 | Selects collaborators dynamically during AI-scientist workflows |
| CATS, Oct 21 2026 | Uses execution traces to identify useful agents and prune teams |
| LangSmith Engine, May 2026 | Finds recurring agent failures in traces and proposes evaluators and fixes |

This is a crowded area.

However, there is a defensible distinction: Team Doctor should optimize the outcome of a task already in progress, not just select an architecture beforehand or provide a diagnosis afterward.

CATS optimizes a team for deployment; DATS selects before execution; AgentDropout eliminates contributions during collaboration; Autonomous Topology Mutation restructures overloaded agents. None of these establishes that a general-purpose live controller can reliably rescue failing coding swarms at a lower cost per successful task.

That is the remaining hypothesis worth testing.

### What a differentiated Team Doctor would do

Consider a swarm of four agents working on a coding task.

After several tool calls, Team Doctor detects that two agents are changing overlapping files, a third is waiting for obsolete work, and the coordinator's task graph is no longer accurate.

It can then intervene:

- Stop unnecessary or conflicting work.
- Preserve verified artifacts and already-completed changes.
- Reassign the remaining dependent work to one agent.
- Continue from a controlled checkpoint.
- Measure whether the final result improves enough to cover the intervention cost.

The critical detail is preserving progress safely. Simply killing three agents and telling the fourth to start again is not a convincing live-restructuring breakthrough.

### Would a strong model plus verifier solve it?

A strong orchestrator and a verifier can already recognize failing tests, revise a plan, and serialize dependent tasks. Magentic-One explicitly includes progress tracking and replanning. [Microsoft's documentation](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html?utm_source=chatgpt.com).

Your differentiator must therefore be when and whether an intervention pays off.

A controller that always reduces four agents to one will look good on tasks that should never have been parallelized. It is not evidence of intelligence in team composition.

You need a mixed workload containing tasks where parallelization helps, tasks where it hurts, and tasks whose dependencies become apparent only after execution begins.

### Day-one kill test

Run the same genuine tasks with three policies:

| Policy | Purpose |
| --- | --- |
| Strong single agent | Baseline that avoids coordination entirely |
| Static coordinator + verifier | Tests whether ordinary replanning already fixes the problem |
| Team Doctor with live control | Tests the extra value of intervention |

Include tasks that benefit from independent parallel work, not only shared-file conflicts.

Require cost-normalized outcomes. My suggested target is at least a 20–25% reduction in dollars per successful completed task, without reducing success, compared with the strongest ordinary orchestration baseline. Also report actual wall-clock time, because cheaper does not necessarily mean faster.

Kill Team Doctor if a static dependency-aware planner or a strong coordinator-plus-verifier matches its performance, or if the doctor cannot safely resume meaningful work after restructuring.

### The Meta issue

Team Doctor could use Muse Spark or Wonder to diagnose traces, and a locally trained Glimmer controller to predict when to intervene. That would be technically meaningful.

But models are not fundamental to the intervention mechanism: much of the detection could be achieved using deterministic telemetry, dependency graphs and scheduler rules.

It is consequently harder to demonstrate that Meta's AI models created the new capability, rather than merely powered a useful operations product.

## 5. Scoring against the actual hackathon priorities

The official [Meta hackathon page](https://dev.meta.ai/events/global-hackathon?utm_source=chatgpt.com) emphasizes creativity, technical ambition and a working implementation in the Indie track. Its Push the Frontier theme explicitly welcomes giving a machine a new capability. That favors a demonstrable capability change rather than another agent-management dashboard.

### Weighted scoring

| Criterion | Weight | Forge | Team Doctor | Gatebreaker |
| --- | --- | --- | --- | --- |
| Impact | 30 | 23 | 25 | 24 |
| Meta tooling | 25 | 22 | 16 | 17 |
| Technical execution | 20 | 15 | 15 | 12 |
| Demo potential | 25 | 21 | 20 | 20 |
| Total | 100 | 81 | 76 | 73 |

Predicted hackathon scores by criterionSubjective estimates assuming successful execution; not observed judging results.

Impact /30Meta tooling /25Technical /20Demo /25Forge wins mostly through its Meta-tooling score, not through stronger evidence of a new scientific algorithm.

If the judges emphasize originality of the underlying method more than integrated execution, its advantage narrows considerably. Conversely, a real, verified improvement from a tuned Meta open-weight model would strengthen both the technical and demonstration scores.

### Which Meta models should actually be used?

| Tool | Forge role | Decision |
| --- | --- | --- |
| Muse Spark 1.3 | Explore tool, generate and execute training tasks | Core |
| Muse Glimmer 30B | Trainable local specialist | Core |
| Muse Code | Build, test and integrate the system | Core development tool |
| Muse Wonder | Optional stronger teacher or difficult-case adjudicator | Use selectively |
| Muse Spark Open | Possible larger-model comparison | Not necessary |
| SAM 3.1 | Image/video segmentation | Not relevant |

Meta's [model documentation](https://dev.meta.ai/docs/models?project_id=3419047751588389&team_id=2431753403985778&utm_source=chatgpt.com) establishes the available model types. Muse Spark Open is an 816B-parameter mixture-of-experts model, making it an unnecessarily ambitious local training target for this six-day project.

Muse Code also supports headless execution, hooks, skills and multi-agent workflows, which gives you a useful way to develop and automate the evaluation pipeline. [Muse Code documentation](https://dev.meta.ai/docs/muse-code/extending?project_id=29035399122726954&team_id=1741581793652561&utm_source=chatgpt.com).

Do not add SAM solely to show another Meta model. Its role would be artificial for a CLI-focused project.

## 6. Can Forge fit the $65 API budget?

Yes, for a bounded SFT-focused experiment. The real constraint is iteration time and reliable task verification.

Meta's published token prices are:

| Model | Input / 1M tokens | Output / 1M tokens |
| --- | --- | --- |
| Muse Spark 1.3 | $1.25 | $4.25 |
| Muse Spark 1.3 Contributor | $0.10 | $0.20 |
| Muse Wonder | $4.00 | $20.00 |

Source: [Meta pricing](https://dev.meta.ai/docs/pricing-rate-limits?project_id=3419047751588389&team_id=2431753403985778&utm_source=chatgpt.com).

Contributor mode permits Meta to use submitted content for training. Do not send confidential internal tool schemas, credentials or proprietary customer data using that mode without appropriate permission.

### Suggested API allocation

Teacher exploration + verified data

$25

Baseline and holdout evaluations

$20

Debugging and contingency

$15

Final live demonstration

$5

Total API budget
$65

These are spending caps, not measured costs. Track actual input, cached-input, output and reasoning tokens; reject runaway generations rather than assuming every synthetic task is cheap.

For GPU training, [Modal](https://modal.com/pricing?utm_source=chatgpt.com) lists the H100 SXM5 at approximately $3.95 per GPU-hour. Three hours would therefore cost about $11.85 in GPU rental before ancillary charges. Treat that separately from your $65 API allowance.

There is also a potentially useful fallback: [Fireworks' current pricing page](https://fireworks.ai/pricing?utm_source=chatgpt.com) advertises free Muse Glimmer 30B supervised fine-tuning through November 30, 2026. That could simplify an emergency training run, subject to data privacy and model-support checks.

Avoid GRPO in the initial build. Meta's training guidance favors SFT when correct demonstrations exist, and RL when the model already attempts tasks but remains unreliable despite objectively checkable success. [Meta post-training](https://dev.meta.ai/docs/muse-glimmer/post-training?utm_source=chatgpt.com).

GRPO becomes a stretch goal only after the complete SFT pipeline, baselines and unseen-task evaluation work.

## 7. Commercial potential: who actually pays?

None of the three has verified customer demand from this research. The commercial scores are hypotheses about who might pay and what existing spend they could replace.

### Market comparison

| Candidate | Most plausible buyer | Sellability /5 | Business model to test |
| --- | --- | --- | --- |
| Forge | AI developers and organizations with specialized private tooling | 3.8 | Paid tool-specialization pilot, adapter delivery and validation |
| Team Doctor | High-volume agent operators and engineering teams | 4.2 | Recurring performance optimization tied to measured savings |
| Gatebreaker | Evaluation providers, model labs, RL training teams | 3.3 | Continuous verifier audit or fixed assessment |

Some published adjacent prices provide useful anchors:

| Existing provider | Public price | What it establishes |
| --- | --- | --- |
| LangSmith | Plus $39/seat/month, plus usage | Teams pay for agent evaluation, deployment and improvement tooling |
| Langfuse | Core $29/month; Pro $199/month | Agent observability is an established software category |
| Braintrust | Pro $249/month | Teams buy hosted tracing and evaluation infrastructure |
| Fireworks | Listed managed LoRA SFT at $3/1M training tokens for 16.1B–80B models, with model-specific promotions | Basic fine-tuning compute is becoming a low-cost commodity |

These prices do not establish that customers would pay the same amount for Forge or Team Doctor.

### Forge's most defensible product

Sell the outcome, not training tokens:

> We turn your private tools and workflows into a reliable specialist agent, then test its performance on tasks it has never seen.

A first paid pilot could be offered at a proposed $2,000–$5,000 per integration, including task discovery, adapter training, independent validation and deployment guidance. This is a pricing experiment, not an observed market rate.

The measurable customer value would be:

Net savings=N(Cbaseline−Cspecialist)−Ctraining−Chosting\text{Net savings} =
N(C_{\text{baseline}}-C_{\text{specialist}})
-C_{\text{training}}-C_{\text{hosting}}Net savings=N(Cbaseline​−Cspecialist​)−Ctraining​−Chosting​where NNN is the expected number of future tasks.

But cost alone is not enough: compare cost per successfully completed task, and include time spent maintaining the adapter as the underlying tool changes.

The local deployment story is commercially valuable only where privacy, offline operation or sufficiently high usage makes it worthwhile. A mostly idle dedicated GPU can cost more than occasional hosted API calls.

### Why Team Doctor might become the better business later

Team Doctor has a clearer recurring financial promise: reduce wasted agent execution without degrading output quality.

However, [LangSmith Engine](https://www.langchain.com/blog/how-we-built-langsmith-engine-our-agent-for-improving-agents?utm_source=chatgpt.com) already analyzes traces, finds repeated problems and proposes fixes. A Team Doctor product must deliver actual runtime intervention and independently measured savings to justify charging separately.

If Forge succeeds as a hackathon project, I would still investigate Team Doctor as part of your longer-term agent-optimization business.

## 8. Forge's three-minute demonstration

The demonstration must be about a real capability change, not a diagram of agents communicating.

Proposed video timeline

180 seconds

- 0:00–0:20 · The problem

Show an unfamiliar, real CLI workflow. An untuned local model struggles to complete a legitimate task despite having tool documentation.
- 0:20–0:55 · Discovery

Feed the tool to Forge. Muse Spark explores commands, discovers state transitions, proposes tasks and validates actual results.
- 0:55–1:55 · Learning

Show accepted training examples, verifier results and real training logs. Explain that an adapter was trained beforehand using the displayed pipeline; do not pretend training completes instantly.
- 1:55–2:35 · New capability

Run untuned and tuned Glimmer side by side on a previously unseen task with identical tools. Demonstrate the tuned specialist succeeding with fewer corrections.
- 2:35–3:00 · Evidence and impact

Display actual holdout success rates, time, tool calls and inference cost. End by showing the tuned model working without the teacher.

I would make the video show one full unseen-task execution without editing or hidden interventions. The rest can be concise screen recordings and accelerated training footage, clearly labeled as such.

Do not show improvement numbers until they have actually been measured.

## 9. Six-day execution plan

The official deadline is November 4, 2026, at 9:00 p.m. Eastern Time, corresponding to November 5 at 03:00 CET in mainland Spain. [Meta event schedule](https://dev.meta.ai/events/global-hackathon?utm_source=chatgpt.com).

| Date | Main deliverable | Exit criterion |
| --- | --- | --- |
| Oct 29 | Tool selected; task benchmark; baseline; single-H100 training smoke test | Genuine learning gap identified |
| Oct 30 | Tool explorer, task generator and executable verification pipeline | Valid tasks run reproducibly |
| Oct 31 | Verified demonstrations and first Glimmer adapter | Tuned model can be reloaded and executed |
| Nov 1 | Proper holdout experiment against four baselines | Improvement is measured, not anecdotal |
| Nov 2 | Improve weakest tool-operation behaviors; audit data leakage and false verification | Result survives control tests |
| Nov 3 | Final interface, reproducibility package and demo rehearsal | End-to-end path works without manual rescue |
| Nov 4 | Record video, publish results and submit | Complete submission before deadline |

### Scope control

Do not attempt a general-purpose tool-learning platform that works with every API, GUI, browser, CLI and MCP server.

For the hackathon, support one real tool family extremely well, while keeping the architecture modular. Prioritize one reliable data pipeline, one tuned model, one independent test suite and one compelling result.

The scope of the deliverable should be:

- A command to register and explore one supported tool.
- Automatic generation and filtering of verifiable tasks.
- A functioning Glimmer QLoRA training workflow.
- A locally runnable specialist.
- An evaluation report with complete baselines.

If the training result is weak, improving verification and data quality takes priority over building a polished dashboard.

## 10. What would change my recommendation?

There are two scenarios in which I would switch to Team Doctor.

First: Forge's baseline agent already operates the selected tool reliably with a short skills file. Then fine-tuning is adding complexity, not capability.

Second: the task generator produces mostly synthetic-looking, repetitive examples and cannot demonstrate success on real unseen workflows. That would reproduce the weakness of research-only agent experiments.

I would not switch merely because the first LoRA run performs poorly. A weak initial run could reflect incorrect formatting, limited data or an unsuitable training recipe. But if there is no evidence of a learnable gap, further training is unjustified.

The runner-up, Team Doctor, becomes attractive specifically if you can reproduce nontrivial coordination failures from real swarms and prove that live intervention beats an already competent static orchestrator, rather than only beating a deliberately poor parallel setup.

## Final commitment

## Build Forge — the local tool apprentice.

Positioning: A system that turns verified experience with an unfamiliar tool into a reusable capability in a private Meta model.

What makes it a strong hackathon entry: It shows a real before/after change in model competence, uses Meta's trainable open weights substantially, and provides a clear testable outcome.

Main risk: The LoRA specialist does not outperform simply supplying documentation, reusable skills and a verifier to an untuned agent.

Decision rule for October 29: Establish a genuine performance gap and verify that Glimmer can be trained and evaluated reliably. If those two conditions fail, switch to Team Doctor rather than polishing a weak demonstration.

My confidence is moderate, not high: Forge is the strongest option after investigating these competitors, but the most important empirical result has not yet been obtained. The day-one baseline experiment is the single most valuable thing you can do before committing the remaining build time.

## Sources

Primary research and official documentation consulted, ordered by subject. All links below were opened during this assessment.

Meta and implementation

1. [Meta Global AI Developer Hackathon — official event page](https://dev.meta.ai/events/global-hackathon?utm_source=chatgpt.com)
2. [Meta Model API — model documentation](https://dev.meta.ai/docs/models?project_id=3419047751588389&team_id=2431753403985778&utm_source=chatgpt.com)
3. [Meta — Muse Glimmer model](https://dev.meta.ai/models/muse-glimmer?utm_source=chatgpt.com)
4. [Meta — Muse Glimmer post-training guide](https://dev.meta.ai/docs/muse-glimmer/post-training?utm_source=chatgpt.com)
5. [Meta — API pricing](https://dev.meta.ai/docs/pricing-rate-limits?project_id=3419047751588389&team_id=2431753403985778&utm_source=chatgpt.com)
6. [Meta — Muse Code extending and automating](https://dev.meta.ai/docs/muse-code/extending?project_id=29035399122726954&team_id=1741581793652561&utm_source=chatgpt.com)
7. [Modal — GPU pricing](https://modal.com/pricing?utm_source=chatgpt.com)

Forge and tool-learning research

1. [NVIDIA — Training an agent for command-line tasks, 2026](https://developer.nvidia.com/blog/how-to-train-an-ai-agent-for-command-line-tasks-with-synthetic-data-and-reinforcement-learning/?utm_source=chatgpt.com)
2. [ToolACE — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/663865ea167425c6c562cb0b6bcf76c7-Abstract-Conference.html?utm_source=chatgpt.com)
3. [Tool-R0 — Self-Evolving Tool Learning, 2026](https://arxiv.org/abs/2602.21320?utm_source=chatgpt.com)
4. [ToolGym — Open-world Tool Environment, 2026](https://arxiv.org/abs/2601.06328?utm_source=chatgpt.com)
5. [AutoPlay — Scaling Synthetic Task Generation via Exploration](https://machinelearning.apple.com/research/scaling-synthetic-task?utm_source=chatgpt.com)
6. [ScaleEnv — ICML 2026](https://proceedings.mlr.press/v306/tu26a.html?utm_source=chatgpt.com)
7. [SPADE — Adaptive Synthetic Executable Environments, 2026](https://arxiv.org/abs/2608.19197?utm_source=chatgpt.com)
8. [ToolForge — EMNLP 2026](https://aclanthology.org/2026.emnlp-main.1250/?utm_source=chatgpt.com)

Gatebreaker, verifiers and reward hacking

1. [Hardening Agent Benchmarks with Adversarial Hacker-Fixer Loops, 2026](https://arxiv.org/abs/2606.08960?utm_source=chatgpt.com)
2. [VerifierBench — Benchmarking Executable Verifiers, October 2026](https://arxiv.org/abs/2610.28679?utm_source=chatgpt.com)
3. [METR — Recent Frontier Models Are Reward Hacking, 2025](https://metr.org/blog/2025-06-05-recent-reward-hacking/?utm_source=chatgpt.com)
4. [Anthropic — Natural Emergent Misalignment from Reward Hacking, 2025](https://www.anthropic.com/research/emergent-misalignment-reward-hacking?utm_source=chatgpt.com)

Multi-agent coordination and Team Doctor

1. [Capable Language Models Can Outgrow the Benefits of Collaboration — MIT Media Lab overview, 2026](https://www.media.mit.edu/projects/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/overview/?utm_source=chatgpt.com)
2. [Worse Together — Multi-Agent Coordination Failures, 2026](https://arxiv.org/abs/2610.00583?utm_source=chatgpt.com)
3. [How Do AI Agents Spend Your Money? — Token Consumption Study, 2026](https://arxiv.org/abs/2604.22750?utm_source=chatgpt.com)
4. [AgentDropout — ACL 2025](https://aclanthology.org/2025.acl-long.1170/?utm_source=chatgpt.com)
5. [Autonomous Topology Mutation, 2026](https://arxiv.org/abs/2607.20488?utm_source=chatgpt.com)
6. [Difficulty-Aware Topology Selection, 2026](https://arxiv.org/abs/2609.13890?utm_source=chatgpt.com)
7. [Can AI Scientists Coordinate at Runtime?, 2026](https://arxiv.org/abs/2610.00980?utm_source=chatgpt.com)
8. [Contrastive Attribution Topology Search, October 2026](https://arxiv.org/abs/2610.29292?utm_source=chatgpt.com)
9. [Microsoft AutoGen — Magentic-One](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html?utm_source=chatgpt.com)
10. [LangSmith Engine — How We Built an Agent for Improving Agents, 2026](https://www.langchain.com/blog/how-we-built-langsmith-engine-our-agent-for-improving-agents?utm_source=chatgpt.com)

Commercial pricing evidence

1. [LangSmith pricing](https://www.langchain.com/pricing?utm_source=chatgpt.com)
2. [Langfuse pricing](https://langfuse.com/pricing?utm_source=chatgpt.com)
3. [Braintrust pricing](https://www.braintrust.dev/pricing?utm_source=chatgpt.com)
4. [Fireworks AI — training and inference pricing](https://fireworks.ai/pricing?utm_source=chatgpt.com)
