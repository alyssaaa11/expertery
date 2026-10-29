# FreeCAD gap test: is there a "teacher can, student can't" gap on a harder, less common tool? (DRAFT)

Status: DRAFT by Claude, 2026-10-29, from the user's idea (the product is the factory; show it on a tool where Glimmer is
weak) and the other Claude pane's validation advice (hivey m1793292625890-145). Needs: the user's yes + budget answer,
free checks, verifier check, then Muse Code (runner adapter + sandbox) and the paid run. Time box: ≤ 3 h, ≤ $3.50.

## Question
On the same 30 held-out jobs, written as neutral text, does Glimmer + a FreeCAD manual fail much more often than
Spark Open + the same manual? If so, FreeCAD is the factory's training target (a bigger, more visible gain).

## Design (decisions)
- Same 30 job texts (experiments/first-test/jobs.py), scanned for CadQuery words (Workplane, ">Z" selectors, box()
  centring hints) and made neutral before freezing. Why: CadQuery words would push the model toward CadQuery.
- Same references and referee: answers are FreeCAD Python that must export the part to a fixed STEP path; the runner
  reads ONLY that path and scores it with experiments/first-test/checks.py at 0.2% (same yardstick as the baseline),
  1e-6 also reported. Why: no new exam = no new exam bugs.
- FreeCAD manual written by Claude, same size and structure as experiments/first-test/manual.md, frozen by sha256
  before any run. Why: otherwise the result can be blamed on the manual.
- Sandbox: the Keel v2-style profile + FreeCAD's own install readable; `import cadquery` / `OCP` blocked inside the
  answer run. Why: FreeCAD can run CadQuery; Glimmer could cheat by writing CadQuery.
- Arms (k = 1, one session each): **G** = Glimmer + FreeCAD manual + job; **S** = Spark Open (Baseten) + the same.
- Every failure tagged: API error / crash (tool knowledge: training can fix) vs wrong geometry (general skill).

## Free checks before any paid call
1. Claude hand-writes FreeCAD answers for 5 jobs: all PASS; 2 deliberately wrong answers FAIL.
2. The 30 CadQuery references round-trip through STEP (export → import) and still PASS against themselves.
3. Cheat test: an answer that imports cadquery is refused in the sandbox.
4. Neutral-text scan done and frozen (sha256).

## Free checks done (verified 2026-10-29, Claude; check commands run ad hoc in Claude's temp folder, not project code)
- FreeCAD 1.1.4 installed (`brew install --cask freecad`); headless `freecadcmd` builds a part and exports STEP in ~4 s
  (0.2 s warm); FreeCAD's own Python is 3.11.14 and has **no cadquery / OCP**.
- A FreeCAD part scored against a CadQuery reference: PASS at 0.2% and at 1e-6, mismatch 0.0.
- Hand-written FreeCAD answers (experiments/freecad/hand/): M1, M6, M10, H6, H13 all PASS at 0.2% and 1e-6;
  M1_wrong (hole 1 mm off) and H13_wrong (countersink too big) FAIL at both.
- The 30 CadQuery references survive a STEP round trip: 30/30 at 0.2% and 1e-6.
- Neutral-text scan of the 30 job texts (workplane, centered, cadquery, selector, >Z, sketch, extrude, cbore, csk…): none.
- Sandbox: freecadcmd runs under `env -i HOME=<scratch>` + sandbox-exec with experiments/freecad/sandbox_fc.reference.sb
  (Keel-v2 style, home + temp reads denied, writes only to scratch); inside it `import cadquery` → ModuleNotFoundError and
  reading experiments/first-test/expected.json → PermissionError.
- Manual: experiments/freecad/manual.md, an excerpt of FreeCAD's official "Topological data scripting" guide + the
  built-in Part `help()` text, 21,640 chars (CadQuery manual 21,696). 27 of its 30 official code examples run as
  written (3 doc quirks: a placeholder `myShape`, a missing `from math import radians`, one example OCC error); kept
  authentic. **Frozen: sha256 865ab9af45eb2fb554f97155fa8f3cf44f92d54973437a1f94c78d67cdc89bb6.**

## Decision rule (pre-registered; reuses the Oct 28 day-1 gate; n = 30 at k = 1 ≈ ±17 points, act only on clear margins)
1. S < 70% → INVALID: fix the manual once, re-run once.
2. G ≤ 60% AND S ≥ 75% AND S − G ≥ 20 points AND ≥ 8 jobs pass in S but not in G → **FreeCAD becomes the factory target**.
3. G ≥ 75% → stay on hard CadQuery jobs.
4. Otherwise (grey zone) → re-run only the differing jobs at k = 3, or decide by the API-error share, with the user.

## Money
Muse Code runner adapter + sandbox ≈ $1-1.2; Glimmer 30 answers ≈ $1 (cold start + run); Spark 30 answers ≈ $0.7.
≈ $3 total, cap $3.50 (session cap via experiments/common/run_session.sh, Baseten guard). Forge total after: ≈ $22.7;
the full plan after the test (factory ≈ $5, training ≈ $4, final ≈ $1.5) ≈ $33-34 → needs the user's budget answer.

## After the test
The gap test shows only room. "The factory works across tools" needs a trained result: train the tool with the bigger
gap; for the other tool, run the factory up to verified training data on screen without training.
In parallel (free): market evidence for Impact with the user's two problem frameworks.
