<!-- Raw source: subagent research report (Claude Sonnet, web + alphaXiv), 2026-10-29, for the training/verifier learning guide. Unedited. -->

# Research report: LLMs that write CAD code, trained or improved with verification (2024 to 2026)

**How this was gathered.** I read alphaXiv structured reports and extracted text for the papers below. Every arXiv id comes from an alphaXiv result I saw. Numbers are as reported by each paper's own tables or report text. I did not read the PDFs line by line, so treat exact figures as "per the alphaXiv summary".

**Not read in depth.** CAD-Llama (2505.04481), CAD-MLLM (2411.04954), CAD-Assistant (2412.13810), CAD-GPT (2412.19663) and RLCAD (2503.18549) appeared in search results, but I did not read them. I cite them only for existence. Query2CAD (2406.00144) I know only through how other papers describe it. I did not find the original Text2CAD paper or GenCAD as standalone results. Text2CAD appears as the data source and baseline in many papers below.

## Part 1: Papers

### Closest match to Forge: text to CadQuery, trained with verification

**1. CAD-Coder (Guan et al., Beihang/HKU), arXiv 2505.19713, 2025**
- **Base model:** Qwen2.5-7B-Instruct.
- **Data:** Text2CAD supplies 178K descriptions and ground-truth meshes. DeepSeek-V3 wrote several CadQuery candidates per item. Each was executed and compared to the ground-truth mesh by Chamfer distance (CD). The lowest-CD candidate became the label. This gave 110K verified triplets, split into 8K high-quality, 70K medium and 32K hard. A further 1.5K chain-of-thought (CoT) samples were built from the hard cases, with filtering and manual refinement.
- **Method:** SFT on 8K high-quality pairs, then a CoT cold start, then GRPO.
- **Reward:** R = λ_geo·R_geo + λ_fmt·R_fmt.
  - R_geo is piecewise in CD: 1.0 for CD < 1e-5, linear down to 0 at CD 0.5, and 0 if the code fails to execute.
  - R_fmt is binary: a `<think>` block plus a python code block.
- **Results:** Mean CD 6.54e-3, median CD 0.17e-3, invalid rate 1.45%. Text2CAD scored mean CD 29.29e-3 and invalid rate 3.75%. GPT-4o scored mean CD 133.5e-3 and invalid rate 93%. Base Qwen2.5-7B had an invalid rate of 98.83%.
- **Ablation (mean CD):** SFT only 74.55; SFT+GRPO without CoT 17.34; full method 6.54. Skipping SFT gave 76.20.
- **Data quality:** 8K high-quality pairs beat 70K medium-quality pairs (6.54 vs 9.89 mean CD).
- **Failure modes they list:** multi-part spatial alignment, extrude versus cut confusion, thin or hollow parts where sparse point sampling lets the reward be gamed.
- **Lesson for Forge:** This is the nearest recipe. Filter the SFT set hard for quality, because small and clean beat large and noisy. Use a graded geometric reward with a format gate. Your exact referee can replace Chamfer distance and avoid the sparse-sampling reward hacking they saw.

**2. Text-to-CadQuery (Xie and Ju, ASU), arXiv 2505.06507, 2025**
- **Base models:** a range from CodeGPT-small 124M up to Mistral-7B, including Qwen2.5-3B. LoRA on the 7B, full fine-tune on the smaller ones.
- **Data:** about 170K text-CadQuery pairs, from DeepCAD/Text2CAD JSON converted to CadQuery by Gemini 2.0 Flash. The pipeline had an error-feedback self-correction loop, which raised the execution success rate from 53% to 85%. A Gemini image-based shape check followed, then a human check. Split 90/5/5.
- **Method:** SFT only.
- **Results:**
  - Qwen2.5-3B was best: median CD 0.191e-3 (Text2CAD: 0.370e-3), Gemini-judged accuracy 69.3% (baseline 58.8%).
  - Mistral-7B had the lowest invalid rate, 1.32%, but lower accuracy; the authors attribute this to underfitting the 170K samples.
  - Even the 124M model beat the 363M Text2CAD transformer.
