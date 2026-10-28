# Forge status: START HERE each day

**Summary**: The one page to read first in a new session. Goal, what is proven, what is open, and the next step. Each
claim links to the page that holds its evidence. Update this page at the end of every work session.

**Last updated**: 2026-10-28 ~21:00

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
| **Total** | **≈ $3.6 of $30** | |

## Open questions
1. **B2 cheap-fix test** (Glimmer + manual + coordinate hint, ~$0.70): run it before the factory? Waiting for the user.
2. **Training recipe** for Glimmer LoRA (tool, settings, memory on one GPU): not researched yet.
3. **Practice-job generator:** new part families that don't overlap the 30 held-out exam jobs.
4. Baseten billing: confirm the Spark Open usage is covered by the $100 credit, not the card on file.
5. SAM 3.1: what it would add beyond CadQuery's exact measurement (it may be decoration; not researched).
6. Which companies would pay (market not validated; use the user's two problem frameworks after the hackathon).

## Next step
User decides on B2. Then the factory ([[factory-plan-2026-10-29]]): recipe research (free) → generator spec → Muse Code
builds → teacher run → one training run → final exam on the same 30 held-out jobs.

## Where things are
- GitHub: **https://github.com/alyssaaa11/expertery** (PRIVATE), created and pushed by **Muse Code** on 2026-10-28 21:01 (commit d23b21a, 22 commits). verified: `gh repo view` → PRIVATE; fresh clone + `gitleaks --all` → no leaks; only envsave reference labels (es_…) appear, not key values. Rule (user): publishing and all code are done with Muse Code; README has an honest "How this was built" section. Later wiki commits must be pushed by Muse Code too.
- Project: `~/projects/forge` (README routes everything). First test: `experiments/first-test/` (PLAN.md frozen, jobs,
  checks, runner, run_live.sh). Results: `results/`. Diagrams: `docs/diagrams/`.
- This wiki: decisions [[forge-plan-2026-10-28]], [[factory-plan-2026-10-29]]; facts [[tools-and-services]]; value
  [[value-and-market-2026-10-28]]; Q&A [[forge-questions-2026-10-28]]; lessons [[lessons]].
