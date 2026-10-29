# Thinking exam pilot (FreeCAD + NDS-1, 40 rules): STOP, too easy for Glimmer

Run: results/thinking-2026-10-29-run2. Session 20:56-21:07 under caffeinate. Launch 1 was lost to Mac idle sleep;
see results/thinking-2026-10-29/LAUNCH_NOTE.md.

## Result (verified: pilot/calls.jsonl, pilot/summary.json)
- 30/30 answers graded; 0 harness errors, 0 INVALID.
- Calibration jobs C1-C3, 3 tries each, judged at 1e-6:

  | Model | Passes |
  |---|---|
  | Glimmer | 8/9 |
  | Spark | 9/9 |

- Glimmer's single miss was C2 (bearing plate): it cut rectangular slots instead of obround ones (rule 9), a 0.2%
  mismatch. At 0.2% Glimmer is 9/9, so the gate says STOP either way (verifier recount).
- Warm-up jobs D1-D2: both models 6/6.
- **Pre-registered gate: Glimmer ≥ 8/9 → STOP, the exam is too easy.** The main run (13 jobs) was not started.

```mermaid
xychart-beta
  title "Pilot calibration jobs (C1-C3), right answers out of 9 (1e-6)"
  x-axis ["Glimmer", "Spark"]
  y-axis "right answers" 0 --> 9
  bar [8, 9]
```

## Speed and cost per answer (main result, verified: pilot/summary.json)
| | Glimmer (Modal A100-80GB) | Spark Open (Baseten) |
|---|---|---|
| median time per answer | 167 s | 18 s |
| prompt tokens | 8,189 | 8,307 |
| output tokens | 4,267 | 3,438 |
| $ per answer | ≈ $0.023 pilot-only, ≈ $0.032 with deploy | ≈ $0.017 (91% of prompt cached; $0.025 if uncached) |

- Glimmer's $ is computed by hand: 11.4 GPU-minutes × $2.50/h = $0.48, over 15 answers, at 8 in parallel.
- WRONG in the first draft, corrected by the verifier: Spark WAS cached. Baseten reports
  usage.prompt_tokens_details.cached_tokens (113,792 of 124,602 = 91%), but runner_fc's cached_tokens_of reads
  usage.cached_tokens and recorded 0. That needs a code fix (fallback + test) before the next paid Spark run.
- **Glimmer is about 9× slower and about 1.4-1.9× dearer per answer** (WRONG first draft said "same cost"). At this
  volume, the "many times cheaper and faster" case is not shown.

## What it means
- verified: Glimmer applies a 40-rule written standard almost perfectly on these jobs. Note: no rule 11-40 fires on
  the pilot jobs, so "ignoring distractors" is shown but "checking thresholds" is NOT tested (verifier). After FreeCAD dictation (93%), this is the second result where Glimmer matches the teacher.
- hypothesis: the remaining gap is not reasoning with rules in the prompt. It may be (a) knowing the company's
  standard WITHOUT the 8k-token prompt, which is what training adds; or (b) much longer, multi-part jobs.
- Money (verifier): Modal ≈ $1.01 for both launches, plus Spark. Forge ≈ $30.4 total.
- Verifier: PASS WITH ISSUES, STOP stands (forge-thinking-pilot-2026-10-29, rubric 7/6/4).
