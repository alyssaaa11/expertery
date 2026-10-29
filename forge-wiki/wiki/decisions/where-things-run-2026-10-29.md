# Where things run (rule + map), 2026-10-29

**Summary**: decision (user, 2026-10-29): **the Mac is the office, the cloud is the workshop.** The Mac does planning,
specs, coordination and saving results; **no AI-written code ever runs on it**. Every model, every execution of an AI
answer, all grading and all training run in the cloud (Modal / Baseten). This page is the single map; update it when
something moves.

**Sources**: user messages 2026-10-29 ("glimmer runs in modal not in my mac", "has to build a same box in cloud", "this
is a mess please put an order"); experiments/freecad/SPEC.md §1-2 (cloud box + grader).

**Last updated**: 2026-10-29

---

| Thing | What it is | Where | Notes |
|---|---|---|---|
| Claude | plans, specs, checks, wiki | Mac | office work |
| Verifier | reviews plans and code | Mac | reads files, runs checks of our own code |
| Muse Code | Meta's coding agent that writes the code | Mac (edits files) + Meta cloud (model) | runs only its own offline tests, never AI exam answers |
| Glimmer | student model | Modal GPU | |
| Spark Open | teacher model | Baseten | |
| Running AI answers | build the part from an answer's code | **Modal Sandbox** (fresh per answer, no network, no answers inside) | from 2026-10-29 |
| Grading | compare the part with the reference | **Modal grader** (separate container, holds references) | from 2026-10-29 |
| Training Glimmer | LoRA + merge | Modal GPU | already cloud |
| Coordinator scripts | send jobs, collect results, write logs | Mac | messages and files only |

## History (verified)
- First CadQuery test, Keel exams and the step-2 baseline ran AI answers **on the Mac inside the macOS sandbox**
  (verified each time by the verifier: no network, no home/temp reads, answer key unreadable). Results stay valid; they
  predate the rule.

## Changes this causes (plan)
1. FreeCAD gap test: cloud box + cloud grader (SPEC §1-2), with the verifier.
2. Factory + final exam (CadQuery): reuse the same cloud box (CadQuery image instead of FreeCAD) and grader.
3. Comparability: before the final exam, the cloud grader re-grades the 270 recorded baseline answers' parts and must give
   the same verdicts as the Mac grader (cents, CPU only).
