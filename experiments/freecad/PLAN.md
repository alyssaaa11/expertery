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
- Arms (k = 1, one session each): **G** = Glimmer + FreeCAD manual + job; **S** = Spark Open (Baseten) + the same;
  **W** = Muse Wonder (`muse-wonder-1.0`, api.meta.ai, Meta credit) + the same, run **only on the jobs S failed**
  (decision, user 2026-10-29: "if Spark fails, it contacts Wonder to be helped"). **Teacher T** = jobs passed by S or
  by W after S failed. Why: shows whether an escalating teacher team can produce correct FreeCAD answers where Spark
  alone cannot. Privacy note: W sends the job + manual to Meta's API; in a real confidential deployment the escalation
  is switched off or uses a stronger open model; every record says which teacher made it.
- Every failure tagged: API error / crash (tool knowledge: training can fix) vs wrong geometry (general skill).

## Free checks before any paid call
1. Claude hand-writes FreeCAD answers for 5 jobs: all PASS; 2 deliberately wrong answers FAIL.
2. The 30 CadQuery references round-trip through STEP (export → import) and still PASS against themselves.
3. Cheat test: an answer that imports cadquery is refused in the sandbox.
4. Neutral-text scan done and frozen (sha256).

## Where answers run (decision, user 2026-10-29)
Nothing Glimmer or Spark writes runs on the user's Mac: every answer runs in a fresh Modal Sandbox (no network, no
answers inside, FreeCAD 1.1.4), and a separate cloud grader holds the references (SPEC §1-2). The Mac checks below were
done with Claude's hand-written answers only.

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
Revised after the verifier's check (forge-freecad-2026-10-29, READY WITH 3 EDITS), before any paid call:
1. **T < 70% → RUN INVALID for FreeCAD: stay on CadQuery.** No manual fix on exam failures (that would tune the manual on
   the exam). A manual fix is allowed only after a new user approval and is tested on the dry jobs D1-D3 only.
   Why: re-running after fixing the manual on exam failures re-touches the exam and biases the result.
2. G ≤ 60% AND T ≥ 75% AND T − G ≥ 20 points AND ≥ 8 jobs pass in T but not in G → **FreeCAD becomes the factory target**
   (teacher = Spark with Wonder escalation). S alone and W's rescues are reported separately.
3. G ≥ 75% → stay on hard CadQuery jobs.
4. Otherwise (grey zone) → **default: stay on CadQuery.** FreeCAD only if api_error ≥ 60% of G's FAILs AND ≥ 6 jobs pass
   in T but not in G. No re-run of only the differing jobs (selecting on the outcome shrinks the gap by regression).
   Why: the grey zone also decides whether to go above the $30 cap, so it must be a fixed rule, not a judgement call.
5. **Rules 1-4 are evaluated twice: on T and on S alone, and both are reported** (verifier edit A2,
   forge-freecad-escalation-2026-10-29). **If they disagree (FreeCAD target only on T, not on S) → stay on CadQuery**
   (decision, user 2026-10-29, fixed before any result); the report says "FreeCAD target only with Wonder escalation
   (closed API) → stay on CadQuery". Why: choosing after seeing the numbers is the bias this plan avoids elsewhere, and
   if Wonder is needed to pass at all it is no longer "Wonder only on the hardest jobs" (the privacy headline). The report also gives Wonder's share of T's passes. S's INVALID (cut-off) jobs
   are NOT escalated; they stay INVALID. Why: T gives each job two tries by two models against G's one (a pass@2 effect
   that leans towards "FreeCAD target"), and every Wonder rescue sends the job to a closed API, which weakens the
   "private" claim; the user must see when the decision rests on that.
Failure tags: api_error = the answer raised, timed out, hit the memory limit or a PermissionError; wrong_geometry =
built but failed the checker, or `result` was not a Part solid; cut off by the token limit = INVALID (as the baseline).
Honest caveat for the report: FreeCAD's Part API has no counterbore/slot/polar-pattern helpers (CadQuery has them), so
part of a G-vs-S gap measures that the tool is harder to use, which is exactly the kind of difficulty a company tool has.
Manual note (not changed, hash frozen): its line "Part.show() is not available" is inaccurate (it exists headless);
harmless.

## Money
Muse Code build ≈ $1.2-1.5; Glimmer 30 answers ≈ $1 (cold start + run); Spark 30 answers ≈ $0.7; Wonder only on S's
failures ≈ $0.10 each (≈ $0.5-2; worst case 16k output tokens ≈ $0.34 per call); cloud sandboxes + grader ≈ $0.1.
- decision (Claude, 2026-10-29, following the existing accounting where Muse Code's Meta-credit spend is already in the
  Forge total): **Meta credit for W counts INSIDE Forge's $30 (or $35) budget.** Why: one budget total, so the user's
  "go above $30?" decision sees every dollar.
- Caps for the test run: Modal + Baseten **$3.50** (session cap via experiments/common/run_session.sh, Baseten guard)
  + Meta (W) **$3** (`--budget-w`) = **$6.50 worst case**, plus the Muse build.
- Typical total ≈ $4.2 (build ≈ $1.35 + run ≈ $2.8); Forge total after ≈ $24 typical, ≈ $28 worst case.
  The full plan after the test (factory ≈ $5, training ≈ $4, final ≈ $1.5) ≈ $34-35 → needs the user's budget answer.

## After the test
The gap test shows only room. "The factory works across tools" needs a trained result: train the tool with the bigger
gap; for the other tool, run the factory up to verified training data on screen without training.
In parallel (free): market evidence for Impact with the user's two problem frameworks.
