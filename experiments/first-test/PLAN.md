# First test: is Forge needed? (plan, written before any run)

Status: **approved by the user (2026-10-28 ~17:20); revised after the verifier audit (~/agents/verifier/reports/forge-2026-10-28.md), user approved the fixes (~18:40).** Free prep done: self-test 33/33, blind rebuild 33/33. Nothing in this file runs until the user says go. After approval
the plan is frozen: no prompt, job, check or rule changes during the run. A change means a new, separately approved
run.

## 1. The question
On CadQuery jobs of medium and hard difficulty, does small Glimmer fail where big Spark often succeeds, **even when
Glimmer gets the manual**?
- Jobs: **30 = 15 medium + 15 hard** (user, 2026-10-28). No easy jobs: one cube already passed, and the dry run keeps 1 easy job as a plumbing check.
- If yes, there is a gap Forge can close by training → GO.
- If Glimmer + manual is already good, training adds nothing → STOP (that is how HerdShot died).
- If Spark also almost always fails, it can't teach → switch tool (OpenSCAD) or STOP.

## 2. Mistakes from HerdShot this plan avoids
| HerdShot mistake | Guard here |
|---|---|
| Identical agents on the same task: one shared mistake hit them all, so the result meant nothing | 30 **different** jobs; every call is a fresh conversation; no model ever sees another answer; one attempt per job per contestant |
| The test did not contain the real mechanism | The jobs need parts placed relative to each other (the exact mistake seen in Glimmer test 1) |
| The free fix was not tested first | "Glimmer + manual" is a contestant |
| Thinking ate the token limit, empty answers counted as failures | Token cap 16,000 (was 8,000; raised after the verifier audit); a cut-off answer is **INVALID**, counted apart, and must stay ≤ 5% |
| Small changes during the run cost more money | Everything is frozen before the run; a 3-job dry run checks the plumbing first |
| Unclear prompt → every model fails the same way (my bracket wording in Glimmer test 1) | Every job text is rebuilt blind by an independent reader before the run (step 4.2) |

## 3. Contestants (3 arms)
| Arm | Model | Gets the manual? |
|---|---|---|
| A | Glimmer 30B on Modal (`forge-glimmer`) | no |
| B | Glimmer 30B on Modal | yes |
| C | Muse **Spark Open** on Baseten (`meta-models/muse-spark-open-1026`, envsave `BASETEN_API_KEY`) | yes |
- The same 30 jobs and the same instructions for all. The "manual" is one fixed file, `manual.md` (CadQuery's own
  docs: Workplane API and selectors, ~5,600 tokens measured in the dry run).
- Settings (revised 2026-10-28 after the verifier audit, user approved): **temperature 1.0, top_p 0.95, top_k 64 for both models**
  (Meta's recommended Glimmer sampling, dev.meta.ai/docs/muse-glimmer/vllm; a 2-call probe on 2026-10-28 showed Baseten
  accepts all three for Spark Open, HTTP 200), **max output 16,000 tokens**, one attempt per job (pass@1). Glimmer's native context is 131,072 tokens; Forge
  serves it with `--max-model-len 32768` (was 16,384, which is our setting, not the model's limit).

## 4. Before the run (all free: no Meta model, no GPU)
1. **30 jobs** in `jobs.json`: 15 medium, 15 hard, all different. Each has the job text, exact
   measurements, one correct reference solution, and 2 deliberately wrong versions.
   - Medium: 2–3 parts placed relative to each other (L-bracket, T-slot, box with a lid lip, stepped shaft).
   - Hard: several features with exact relations (hinge with pin hole, enclosure with screw bosses, gear-like
     cut-outs, a bracket that must clear a given bolt).
2. **Blind rebuild:** a fresh, independent reader (a new agent that never saw the reference) builds each part from the
   text only. If its part doesn't match the reference, the text is unclear and gets rewritten. This stops my wording
   from causing failures.
3. **Check self-test:** each job's check (one valid solid, bounding box ±0.1 mm, volume and area ±1%, centre of mass ±0.3 mm,
   and **overlap mismatch ≤ 0.2%**: the volume in the answer XOR the reference) must pass the reference and fail both
   wrong versions. Result 2026-10-28: 33/33 after adding the overlap check (without it, 17 wrong parts passed). A check that fails this is fixed before the run.
4. **Dry run on 3 jobs** (1 easy, 1 medium, 1 hard, not among the 30) on all arms, to test the plumbing only. It is excluded from the results.