- **Lesson for Forge:** Pretrained code models adapt cheaply. Their finding that the 7B model underfit while the 3B did better suggests that a 30B LoRA needs enough varied data, or it will plateau below a smaller model.

**3. TOOLCAD (Gong et al., Shanghai Univ.), arXiv 2604.07960, 2026**
- **Setup:** An agent calls FreeCAD tools through MCP, so this is not pure code generation. The base models were Qwen2.5-7B and Qwen3-8B.
- **Data:** 982 GPT-4o-generated demonstration trajectories with human checking.
- **Method:** SFT, then online GRPO with a part-count curriculum.
- **Reward:** a weighted sum of three terms: a trajectory-level outcome score from a trained reward model (Qwen2.5-7B ORM), step-wise 0/1 engine feedback, and a format reward.
- **Results:**
  - The 7B/8B agents reached 63.9% and 61.8% success, versus 62.7% for GPT-4o with ReAct prompting.
  - SFT alone gave 43.7%, so online RL added about 20 points.
  - Removing the step-wise reward hurt badly.
  - Curriculum helped.
  - Scaling online RL data 1x to 5x gave larger gains than adding parameters; SFT saturated beyond 7B.
- **Lesson for Forge:** Step-level or partial-credit rewards plus a difficulty curriculum stabilised RL. Rank jobs by number of features or parts and train easy to hard. For a 30B base, expect RL data volume to matter more than size.

**4. RA-CAD (Yan et al., Sichuan), arXiv 2608.05714, 2026**
- **Base model:** Llama-3-8B-Instruct with LoRA.
- **Data:** CADFusion and Text2CAD data, recoded into a quantised sketch-and-extrude token code.
- **Method:** SFT bootstrap, then GRPO over a generate, execute, critique, rewrite loop. The critique is a learned action.
- **Reward:** terminal reward from F1 of sketch tokens plus CD. It is 0 for non-executable code.
- **Results:**
  - Invalid rate 6.2%, average CD 35.44 on the CADFusion data.
  - GPT-4o, DeepSeek and others with 8-shot prompting had invalid rates of 54% to 88%.
- **Ablation:** without SFT bootstrap the invalid rate was 100%. SFT alone left it at 90%. SFT plus the agent loop gave 18.8%. Adding GRPO and the critique gave 6.2%.
- **Lesson for Forge:** RL from scratch fails, so SFT first is needed. A multi-turn repair loop plus RL on the final geometric outcome beat RL without critique.

**5. CAD-RL / ExeCAD, "From Intent to Execution" (Niu et al., Fudan/ByteDance), arXiv 2508.10118, 2025**
- **Base model:** a vision-language model (the alphaXiv report does not name it).
- **Data:** ExeCAD, 16,540 examples. GenCAD-Code CadQuery was paired with Text2CAD prompts, and GPT-4o iteratively fixed code and text to agree.
- **Method:** CoT cold-start SFT, then RL with three stability tricks:
  - Trust Region Stretch, which loosens PPO clip bounds.
  - Precision Token Loss, which upweights numeric tokens.
  - Overlong Filtering, which drops truncated samples from the reward.
