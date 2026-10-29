# Thinking exam (FreeCAD, company standard NDS-1): what the models will be asked

Status: prepared and hardened 2026-10-29; not run yet. Source: experiments/thinking/ (commit dc4e800).

## Why this exam
- verified: the first exam was dictation. Every coordinate was in the text, so Glimmer scored 93% (see
  [[freecad-gap-2026-10-29]]).
- decision: here a request gives only the goal. The model must derive every size from 10 company rules (NDS-1),
  as an engineer at a company would.

## How it can't be "too easy" again
1. Every main job chains 2-6 rules. The three 1-2-rule jobs (T1, T3, T4) were dropped.
2. Each job has 2 "typical mistake" versions, such as a forgotten clearance, the wrong inset, or plastic walls on an
   aluminium part. verified: the checker catches all of them (selftest 18/18).
3. **Difficulty gate before the main run (pre-registered).** The pilot gives both models 3 calibration jobs, C1-C3,
   in the same style, 3 times each. These are not exam jobs. If Glimmer gets 8 or 9 of its 9 answers right, the exam
   is too easy: we stop before spending money on the main run and write harder jobs. If Spark gets 4 or fewer of its
   9 right, the exam is too hard or unclear, and we also stop.
4. Two independent blind solves check that each job has exactly one right answer.

## The 13 exam jobs (what the model reads → what it must work out)
| Job | Request (short) | What it must work out | Rules |
|---|---|---|---|
| T2 | plastic clamp plate 100×60×12, M6 socket-head corners, flush | inset 12 → holes at ±38/±18; hole 6.6; counterbore 11 × 6.5 | 3 4 5 |
| T5 | plastic lid for an enclosure, outside 66×46, walls 2.5 | inside 61×41; lip 60.4×40.4, walls 2.5, 4 tall; upside down | 6 10 1 |
| T6 | plastic enclosure for a 70×45 board, M3 holes 3.5 in, 6-tall bosses, inside 25 | inside 71×46, outer 76×51; bosses Ø7.5 at ±31.5/±19 on the floor; pilot Ø2.4 | 6 7 8 |
| T7 | aluminium housing inside 50×30×25, central M3 socket-head screw from inside | walls 4; Ø3.4 through the floor; counterbore 6.5 × 3.5 from the inside | 3 4 6 |
| T8 | plastic enclosure inside 80×50×30, M3 lid-screw bosses | bosses touch both walls (centres ±36.25/±21.25), up to the rim | 6 8 |
| T9 | aluminium flange 90×90×10, 30 pipe, M5 socket-head corners | bore 31; inset 10; Ø5.5 + counterbore 10 × 5.5 | 3 4 5 7 |
| T10 | plastic bracket 60×40×5, M4 slots at ±20, M3 boss 12 tall | slots 4.5 × 14.5; boss Ø7.5 from Z 5 to 17, pilot 2.4 | 8 9 |
| E1 | plastic enclosure inside 90×60×30 + lid bosses + 60×40 board on 6-tall bosses | 8 bosses: 4 board bosses at ±26.5/±16.5 (to Z 8.5) and 4 corner bosses at ±41.25/±26.25 (to the rim) | 6 8 1 |
| E2 | aluminium motor plate 120×80×8, M6 flush corners, Ø40 motor, M4 on a 46 square | inset 12; counterbore 11 × 6.5; bore 41; four Ø4.5 at ±23 | 3 4 5 7 |
| E3 | plastic enclosure inside 60×40×20, two M5 slots in the floor at ±20 | walls 2.5; slots 5.5 × 15.5 along X through the floor only | 6 9 |
| E4 | aluminium housing for a 40×40 module, inside 15 deep, M4 corner screws through the floor | inside 41, walls 4 → outer 49; holes inset 8 from the OUTER edge → ±16.5 | 3 5 6 7 |
| E5 | plastic plate 80×60×6, M4 flush corners, 22 cable gland, two M3 bosses 10 tall | inset 8; counterbore 8 × 4.5; bore 23; bosses Ø7.5 at ±20 from Z 6 to 16 | 3 4 5 7 8 |
| E6 | lid for an ALUMINIUM enclosure inside 70×40, M5 handle hole | plate 78×48×4; lip 69.4×39.4 with walls 4; Ø5.5 hole | 3 6 10 |

Pilot only (not scored): D1 and D2 (warm-up), and C1-C3 (difficulty gate: board enclosure, bearing plate with
slots, lid derived from a board size).

## Decision (pre-registered in experiments/thinking/PLAN.md)
- **Gap found** if Spark scores at least 70%, Spark beats Glimmer by at least 25 points, and at least 4 jobs are
  solved by Spark and missed by Glimmer. Then the factory target is company-standard thinking jobs in FreeCAD.
- **No gap** if Glimmer scores at least 70%. The next test removes the standard from the prompt.
- **Exam invalid** if Spark scores below 60%. We write new jobs.
