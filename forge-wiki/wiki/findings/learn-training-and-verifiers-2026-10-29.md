# Learning guide: how to train weights and build a verifier (for Forge)

**Summary**: What the research (2022–Oct 2026) says about the two skills Forge depends on: training a model's
weights from verified examples, and building the automatic checker (the referee or verifier). Written for the user to
level up, and tied to Forge's real setup at each step. Main messages: (1) the plan Forge has now is a known method,
rejection-sampling fine-tuning (RFT) from a stronger teacher. Clean, varied data beats big data. (2) The referee already
follows best practice (property checks plus mutant self-tests). Its weak spot is that it needs a reference part. (3) SAM
3.1 adds nothing for sizes and positions. (4) RL (GRPO) is the next level, and the research says it turns "sometimes
right" into "right in one try", which is exactly Forge's new goal. But it costs far more than the $30 budget on a 30B
model.

**Sources**: three research reports from 2026-10-29 (subagents, web + alphaXiv), saved unedited in
`raw/knowledge/research-training-from-verified-data-2026-10-29.md`, `raw/knowledge/research-verifier-design-2026-10-29.md`
and `raw/knowledge/research-cad-code-papers-2026-10-29.md`. Three key papers were re-read by me in full text (marked
**verified (read)**). Forge facts: `experiments/first-test/checks.py`, [[new-goal-2026-10-29]], [[night-prep-2026-10-28]].

**Last updated**: 2026-10-29

---

## 0. The map: five levels of "making a model good at a tool"

| Level | What it is | Forge today | Cost |
|---|---|---|---|
| 0. Prompting | manual, hints, examples, retries with the error, self-check | **B-max arm** (the baseline to beat) | per call, every time |
| 1. SFT on verified teacher answers (RFT / distillation) | teacher tries many times, referee keeps the correct ones, student trains on them | **the Forge plan** (factory → LoRA) | ~$4–6 one-off |
| 2. Better SFT data | repaired failures, hint-then-remove, short plans before the code, per-job caps | not yet | almost free |
| 3. Learning from failures | DPO/KTO pairs (pass vs fail on the same job) | not yet | ~1 more training run |
| 4. RL with the referee as reward | GRPO: the student tries, the referee scores, the weights move toward what scored | not yet | 10–100× level 1 |
| + Inference-time checks | best-of-n, retry until the referee passes | B-max already does this | per call |

Forge's claim lives between levels 0 and 1. It says level 1 gives level-0 quality at one try, cheaper and faster.

---

## Part A: How training from verified examples works

### A1. What SFT really teaches
- **verified (read)**: CAD-Coder (arXiv 2505.19713) trained Qwen2.5-7B on text → CadQuery. SFT alone taught *valid
  code* (invalid rate 5.3%) but not *accurate geometry* (mean Chamfer distance 74.55 ×10⁻³). GRPO on a geometric reward
  brought it to 17.34, and a short planning cold start brought it to 6.54. Without SFT first, RL failed (76.20). Table 2 of
  the paper.
- **verified (read)**: same paper, Table 3: **8K high-quality examples beat 70K medium-quality ones** (6.54 vs 9.89).
  The authors' words: "quality outweighs quantity … small inconsistencies in code can lead to significant errors in CAD
  geometry."
- verified (report): ExeCAD/CAD-RL (2508.10118): SFT left IoU near 50%, planning lifted it to 60.8%, RL to 72.3%. The
  same pattern: SFT teaches syntax and format, RL teaches the exact numbers.
- **Meaning for Forge (hypothesis):** Forge differs from these papers in one important way. Its teacher (Spark Open)
  solves jobs the student fails (first test: 30/30 vs 20/30). So SFT carries *new* knowledge from teacher to student,
  not just the student's own lucky answers. That is the case where SFT should help most. The final exam is what tests it.

### A2. The sobering result about RFT on the model's own answers
- **verified (read)**: "Is it RL or data?" (arXiv 2610.25812, Oct 2026). Qwen3-4B, LoRA, a counting task, 3 seeds,
  pre-registered:
  - Single-round RFT (sample 192 answers per problem from the base model, keep the correct ones, fine-tune) **barely
    moved one-try (greedy) accuracy**: base 67.3%, RFT 65.9–69.6%.
  - GRPO beat it by 8–11 points (77.8% vs 66.9%).
  - Three rounds of iterated RFT recovered only ~30% of the gap.
  - GRPO did **not** raise pass@64 (the base model already solved 98% with 64 tries). It made the model *reliable*, not
    *smarter*: "turns problems the base model solves occasionally into problems it solves reliably".
