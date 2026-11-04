# Competitor: MARKOV (Muse Glimmer GRPO tool-calling), 2026-11-03

## Goal
Assess another Meta Muse hackathon entry that fine-tunes the same student model (Glimmer 30B).

## Relevant findings
- verified: MARKOV = GRPO + LoRA on Glimmer 30B (FP4, Modal RTX PRO 6000), trained on 10k trajectories from
  PersonalAILab/AFM-WebAgent-RL-Dataset. Reward has 4 terms: channel format, answer shape, ground truth, and a
  Muse Wonder LLM judge. Spark 1.3 was used only as the coding assistant. (source: github.com/pranav-upd/Muse-MARKOV README, fetched 2026-11-03)
- verified: headline is BFCL v4, only the "multiple" + "parallel" categories, n=200, seed 7: 0.63 → 0.725 (+9.5 pts),
  discordant pairs 26/7, McNemar p≈0.0013, bootstrap 95% CI [+0.04, +0.15]. GPQA Diamond 0.414 → 0.434, which the
  author calls noise. (source: README Results)
- verified: the p-value checks out. Continuity-corrected McNemar (|26−7|−1)²/33 = 9.8 → p≈0.002; exact ≈0.001. (method: hand calc)
- verified: the 2:49 video (9 views) is mostly narration over slides. Its demo runs GSM8K with n=5 and ends with "not
  much difference... considered noise", so the demo never shows the BFCL result. (source: ~/transcripts/MARKOV*.txt, yt-dlp metadata)
- verified: repo created 2026-10-29, 18 commits, 0 stars. Contains starter.py, eval.py, eval_out.zip. (source: gh api)
- hypothesis: picking 2 of the BFCL categories could be cherry-picking. The README lists "score remaining categories" as a todo. Not checked.

## Open questions
- Do the other BFCL categories (simple, live, multi-turn) hold the gain? Is the raw eval_out.zip consistent with the table?

## Next step
None for Forge. Takeaway for our pitch: pair every number with n, a CI and a paired test the way MARKOV does, and make sure the
live demo shows the headline result, not a noisy n=5 run.
