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

## Hardening (2026-10-29, after the user's request "you can't fail another experiment because the jobs were easy")
- decision: T1, T3 and T4 were dropped. Each needed only 1-2 rules, so they were close to dictation. Six expert jobs
  were added, each chaining 3-6 rules: E1, enclosure with board bosses and lid bosses; E2, motor adapter plate; E3,
  enclosure with floor slots; E4, aluminium housing, where corner holes are inset from the OUTER edges; E5, plate with
  counterbores, gland bore and bosses; E6, aluminium lid. The main exam is 13 jobs: T2, T5-T10, E1-E6.
- verified: selftest 18/18 OK, with every wrong version caught (13 main + D1, D2 + C1-C3).
- **Pilot difficulty gate (pre-registered).** The pilot runs G and S at k = 3 on D1, D2 and three calibration jobs,
  C1-C3. These are the same expert style but are NOT exam jobs, so stopping on them never tunes the exam.
  - G passes ≥ 8 of 9 calibration answers → the exam is probably too easy → STOP before the main run. Write harder
    jobs; no main money is spent.
  - S passes ≤ 4 of 9 → too hard or ambiguous → STOP.
  - Otherwise GO.
- Rule 2 keeps ≥ 4 win jobs (now out of 13).
- Money: 13 × 3 × 2 = 78 main answers + 30 pilot answers + Wonder ≤ $3 cap. Typical ≈ $3-4.5.
- verified (2026-10-29, second blind Sonnet solve of E1-E6 and C1-C3, from the standard and the texts only): all
  geometry equals the references, and nothing is physically impossible. Two flagged forks were fixed in STANDARDS.md
  (geometry unchanged, selftest 18/18):
  - rule 4 now says screws not called socket-head get a plain hole (E2's M4);
  - rule 7 now covers any part given by its outside size: cable gland, motor body and shaft housing (E5, E2, C2).
  - STANDARDS.md sha256 = 162f9fa119574b92575f696e55d5fa1010363d32d1f9b1ed7fd63fec9b914f0e (the runner's frozen
    constant must equal this).
