# Forge status: START HERE each day

**Summary**: The one page to read first in a new session. Goal, what is proven, what is open, and the next step. Each
claim links to the page that holds its evidence. Update this page at the end of every work session.

**Last updated**: 2026-10-28 ~23:35

---

## Goal
Meta hackathon (Indie track, Push the Frontier), submit by **Nov 4, 18:00 CET**. Forge trains a small, private, offline
model (Muse **Glimmer** 30B) to become a pro at one company tool by learning from practice that a big teacher (Muse
**Spark Open**) solved and an automatic referee (**CadQuery** measurement) confirmed. Demo tool: CadQuery.
Budget **$30 max** for the whole project (user), so credits stay free for another project if Forge fails.

## Proven so far (verified)
- **There is a real gap** ([[first-test-2026-10-28]]). On 30 held-out jobs: Spark Open + manual 30/30, Glimmer + manual
  20/30 (67%), Glimmer alone 16/30. On the jobs where they differ, the teacher won 10 of 10 (McNemar p = 0.002). The
  pre-registered rule said **grey zone** (Glimmer + manual is above the 60% GO ceiling). **User decision: GO**, because 6
  of Glimmer + manual's 10 failures are badly wrong parts and it is unstable.
- **Caveat** (same page): 3 of those 10 failures are position-only (right shape, wrong place). Shape-only score would be
  77%. A one-line coordinate hint might fix them without training (cheap-fix risk). The B2 test is proposed.
- The whole pipeline works end to end: Glimmer on Modal, Spark Open on Baseten, the CadQuery referee, the runner built
  by Muse Code, the report ([[glimmer-test-1-2026-10-28]], [[first-test-2026-10-28]]).
- The exam is trustworthy: referee self-test 33/33, blind rebuild 33/33, independent verifier audit + re-check GO
  (`~/agents/verifier/reports/forge-2026-10-28.md`).

## Money (verified where marked)
| Credit | Spent on Forge | Source |
|---|---|---|
| Modal | $1.65 (Glimmer test 1, dry run, main run) | `modal billing summary` 2026-10-28 ~18:45 |
| Meta | ~$1.13 (three Muse Code sessions: build, fixes, publish ~$0.11) | run.usage events in `results/muse-*.jsonl` × list prices |
| Baseten | ~$0.85 (estimate: dry + main + 2 probe calls) | runner token estimate; the dashboard showed $0.00, credit not visible |
| **Total** | **≈ $9.8 of $30** (Meta/Muse Code ≈ $5.7; Modal $2.22 metered, covered by credits; Baseten ≈ $1.85) | |

## Quillon Orbital Works (verified 2026-10-28 ~22:45)
- decision (user): fictional space company with a realistic private tool. Keel 2.1 in `company/` (built by Muse
  Code: v1 ~$0.40, v2 ~$0.80, fixes ~$0.20): materials, flight class, countersinks, wall holes, company mounts,
  mirror, FRM centre datum; order-free build. Company self-test 92/92. Offline dashboard opens in Chrome; request
  statuses are labelled sample data.
- Held-out exam `experiments/keel-exam-v2/` (v1 exam in keel-exam/ is history): 30 jobs by Claude, referee 1e-6,
  self-test 90/90, blind rebuild 30/30. Verifier: v1 NO-GO with 3 fixes (all applied); v2 exam GO; runner + sandbox GO for pilot AND main run at 74ae975
  (~/agents/verifier/reports/forge-keel-v2-exam-2026-10-28.md). PLAN frozen by sha256 (9 files). Rule 1 = C pass@3 < 30% (user).
- Next paid step (user yes needed after verifier GO): baseline B (Glimmer + manual) vs C (Spark Open + manual),
  ~$3–4 (k=3), caps Modal 2.50 / Baseten 4.00; rules in keel-exam-v2/PLAN.md (INVALID gate, STOP C pass@3<30%, NO ROOM
  B≥80%, GO C−B≥25 & B≤70%, else GREY). After the run: check no FAIL reason contains 'harness' or 'PermissionError'.
  The runner change is done by Muse Code from PLAN section 4b.

## Open questions
0. decision (user, 2026-10-28 ~22:30): the private tool belongs to a **fictional space company, Quillon Orbital Works** (satellite structural parts; name checked by web search, no real company found). Its private tool is **Keel** (compiles to CadQuery, so the same referee works). The user also wants an **internal company dashboard** like a real company. Draft spec: `company/SPEC.md`, waiting for the user's review, then one Muse Code build (~$0.50–0.80, needs approval). B2 was cancelled by the user earlier (21:50) and is kept as history in experiments/b2-hint/.
2. **Training recipe** for Glimmer LoRA (tool, settings, memory on one GPU): not researched yet.
3. **Practice-job generator:** new part families that don't overlap the 30 held-out exam jobs.
4. Baseten billing: confirm the Spark Open usage is covered by the $100 credit, not the card on file.
5. SAM 3.1: what it would add beyond CadQuery's exact measurement (it may be decoration; not researched).
6. Which companies would pay (market not validated; use the user's two problem frameworks after the hackathon).

## Next step (Oct 29)
- verified (2026-10-28 23:30): Keel v2 baseline = **NO ROOM**: Glimmer + manual 97.8%, Spark Open 100%
  ([[keel-v2-baseline-2026-10-28]]). A short complete manual is enough for a 30B model; "private" alone makes no gap.
- decision (user, ~23:40): **Option A tomorrow** = hidden company standards that live only in ~300 past designs, with
  a B-search arm (Glimmer + manual + 5 most similar designs), Spark context check, blind check of the hidden rules,
  and the B2 CadQuery hint test in parallel as the fallback check. Plan: [[option-a-plan-2026-10-29]].
- Tonight: no builds, no Muse Code, no paid calls. Tomorrow: every paid step waits for the user's yes.

## Where things are
- GitHub: **https://github.com/alyssaaa11/expertery** (PRIVATE), created and pushed by **Muse Code** on 2026-10-28 21:01 (commit d23b21a, 22 commits). verified: `gh repo view` → PRIVATE; fresh clone + `gitleaks --all` → no leaks; only envsave reference labels (es_…) appear, not key values. Rule (user): publishing and all code are done with Muse Code; README has an honest "How this was built" section. Later wiki commits must be pushed by Muse Code too.
- Project: `~/projects/forge` (README routes everything). First test: `experiments/first-test/` (PLAN.md frozen, jobs,
  checks, runner, run_live.sh). Results: `results/`. Diagrams: `docs/diagrams/`.
- This wiki: decisions [[forge-plan-2026-10-28]], [[factory-plan-2026-10-29]]; facts [[tools-and-services]]; value
  [[value-and-market-2026-10-28]]; Q&A [[forge-questions-2026-10-28]]; lessons [[lessons]].
