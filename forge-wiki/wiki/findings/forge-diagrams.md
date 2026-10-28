# Forge diagrams: all five Archify diagrams in one place

**Summary**: Every diagram made for the Forge project on 2026-10-28, in reading order: what Forge is, the design, who
uses it, what to prepare, and the day-by-day plan. Each shows as a picture here. The interactive version (zoom, dark
mode, export) is the `.html` file next to it; open it in a browser.

**Sources**: Archify workflow diagrams made in the main session on 2026-10-28. Originals and their check receipts are
in `~/agents/.archify/workflow-forge-*`. All five passed `finalize --quality showcase` and `visual-check`.

**Last updated**: 2026-10-28

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
