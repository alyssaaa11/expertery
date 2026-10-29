<!-- Raw source: subagent research report (Claude Sonnet, web + alphaXiv), 2026-10-29, for the training/verifier learning guide. Unedited. -->

# Forge learning-guide research: fine-tuning a 30B student on referee-verified CadQuery

Every source below is one I opened this session, either through alphaXiv or a page fetch. I could only read abstracts or summaries for most papers, and I say so where a number is missing. Today is 2026-10-29. The 2026 arXiv ids are as alphaXiv returned them.

## 1. Rejection-sampling fine-tuning, expert iteration, STaR, ReST-EM, RAFT

**What they are.** All of them follow one loop: sample, keep what a verifier passes, fine-tune on the kept samples, optionally repeat.

- **STaR** (Zelikman et al. 2022, arXiv 2203.14465) keeps rationales that reach the right answer. For failures it gives the model the answer and asks it to write a rationale ("rationalization"). It beat answer-only fine-tuning, and on CommonsenseQA it matched a model about 30x larger.
- **ReST-EM** (Singh et al., DeepMind, TMLR 2024, arXiv 2312.06585) used PaLM-2 on MATH and APPS code.
  - It sampled 32 solutions per problem for MATH and 64 for APPS.
  - It capped the number of kept solutions per problem so easy problems did not dominate.
  - Each round it re-fine-tuned from the base model, not the previous round, to limit drift.
  - Its note on STaR: "rationalization leads to substantial increase in false positive solutions". These are right answers with wrong reasoning.
  - More than a couple of iterations gave diminishing returns, which the authors read as overfitting to a small set of training problems.
  - Gains were largest on medium and hard problems. Model-generated data beat human data.
- **RAFT** (Dong et al. 2023, arXiv 2304.06767) is "rank by reward, keep the top, fine-tune". It is the plain version of rejection sampling.
- **Expert iteration** (Havrilla et al. 2024, arXiv 2403.04642, Llama-2 7B/13B on GSM8K and SVAMP) beat PPO.
  - It needed about 10^6 samples to converge.
  - Starting from an SFT checkpoint was much better than starting from the raw base model.
  - Exploration was the bottleneck: the model rarely found solutions far from what SFT already produced.
- **Minimalist RAFT/GRPO study** (Xiong et al. 2025, arXiv 2504.11343, Qwen2.5-Math-7B). Plain RAFT reached 52.3% average, iterative DPO 48.8%, PPO 52.5%, and RAFT++ (RAFT plus importance sampling and clipping) 56.1% against GRPO's 56.3%.
  - Positive-only training converges faster early but its entropy collapses. GRPO overtakes it later.
  - GRPO's real advantage came from implicitly dropping prompts where every sample was wrong. Reward normalization mattered little.

**Do several rounds help?** Mildly, then they plateau.

- ReST-EM saw diminishing returns after about 2 iterations.
- In a controlled GRPO-versus-RFT comparison (arXiv 2610.25812, Qwen3-4B-Base with LoRA, one synthetic task, 3 seeds), GRPO beat RFT by 10.9 points on curated prompts. An iterated RFT arm that resampled from the current policy recovered only about 30% of that gap. Mixed-difficulty prompts helped RFT by 3.7 points, and curation did not (-2.7).
- A 2026 study of multi-round self-improvement (arXiv 2603.21558, Qwen3-4B-Thinking on GSM8K) found that filtering on final answers alone plateaus or collapses over rounds. Adding step-level checks lifted accuracy from 80.5% to 91.0% over 5 rounds. The checks rejected about 34% of solutions that had correct final answers.

**What this means for Forge.** Sample many programs per job from the teacher, not one or two. Cap the kept programs per job and keep the harder jobs. Run one student self-improvement round at most, and always retrain from the base model. "Lucky" passes are a real risk, so also check that the referee's tolerances on bounding box, volume and hole positions are tight enough that a program cannot pass by accident.

## 2. Teacher distillation filtered by a verifier: quantity, diversity, difficulty, correctness

