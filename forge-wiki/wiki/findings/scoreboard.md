# Forge scoreboard: every measured number on one page

Updated 2026-10-29 21:30. Every number is verified; each line links to its evidence page.

## 1. How accurate is Glimmer already? (we looked for a gap 4 times)
| Test | Glimmer (student) | Spark (teacher) | Gap | Evidence |
|---|---|---|---|---|
| Keel private tool + manual | 97.8% | n/a | none | [[keel-v2-baseline-2026-10-28]] |
| 30 held-out CadQuery jobs, plain | 87% | n/a | n/a | [[bmax-baseline-2026-10-29]] |
| same, with every fair fix (B-max) | **95%** | n/a | n/a | [[bmax-baseline-2026-10-29]] |
| FreeCAD, 30 jobs | 93% (28/30) | 100% (30/30) | 7 pts | [[freecad-gap-2026-10-29]] |
| Thinking exam (40-rule company standard), pilot gate | 89% (8/9) | 100% (9/9) | 11 pts | [[thinking-exam-pilot-2026-10-29]] |

**Finding:** Glimmer is already 87-97% correct whenever the job and the rules are in the prompt. Accuracy is not where
a trained model wins.

## 2. What does that accuracy cost? (this is where the room is)
| Setup | Time per answer | Tokens | Evidence |
|---|---|---|---|
| Glimmer with every fair fix (B-max, 95%) | n/a | **21,300 tokens per correct part** | [[bmax-baseline-2026-10-29]] |
| Glimmer, hint only (88%) | n/a | 10,700 tokens per correct part | [[bmax-baseline-2026-10-29]] |
| Glimmer, thinking exam | **167 s** | 8,189 prompt + 4,267 output | [[thinking-exam-pilot-2026-10-29]] |
| Spark (teacher, Baseten) | 18 s | 8,307 prompt + 3,438 output | [[thinking-exam-pilot-2026-10-29]] |
| **Trained Glimmer, smoke test** (1 job, PASSED the strict referee) | **3 s** | **84 output tokens** | [[training-smoke-2026-10-29]] |

On one job, the trained model took 3 s and 84 output tokens. Glimmer with fixes needs about 21,300 tokens per correct
part. That is about 100-250× fewer tokens, but it is ONE job. It is the number the final exam must confirm on all 30.

## 3. The headline we are going for (goal, user 2026-10-29)
> A trained Glimmer is as correct as Glimmer with every fair fix (95%), but many times cheaper and faster, and private.

What remains to measure, once, on the same frozen 30 CadQuery jobs and with the same referee:
| | B-max Glimmer (measured) | Trained Glimmer (to measure) |
|---|---|---|
| accuracy | 95% | ? (target ≥ 95%) |
| tokens per correct part | 21,300 | ? |
| seconds per answer | ? (to log in the same run) | ? |
| $ per correct part | ? | ? |
| data leaves the company? | prompt goes to the model | no; the rules are inside the model |

## 4. Training results on the factory dev set (Oct 30, 20 jobs × 3, short prompt, strict referee)
| Model | Pass | pass@3 | tokens/correct | Source |
|---|---|---|---|---|
| Untrained Glimmer | 51.7% | 85% | 9.2k | results/dev-base-2026-10-30 |
| Trained R1 (Spark code only) | 38.3% | 75% | 1.7k | results/dev-2026-10-30 |
| Trained R3 (Spark thinking + code) | 48.3% | 85% | 14.8k | results/dev-r3-2026-10-30 |
Details and diagnosis: [[training-experiments-2026-10-30]]. Dev set noise ≈ ±8 points (SE).


## 4. R5 (Nov 1): base Glimmer with and without the rule card, 100 held-out factory jobs (R5D), first try
| Arm | Pass | Crashes | Completion tokens per correct part | Evidence |
|---|---|---|---|---|
| Base Glimmer, short prompt | 62/100 | 12 | 7,637 | [[r5-own-answers-training-2026-11-01]] |
| Base Glimmer + rule card v2 (~420 tokens) | **96/100** | 0 | 3,580 | [[r5-own-answers-training-2026-11-01]] |
| R5-trained Glimmer, no card | pending | | | |
Factory training jobs, first try with card v2: 1,882 / 2,000 = 94.1% (pilot 188/200 + rest 1,694/1,800).