- **Meaning for Forge:**
  1. Measure the student's pass@1 *and* pass@k (k = 3 is already in the Keel and B-max plans). If Glimmer's pass@3 is
     much higher than its pass@1, the gap is "reliability", which is what training (and especially RL) fixes best, and
     which is exactly the "one try, cheaper" claim.
  2. Train on the **teacher's** verified answers, not Glimmer's own. That is the plan already. This paper shows
     self-RFT is weak, so the teacher matters.
- Gotcha from the same paper (logged deviation 1): their first RFT recipe **did not train the end-of-sequence token**,
  and validation truncation rose to 36%. Check that the training text ends with Glimmer's `<|eot|>` and that the loss
  covers it.

### A3. Data: what matters most (in order)
1. **Correctness.** Only referee-passed answers. Forge's referee is exact, which is better than the Chamfer-based
   filters most papers had (verified (read), CAD-Coder used the lowest-Chamfer candidate, which can still be slightly
   wrong).
2. **Diversity of jobs, not many copies of one job.** verified (report): "Fine Until Fine-Tuned" (2609.33559): drilling
   a few hundred problems about 8× each looked fine on test (~95%) but made the model fragile. Accuracy fell to 86% and
   then 59% after later training. New *different* solutions to the same problem did not hurt. Rule of thumb: **1–3
   distinct passing programs per job, and many jobs**. Deduplicate by normalised code and by the geometry hash.
3. **Difficulty mix.** verified (read, 2610.25812): mixed easy, medium and hard jobs helped RFT by +3.7 points. Their
   RFT data was dominated by easy jobs (595 of 7,961 samples hard), because easy jobs pass more often. **Cap kept answers
   per job** so easy families don't flood the set (ReST-EM did this too, 2312.06585).
4. **Quantity last.** A few hundred to a few thousand clean examples teach format and style (LIMA 2305.11206, s1
   2501.19393). Forge's ~300 jobs is in the normal range for a LoRA on a 30B model, *if* they are varied.
- How CAD papers make varied jobs (verified (report)): BenchCAD (2605.10865) uses 106 parametric part families, each
  with typed parameters, a sampler and three difficulty tiers, about half based on real standards (ISO/DIN). Zero-to-CAD
  (2604.24479) uses an LLM-written catalog of 65 part categories with no dimensions, then has the teacher write the code
  with tool feedback (up to 10 turns). **For Forge:** the practice-job generator should be family modules with parameter
  ranges (BenchCAD style). Hold out *whole families* for the exam, not random jobs. Forge's rules already require this
  ([[factory-plan-2026-10-29]]).

### A4. Cheap data tricks (level 2)
- **Hint-then-remove (FailForge, 2608.08570, verified (report)):** when the teacher fails a practice job, give it the
  referee's failure message ("hole 2 is 3 mm off in x") and let it retry. If it now passes, **train on the passing
  program with the original prompt, without the hint**. This turned >26% of failures into training data and gave +6.6
  points over plain RFT. It fits Forge directly: the referee already explains its failures.
- **Repair trajectories with masked mistakes (Step-RFT, 2605.10674, verified (report)):** keep the broken attempt and
  the error in the context, but put no loss on the broken code; train only on the fix. That teaches recovery without
  teaching the mistake. It is only useful if the deployed student will also get retries.
- **Short plan before the code (verified (read), CAD-Coder):** a 5-step plan (parts, coordinate system, sketches,
  extrusions, code) in the training target helped a lot *together with RL*. For SFT only the evidence is weaker. Keep any
  plan short: long reasoning costs tokens at every call, which works against Forge's cost claim.

### A5. LoRA settings that research supports
- verified (report): "LoRA Without Regret" (Thinking Machines, 2025): apply LoRA to **all layers including the MLP**
  (attention-only learns slower). The best LoRA learning rate is about **10× the full fine-tuning rate**; the best rate
  barely depends on rank; LoRA dislikes very large batches. In RL even rank 1 was enough.