## 5. Exact words sent to the models
System message (all arms):
> You write CadQuery Python code. Units are millimetres. Assign the final solid to a variable named `result`. Reply
> with exactly one Python code block and nothing else.

Arms B and C add, before the job:
> Here is the CadQuery manual. Use it.
> `<contents of manual.md>`

User message (all arms): the job text from `jobs.json`, unchanged. Example (medium):
> An L-bracket. Base plate: 40 mm along X, 20 mm along Y, 3 mm thick, bottom face at Z = 0, centred on X = 0, Y = 0.
> Wall: 40 mm along X, 3 mm along Y, total height 20 mm from Z = 0, standing on top of the base so that its back face
> is flush with the base's back edge at Y = +10. Two 5 mm through holes in the base, at X = −15 and X = +15, Y = −1.5.

## 6. How an answer is scored
Code block → run in CadQuery on the Mac (time limit 60 s) → measure → compare with the job's check.
- **PASS:** all checks within tolerance.
- **FAIL:** wrong shape, code error, or no `result`.
- **INVALID:** cut off by the token limit, API/network error, or empty reply. Not counted as FAIL; reported apart.

## 7. Decision rules (fixed now)
The run counts only if: INVALID ≤ 5% per arm, and all 30 checks passed the self-test.

Pass rate = PASS ÷ (PASS + FAIL), in **whole percentage points** (rounded); INVALID answers are reported apart.
Rules are applied **in this order; the first that matches decides** (revised 2026-10-28 after the verifier audit found
the old rules contradicted each other; user approved; GO bar raised from 20 to 25 points because 20 points on 30 jobs
is weak evidence):
| Order | Result | Decision |
|---|---|---|
| 1 | B (Glimmer + manual) ≥ 80% | **STOP**: the manual is enough, Forge not needed for CadQuery |
| 2 | C (Spark Open) < 20% | **Spark can't teach**: one OpenSCAD run (new approval) or STOP |
| 3 | B ≤ 60% **and** C ≥ 30% **and** C − B ≥ 25 points | **GO** to training |
| 4 | anything else (including a gap of 15–24 points) | **Grey zone**: no re-runs to "fish" for a better number; decide with the user from the data |

## 8. Budget (hard limits)
| Item | Estimate | Hard stop |
|---|---|---|
| Glimmer arms A + B: 60 calls + 6 dry-run calls, up to 16 in parallel, ~25 min A100 incl. a one-time ~60 GB download into `forge-hf-cache` | ~$1.00–1.50 | the app stops itself after the run; max 1 GPU |
| Spark Open arm C on **Baseten credits** (user, 2026-10-28): 30 calls (~6k tokens in, up to ~8k out each; $1.25/M in, $4.25/M out, verified by the verifier) | ~$0.90–1.50 | runner stops arm C once its estimate passes $3 |
| **Total** | **~$1.50–2.50** | **abort at $5** |
- Spent so far (before the main run): ≈ $1.6 of $30 (Modal ~$0.99 incl. Glimmer test 1 + dry run, Meta ~$0.51 Muse Code, Baseten ~$0.06). The runner's GPU estimate leaves out the cold start (~3× low); the real Modal figure comes from `modal billing report`.
- decision (user, 2026-10-28): Spark runs as **Spark Open on Baseten**, paid from the $100 Baseten credit (~$0.02 spent before). Meta credits are not used. Both models are now open weights, which also fits the "Best Build on Meta Open Weights" bonus. Every Baseten call is logged in this run's cost file, because HerdShot's limiter is not used.

## 9. Who builds what
- Jobs, references, wrong versions, checks: written before the run and checked by CadQuery (free). This is the exam,
  not the factory.
- Test runner (send job → get code → run → measure → score): the user's rule is that **Muse Code builds it** from a
  spec. Open: whether Muse Code spends Meta credit. Check before using it, and add it to the budget.
- I check the numbers and write the report; the user makes the GO/STOP decision.

## 10. What I expect (written now, to compare later)
- Medium + hard (30 jobs): A ≈ 20–40%, B ≈ 30–50%, C ≈ 50–70% → probably **GO**, but an honest guess, not a promise.
- The biggest risk: B close to C (the manual is enough). Then the answer is STOP, and the remaining ~$27 stays free for
  another project.

## 11. Output
`results/first-test/`: every prompt, answer, measurement and cost, plus `report.md` with the table, the decision rule
applied and the real cost.
