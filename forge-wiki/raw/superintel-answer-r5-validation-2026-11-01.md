# Answer: validate R5 training (no-card context distillation) before spending (superintel, 2026-11-01)

For hivey / Alyssa (brief: raw/brief-for-superintel-2026-11-01.md). Read-only, $0 spent; nothing run, no code or plan edited.
**verified** = recomputed from repo files (script in this note's Sources); **hypothesis** = my judgement; **decision** = left to the user.

## Verdict: GO with changes (none of them blocks starting today)
The recipe is sound: on-policy, referee-filtered, own-style rows, ~11× R3's data, same LoRA settings that already fitted
targets twice. Keep the hyperparameters. Changes, ranked:

| # | Change | Expected effect | Cost |
|---|---|---|---|
| 1 | **Run self-fix on the 118 FAILs first**, then rebuild the mix with `--selffix` (verifier's order) | Only training signal for goal (2) "fix its own mistakes"; adds ≈35-60 rows from the *hard* jobs (counters the easy-job bias). First-try dev effect ≈ 0 to +1; product-mode effect positive | ≈ $1, ≈ 30 min |
| 2 | **Add a 4th dev arm FT + card v2** (pre-register before dev: reported, not a gate) and, if it is the best dev arm, **add it to the exam** (amend final/PLAN step 6 before the exam) | Protects the exam: the card's rules cover CadQuery generally, the weights learned them only as used in 10 families. Old dev: R3 + card 86.4% vs A + card 68.3% (verified, check-r3card / check-acard summary.json): training + card stacked | dev ≈ $0.8; exam ≈ $1.6 more (≈ $4.9 vs $5 cap: tight, user yes if over) |
| 3 | **Prompt-token guard per dev arm** (free): A and FT median prompt_tokens must be ≈ 450-600, A + card ≈ 870-1,080 (verified range of card-v2 prompts); otherwise STOP | `a_messages`/`ft_messages` read `FORGE_RULE_CARD` from the env (runner_final.py:75-99). A shell that still exports it silently turns "A" into "A + card" and "FT" into "FT + card", and the main comparison is void | $0 |
| 4 (optional) | Instead of dropping the 204 card-naming rows, replace the phrase ("rule card" is 343 of 348 matches) with a neutral one ("the CadQuery rules") | Recovers 11% of rows, skewed to hard families (see Q4). +0-2 points on F8/F10 | one build_mix edit (Muse Code) + verifier, ≈ 30 min |
| 5 (optional) | Raise R5_MAX_TOKENS 8,192 → 12,288 | Keeps the 10 dropped rows, all F10 (the longest, hardest solutions). R3 trained at 12,288 on H200, peak 94 GB (train-r3/train.json) | ≈ +$0.1 |

If time is short: do 1-3, skip 4-5.

## Data facts I checked (verified)
Source: results/r5-pilot-v2-2026-10-31/pilot-A/calls.jsonl + results/r5-first-2026-10-31/rest-A/calls.jsonl (2,000 records).
- Rest run: 1,694/1,800 = 94.1% (summary.json). Rest is out-of-sample for card v2 (v2 was tuned on the 200 pilot jobs), so 94% is a fair A + card estimate for R5D.
- Per family, first try with card (pass %, PASS median completion tokens, card-name drop %):
  F1 88.0 / 2,275 / 9.7 · F2 100 / 2,659 / 7.5 · F3 98.5 / 3,564 / 7.6 · F4 82.5 / 3,547 / 6.1 · F5 98.0 / 3,734 / 7.1 ·
  F6 99.5 / 2,614 / 6.0 · F7 99.5 / 2,561 / 5.0 · F8 90.0 / 3,866 / **29.4** · F9 95.0 / 2,765 / 12.1 · F10 90.0 / 6,009 / **19.4**.
- Kept completion tokens per family: F10 852k (15% of 5.56M), F2/F6/F7 ≈ 490k each. Hard families are not under-weighted in tokens.
- The card's rules are already in the targets as Glimmer's own words: "fuse every part before you cut" in 1,795/1,882 PASS reasonings, "1 mm longer" 1,581, "positional" 936, ".val()" 897. **0** PASS rows use `start=` (16 FAILs crash on it).
- 0 PASS rows have reasoning < 200 chars; all finish_reason = stop. PASS median 3,112 completion tokens vs FAIL 3,629.
- Remaining crashes with the card: makeCylinder `start=` 16, `rotate()` missing angle 5, `rotateZ` 4, positional-after-keyword 4, no solid on stack 4. Non-crash FAILs are mostly near misses (volume/com/area, 0.2-0.4%).
- Glimmer is 30B dense (wiki findings/spark-vs-glimmer), so the LoRA pattern (attn + MLP, 104.8M params) covers the MLPs.
- Schedule: 1,678 rows × 2 epochs / GA 8 ≈ 420 optimizer steps (R3: 39). Cosine, 5% warmup (forge_train.py:1794).

## Q1. Will FT (no card) ≈ A + card on R5D?
**Likely close, slightly below** (hypothesis). Why it should work:
- Context distillation works when the same model produced the with-context outputs and is trained to produce them without the context (Snell et al. 2209.15189; Choi et al. 2206.11349). That is exactly this setup.
- The card mainly prevents crashes on a few high-frequency API patterns (v1 → v2 card: 47 → 3 crashes on the same 200 jobs). Each pattern is shown correctly hundreds of times, and the targets even recite the rules. LoRA learns such surface habits fast (R1 fitted its targets in 42 steps).
- On-policy rows avoid R3's failure (off-policy Spark style, manual recall).
Risks:
- **Overfit to 10 families:** real for the exam, not for dev (same families). Change 2 hedges it.
- **The unsolved 6% are absent:** standard for STaR/RFT/ReST-EM (2203.14465, 2308.01825, 2312.06585). It caps FT near the with-card pass@1. It cannot make FT worse than base on those jobs. Self-fix rows (change 1) put some of them back.
- **Temp-1 samples as targets:** fine. That is the serving distribution (dev also samples at 1.0, top_p 0.95), and the referee removes wrong ones. The hesitations ("Wait", "Hmm") get trained in. Harmless.
- **Where the gap will come from:** rarely used rules (F8 rounded-rectangle fillet, F10 arcs/revolve). Losing the card as something to "consult" hurts most there.

## Q2. Hyperparameters
**Keep r 16, α 32, lr 1e-4, 2 epochs, all attn + MLP.**
- LoRA's best LR is about 10× full-FT. Apply it to all layers, especially the MLPs. α = 32. Keep batches modest (Thinking Machines, "LoRA Without Regret", thinkingmachines.ai/blog/lora). Effective batch 8 and 1e-4 fit that.
- Don't go to 1 epoch / 5e-5. That is ≈ 4× less update, and the rare rules are the ones that need it. Overfitting risk is low with on-policy targets and 420 steps over 1.7k distinct jobs.
- Pre-register now: the **final adapter** is the one evaluated. Half-epoch checkpoints are only a fallback if the thinking STOP fires. No checkpoint shopping on dev.

## Q3. Filter or upweight families?
**No.**
- F2/F6/F7 rows are short (≈ 2.6k tokens) and carry the core rules (makeBox, fuse-before-cut).
- The hard families already carry the most tokens.
- Duplicating hard rows invites memorizing a few traces. More *samples* would help, not copies.
- The cheap way to add hard rows is self-fix (change 1) plus not dropping F8/F10 rows (changes 4-5).

## Q4. Does dropping the 11% card-naming rows bias the data?
**Yes, mildly, toward easier and shorter rows.**
- Drops are 29% of F8 PASSes and 19% of F10, against 5-8% of F2/F6/F7.
- Dropped rows are longer (median 3,713 vs 3,040 completion tokens). They are where the model deliberately looked up a rule (mostly the fillet window).
- The bias is not fatal: 127 F8 and 145 F10 rows remain.
- Rewording the phrase (change 4) is better than dropping. A neutral phrase teaches "recall the rule", not "a card exists".

## Q5. Transfer to the exam (30 hand-made jobs, k = 3)
Hypothesis. Reference points: Glimmer short prompt, no manual = 16/30 = 53% (wiki status); + 5.7k manual = 87-88%.
- **A + card:** ≈ 70-85%.
- **FT (no card):** ≈ 60-80%, likely 0-10 points below A + card. The rules transfer only as far as the 10 families used them.
- **FT + card:** ≈ 75-90%, the best bet for the submission (change 2).
- With 30 jobs the paired SE is ≈ 6-8 points, so a gap under ≈ 12 points is not decisive. Say so in the report.

## Q6. Things that should STOP the run (all free to check)
1. **Env leak:** prompt_tokens per arm outside the bands in change 3 → STOP (void comparison).
2. **Served model:** `/v1/models` must show the merged R5 model for FT (the old modal_forge bug served a stale model).
3. **First training loss:** on own samples it should start well below R3's off-policy 0.95. Hypothesis: ≈ 0.3-0.6. A mean over the first 10 steps ≥ 0.9 → STOP and check the render. Final loss < 0.1 → memorization warning; report it.
4. **First loss tokens per source** must open the thinking turn (`to=self`). Otherwise STOP (the R1 failure).
5. **Thinking ≥ 200 chars in ≥ 90% of FT dev answers** (already pre-registered).
Nothing in the data or code I read is a reason not to start.

## Predicted dev result (100 R5D, k = 1, first try)
| Arm | Range | Point |
|---|---|---|
| A + card v2 | 90-96% | 93 |
| A (no card) | 50-68% | 58 |
| FT (no card) | 85-94% | 90 |
| FT + card (if added) | 90-97% | 94 |

Reasoning:
- A: old dev A = 51.7%.
- R5 jobs are of similar difficulty: A + card v1 got 68.3% on old dev and 74.5% on the R5T pilot.
- The v2-card crash classes (`.solid()`, `start=`) hit A too.

Probabilities of the pre-registered readings (hypothesis):
| Reading | Probability |
|---|---|
| "as good as the card" (FT − (A+card) ≥ −3, CI lb ≥ −10) | ≈ 55% (expected delta ≈ −3, range −8 to +2) |
| "beats plain" (FT − A ≥ +10) | ≈ 95% |
| "cheaper" (completion tokens per correct) | ≈ 60% (trained on PASS rows, which are shorter than FAILs) |
| thinking STOP | < 5% |

## Sources
- Forge (verified): experiments/r5/PLAN.md; results/r5-first-2026-10-31/rest-A/{summary.json,calls.jsonl}; results/r5-pilot-v2-2026-10-31/pilot-A/calls.jsonl; results/check-acard-2026-10-30, check-r3card-2026-10-30 summary.json; results/train-r3/train.json; experiments/train/forge_train.py (lines 40-95, 785-789, 1763-1794, 1922); experiments/final/runner_final.py:75-99; experiments/final/RULE_CARD.md; experiments/final/PLAN.md:96-100; forge-wiki/wiki/findings/training-experiments-2026-10-30.md, spark-vs-glimmer-2026-10-31.md, status.md.
- Analysis scripts: /tmp/si_an.py, /tmp/si_an2.py (read-only over the two calls.jsonl).
- Verifier: ~/agents/verifier/reports/forge-r5c-build-2026-11-01.md (+ evidence/03-dry-mix.txt), forge-r5c-plan-2026-10-31.md.
- Papers checked today: 2209.15189 (Snell, Klein, Zhong, Learning by Distilling Context), 2206.11349 (Choi et al., Prompt Injection: Parameterization of Fixed Inputs); Thinking Machines "LoRA Without Regret" (thinkingmachines.ai/blog/lora).
- Checked 2026-10-30 (full texts in ~/agents/superintel/superintel-wiki/raw/papers/training-diagnosis-2026-10-30/): 2203.14465 (STaR), 2308.01825 (RFT), 2312.06585 (ReST-EM).