- verified (report): "LoRA learns less and forgets less" (2405.09673): LoRA damages general skills less than full
  fine-tuning.
- Forge's recipe ([[night-prep-2026-10-28]] §2: r = 16, alpha = 32, all q/k/v/o/gate/up/down of the language model, lr
  1e-4 cosine, 2–3 epochs, batch 8) **matches all of this**. Nothing to change. Optional: r = 32.
- **Forgetting check (hypothesis, cheap):** keep 20–30 general prompts (simple Python, a chat question) and compare base
  and trained Glimmer. A private agent that forgets how to chat is a demo risk.

### A6. Learning from failures (level 3)
- verified (report): negatives can be worth a lot. Setlur et al. (2406.14532) found well-chosen negatives equal to ~8×
  more positive data. But a minimalist study (2504.11343) found plain positive-only training close to methods that use
  negatives. The harmful part was jobs where *every* attempt failed.
- **No study tests DPO vs SFT at Forge's size (a few hundred examples)**, the biggest gap in the evidence.
- If tried: pairs = (teacher pass, failed attempt) on the same job, ideally the fail from a weaker model (Glimmer
  itself). Keep an SFT loss term on the chosen answer. Skip jobs with no pass. Decide on the dev set only.

### A7. RL with the referee (level 4)
- How it works: for each practice job, the student writes 8 programs; the referee scores each one; answers above the
  group average are made more likely, answers below less likely (GRPO). Jobs where all 8 pass or all 8 fail teach
  nothing and are skipped (that skipping is a large part of why it works, 2504.11343).
- Reward shape used by CAD papers (verified (read), CAD-Coder): 0 if the code doesn't run; 1.0 for a near-exact shape;
  a ramp in between; plus a small format reward. With **only** the geometric reward and no validity handling, training
  broke after ~200 steps (supplement B). For Forge the natural reward is partial credit from `checks.py`: runs → one
  valid solid → bbox → volume/area → centre of mass → mismatch ≤ 0.2%.
- **Cost reality (verified (read)):** CAD-Coder's GRPO stage took **146 hours on 8 A800 GPUs** (~1,170 GPU-hours) for a
  7B model. The RFT-vs-GRPO study needed 15–27 H100-hours per GRPO arm for a 4B model. Forge has ~2–5 H100-hours of
  budget. **Decision-ready conclusion:** RL on Glimmer 30B is not realistic before Nov 4. It is the "after the hackathon"
  level. A cheap way to learn it later is TRL `GRPOTrainer` with LoRA on a small open model (4B–8B) and the same
  `checks.py` as the reward.

---

## Part B: How to build a verifier you can trust

### B1. Two kinds of referee
- **Reference-based (what Forge has):** `experiments/first-test/checks.py` compares the answer with a known-correct
  solid: one valid solid; bbox ±0.1 mm; volume and area ±1%; centre of mass ±0.3 mm; and the volume in one part but not
  the other (XOR) ≤ 0.2% of the reference. The XOR check catches moved features that keep size and volume. This is
  stronger than the Chamfer distance and IoU used in most papers, and it works in absolute millimetres (CADSmith
  2603.26512 warns that normalised metrics hide scale errors).
- **Spec-based (CADTests):** **verified (read)**: "Text-to-CAD Evaluation with CADTests" (arXiv 2605.07807, May 2026)
  writes about 15 small CadQuery property tests per prompt (solid count, face and vertex counts, bbox, volume, centre of
  mass, `isInside`, through-hole vs blind pocket). Each suite must pass the reference and **kill every mutant** (a
  deliberately wrong version). Against human judges: accuracy **0.938**, F1 0.962. A vision-language judge reached
  accuracy 0.474 (recall 0.392). As a continuous score: CADTests AUC 0.928, Chamfer 0.663, CLIP 0.665.
- **Why this matters for Forge:** in the factory, the job generator makes the reference, so reference-based checking is
  fine and exact. **At a real company there is no reference part for a new request.** The production referee has to be
  spec-based: check the numbers and features the request states. That is the honest answer to a judge asking "how does
  this work at a real company?" (hypothesis: worth one slide).

