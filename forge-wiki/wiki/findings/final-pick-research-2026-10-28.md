# Final pick research (Oct 28): Forge vs Gatebreaker vs Team Doctor

**Summary**: The user asked for a `/research` run to settle on one project after removing PhysLoop. claude.ai Research
and GPT-6 Astra both independently pick **Forge**: Muse Spark writes tasks for one unfamiliar tool, with checks
that run, then Glimmer is LoRA-tuned on Modal into a private local agent for that tool. It is Meta-native rather than
new research. The main risk is the test A trap again: Glimmer with the docs or a skills file may already handle the
tool. A day-1 gap test is therefore mandatory. The user has not decided yet.

**Sources**: raw/knowledge/2026-10-28-final-pick-merged.md (scores, spot checks, merged answer),
raw/knowledge/2026-10-28-final-pick-claude.md, -chatgpt.md, -brief.md; work folder
~/Research/2026-10-28-hackathon-final-validation (arXiv sweeps + 22 full texts)

**Last updated**: 2026-10-28

---

## Quality
- verified (merged report): GPT-6 Astra High **92/100** (7/7 spot checks hold, primary share 0.52). claude.ai Fable
  5.1 High **90/100** (6/7 hold; error: "180 configurations" for 2512.08296, which says 260; the most specific
  report). No model downgrade on either side.

## Verdicts (hypothesis unless marked)
- **Forge = pick** ([C] 8.25/10, [G] 81/100). Prior art is dense: NVIDIA CLI training, Nemotron-Terminal 2602.21193
  (verified: Qwen3-32B 3.4% → 27.4% on Terminal-Bench 2.0), ToolACE, Tool-R0, OpenPipe ART, ToolForge (name clash).
  So the pitch is the per-tool private specialist with honest baselines.
- **Strongest cheap baseline Forge must beat**: harness adaptation with no training. Verified: 2607.08938 reached
  89.7% of LLM performance at 4% of the cost. Neither report cited it; the arXiv sweep found it.
- **Gatebreaker alone = no.** Verified: Hacker-Fixer 2606.08960 already does the loop (16% of 1,968 tasks hackable),
  and Muse Spark cheats 0% on ImpossibleBench (2606.12429). Use it inside Forge to attack task checks before training.
- **Team Doctor = fallback.** The problem is the best documented (verified: 2512.08296 shows −39% to −70% on
  sequential planning and 17.2× vs 4.4× error amplification; 2604.22750 shows up to 30× token variance with no
  accuracy gain). But the fixes are crowded (AgentDropout, CATS, topology mutation, Magentic-One, Dream2Discern) and
  Meta's models aren't essential.
- **Meta-essential**: Forge would run with another open model ([G], the accurate view). The Meta case is Apache-2.0
  Glimmer distilled from Spark, Spark as teacher, and Meta's documented single-H100 QLoRA ([C+G]).

## Day-1 gate (hypothesis, merged from both reports)
- Run 2–3 low-exposure tools (hivey CLI is a candidate) with about 60 Spark tasks each. Each task gets a reference
  solution and 2 wrong ones, and only checks that pass the reference and fail both wrong ones are kept. Freeze 40–60
  held-out tasks plus 10–15 hand-written ones.
- Arms: Glimmer no docs; Glimmer + docs; Glimmer + skills file / adapted harness; Spark + docs + verifier.
- Proceed if the best cheap Glimmer arm is at or below 60%, Spark is at least 75% and at least 20 points above it,
  check false-passes are under 5%, and Glimmer QLoRA step + adapter reload works on Modal. Kill the tool if Glimmer +
  docs reaches 80% or more.

## Lesson
- **Run the "cheap fix" baseline before building** (main session, Oct 28). How learned: test A died because agents
  that read the files rejected the lie (70/70). This research then found the same risk for Forge: docs, skills or
  harness adaptation may close the gap without any fine-tuning (2607.08938). Check: in every new plan, list the
  cheapest non-novel fix as an arm of the day-1 test, and kill the idea if that arm already meets the bar. See [[lessons]] and
  HerdShot wiki `findings/test-a` (earlier project), HerdShot wiki `findings/approaches-research-2026-10-28` (earlier project).
