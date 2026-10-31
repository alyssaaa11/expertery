# Free CadQuery training data on Hugging Face (2026-10-31)

**Summary**: Hugging Face has large text → CadQuery datasets. The best fit is **CAD-Coder** (NeurIPS 2025, Apache-2.0):
8,177 high-quality text→code pairs and 1,503 chain-of-thought examples. Their recipe (SFT, then RL with a geometric
reward) is the same shape as Forge's (referee = geometric reward). Related: [[fireworks-workshop-lessons-2026-10-31]],
[[spark-vs-glimmer-2026-10-31]], [[training-experiments-2026-10-30]].
Method: HF API search (`/api/datasets?search=cadquery|cad-recode|text2cad|cad code|text-to-cad`), then
datasets-server `/first-rows` + `/size` + the README of each candidate. Repeat with the same calls to re-check.

## Candidates (verified 2026-10-31 via HF API)
| Dataset | Rows | Licence | Format | Fit |
|---|---|---|---|---|
| **gudo7208/CAD-Coder** (arXiv 2505.19713) | 250k total; **8,177 high**, 66.5k middle, **1,503 CoT**, 8.8k val | Apache-2.0 (built from Text2CAD, which is CC-BY-NC-SA: licence lineage to disclose) | messages: description → CadQuery code | **best** |
| ThomasTheMaker/TextToCadQuery-2 | 99k | none stated | input text → CadQuery code | good format, unclear licence |
| CADCODER/GenCAD-Code | 163k | not stated | **image** → code | wrong input (image) |
| filapro/cad-recode(-v1.5) | ~1M | CC-BY-NC-4.0 | point cloud → code | wrong input, NC |
| wanhin/text2CAD-reasoning | 96k | none | reasoning → JSON (not CadQuery) | no |
| sanjuhs/cadforge-cadquery-agentic-traces | small | MIT | repair traces | too small |
| rumike7/cadquery-creating-basic-2d-and-3d-forms | 16k | MIT | bare scripts, no text | no |

## Differences from Forge jobs (verified from the first rows)
- CAD-Coder descriptions are DeepCAD sketch-and-extrude steps in normalised units ("Euler angles…, line from (0,0) to
  (0.75,0)…, scale 0.75, extrude 0.0109"). Forge jobs are dimensioned mm parts with coordinates. Style shift: real risk.
- Most rows are code only (no reasoning). Our R1 showed that code-only SFT makes Glimmer stop thinking (38%). Keep the
  1,503 CoT rows + our own reasoning rows in the mix, and check thinking on dev before the exam.
- CadQuery version unknown: run a sample in the cloud box (CadQuery 2.8) before training; drop rows that fail.

## Proposed use (hypothesis, decision pending, user)
SFT on CAD-Coder high (8,177) + CoT (1,503) + Forge factory rows, free on Fireworks; dev check (≈ $1.5) before the
exam (≈ $2-3). Data and training are $0, so this fits the ≈ $16 left.