### B2. Precision and recall of the referee
- **False pass** (wrong part accepted) means bad training data and an inflated exam score. **False fail** (right part
  rejected) means lost training data and an unfair exam.
- verified (report): "When the Reward Suite Is Leaky" (2607.11022): with weak tests, 47.6% of the reward paid on false
  passes went to genuinely wrong code. For SFT-style use it barely hurt held-out accuracy (0.2 points), but it inflated
  the *score*. False passes clustered in a few tasks (fixing the worst 18 removed half of them).
- verified (report): under RL a bad verifier is far worse. In a toy model with a verifier that checked only the last
  two digits, GRPO reached 99.4% "accepted" with 2.2% truly correct (2609.35677).
- **Forge already does the main defences** (verified, [[status]] and [[quillon-keel-build-2026-10-28]]): referee
  self-test 33/33 and 90/90 (references pass, wrong versions fail; this *is* mutation testing), blind rebuild 30/30, an
  independent verifier audit, freeze by hash, and sandboxing. The literature names these as best practice. Keep the names
  in the write-up: "mutation-tested referee" and "blind rebuild".

### B3. Ways a model can fool a geometry referee (red-team list)
Known from papers (verified (report)): editing or special-casing tests, monkey-patching the scorer (ImpossibleBench
2510.20270; METR's o3 report), fake binaries and no-op assertion helpers in agent sandboxes (2610.15924), sparse point
sampling missing thin walls (CAD-Coder failure analysis), and small gaps between parts that pass both kernel metrics and
a vision judge (CADSmith).
Forge-specific (hypothesis, my inference):
1. Several solids that together match bbox and volume → blocked: `solids == 1`.
2. A blind pocket instead of a through hole → mostly caught by volume and XOR. Add a "through" test if exam jobs use
   thin plates.
3. The program reads or overrides the measuring code → blocked by the sandbox, *if* the referee runs in a separate
   process and only receives the exported STEP (the B2 sandbox design does this; keep it that way).
4. A symmetric move of a feature → caught by XOR (that is why it exists).
5. Tolerance shopping: an answer 0.09 mm off on every face passes the 0.1 mm bbox check, but the XOR check limits it.
Rule from the hardening paper (2610.15924): after every referee fix, re-run all known-good answers so the fix doesn't
reject right parts.

### B4. SAM 3.1 and visual checks
- verified (report): SAM 3 (Meta, Nov 2025, arXiv 2511.16719) does *promptable concept segmentation*: give it a short
  phrase or an example and it outlines every matching object in an image or video. SAM 3.1 (Meta blog, 27 Mar 2026) is a
  speed upgrade for video (tracks up to 16 objects per pass, ~2× throughput). It outputs **pixel masks, not
  millimetres**.
- verified (report): **no paper found that uses SAM to check CAD parts.** CADTests found multi-view renders **did not
  improve** generation and cost many tokens. CADCodeVerify's vision answers were only 65–68% correct. CADSmith found
  renders helped only on the most complex parts, *on top of* exact kernel numbers.
- **Recommendation (decision for the user):** drop "SAM 3.1 checks" from the diagram. CadQuery's exact measurement is
  the checker. If a visual is wanted for the demo, show a render as a *picture for humans*, not as a check. The diagram
  should also say CadQuery, not OpenSCAD (Forge switched on 2026-10-28).

### B5. Learned judges (LLM or VLM) — only for fuzzy requirements
- Use them only where no exact check exists ("looks like a phone stand", "ergonomic"). Calibrate on outputs the exact
  referee already labelled, use a different model family than the generator, and **never let a judge override a referee
  fail** (verified (report): Generative Verifiers 2408.15240; CADTests VLM accuracy 0.474).
- Forge's jobs are all exact numbers, so Forge needs no learned judge. Good: fewer moving parts.

---

## Part C: What this means for the next Forge steps (checklist)

Factory (teacher run):
- [ ] Practice jobs from **parametric families** with three difficulty tiers; exam families fully held out; overlap
      check by family *and* geometry hash.
- [ ] Teacher samples several attempts per job (e.g. 4). **Keep at most 2–3 distinct passes per job**; dedupe by
      normalised code.
- [ ] On teacher failure: one retry with the referee's failure message; train on the pass **without** the hint
      (FailForge).
- [ ] Keep the failures with their referee messages (free; needed for DPO or analysis later).
- [ ] Record per-check pass rates (bbox / volume / com / XOR), not just pass/fail.

Training:
- [ ] Build training text with `apply_chat_template` only, at the served reasoning level; check one rendered example
      by eye; **the loss covers the final `<|eot|>`**; no example is cut by `max_length`.
- [ ] Recipe as in [[night-prep-2026-10-28]] §2 (it matches the research). Smoke test first.
- [ ] Pick the checkpoint on the ~20 dev jobs, never on the exam (already a user rule).
- [ ] Forgetting probe: 20–30 general prompts, base vs trained.

Final exam:
- [ ] Report **pass@1 and pass@3** for every arm, plus $ and seconds per correct part (the new-goal chart).
- [ ] Add a small **prompt-style shift** check on the dev set (the same jobs, worded differently). Several papers found
      fine-tuned CAD models break on unfamiliar wording (CADTests excluded cadrille as degenerate; CADmium found caption
      style mismatches hurt). This is the most likely way a trained Glimmer looks good on the exam and bad in a live demo.
- [ ] Be honest about the strongest baseline. CADTests (verified (read), finding ii) found that models fine-tuned on
      synthetic data *lost* to frontier models with a CAD-kernel feedback loop. B-max is that kind of baseline, so Forge's
      claim (same quality, much cheaper, private) is the right one. Don't claim "smarter".

---

## Part D: Learning path for the user

Read in this order (each about 20–40 min):
1. **CAD-Coder** (arXiv 2505.19713): the closest recipe to Forge: data pipeline, SFT → GRPO, reward design, ablations.
2. **CADTests** (arXiv 2605.07807): how to build a referee from property tests and mutants; why vision judges fail.
3. **Is it RL or data?** (arXiv 2610.25812): a clean, pre-registered experiment comparing RFT and GRPO. It is also a
   model for writing Forge's own result page.
4. **LoRA Without Regret** (https://thinkingmachines.ai/blog/lora/): why the LoRA settings are what they are.
5. **ReST-EM** (arXiv 2312.06585): the classic "sample, filter, fine-tune, repeat" paper.
6. **Scalable Weak-to-Strong Verifier Hardening** (arXiv 2610.15924) and **ImpossibleBench** (arXiv 2510.20270): how
   models cheat verifiers and how to red-team them.
7. **Zero-to-CAD** (arXiv 2604.24479) and **BenchCAD** (arXiv 2605.10865): how to generate many varied, verified
   practice jobs.
8. **TRL docs**: SFTTrainer and GRPOTrainer (https://huggingface.co/docs/trl/main/en/sft_trainer,
   https://huggingface.co/docs/trl/main/en/grpo_trainer).

Hands-on exercises, cheapest first (hypothesis: each teaches one idea with real Forge data):
1. **Free:** from existing results, compute Glimmer's pass@1 vs pass@3 per job. That shows how much of the gap is
   "reliability" (trainable) vs "can't do it" (needs the teacher).
2. **Free:** write 5 new mutants for 3 exam jobs (blind hole, two solids, a 0.15 mm shift, a mirrored feature, a scaled
   copy) and check `checks.py` kills them all. If one survives, you found a referee hole.
3. **Free:** write 3 CADTests-style spec checks for one job *without* using the reference (the numbers from the request
   only). Compare their verdicts with `checks.py` on the same answers. This is the "real company" referee.
4. **~$0.5–1:** the planned training smoke test. Watch the loss fall and check the memory peak.
5. **After the hackathon, ~$5–20:** GRPO with LoRA on a small model (4B–8B) with `checks.py` as the reward, on 50
   practice jobs. Compare pass@1 before and after, and look for reward hacking in the outputs.

## Open questions
- No study of DPO vs SFT on a few hundred examples. Forge would have to test it on the dev set itself.
- Whether training text should include a short plan: evidence exists only together with RL. Test on the dev set if
  time allows.
- The papers with 2026 arXiv ids are mostly preprints, not peer-reviewed. The three marked "verified (read)" were checked
  in full text on 2026-10-29. The others come from the subagent reports (abstracts and summaries).
