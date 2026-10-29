# Night prep for Oct 29 (Option A): results, risks and second plans

**Summary**: The 5 free night tasks the user asked for on 2026-10-28 ~23:45 ("do this task of forge to be prepared",
including the risks and second plans), all done with no builds, no Muse Code and no paid calls. **Biggest finding:**
the past-design library is small (~27-47k tokens), so "Glimmer can't hold the library" is false unless we fix the
design. The verifier says READY WITH FIXES (4 must-fixes). Morning decisions are listed at the end.

**Sources**: verifier pre-review `~/agents/verifier/reports/forge-option-a-prereview-2026-10-28.md`; training
research `forge-wiki/raw/training-recipe-research-2026-10-28.md`; drafts in `experiments/option-a/` and
`experiments/b2-hint/SANDBOX_SPEC.DRAFT.md`; plan [[option-a-plan-2026-10-29]].

**Last updated**: 2026-10-29 ~00:15

---

## 1. Spark Open context limit (task 1, free)
- verified: `GET https://inference.baseten.co/v1/models` (free metadata call, with the skill's key) lists
  `meta-models/muse-spark-open-1026` with `context_length: 1048576`, `quantization: fp4`, prices $1.25/M in,
  $4.25/M out, $0.15/M cache read. Baseten's launch blog says "the full 1M context window".
- verified: Baseten docs warn that catalog values "can differ from the limits the endpoint enforces", so 1M is
  advertised, not tested.
- verified (verifier, same page): Meta's deploy docs also give 1M.
- verified: rate limits are per model. The defaults are 15 RPM / 100k TPM (unverified account) and 120 RPM / 500k TPM
  (verified). The hackathon key's tier is unknown.
- decision (recommendation): **the 60k/150k probe is not needed.** Arm C's real prompt is ~35-55k tokens, and the
  3-job pilot measures it for free as part of the run (latency, `cached_tokens`). Saves ≈ $0.27.
- Gotcha: `envsave get BASETEN_API_KEY` says "Secret not found"; the opaque ref is in the `baseten-muse-spark` skill.

## 2. Training recipe for Glimmer LoRA (task 2, free)
Full notes: `forge-wiki/raw/training-recipe-research-2026-10-28.md` (web only, nothing run).
- verified: Meta gives no fine-tuning recipe. The HF blog shows **TRL + PEFT LoRA on one H100 in bf16** (micro-batch
  1, gradient checkpointing). Unsloth supports Glimmer from day 0 (QLoRA ~24 GB, 16-bit LoRA > 40 GB).
- verified: chat template uses `<|start|>{role}<|message|>…<|eot|>`; the answer turn is `assistant to=user`; private
  reasoning goes in a `self` channel; `reasoning_strength` is low/medium/high/xhigh.
- hypothesis: bf16 LoRA at 8k length needs ~70-78 GB, so it is tight on H100-80GB. QLoRA (~21 GB of weights) is the
  fallback. There is no smaller Glimmer.
- decision (proposed recipe): TRL+PEFT, r=16, alpha=32, all attention + MLP projections of the language model only,
  lr 1e-4 cosine, 2-3 epochs, effective batch 8, max length 8192, loss on the answer only, chat text built with
  `apply_chat_template` at the same reasoning level we serve.
- hypothesis (cost): ~1.5M tokens × 2.5 epochs on one H100 ≈ 1-1.3 h ≈ **$4-5**. A100 ≈ 2.3 h ≈ $6. Hard stop $8.
- verified risk: vLLM LoRA on this model crashed at startup (issue 53254, NVFP4 base). The fix (PR 53513) merged
  2026-08-24. Unknown whether our `vllm/vllm-openai:muse-glimmer` image has it. **Fallback:** `merge_and_unload()`
  and serve the merged model.
- **Smoke test first (~$0.5-1):** 10 steps on 8 examples on an H100, save to a Volume, check peak memory < 76 GB and
  that loss falls, then serve with `--enable-lora --max-lora-rank 32 --lora-modules forge=/vol/smoke`. Check that
  `/v1/models` lists `forge` and that one request with the full prompt returns an answer.

## 3. Verifier pre-review of Option A (task 3, free)
Verdict **READY WITH FIXES**, 12 fixes. The 4 must-fixes before any build:
1. **Glimmer context.** The library is ~47k tokens by the verifier's count, ~27k by mine (300 × ~89 tokens measured
   on the 30 draft jobs: `experiments/option-a`, avg 310 chars of request + program). Either way it is close to or
   under Glimmer's native 131k. Our 32k cap is only a serving setting. **Fix:** add a **B-full** arm (Glimmer + the
   whole library, `--max-model-len 65536`), or make the library much bigger than 131k.
