# Thinking-jobs gap test (FreeCAD + company standard) — DRAFT, needs verifier + the user's yes

Status: written by Claude 2026-10-29 after the FreeCAD gap test (Glimmer 93%, Spark 100%: the first exam gives every
coordinate, so it tests dictation, not design reasoning; user: "prepare the next experiment for thinking jobs using
free cad").

## Question
When a request is written like real company work (a goal + the company's design standard, no coordinates), does
Spark Open clearly beat Glimmer? If yes, that is the gap the factory trains away: a private Glimmer that applies the
company's standard as well as the teacher.

## Design (decisions)
- Tool: FreeCAD 1.1.4 (decision, user 2026-10-29). Same cloud box, grader, manual (sha 865ab9af…) and runner as the
  FreeCAD gap test.
- Exam: `thinking_jobs.py`, 10 requests (T1-T5 medium, T6-T10 hard) + 2 dry jobs (D1, D2), written by Claude; the
  standard `STANDARDS.md` (NDS-1, 10 rules: placement, material, clearance holes, counterbores, corner holes, walls,
  fit clearance, bosses, slots, lids). Each answer needs 2-5 derived numbers (e.g. T8: walls 2.5 from rule 6, boss
  diameter 7.5 and pilot 2.4 from rule 8, boss centres 3.75 from the inner walls).
- Self-test (verified, `selftest.py`, 2026-10-29): 12/12 references valid single solids; every wrong version (a
  typical reasoning mistake: a rule ignored or misapplied) is caught at 0.2%. Two first drafts were not catchable at
  0.2% (T7 counterbore from the wrong side, T10 pilot into the plate: < 0.2% volume) and were replaced before freezing.
- FreeCAD feasibility (verified): hand/T6.py and hand/T8.py PASS against the references through checks.py; T8_wrong
  (boss centres from the wall corner) FAILs (mismatch 5.3%).
- Ambiguity check: an independent blind solve from STANDARDS.md + the request texts only (results recorded below
  before freezing). Any job a careful engineer can read two ways is fixed before the run.
  - verified (2026-10-29, Sonnet subagent, blind: STANDARDS.md + request texts only, no references): 12/12 jobs
    give ONE geometry, all equal to the references. Four wordings it ranked as possible misreadings were tightened in
    STANDARDS.md (geometry unchanged): a stated boss height is measured from the surface it stands on (T6, T10);
    "inside space" depth or height is from the floor top to the rim (T7, T8, D2); lid-screw bosses are one in each of
    the four inner corners (T8); 0.5 per side = +1.0 per size or diameter, and the lip is 0.6 smaller (T3, T5, T6, T9).
    selftest.py re-run after the edit: 12/12 OK, every wrong version caught ("BAD: none").
- Prompt (arm B layout): system = the FreeCAD system prompt; user = "Here is the FreeCAD manual. Use it." + manual +
  "Here is the company design standard. Apply it." + STANDARDS.md + request. The standard is in the prompt, so the
  test is about APPLYING rules, not knowing them (the trained model's later advantage is not needing them in the prompt).
- Arms: G = Glimmer, S = Spark Open, k = 3 each (n = 10 jobs is small; 3 answers per job halve the noise); W = Wonder,
  one try, only on S's FAILED answers (per job and sample). Teacher T = S ∪ W rescues.
- Referee: the same grader, 0.2% verdict (1e-6 recorded). Pilot D1-D2 for G and S before GO.

## Decision rule (pre-registered; rates = PASS ÷ (PASS + FAIL) over all answers of an arm)
0. Harness or INVALID > 5% in any arm → RUN INVALID (fix, re-run).
1. S < 60% → the exam is probably ambiguous or too hard even for the teacher → INVALID for a factory decision; inspect
   S's failures, write NEW jobs (never edit and re-run the same jobs; that would tune on the exam).
2. S ≥ 70% AND S − G ≥ 25 points AND ≥ 4 jobs where S passes ≥ 2 of 3 and G passes ≤ 1 of 3 → **gap found: the
   factory target is company-standard thinking jobs in FreeCAD.**
3. G ≥ 70% → no gap: Glimmer applies a written standard well; next step = the same jobs WITHOUT the standard in the
   prompt (does Glimmer need it? that is the privacy/cost case for training), as a separate pre-registered test.
4. Otherwise (grey) → no factory claim; report and decide with the user.
Rules 1-4 are evaluated on S and on T; if they disagree, the S-only decision governs (user rule 2026-10-29: a result
that needs Wonder is not "Wonder only on the hardest jobs"). Wonder's share of T's passes is reported (privacy headline).

## Money (estimate)
Muse Code (runner generalisation + report fixes) ≈ $0.7; Glimmer 30 answers + cold start ≈ $1.0; Spark 30 ≈ $0.4;
Wonder ≤ $3 cap (≈ $0.10 per rescue); box + grader ≈ $0.05. Typical ≈ $2.5-3.5. Forge spent ≈ $25.5 before; the user
allows going above $30 (2026-10-29: "u can spend more"), within the $35 agreed for the FreeCAD work.