- **LIMA** (2305.11206, 2023): 1,000 curated examples on a 65B model gave answers equal to or preferred over GPT-4's in 43% of comparisons. Its thesis is that nearly all knowledge comes from pretraining.
- **LIMO** (2502.03387, 2025): about 1% of the usual training data reached 63.3% on AIME24 and 95.6% on MATH500. I could not confirm the example count from the abstract.
- **s1** (2501.19393, 2025): 1,000 examples selected for difficulty, diversity and quality, validated by ablations.
- **OpenThoughts** (2506.04178, 2025): ran over 1,000 controlled data-pipeline experiments and scaled to 1.2M examples. The abstract gives no recipe details, so I cannot report its question-versus-answer-count findings.
- **Diversity of problems versus repeated solutions** (2609.33559, "Fine Until Fine-Tuned", Qwen3.5-9B-Base, 2026):
  - A model drilled on a few hundred problems about 8 times each looked as good as one trained on many problems once (both about 95% held-out).
  - After one later instruction-tuning pass the drilled model fell to 86.0%, and harsher later stages dropped it to 59.3% or lower.
  - New solutions to the same problems did not hurt. Replaying 6.25% of the original data also protected it.
  - Conclusion: repeating identical text is the problem, not having few problems.
- **Correctness may matter less than structure.** "LLMs can easily learn to reason from demonstrations" (2502.07374) trained Qwen2.5-32B with LoRA on 17k long-CoT samples. Wrong-answer samples cost only 3.2% accuracy. Shuffling or deleting steps hurt a lot. This is for math CoT, and I would not assume it holds for exact-geometry code.
- **Teacher gap.** "Small models struggle to learn from strong reasoners" (2502.12143) says models of 3B or less do not benefit from long CoT or large-teacher traces. Mixing long and short traces, or large-teacher and small-teacher traces, helped. A 30B model is well above that size, but it is a reason not to feed it very long traces.
- **Difficulty.** "Learning from Less" (Bauer et al., MLSys 2026, arXiv 2604.18381, RLVR) found mixed-difficulty data gave up to 5x the sample efficiency of easy-only data. It also found a minimum of about 100 to 200 examples for stable optimization. That is RL, not SFT.

**What this means for Forge.** A few hundred verified programs is enough to teach format and style, so quantity is not the main lever. Diversity of jobs is. Aim for many different jobs with 1 to 3 distinct passing programs each, not one job with 20 near-duplicates. Deduplicate near-identical programs by normalized code and by (job type, parameters). Include medium and hard jobs. Keep epochs low (about 2 to 3), because repeated identical text can make the model fragile to later training.

## 3. Reasoning in the targets, or only the final program; self-correction

- The evidence is mostly math. Structure and consistency of the reasoning matter more than the exactness of each step (2502.07374). Small models learn better from shorter reasoning (2502.12143). I did not find a source specific to CAD or code.
- Self-correction from offline traces is hard. SCoRe (Kumar et al., DeepMind, 2409.12917, 2024) says SFT on correction traces fails for two reasons. The mistakes in the traces do not match the mistakes the model actually makes, and SFT collapses to one narrow correction style. Online multi-turn RL fixed this: +15.6% on MATH and +9.1% on HumanEval for the Gemini models.
- Step Rejection Fine-Tuning (2605.10674, JetBrains, 2026, SWE-bench agents) keeps failed steps in the context but masks their loss. The model sees the error and the recovery but is not trained to reproduce the error. Plain RFT gave +2.4%, SRFT +3.7%, reaching 32.2%.
- FailForge (2608.08570, 2026) turned failed jobs into successes by giving the agent a hint distilled from the failure. It recovered more than 26% of failed instances, and removing the hint at training time gave +6.6 points over an RFT baseline on SWE-bench Verified with Qwen3.5-4B.

**What this means for Forge.** Train on a short plan or comment plus the CadQuery program, in the format the student will see at test time, and keep it concise. Failed attempts followed by a fix are worth trying as a second data type: show the error message in the prompt, mask the loss on the broken program, and train on the corrected one. Test whether it helps on the dev set before relying on it. The FailForge idea fits Forge well: when the teacher fails a job, give it a hint from the referee's report, accept the pass, and train without the hint.

## 4. Using failed attempts: DPO, KTO, step-level preference

- Setlur et al. (2406.14532, 2024):
  - Positive-only synthetic data can show flat or inverse scaling because of spurious correlations.
  - Careful negatives (per-step credit) gave gains equivalent to 8x more positive data.
  - The negatives must be built so that the training recovers the value of each intermediate step.
- Iterative Reasoning Preference Optimization (Pang et al., 2404.19733, 2024): DPO plus an NLL term, which they call "crucial". Llama-2-70B-Chat went from 55.6% to 81.6% on GSM8K, and to 88.7% with majority voting over 32 samples.
- Minimalist study (2504.11343): positive-only is close to negatives-using methods. The harmful negatives were whole prompts where every sample failed.
- Preference-pair studies:
  - 2604.08723 found the gap between the capability of the chosen-trace generator and the rejected-trace generator matters most for out-of-domain gains.
  - 2609.38987 found that rejects from a smaller frozen model trained stronger students than self-generated rejects, and that low-likelihood rejects transferred better. It covers code and math, 7B to 72B students.