2. **C-search arm** (Spark + the same top 5), so the model effect and the information effect can be separated. STOP
   only if both C and C-search are < 30%. Cost ≈ $1.
3. **Freeze retrieval and the rule-key mix before writing the exam.** Retrieval with a programme+family bonus finds
   exactly the rules keyed on programme+family. Report the result per rule.
4. **Every arm gets one fixed sentence:** "Approved past designs follow house standards that apply even when a request
   does not mention them; the request wins on conflict." Without it, adding unrequested features would be disobeying
   the request.
Others: a manual-only check per rule, a stronger blind-helper gate (clean folder, scored by a rubric, ideally a
non-Claude helper), contrast designs, a structural overlap check, the runner cost estimate must count
`cached_tokens` (otherwise the $4 C cap stops the run at ~57/90 calls), and freeze everything by hash.

## 4. Drafts: hidden standards + 30 exam requests (task 4, writing only)
- `experiments/option-a/HIDDEN_STANDARDS.DRAFT.md`: 11 rules S1-S11, private.
- decision (Claude, for the user to confirm): the rules are keyed on two **new programmes, Tern and Skua**, not
  Petrel-1/2. verified: manual example BRK-0101 is titled "Petrel-2 L-bracket" (`company/examples/requests.json`
  line 5) and would contradict any Petrel-2 rule.
- The rules mix simple tag rules (programme → material/class) with threshold and interaction rules (Tern wall > 30
  → +1 mm, bracket L ≥ 90 → 6 holes, clip L ≥ 60 → 2 harness mounts, KF-M2/HARNESS take CS while everything else
  takes CB) and explicit overrides.
- `experiments/option-a/jobs.DRAFT.py`: 30 jobs (15 medium, 15 hard). Each has a reference + 2 wrong versions
  (mostly "standard ignored or misapplied") and a `rules` tag.
- verified: local self-test `selftest_draft.py` (forge venv, free) = **90/90 OK**. The first run was 88/90: two wrong
  versions only changed the material, which does not change the solid when the wall and fillet are explicit. Both were
  replaced.
- verified: no part number is shared with the Keel v2 exam or the manual examples (comm check).
- verified (verifier drafts review, `~/agents/verifier/reports/forge-option-a-drafts-2026-10-29.md`): **READY WITH
  FIXES (9)**. The 11 rules are deterministic and don't contradict the manual or the examples; all 30 references follow
  them (self-test reproduced, hand-checked).
- Already applied (00:25, self-test still 90/90): fix 2 (M5, M7 and M9 resized so no job shares family + stock with a
  manual example) and fix 7 (B2 sandbox 60 s, not 120 s).
