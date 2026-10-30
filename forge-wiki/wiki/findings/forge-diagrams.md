# Forge diagrams: all Archify diagrams in one place

**Summary**: Every diagram made for the Forge project on 2026-10-28, in reading order: what Forge is, the design, who
uses it, what to prepare, and the day-by-day plan. Each shows as a picture here. The interactive version (zoom, dark
mode, export) is the `.html` file next to it; open it in a browser.

**Sources**: Archify workflow diagrams made in the main session on 2026-10-28. Originals and their check receipts are
in `~/agents/.archify/workflow-forge-*`. All five passed `finalize --quality showcase` and `visual-check`.

**Last updated**: 2026-10-30

---

## 1. What Forge is (v1, simple)
![[assets/diagrams/forge-explained.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-explained.html`. This early version uses a command-line tool as the example; the
current design uses OpenSCAD (see 2).

## 2. The design: a private agent that becomes a pro at your tool (v2)
![[assets/diagrams/forge-pro-agent.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-pro-agent.html`. Explained in [[forge-design-2026-10-28]].

## 3. Use cases: who gets a private pro agent, and why
![[assets/diagrams/forge-use-cases.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-use-cases.html`. Only the top row (OpenSCAD demo) is built. The other rows
are a hypothesis for the pitch. See [[forge-plan-2026-10-28]].

## 4. Preparation checklist before running anything
![[assets/diagrams/forge-prepare.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-prepare.html`. Status shown was checked on 2026-10-28 12:40. Recheck it
before relying on it. See [[forge-plan-2026-10-28]].

## 5. Plan: Oct 28 to Nov 4, with one stop-or-go test
![[assets/diagrams/forge-plan.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-plan.html`. See [[forge-plan-2026-10-28]].

## 6. The factory: what a company installs, and what leaves it
![[assets/diagrams/forge-factory.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-factory.html`. Answers the user's question "if 2 companies use it, how is it
private?" (2026-10-28). Each company runs its own copy, with the same free Glimmer plus its own add-on file. Only
practice jobs with fake data go to Muse Spark. The zero-cloud option is Spark Open as the teacher (hypothesis: not
tested).

## 7. Final plan (current; replaces 5 for dates and money)
![[assets/diagrams/forge-final-plan.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-final-plan.html`. It shows the $30 cap and the stages: free prep →
first test (~$2, 30 jobs, 3 contestants) → STOP (~$27 left) or GO → Spark Open teaches (Baseten) → one LoRA run
(Modal) → scoreboard → video + submit on Nov 4. Diagram 5 is out of date (60 jobs, OpenSCAD, $12 training).

## 8. Training + final exam plan (current, Oct 30; replaces 7)
![[assets/diagrams/forge-training-exam-plan.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-training-exam-plan.html`. Steps 0-7 of `experiments/final/PLAN.md`:
Muse build → fairness check → factory (Spark teacher + strict referee) → LoRA training → dev check (≥ 80%) → final
exam with bars a-d. Prepared, not run. Step 6a (finish B-max to 30 jobs) was added after this picture was drawn.

## 9. How training changes Glimmer's weights (LoRA)
![[assets/diagrams/forge-how-training.png]]
Interactive: `forge-wiki/wiki/assets/diagrams/forge-how-training.html`. One training step, repeated: example → guess →
loss → gradient → nudge only the patch A, B → merge. Explained in [[how-training-changes-weights-2026-10-30]].

## 10. How Glimmer learns (simple words)
![[assets/diagrams/forge-simple-how-glimmer-learns.png]]
Same as 9 without technical words. Word list in [[forge-in-simple-words]].

## 11. The plan from today to the exam (simple words)
![[assets/diagrams/forge-simple-plan.png]]
Same as 8 without technical words.

