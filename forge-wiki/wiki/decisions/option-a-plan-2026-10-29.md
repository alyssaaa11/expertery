# Option A plan for Oct 29: hidden company standards in past designs (draft)

**Summary**: The plan for tomorrow (Oct 29) after the Keel v2 NO ROOM result. decision (user, 2026-10-28 ~23:40):
Option A, planned for Oct 29, with the user's 4 changes (B-search arm, verify Spark's context limit, blind check of
the hidden rules, B2 CadQuery test in parallel). Tonight: no builds, no Muse Code, no paid calls. Nothing paid runs
tomorrow without the user's yes.

**Sources**: NO ROOM result [[keel-v2-baseline-2026-10-28]]; Keel v2 exam and runner `experiments/keel-exam-v2/`;
B2 plan `experiments/b2-hint/PLAN.md` (frozen); budget [[status]]; lessons [[lessons]].

**Last updated**: 2026-10-28

---

## 1. Idea (hypothesis to test)
Keel v2 showed that a 30B model follows a short, complete manual almost perfectly (97.8%). Real companies also have
knowledge that is **not in the manual**: house standards that live only in past approved designs ("Petrel-2
brackets always get counterbored KF-M5 corner holes 8 mm in", "harness clips always carry a HARNESS-P2 10 mm from
the west edge"). Engineers learn them by looking at earlier parts. Requests then leave them out ("Petrel-2 bracket,
70 x 40 x 5, north wall 30 high"), and the referee checks the full part, standards included.
Forge's claim for Option A: the teacher can read the whole library of past designs; the small model cannot hold it
all, and simple retrieval of a few similar designs may not be enough. Training would bake the standards in.

## 2. What gets built (Muse Code from specs; exam and hidden rules written by Claude)
1. **Hidden standards** (Claude): 8–12 deterministic rules keyed on programme (Petrel-1, Petrel-2), family (BRK, PLT,
   FRM, STD, CLP), material and class. Each rule shows up in ≥ 15 past designs, the rules never contradict each
   other, and none is written in the manual. Kept in a private file the models never see.
2. **Past-design library** (Muse Code, generator from a spec): ~300 approved designs, each = short request text +
   approved Keel program + programme/family tags. Deterministic (seeded), built with Keel 2.1, every design passes
   the referee against itself.
3. **Exam** (Claude): 30 new short requests (15 medium, 15 hard) that need the hidden rules; part numbers and sizes
   disjoint from the library (overlap check script, as before). Self-test 90/90-style (references pass, wrong
   versions fail, including "standard ignored" wrongs) and a blind rebuild with manual + library.
4. **Retrieval for B-search** (Muse Code): simple and deterministic: rank library designs by BM25 on the request
   text plus a bonus for the same programme and family; take the top 5. Same function for every arm that uses it.
5. **Runner change** (Muse Code): the Keel v2 runner (sandbox, caps, k = 3, freeze by hash, NOT_RUN, pass@k) with
   three arms and the library in the prompt; re-frozen and verifier-checked before any paid call.

## 3. Arms (k = 3 samples per job per arm, as in Keel v2)
| Arm | Model | Gets |
|---|---|---|
| B | Glimmer | manual + request |
| B-search | Glimmer | manual + the 5 most similar past designs + request (what a company would try first; fits Glimmer's prompt) |
| C | Spark Open | manual + the whole library (~300 designs) + request, if check 2 shows it fits; otherwise the largest library slice that fits, stated in the plan |

## 4. Decision rules (percent of answers, whole points, first match wins; B-search replaces B for 2 and 3)
0. INVALID > 5% in any arm → RUN INVALID.
1. C pass@3 < 30% → STOP (the teacher cannot work out the standards either).
2. B-search ≥ 80% → NO ROOM (retrieval already solves it; training not needed).
3. C − B-search ≥ 25 points and B-search ≤ 70% → GO to the factory.
4. Otherwise → GREY (the user decides).
Reported: B (manual only) as the floor, C mean pass rate and medium/hard pass@3 with the EASY-ONLY flag, bootstrap CI
of C − B-search, which hidden rules each arm misses.

## 5. Checks before anything paid
1. **Spark Open context limit on Baseten** (user change 2). The 1M-token claim is unverified (it came from the Hugging
   Face card, not tested on Baseten). First free: the Baseten model page/docs and the `/v1/models` metadata. Then, with
   the user's yes, one probe: a ~60k-token prompt (≈ $0.08) and, only if needed, a ~150k-token prompt (≈ $0.19);
   record max context, latency and cost. The library size in arm C follows from this.
2. **Blind helper on the hidden rules** (user change 3): a fresh helper gets only the manual and the past-design
   library (not the rule file) and writes down every standard it can infer. GO only if it recovers all rules; any rule
   it cannot recover is changed or dropped. Then the usual blind rebuild of the 30 exam jobs (manual + library only)
   must reach 30/30.
3. Exam self-test, overlap check, sandbox e2e, freeze by hash, verifier GO (as Keel v2).
4. Pilot: 3 jobs, arm C only.

## 6. In parallel: B2 one-line hint test on CadQuery (user change 4)
- Purpose: know whether Option B (train on CadQuery, proven gap 67% vs 100%) is a real fallback, or whether a one-line
  coordinate hint already closes most of the gap.
- Plan: `experiments/b2-hint/PLAN.md`, frozen and verifier GO on Oct 28, cancelled by the user during the cold start
  (no answers produced). Rules: best = max(B′, B2); ≥ 80 don't build on plain CadQuery, ≤ 75 build, 76–79 grey.
- Open point to settle before running (needs the user): the first-test runner runs model answers **without the
  sandbox** the user asked for on Keel v2. Options: (a) run B2 as frozen (same harness as the first test, answers run
  unsandboxed on the Mac); (b) Muse Code adds the Keel v2 sandbox to a copy of the first-test runner first (~$0.3–0.5,
  re-verify). Recommendation: (b), for the same safety reason as Keel v2.
- Cost ≈ $0.7–1.0 (Modal cold start + 60 Glimmer answers), no Baseten.

## 7. Order and gates for Oct 29
| Step | What | Gate | Paid? |
|---|---|---|---|
| 1 | Hidden rules + library spec + exam draft (Claude) | — | no |
| 2 | Spark context: free docs check, then probe | user yes for the probe | ≈ $0.1–0.3 |
| 3 | Muse Code: library generator + retrieval + runner change | user yes | ≈ $1.5–2.5 (Muse Code has been the biggest cost so far) |
| 4 | Blind helper infers rules; blind rebuild 30/30; self-test; verifier GO | all pass | no |
| 5 | Pilot (3 jobs, C) then main run (B, B-search, C; k = 3) | user yes | ≈ $2.5–4 (C's prompt is long) |
| 6 | B2 CadQuery test (after the sandbox decision) | user yes | ≈ $0.7–1.0 |
Result by evening Oct 29: GO → factory Oct 30–31 (practice requests → teacher answers verified by the referee →
LoRA training), final exam Nov 1, demo Nov 2, video Nov 3, submit Nov 4.

## 8. Budget (user's frame)
Spent ≈ $9.8 of $30. Tomorrow's tests ≈ $4–7 including Muse Code builds; factory ≈ $12 → ≈ $26–29 of $30. Tight:
keep Muse Code sessions small (precise specs, step caps), and stop at any gate that fails.

## 9. Risks
- The teacher may also fail to infer the standards (rule 1 STOP), or retrieval may already be enough (rule 2).
  Both are honest, useful results.
- Glimmer's prompt limit is our serving setting (max-model-len 32768; native 131,072, but an A100-80GB has little
  memory left for a long cache). The "cannot hold the whole library" argument depends on this; the B-search arm keeps
  the comparison fair.
- Time: one day for build + checks + run; the CadQuery fallback (B2) runs the same day.