- Open for the morning:
  - fix 1 (high): drop the programme/family retrieval bonus, freeze plain BM25, and raise the jobs that depend on a rare
    threshold side, interaction or override from 13 to ≥ 18 of 30.
  - fixes 3-6: edge designs at h = 30, L = 90 and L = 60 in the library; per-rule attribution; the generator must
    reproduce all 30 refs; a runner test that prompts contain no rule text.
  - fix 8: commit the drafts.
  - fix 9: the free retrieval-coverage audit once the library exists. It predicts B-search before any paid call.
    Pre-register: if ≥ 80% of exam jobs are fully covered by their top 5, expect NO ROOM.
  - Optional re-keys (verifier): S7 cross-family (any Tern/Skua wall > 20 gets the mid-height hole); S9 rim by
    thickness (12 if T ≤ 6, else 15). Freeze the BM25 tokenisation too: numeric tokens like "35" can pull a neighbour
    with the same wall height.
  - Cost correction (verifier): C-search ≈ $0.6, not $1.

## 5. B2 sandbox spec (task 5, writing only)
`experiments/b2-hint/SANDBOX_SPEC.DRAFT.md`: the first-test runner runs answers with the full environment and no
limits. The spec adds a `--sandbox` flag that reuses the Keel v2 profile (no network, home and temp reads denied,
writes only to scratch, `env -i`, 60 s limit as in the frozen first test so BR = B, 4 GB RSS kill) through a new `run_one_cq.py` (STEP hand-off as today).
Default behaviour is unchanged. It comes with tests and a 30/30 reference re-check before re-freezing. Muse Code cost
≈ $0.3-0.5.

## 6. Risks and second plans (hypothesis: each one is a plan, not a measured result)
| Risk | How we see it | Second plan |
|---|---|---|
| **R1. Retrieval or the full library already solves it** (B-search or B-full ≥ 80 → NO ROOM). Most likely, given the small library and tag-keyed rules. | Option A rule 2 | (a) Plan B = CadQuery factory if B2's best ≤ 75 (proven gap 67% vs 100%). (b) Option A-big: ~40 rules + ~1,500 designs (≫ 131k tokens), so neither retrieval nor the prompt can hold it. Costs one more day. |
| R2. The teacher can't infer the standards (C and C-search < 30%) | rule 1 | Simplify the rules (fewer interactions, more contrast designs). Or give the teacher the rule file as "senior engineer notes" for the practice runs only; the student still learns from verified answers. |
| R3. B2's cheap hint closes the CadQuery gap (best ≥ 80) | B2 rule 2 | Then Option A is the only route. If it is NO ROOM as well, report honestly and switch to the fallback story (Team Doctor or the pipeline demo). |
| R4. bf16 LoRA runs out of memory, or vLLM LoRA crashes | smoke test | QLoRA, max length 6k, r=8; serve merged weights instead of an adapter. |
| R5. Training gives no gain on the final exam | stage-5 paired test | An honest negative result plus the full pipeline as the demo. Keep one retry ($4) in the budget. |
| R6. Money: cost estimate without caching stops C early; Muse Code overruns | NOT_RUN at the cap | Count `cached_tokens`, put the library as the same prefix (manual + library first), add `x-session-affinity`; Muse Code step cap 60, precise specs. |
| R7. Time: one day for spec → Muse Code build → checks → run | evening without a result | Run B2 first (smallest). If the day slips, drop B-full or B-search sensitivity rows, not the gates. |

## 7. Morning decisions for the user (nothing paid runs before these)
1. **The library-size question (verifier must-fix 1):** add a B-full arm (cheaper, honest) or a much bigger library
   (stronger story, +1 day)? Recommendation: **B-full** tomorrow. Plan the big library only if B-full ≥ 80.
2. Accept the other must-fixes: C-search, frozen retrieval, the "standards exist" sentence. Recommendation: yes.
3. Tern/Skua instead of Petrel for the hidden rules. Recommendation: yes.
4. Skip the paid context probe (the pilot measures it). Recommendation: yes.
5. B2 sandbox: (b) Muse Code builds the sandbox from `SANDBOX_SPEC.DRAFT.md` (~$0.3-0.5). Recommendation: (b).
6. Then the Muse Code builds: library generator spec (Claude writes it in the morning from the rule file and coverage
   targets) + retrieval + runner arms.