- RIFT (2601.09253) is a method for reusing negatives, but I only saw its snippet.
- I found no source that directly compares DPO/KTO against SFT on a few hundred examples at this scale. This is the biggest gap in the evidence.

**What this means for Forge.** Do SFT on passes first. If you add preference training, build pairs as (teacher pass, failure) from the same job, with the failure ideally from a weaker model, and keep an NLL term on the chosen program. Do not include jobs where everything failed, since they carry no good chosen answer. Treat it as an experiment checked on the dev set, not an expected win.

## 5. Beyond SFT: RLVR with LoRA on one GPU

- **Algorithms.**
  - GRPO: group-normalized advantages.
  - Dr. GRPO (2503.20783): removes a length bias that inflates wrong answers. Its minimalist recipe on a 7B base reached 43.3% on AIME 2024.
  - DAPO (2503.14476): Qwen2.5-32B reached 50 on AIME24, with code on verl. The four techniques include clip-higher and dynamic sampling, which drops groups that are all right or all wrong. I could not read the full list from the abstract.
  - A 2026 identity paper (2607.00152) says GRPO, Dr. GRPO and DAPO adjust one number, the group standard deviation. I only saw its snippet.
- **Libraries.**
  - TRL GRPOTrainer (docs https://huggingface.co/docs/trl/main/en/grpo_trainer): takes `peft_config`; vLLM colocate mode shares the GPU (default `vllm_gpu_memory_utilization=0.3`); `num_generations` default 8; `loss_type` supports `dapo` and `dr_grpo`; `beta=0.0` by default, with `epsilon_high=0.28` recommended; learning rate 1e-6 shown for full fine-tuning (use roughly 10x for LoRA per Section 6).
  - Unsloth RL guide (https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide): QLoRA 4-bit GRPO needs about as many GB of VRAM as the model has billions of parameters. 16-bit LoRA needs at least 4x more. It lists Qwen3-30B-A3B 16-bit LoRA at 63 GB (this figure is for fine-tuning in general, not GRPO).
  - OpenPipe ART (https://github.com/OpenPipe/ART): GRPO with LoRA adapters and vLLM rollouts. Its email-agent run on Qwen 14B used one H100 and cost about $80 in under a day. OpenPipe's launch post says runs often cost $15 to $200, and that RL often costs more than SFT.
  - verl and OpenRLHF are the heavier multi-GPU options. I did not open their docs.
- **SFT first, then RL.** Expert iteration found SFT initialization much better than a raw base model (2403.04642). DeepSeek-R1 (2501.12948) shows reasoning emerging from RL, and distillation transferring it to smaller models. I could not confirm the cold-start stage details from the abstract.
- **Does RL beat rejection sampling?** On one narrow synthetic task, yes: by 8 to 11 points (2610.25812). That finding is limited to one model family, one task and 3 seeds.
- **Forgetting.** RL's Razor (2509.04259, ICLR 2026) found on-policy RL forgets less than SFT at the same new-task performance.
- **Feasibility.** My arithmetic from Modal's H100 price of about $3.95/hr (https://www.thundercompute.com/blog/nvidia-h100-pricing): $10 buys about 2.5 GPU-hours and $20 about 5. The OpenPipe $80 run was for a 14B dense model with a day of training. A 30B model with LoRA plus vLLM rollouts on a single 80 GB card is tight on memory, and 5 hours allows only a few dozen to a few hundred RL steps. If it is a mixture-of-experts model, Unsloth's MoE kernels (https://unsloth.ai/docs/basics/faster-moe) may help, but I found no GRPO figures for it. I judge full RL on a 30B model at this budget as unrealistic. This is a judgment, not a measured result.

**What this means for Forge.** Do SFT on verified teacher programs first. If any budget remains, try a short GRPO run, or a smaller student to test the reward design. Use the referee as the reward and give partial credit (builds, bounding box, volume, holes). Filter jobs that are all-pass or all-fail, which is what GRPO's gains mostly come from.

## 6. LoRA specifics and forgetting

"LoRA Without Regret" (Schulman et al., Thinking Machines, 2025, https://thinkingmachines.ai/blog/lora/):

- Apply LoRA to all layers, especially MLP and MoE layers. Attention-only LoRA learned more slowly even at matched parameter counts.
- The best LoRA learning rate is about 10x the full fine-tuning rate (fitted 9.8), and about 15x for runs under roughly 100 steps. It changes by less than 2x between rank 4 and rank 512.
- Rank 1 matched full fine-tuning in RL, because RL gives roughly 1 bit per episode. Supervised data with many tokens needs more rank, and capacity limits show up on large datasets.
- LoRA tolerates large batches less well than full fine-tuning, and that gap does not depend on rank.
- LoRA uses a bit over 2/3 of the FLOPs per pass.
- The post does not measure forgetting.

"LoRA Learns Less and Forgets Less" (Biderman et al., 2405.09673, 2024) found that LoRA underperforms full fine-tuning on code and math, and degrades less outside the target domain. It reduced forgetting more than weight decay or dropout, and full fine-tuning learned perturbations of rank 10 to 100 times higher than typical LoRA ranks.

TRL says to use about 1e-4 for adapters (https://huggingface.co/docs/trl/main/en/sft_trainer).

**Measuring forgetting.** Hold out a small general suite (some general coding, a few instruction-following and chat prompts) and run it before and after training on the base model, the checkpoint, and an earlier checkpoint. Also track KL divergence on general prompts, since RL's Razor ties forgetting to distribution shift (2509.04259).

**What this means for Forge.** Use LoRA on all linear layers with a rank of about 32 to 64. Start the learning rate around 1e-4 to 2e-4 and use small batches (8 to 16). Keep a 20 to 50 prompt "general" probe set and compare before and after.

## 7. Common mistakes in small fine-tunes

- **Chat template and end-of-sequence.** TRL warns that with a base model's predefined template you must set `eos_token` to match, for example `<|im_end|>` for Qwen2.5, or responses will not terminate correctly. Check that training and inference use the identical template, including the system prompt.
- **Loss masking.**
  - `completion_only_loss` is on by default for prompt-completion datasets.
  - `assistant_only_loss=True` needs a template with generation markers.
  - `max_length` defaults to 1024 and `truncation_mode` is `keep_start`, so long CadQuery programs get silently cut. Check token lengths.
  - Instruction Modelling (2405.14394) found that adding loss on the prompt tokens reduces overfitting when training sets are small and outputs are short relative to instructions. The default is still masked prompts.
- **Overfitting signs.** Training loss near zero, mean token accuracy near 1.0 on a tiny set, dev pass rate falling while loss keeps falling, and fragility to later stages after repeating data (2609.33559). Evaluate on the dev set every epoch.
- **Checkpoint selection.** Choose on the practice dev set, not the 30 exam jobs. With 20 dev jobs one job is 5 points, so noise is large. Use multiple seeds and average over several samples per job.
- **Contamination.** Deduplicate between practice and exam at the level of job template and parameters, since a renamed copy of the same part counts as the same job. The sources I opened did not cover this directly. This is common practice, not a cited finding.
- **Hint leakage.** Remove hints from the prompts when training on hint-assisted successes, as FailForge does (2608.08570).

## Ranked reading list

1. LoRA Without Regret (Thinking Machines, 2025): https://thinkingmachines.ai/blog/lora/
2. A Minimalist Approach to LLM Reasoning: from Rejection Sampling to Reinforce (arXiv 2504.11343, 2025)
3. Beyond Human Data: ReST-EM (arXiv 2312.06585, 2024)
4. Is it RL or Data? GRPO vs Rejection-Sampling Fine-Tuning (arXiv 2610.25812, 2026)
5. Step Rejection Fine-Tuning (arXiv 2605.10674, 2026), with FailForge (arXiv 2608.08570, 2026)
6. LoRA Learns Less and Forgets Less (arXiv 2405.09673, 2024)
7. Fine Until Fine-Tuned: Repeated Solutions Make Reasoning Fragile (arXiv 2609.33559, 2026)
8. TRL SFTTrainer and GRPOTrainer docs: https://huggingface.co/docs/trl/main/en/sft_trainer and https://huggingface.co/docs/trl/main/en/grpo_trainer

Runners-up: s1 (2501.19393), LIMO (2502.03387), Setlur et al. on negatives (2406.14532), SCoRe (2409.12917).

**Not verified.** I did not read these papers' full text, only abstracts or summaries: STaR's numbers, LIMO's example count, OpenThoughts' recipe findings, DAPO's four techniques, and the "Learning from Less" result in detail. I found no study of DPO/KTO against SFT on a few hundred examples, nothing specific to CAD or CadQuery, and no GRPO memory figure for a 30B model.

DONE: fine-tuning research report