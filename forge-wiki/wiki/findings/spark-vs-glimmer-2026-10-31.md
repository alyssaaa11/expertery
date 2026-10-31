# Spark vs Glimmer: who is who, and what it means for training (2026-10-31)

**Summary**: Spark Open is a much stronger model than Glimmer: 816B MoE vs 30B dense, and an Artificial Analysis
Intelligence Index of 25 vs 6. Glimmer was already distilled from Spark by Meta. Copying Spark's final code (R1) or its
long thinking (R3) did not work for the reasons Meta's own guide warns about. Related: [[training-experiments-2026-10-30]], [[status]].

## Facts (verified, fetched 2026-10-31)
| | Muse Spark Open | Muse Glimmer |
|---|---|---|
| Size | 816B total, 42B active (MoE) | ≈ 30B dense (29.6B incl. 1.8B vision) |
| AA Intelligence Index | **25** (class median 23) | **6** (class median 13) |
| Output tokens to run the AA index | 91M | 39M |
| Speed | 139 tok/s | 106 tok/s |
| Price (hosted, per 1M in/out) | $1.25 / $4.25 | $0.30 / $1.20 |
| Context | 1M | 131k |
| Licence | Muse Model License (commercial use restricted) | Apache 2.0 |
| Origin | — | "distilled from Muse Spark", "generally less capable than Muse Spark" |
Sources: artificialanalysis.ai/models/muse-spark-open, artificialanalysis.ai/models/muse-glimmer,
huggingface.co/meta-models/Muse-Glimmer-30B, dev.meta.ai/docs/models.

## Meta's Glimmer post-training guide vs what we did (verified, dev.meta.ai/docs/muse-glimmer/post-training)
| Meta says | We did | Result |
|---|---|---|
| Include reasoning traces in `reasoning_content`; "fine-tuning only on final answers may suppress chain-of-thought" | R1: Spark's code only | Glimmer stopped thinking: 38% |
| Match training data to the behaviour you want at inference | R3: Spark's thinking, written with the manual open; Glimmer trained without the manual | made-up API arguments, 15 crashes; loss stuck ≈ 0.7 (Glimmer could not imitate Spark's style) |
| ≥ ≈ 500 good examples (5-10k for strong domain results) | 154-167 | too few |
| LoRA r 8-32, lr 1e-4 to 3e-4, 2-5 epochs | r 16, lr 1e-4, 2 epochs | in range (not the cause) |

## What it means (hypothesis, then decision pending, user)
- hypothesis: a 4× weaker student learns badly from the strong teacher's long thinking (also in the literature,
  2502.12143). It learns better from its own correct answers (self-distillation / STaR).
- verified (rule-card check 2026-10-30): giving Glimmer the missing information in the prompt helped more than either
  training (A 52 → 68%, R3 48 → 85%), and R3 + card > A + card by ≈ 17 points.
- Proposed next step: Glimmer + card writes its own answers, the referee keeps the correct ones (≥ 300-500), and we
  train with those answers' reasoning in `reasoning_content`. Spark is used only for jobs Glimmer cannot solve, if at all.
