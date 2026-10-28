# Factory plan (next stage, from Oct 29)

**Summary**: What gets built after the GO decision (user, 2026-10-28 ~19:00), in which order, with which rules and
money. Status: **plan, not started**. Waiting for the user's answer on the B2 cheap-fix test first.

**Sources**: GO decision and B2 proposal in [[first-test-2026-10-28]]; budget in [[status]]; lessons in [[lessons]].

**Last updated**: 2026-10-28

---

## Stages
| # | Stage | Built / run by | Cost (estimate) | When |
|---|---|---|---|---|
| 0 | **B2 cheap-fix test** (Glimmer + manual + coordinate hint, same 30 jobs, rules first): sets the real bar training must beat | runner (needs a small change) | ~$0.70 | Oct 29, if the user agrees |
| 1 | Training-recipe research: LoRA on Glimmer 30B on one GPU (Unsloth / TRL / Meta's post-training guide, memory, settings, serving the adapter with vLLM `--lora`) | me (docs, free) | $0 | Oct 29 |
| 2 | Practice-job generator: ~300 new jobs from part templates with varying sizes and exact references | Muse Code from my spec | ~$0.50 | Oct 29 |
| 3 | Teacher run: Spark Open solves the practice jobs; the referee keeps only correct answers | Baseten | ~$8 | Oct 30 |
| 4 | One LoRA training run on the kept answers | Modal GPU | ~$2–4 | Oct 30 |
| 5 | Final exam: trained Glimmer on the same 30 held-out jobs, plus Glimmer + manual and Spark Open for comparison | Modal + Baseten | ~$0.70–1.50 | Oct 31 |
| 6 | Replay viewer + demo + 3-min video | Muse Code + HyperFrames | ~$0.50 | Nov 1–3 |
| | **Total** | | **~$13–16** (≈ $3.5 already spent → ≈ $17–20 of $30) | |

## Rules (decision)
- **The 30 exam jobs are held out.** No exam job, and no near-copy of an exam family, may appear in practice data.
  Practice part families must be different. Check this with a script before the teacher run.
- Training uses **only referee-confirmed answers** (the same checks.py, overlap ≤ 0.2%).
- Freeze each stage's plan before running it (as PLAN.md did), and get the verifier to check before paid runs.
- Code is built by Muse Code from specs; I write the specs and check the results.
- Ask the user before every paid run; report the real cost after it (Modal billing, Muse Code run.usage, Baseten estimate).
- Success bar for the final exam (to be written into the stage-5 plan before it runs): trained Glimmer clearly above
  max(Glimmer + manual, B2), with a paired test on the 30 jobs.

## Risks
- Training may not help (the main open risk): then report it honestly.
- The B2 hint may close much of the gap, which raises the bar.
- One training run only (budget): run a tiny training smoke test first.
- The time cap: ~7 days to the deadline.
