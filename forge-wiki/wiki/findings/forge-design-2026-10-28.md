# Forge design (Oct 28): a private AI agent that becomes a pro at your tool

**Summary**: The design of the leading project candidate, Forge, after the user's questions on Oct 28. In the user's
words (decision of meaning, not yet a GO): Forge "trains a private AI agent for your company or tools to become
professional on the usage and better understanding". The design combines three upgrades: (1) tools where reading
the manual isn't enough, (2) learning from real results checked by SAM 3.1, and (5) a small offline Glimmer that
beats big Muse Spark with the manual. The novelty of 2 and 5 hasn't been checked yet. The user has not committed.

**Sources**: this conversation (user, 2026-10-28); [[final-pick-research-2026-10-28]] (research basis);
diagrams ~/agents/.archify/workflow-forge-explained-20261028-115029/forge-explained.html (v1, CLI version) and
~/agents/.archify/workflow-forge-pro-agent-20261028-120925/forge-pro-agent.html (v2, this design; Archify finalize
+ visual-check pass)

**Last updated**: 2026-10-28

---

## What it is, simply
- **Forge is the factory, not the agent.** Give it a tool and it trains a Glimmer model into a private expert on
  that tool, running offline on your own servers, so the data stays in-house.
- **How it learns:** like an apprentice. It practises, sees what really happened, keeps what worked and learns from
  that, instead of only reading the manual.

![[assets/diagrams/forge-pro-agent.png]]

> Current state (2026-10-28 evening): tool **CadQuery** (OpenSCAD backup); teacher **Spark Open on Baseten**; referee = CadQuery exact
> measurement (SAM 3.1 not used so far, open question). The first test found a real gap and the user chose GO. Read [[status]] first.

## How it works (v2 design, hypothesis)
1. **Your tool:** for the demo, a free 3D-design program, OpenSCAD (or CadQuery). Code becomes a 3D part plus a
   rendered picture. No hardware is needed; a printer is an optional final shot. The user owns no 3D tools, but
   both are free installs (`brew install --cask openscad`, `pip install cadquery`).
2. **Practise (Muse Spark = teacher):** it writes practice jobs with measurable requirements (e.g. "a phone stand,
   15° tilt, fits a 75 mm phone") and tries many designs as design code.
3. **See what really happened:** the tool builds the part and its picture. SAM 3.1 finds the features, and code
   measures them (fit, sizes, angle). Each check is tested first: it must pass a correct part and fail
   deliberately wrong ones. Wrong designs are thrown away.
4. **Learn and use (Glimmer = student):** LoRA fine-tune on Modal on correct designs only, producing a private pro
   agent offline.

## Why these upgrades (reasoning)
- **1. Manual isn't enough:** docs say what commands *are*, not what *happens*. Answers the main risk from
  [[final-pick-research-2026-10-28]] that Glimmer + docs, a skills file or an adapted harness already closes the
  gap (2607.08938).
- **2. Real results via SAM 3.1:** fits Push the Frontier ("give a machine a new capability… meet the real world")
  and is a surprising Meta-tooling use (Spark teaches, SAM judges, Glimmer learns). Risk: SAM must add something
  that plain geometry code can't, or it's decoration.
- **5. Student beats teacher:** a memorable result, and the strongest proof that the training matters.
- **Dropped (decision, after the user challenged it):** "a team of teachers aiming at the student's weak spots".
  It's close to ideas the user rejected (Hivey Evolve, group-vs-solo) and already done (Tool-R0 2602.21320, SPADE
  2608.19197, ActiveSaddler).
- **Optional later:** relearn automatically when the tool changes (tool drift).

## Honest position (verified against the research)
- **Novelty is low to medium:** the method exists (NVIDIA CLI training, Nemotron-Terminal 2602.21193, ToolACE,
  Tool-R0, OpenPipe ART). The newer parts are one tool → one private expert automatically, self-tested checks,
  learning from real results, and Meta's teacher→student pairing.
- **Better than HerdShot because the problem can be measured on day 1** (HerdShot: 0/70 infection, a verifier
  already solved it; see HerdShot wiki `findings/test-a` (earlier project)). HerdShot's novelty was in the defense (private ballot, runnable corrections,
  0/4,558 forgeries), but the attack never worked.

## Demo (3 min, hypothesis)
- Before: Glimmer and Spark + manual make parts with wrong sizes, which SAM marks in red.
- Forge runs: jobs, renders, SAM checks, bad designs dropped, training curve.
- After: the same request with Wi-Fi off, and trained Glimmer gets it right (green).
- Scoreboard: accuracy, cost and speed for base Glimmer, Spark + manual and Forge-Glimmer. Optional printed part.

## Day-1 gate (hypothesis)
- About 60 design tasks with measurable requirements; arms Glimmer alone, Glimmer + manual, Spark + manual.
- Proceed if both still fail often, the SAM + code checks reliably catch wrong parts, and Glimmer fine-tune +
  reload works on Modal. If Spark + manual already gets nearly everything right, the tool is too easy: pick a harder one.
- Fallback: Team Doctor (see [[final-pick-research-2026-10-28]]).

## Open questions
- Has "learning a tool from real results checked by SAM" (2) or "relearn on tool change" already been published?
  A free superintel check was offered and not yet run.
- Does the user commit to Forge, and with which main-demo tool?
- Build rule (decision, user, Oct 28): our agents write specs and Muse Code builds the code. Open: which agents write
  the specs (a new Forge swarm, or this coordinator alone). The HerdShot swarm belongs to the earlier project.