- **Reward:** R = R_exec · (λ·IoU + λ'·GPT-4o semantic score). Executability gates the other terms.
- **Results:**
  - Executability 99.6% and IoU 78.7% with structured design-language input.
  - Plain GPT-4o reached 72.7% executability and 47.7% IoU.
  - SFT alone left IoU near 50%. CoT lifted it to 60.8%. RL lifted it to 72.3%.
- **Lesson for Forge:** SFT teaches valid code but not accurate dimensions. Dimensional accuracy needed RL, so keep numeric tokens and truncation noise in mind.

**6. cadrille (Kolodiazhnyi et al.), arXiv 2505.22914, ICLR 2026**
- **Base model:** Qwen2-VL-2B. Inputs are point cloud, multi-view image or text. Output is CadQuery.
- **Data:**
  - SFT on the roughly 1M procedurally generated CAD-Recode programs plus DeepCAD (about 160K).
  - RL used only meshes as references, with no ground-truth code. Hard-example mining kept only inputs where the SFT model's average reward fell below a threshold.
- **Method:** SFT, then either DPO (5 samples, best versus worst) or online RL (Dr. CPPO, a GRPO variant).
- **Reward:** 10·IoU, plus −10 for invalid code.
- **Results:**
  - Online RL beat DPO by 3 to 9 IoU points and cut the invalid rate to under 0.2%.
  - On the real-scan CC3D set, the image invalid rate fell from 7.7% to 0.1%.
  - A single RL sample beat CAD-Recode with 10 samples on invalid rate.
- **Lesson for Forge:** The SFT-on-synthetic then RL-on-harder-verified-data split closes the domain gap. Hard-example mining saves RL compute. Note that the CADTests paper (item 14) found cadrille produced "degenerate solutions" on text prompts outside its training style.

**7. CAD-Recode (Rukhovich et al.), arXiv 2412.14042, 2024**
- **Base model:** Qwen2-1.5B with a point-cloud projector.
- **Data:** 1M procedurally generated CadQuery sketch-extrude programs, with syntactic and geometric validation. Real DeepCAD/Fusion360/CC3D data was used only for testing.
- **Method:** SFT only. At inference they sample 10 candidates, run each, and keep the lowest-CD one.
- **Results:** DeepCAD mean CD 0.30 (versus 3.43 for the prior best CAD-SIGNet) and IoU 92.0% (versus 77.6%). On CC3D the invalid rate was 0.3%. Procedural data at 160K already beat real data at the same size, and 1M beat 160K.
- **Lesson for Forge:** A parametric generator gives cheap, unlimited, verified data, and execution-based best-of-N reduces invalid rate. Zero-to-CAD (item 9) shows its weakness.

**8. CADCodeVerify and CADPrompt (Alrashedy et al., Georgia Tech), arXiv 2410.05340, ICLR 2025**
- **Models:** prompted GPT-4, Gemini 1.5 and CodeLlama-70B. No training.
- **Method:** compile-error repair loop, then a vision-language model generates yes/no questions about the rendered object and turns the answers into feedback. Two refinement rounds.
- **Data:** CADPrompt, 200 prompts with expert CadQuery.
- **Results:** GPT-4 compiled 96.5% of the time. Refinement cut point-cloud distance 7.3% (0.155 to 0.127), roughly matching a ground-truth geometric-solver oracle. 48% of initial errors were structural configuration errors and 18% logical errors.
- **Lesson for Forge:** The error taxonomy is useful. Their vision feedback worked, but the CADTests paper (item 14) found renders did not help while code-level tests did. Your exact referee is the stronger signal.

**9. Zero-to-CAD (Ataei et al., Autodesk), arXiv 2604.24479, 2026**
- **Data:** about 1M CadQuery programs and 100K curated.
  - The generator was gpt-oss-120b in an agentic loop with tools: execute and validate, and documentation lookup.
  - A catalog of dimension-free part descriptions came from 65 part categories. A second stage wrote the code, with up to 10 turns per attempt.
  - Acceptance required: runs, one connected solid, at least 7 faces, positive volume, STL/STEP export succeeding.
  - 22.3% of designs passed on the first attempt, with a mean of 3.3 attempts.
- **Comparison with CAD-Recode:** CAD-Recode had 56.3% disjoint multi-body solids and an average of 16.4 faces. Zero-to-CAD averaged 46.2 faces (the human ABC set averages 50.7).
- **Downstream test:** Qwen3-VL-2B fine-tuned on it reached 82.1% valid code and IoU 0.747 in distribution. On the real ABC set it got 61.0% valid and IoU 0.377. GPT-5.2 managed 72% valid in distribution and IoU about 0.49.
- **Failure modes:** thin features breaking connectivity, misplaced holes, self-intersections, scale drift.
- **Lesson for Forge:** This is almost exactly your teacher-plus-referee pipeline, and it documents that the acceptance gates are the quality lever. The 65-category catalog is a template for diversity.

**10. CADSmith (Barkley et al., CMU), arXiv 2603.26512, 2026**
- **Model:** prompted Claude Sonnet as the coder, Claude Opus as the judge. No training.
- **Method:** planner, coder, executor, validator, refiner. The judge sees the prompt, the code, exact OpenCASCADE measurements (volume, bounding box, face counts) and three rendered views. Up to 5 outer iterations.
- **Data:** 100 hand-written prompts in three tiers.
- **Results:** 100% execution versus 95% for zero-shot. Mean CD fell from 28.37 to 0.74 and median IoU rose from 0.81 to 0.96. Removing vision from the judge made the T3 (complex-part) mean CD jump from 1.42 to 49.68.
- **Lesson for Forge:** Exact kernel numbers drove most repair. Image checks mattered only for complex parts. Use the same measurements as feedback during teacher generation.

**11. BlenderLLM (Du et al., CUHK-SZ), arXiv 2412.14203, 2024 (Blender bpy, not CadQuery)**
- **Base model:** Qwen2.5-Coder-7B-Instruct.
- **Data:** 135 seed instructions across 16 object categories, 8 instruction tones and 5 complexity levels, expanded by Self-Instruct to about 50K. GPT-4o wrote the scripts. An image-based GPT-4o check kept 8K (2K human-verified, 6K model-verified).
- **Method:** SFT, then 3 or 4 rounds of self-improvement. Each round generates scripts, filters them with a cascade (Qwen2-VL coarse filter, GPT-4o fine filter, 81.8% precision) and retrains.
- **Results:** CADBench-Sim 0.748 versus 0.687 for o1-Preview, CADBench-Wild 0.664 versus 0.583. Syntax error 3.4% versus 18.2% for GPT-4-Turbo. Self-improvement beat extra epochs and beat adding the same amount of predefined data.
- **Lesson for Forge:** Rejection-sampling self-improvement works, but their filter was a model judge. Your exact referee is a stronger filter.

**12. CADmium (Govindarajan et al.), arXiv 2507.09792, 2025 (JSON sequence, not code)**
- **Models:** Qwen2.5-Coder 1.5B/3B/7B/14B with LoRA rank 64.
- **Data:** about 170K DeepCAD/Fusion360 models re-captioned by GPT-4.1 from minimal JSON plus 10 renders.
- **Method:** SFT only.
- **Results:** invalid rate fell as model size rose. The 14B model beat Text2CAD on CD and per-primitive F1, but had a higher invalid rate than Text2CAD.
- **Lesson for Forge:** Style mismatch between training and test captions drops performance, so keep your training prompt style consistent with the real user prompt style.

**13. Test-Time Scaling via Consensus Selection (Haag et al., Siemens), arXiv 2608.09706, 2026**
- **Method:** sample N CadQuery programs, discard failures, pick the one geometrically closest to the others (minimum average Chamfer distance), with no verifier.
- **Results:** beat a VLM-verifier selector on identical candidate pools. Gains saturate around N = 9. An oracle best-of-N stays well above any selector. Chamfer improvement was 8 to 10% for gpt-oss-20b and Gemma 3 12B, and 1 to 3% for Gemini 3 Flash.
- **Lesson for Forge:** Weaker models gain more. This is a cheap inference-time add-on to your trained model, and it shows how much headroom best-of-N leaves.

**14. CADTests (Mallis et al., Luxembourg), arXiv 2605.07807, 2026**
- **Data and method:**
  - It rebuilds CADPrompt with 5,937 executable tests, about 15 per prompt, written by Claude and refined against mutated wrong programs until over 90% of mutants are caught.
  - Tests check topology counts, bounding-box dimensions, volumes and spatial relations.
- **Results:**
  - Fine-tuned models trained on synthetic data (Text2CAD, cadrille) generally did worse than training-free LLM agents with a CAD kernel loop.
  - Kernel feedback lowered invalid rate.
  - Multi-view renders did not help.
  - Test feedback added about +10 points of pass rate on abstract prompts.
  - Test results agreed with humans at 0.938 accuracy, better than CD or CLIP.
- **Lesson for Forge:** This is the strongest evidence that spec-based checks beat similarity to one reference. If your referee compares to an exact reference, it can penalise valid variants. Consider also checking stated constraints (hole count, dimensions).

### Other relevant 2026 items (seen in search results, not read in depth)
BenchCAD 2605.10865 (read: 17.9K CadQuery programs in 106 industrial part families from parametric Python modules with typed parameter schemas and samplers, three difficulty tiers; the reported failure modes were wrong extrusion plane and simplified operations such as a twisted bracket built from two flat ones); Text2CAD-Bench 2605.18430; Clarify Before You Draw 2602.03045 (CadQuery text-to-CAD with clarifying questions); CIT-CAD 2609.07434; ExpConCAD 2608.24760; ReliCAD 2609.22325; PR-CAD 2604.19773.

## Part 2: Synthesis

### (a) The most common successful recipe
- **Stages:** SFT first, then RL. Nearly every paper that tried RL without SFT reports failure (RA-CAD: 100% invalid; CAD-Coder: mean CD 76.2 without SFT).
- **SFT size:** ranges from 8K clean pairs (CAD-Coder) to 170K (Text-to-CadQuery) to 1M procedural (CAD-Recode, cadrille). The one direct comparison found 8K high-quality beat 70K medium (CAD-Coder).
- **RL algorithm:** GRPO or a close variant (CAD-Coder, TOOLCAD, RA-CAD, cadrille's Dr. CPPO). cadrille found online RL beat DPO by 3 to 9 IoU points.
- **Reward shape:** all combine a validity gate with a graded geometry score.
  - CAD-Coder: CD ramp (1.0 at CD < 1e-5, down to 0 at 0.5) plus a format term.
  - cadrille: 10·IoU, with −10 for invalid code.
  - CAD-RL: executability multiplied by (IoU plus a semantic score).
  - TOOLCAD: step success plus outcome model plus format.
  - RA-CAD: terminal CD and F1.
- **Common stabilisers:** a CoT cold start; hard-example mining (cadrille); loosened clipping, numeric-token weighting and dropping truncated samples (CAD-RL); curriculum by part count (TOOLCAD).
- **What each stage buys:** SFT buys validity and syntax. RL buys dimensional accuracy and robustness. CAD-RL reports SFT IoU near 50%, rising to 72% with RL. cadrille reports invalid rates falling to under 0.2%.

### (b) Keeping training data separate from test data
This is the weakest-documented area. What I could verify:
- Most papers reuse the standard splits of DeepCAD/Text2CAD (CAD-Coder, Text-to-CadQuery 90/5/5, CADmium 118,299/8,925/8,046).
- I did not find an explicit duplicate or near-duplicate check in any of the summaries I read. That is a hypothesis, not a verified absence, because I did not read the full texts.
- DeepCAD itself contains many near-duplicate shapes, so a random split may leak.
- cadrille and CAD-Recode train on procedural data and test on separate real datasets (DeepCAD, Fusion360, CC3D), so test shapes are by design a different distribution.
- BenchCAD holds out whole families (10 families in the OOD test) and still found a large IID-to-OOD gap.
- CADTests built a new test set with tests written by a different pipeline than the training data.
- **For Forge:** hold out whole part families and parameter ranges, not random rows. Hash the geometry of every training program, and reject test jobs whose reference shape matches any training shape within a tolerance. This goes beyond what I saw in the literature.

### (c) Typical failure modes and fixes that helped

| Failure | Evidence | What helped |
|---|---|---|
| Invalid code | GPT-4o 93% and base Qwen 98.8% invalid in CAD-Coder; 54 to 88% for prompted LLMs in RA-CAD | SFT on CadQuery; RL with a validity gate (cadrille to under 0.2%); an execute-and-repair loop |
| Wrong dimensions | SFT IoU near 50% in CAD-RL; scale drift in Zero-to-CAD | RL on geometric reward; numeric-token weighting; exact kernel measurements in the loop (CADSmith) |
| Wrong positions or orientation | wrong extrusion plane (BenchCAD); misplaced holes (Zero-to-CAD); multi-part alignment (CAD-Coder) | CoT planning with coordinate assignment; per-part curriculum; spec tests |
| Missing features | structural errors 48% of initial errors (CADCodeVerify); fine details dropped (BenchCAD) | iterative critique; mutation-tested spec checks |
| Booleans, extrude vs cut | cut vs extrude confusion (CAD-Coder); Boolean errors flagged as near-miss by ORM (TOOLCAD) | CoT; outcome reward models; a CadQuery error-pattern knowledge base (CADSmith) |
| Disconnected or degenerate solids | 56.3% disjoint multi-body in CAD-Recode data | validation gates: one solid, minimum faces, positive volume |
| Reward hacking | sparse point sampling on thin parts (CAD-Coder) | exact volumetric or B-rep comparison |
| Simplified operations | models avoid sweeps, lofts, twists (BenchCAD) | data with broader operations (Zero-to-CAD, BenchCAD) |

### (d) Generating diverse practice jobs
- **Procedural generators:** CAD-Recode makes 1M programs from randomized sketch primitives and extrusions. BenchCAD uses 106 hand-built family modules, each with typed parameters, a sampler, a validator and three tiers. About half are anchored to real standard tables (ISO, DIN and others).
- **LLM-written catalogs:** Zero-to-CAD generates dimension-free descriptions across 65 categories, adds reference snippets, and selects operations from the description text. Final diversity curation used DINOv3 embeddings and k-means.
- **Self-instruct from seeds:** BlenderLLM expands 135 seeds along category, tone and complexity axes to about 50K.
- **Re-captioning real data:** CADmium and Text-to-CadQuery rewrite descriptions from existing CAD histories with GPT-4.1 or Gemini.
- **Paraphrase and style:** CAD-RL and CADTests both show prompts differ greatly in detail (abstract versus structured). Test across several prompt styles.
- **Hard-example mining:** cadrille keeps only items where the SFT model scores poorly, and TOOLCAD orders by part count.
- **For Forge:** a parametric family generator (BenchCAD-style) gives exact ground truth, and an LLM catalog (Zero-to-CAD-style) adds breadth. The two are complementary.

### (e) Do small models with verification beat large prompted models?
Yes in-distribution, with caveats. Verified numbers:
- CAD-Coder 7B: invalid 1.45%, mean CD 6.54e-3, versus GPT-4o at 93% invalid and 133.5e-3 (2505.19713).
- RA-CAD 8B: invalid 6.2%, versus 54 to 88% for prompted frontier models (2608.05714).
- TOOLCAD 7B/8B: 63.9% and 61.8% success versus 62.7% for GPT-4o with ReAct (2604.07960). This is a small edge.
- BlenderLLM 7B: 0.748 versus 0.687 for o1-Preview on its own in-distribution benchmark (2412.14203).
- Zero-to-CAD 2B: 82.1% valid, IoU 0.747 in distribution versus GPT-5.2 at 72% and about 0.49. On human-designed ABC data the lead shrinks: IoU 0.377 and 61.0% valid versus GPT-5.2's 66.2% valid. It still led on IoU (2604.24479).
- CAD-RL: its tuned model reached 99.6% executability versus 72.7% for GPT-4o (2508.10118).

The counter-evidence is serious. CADTests (2605.07807) found that fine-tuned models trained on synthetic data generally lost to training-free frontier LLMs with a kernel feedback loop on a new, differently styled benchmark. cadrille was excluded as degenerate there. Also, wins on in-distribution benchmarks may be partly template memorisation. CADSmith shows a prompted frontier model with exact feedback reaches 100% execution and median IoU 0.96 on its tier set. So a fair statement is: small models with verified training beat frontier models prompted once, but a frontier model plus an execute-and-repair loop is a much tougher baseline that most papers do not run.

## Part 3: Takeaways for Forge
1. Use the validity gate times graded geometry reward shape, and keep the exact referee as the geometry term. Add constraint checks (CADTests-style) if prompts state dimensions or counts.
2. Prefer a smaller, cleaner SFT set to a big noisy one. Gate teacher outputs as Zero-to-CAD does.
3. Run SFT first, then GRPO. Mine hard examples and order by number of features.
4. Evaluate against a strong baseline: a frontier model with an execute-and-repair loop, not single-shot prompting.
5. Build held-out splits by part family and parameter range, and deduplicate by geometry hash. The literature barely documents this.
6. Plan for a 30B model with LoRA: TOOLCAD and Text-to-CadQuery both suggest that more varied data and RL volume matter more than parameters.

DONE: CAD-code papers report