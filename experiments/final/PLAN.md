# Training + final exam plan (DRAFT, prepared not run)

Status: DRAFT by Claude, 2026-10-29 ~22:30. User: "prepare the training, not run". Nothing here has been paid or run.
Order of gates: verifier check of this plan + MUSE_SPEC.md → user's yes to the Muse build → build + tests → verifier
→ user's yes (and budget raise) for each paid run step below.

## Question (the goal, user 2026-10-29)
Is a trained Glimmer 30B, with a short prompt and one try, **as correct as Glimmer + every fair fix (B-max, 95%)**
on the 30 held-out CadQuery jobs, and **many times cheaper and faster**, while running on one GPU that a company owns?

## Why privately run Glimmer is the comparison, not Spark (verified)
- Spark Open is 816B parameters (42B active) and needs ≥ 700 GB GPU memory for NVFP4 (one B200 node; BF16 = 4 nodes
  of 8 H200). Source: https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B and
  https://huggingface.co/blog/meta-muse-spark-open. Glimmer 30B is dense ~29.6B; its 4-bit build is < 20 GB (fits a
  24-32 GB GPU). Source: https://huggingface.co/meta-models/Muse-Glimmer-30B.
- Fair note (verifier F4): the Spark Open model card also says it is "optimized to run on two Mac Studios with M5
  Ultra using MLX". So private Spark is possible, but needs ~700 GB of memory (two top Mac Studios or a B200 node);
  Glimmer needs < 20 GB.
- decision: the headline compares trained vs untrained Glimmer **on the same A100-80GB**. We never claim "cheaper than
  Spark via an API" (it is not: Spark on Baseten ≈ $0.017 per answer, 18 s). Spark appears only as the teacher and in a
  "why not run Spark privately" line with the hardware figures above.

## Steps (each paid step needs the user's yes; caps are hard stops)
| # | Step | Where | Cap | Expected |
|---|---|---|---|---|
| 0 | Muse Code build (MUSE_SPEC.md: cloud CadQuery box, factory, trained arm, compare script, C1 fix) | Meta | — | $2-4 (1-2 rounds + fixes) |
| 1 | Comparability check: the cloud box + grader re-run the 270 recorded baseline answers; verdicts must equal the recorded ones | Modal CPU | $0.50 | ~$0.10 |
| 2 | Factory pilot: 20 jobs (2 per family), Spark k=1 | Baseten + Modal CPU | $1.00 | ~$0.5 |
| 3 | Factory main: ~170 jobs (yield rule in experiments/factory/PLAN.md) | Baseten + Modal CPU | $5.00 (incl. step 2) | ~$4.2 |
| 4 | Training: LoRA on H100 + merge | Modal H100 | $4.00 | ~$2-3 |
| 5 | Dev check: trained model on the 20 dev jobs, k=3 | Modal A100 | $1.00 | ~$0.5 |
| 6a | Finish BX: its 11 missing answers (H12 ×2, H13-H15 ×3), base Glimmer, 12 workers (one wave) | Modal A100 | $1.00 | ~$0.6 (worst ≈ $0.74) |
| 6 | Final exam: trained model on the 30 exam jobs, k=3 | Modal A100 | $2.00 | ~$1 |
| 7 | (optional, free GPU) offline Mac demo with MLX | Mac + Modal CPU | $0.30 | ~$0 |
Total ≈ **$10-14 expected; worst case caps $13.80 + Muse $3-5 = $16.8-18.8** (verifier N2, + step 6a) → Forge ≈ $41-45
expected, ≈ $49 worst, of the $50 the user may approve. Within the
current $35 only step 0 fits. decision (user, 2026-10-29): budget raised to $50; each paid step still needs the
user's yes and the verifier.

## Step 1: comparability (why: baselines were graded on the Mac; the trained arm will be graded in the cloud)
Re-run the code of the 199 recorded final answers (BR 30, B2 90, BX 79; results/bmax-baseline-2026-10-29) in the
cloud box and grade it in the cloud grader, recording both 0.2% and 1e-6. Box and grader pin the Mac's versions:
cadquery==2.8.0, cadquery-ocp==7.9.3.1. Pass = 0 verdict changes at 0.2%, AND the box's measurements (bbox, volume,
solids) equal the recorded ones at print precision (verifier A3: BX's round 2 feeds these measurements back to the
model, so a Mac-vs-cloud difference would change BX's conversation). Any change → STOP and explain before step 6 (a grader difference
would make the comparison unfair).

## Steps 2-3: factory (frozen plan: experiments/factory/PLAN.md, spec experiments/factory/SPEC.md)
Changes from this plan: teacher answers run in the cloud box (not the Mac sandbox); `cached_tokens` read from
`usage.prompt_tokens_details.cached_tokens` (C1, verifier). Before the pilot, Claude does the blind rebuild: one job
per family from its text alone through the cloud box, 10/10 PASS at 1e-6.

## Step 4: training (pipeline: experiments/train/forge_train.py, built and tested; smoke test passed)
- decision: one configuration, chosen before seeing any dev result: epochs 2, LoRA r 16 / alpha 32, lr 1e-4, grad
  accumulation 8, max 4,096 tokens per example, short prompt (first-test SYSTEM_PROMPT + job text), loss on the answer
  only. Same as the smoke test that passed.
- The exam guard runs first (refuses exam look-alikes; aborts if > 5% refused). Its code check now uses the cloud box.
- Stop early if peak memory after the first optimizer step > 76 GB (built in).
- Log: loss per step, examples dropped for length, tokens learned, minutes, $ (Modal billing before/after).

## Step 5: dev check (pre-registered gate before the exam is touched)
Trained model on the 20 dev jobs (never trained on), k = 3, strict 1e-6 and 0.2% both reported; decision on 0.2%.
- dev ≥ 80% → GO to the final exam.
- dev < 80% → STOP. Report it. One retry (epochs 3) only with a new user yes; never touch the exam to decide.

## Step 6: final exam (rules pre-registered in experiments/bmax/PLAN.md rule 3, copied here unchanged)
Arm FT = the trained model, short prompt, one try, k = 3, 8 workers, alone on an A100-80GB, max_tokens 16,000, same
sampling (temperature 1.0, top_p 0.95, top_k 64), 0.2% referee for the decision, 1e-6 reported. Paired bootstrap over
the 30 jobs, 10,000 resamples, each job's pass rate over its answers:
- (a) **as good as B-max**: FT − BX ≥ −5 points AND 95% CI lower bound ≥ −15;
- (b) **clearly beats the one-try arm**: 95% CI of FT − B2 entirely above 0;
- (c) **about the same cost as B2**: FT tokens per correct part ≤ 1.5 × B2's (≤ 15,993);
- (d) **much cheaper than B-max**: FT tokens per correct part ≤ BX ÷ 3 (≤ 7,105), or wall-clock per correct part ≤ BX ÷ 3.
  Reported first as wall-clock and $ per correct part, then tokens split into prompt and completion (verifier F2):
  B2 = 6,458 prompt + 4,205 completion per correct part, BX = 14,101 + 7,213. Most of the token saving comes from
  dropping the 5.7k-token manual (the knowledge moved into the weights); the report says so.
- The full claim holds only if all four hold. "Within 5 points" is never called "better". Medium and hard are reported
  separately (medium is saturated: B2 100%).
- Honest-risk note (from the baseline page): (b) will likely fail on 30 jobs even if training works; then the report
  says "as good as B-max, N× cheaper" and states that (b) failed.
- **BX's 11 missing answers are run (user decision 2026-10-29: "finish until the 30 jobs").** BX had 0 final answers on
  H13, H14, H15 and 1 of 3 on H12 (cap stop in the baseline). Step 6a runs only those 11 (job, rep) pairs with the
  frozen BX prompt, settings and loop, on the cloud box, base Glimmer on the same A100-80GB. Then all 30 jobs have 3
  BX answers and rule 3's 30-job paired bootstrap applies unchanged. Disclosed: these 11 answers ran on a later day
  and were graded in the cloud (step 1 shows the grader gives the same verdicts).
  - 12 workers, so all 11 run in one wave (verifier A1: hard BX answers take up to 821 s; 8 workers = 2 waves ≈ $1.31
    worst, over the cap). Concurrency differs from the baseline's 8, so the median latency is reported too.
  - If 6a stops before 11 final answers exist → STOP and ask the user; compare.py is not run.
  - Bar (d) is recomputed over all 90 BX answers, as rule 3 says. The 7,105 above is the 79-answer value; hard answers
    average 22,303 tokens against 20,235, so the bar will likely get a little looser for FT. Disclosed in the report
    (verifier A2).
  - BX wall-clock for "per correct part" = 3,050 s (baseline arm) + 6a's arm wall-clock without the cold start.
- Reported per arm: pass rate (all / medium / hard), pass@3, tokens per correct part, seconds per answer (median and
  mean), $ per correct part (= arm wall-clock h × $2.50 ÷ PASS), chart accuracy vs $ per correct part.

## Step 6 amendment (R5 option B, written 2026-10-31 BEFORE any exam run; experiments/r5/PLAN.md)
The exam runs once with two arms: FT = the R5-trained model served WITHOUT the rule card (short prompt), and A + card v2
(base Glimmer, short prompt + experiments/final/RULE_CARD.md sha256 9d0929b2…29c7). Runner, referee (0.2%), 16,000
tokens, sampling and k = 3 as in step 6; bars (a)-(d) are reported against B2/BX as written, and FT vs A + card is
reported with the same paired bootstrap. Disclosed: B2/BX used the 5.7k manual and no card. Cap $5.

## Step 7: offline demo (other agent's condition 3; only if it takes under ~2 h)
hypothesis: download the merged model (~56 GB; 587 GB free) and convert it with `mlx_lm.convert -q` on the Mac, then
answer one exam-style job offline. The model only writes text on the Mac; its code is still built in the cloud box
(rule: no AI-written code runs on the Mac). Shown as a demo, not scored.

## Not in this plan
- Thinking jobs without the standard (optional idea): later, only if money is left.
- No defence or war examples anywhere (user rule).

## Before step 6
Check that the merged model's generation_config.json equals the base model's (same sampling defaults). Log the vLLM
image digest for every session (base and trained).

## Freeze (sha256 recorded here before step 6)
runner_final.py, cloud_cq.py, the grader, deploy/modal_forge.py, the merged model's file list, this PLAN.

## Retry R3: Spark's reasoning in the training data (pre-registered 2026-10-30, before any R3 money; verifier P1-P6)
Context: dev check STOP (38.3%, results/dev-2026-10-30): answer-only training removed the thinking turn. User decision:
keep Spark as teacher, train on its worked solution (reasoning_content + code).
1. **Teacher pilot gate:** ≥ 95% of pilot PASS answers have non-empty reasoning, else STOP. Then the usual yield rule.
2. **Training config frozen:** epochs 2, r 16, alpha 32, lr 1e-4, GA 8; only changes: reasoning in the thinking turn,
   max 12,288 tokens, H200, GPU stop 135 GB. Over 12,288 → dropped and counted. Format check PASS (H3) before training.
3. **Manual mentions:** keep every passing record and report the share whose reasoning mentions "manual" (decision,
   user 2026-10-30 "yes").
4. **Dev re-check:** the same 20 dev jobs, k = 3, factory grader, gate ≥ 80% at 0.2% only on a COMPLETE 60-answer run;
   disclosed as the second look at dev. Session with the budget fix (4b) and cap ≈ $2.00 (or $3.50 if unfixed); D3
   (vLLM default sampling + image digest) captured in that session.
5. **Control:** base Glimmer arm A on the same 20 dev jobs, k = 3, through the same Modal vLLM stack (≈ $0.3-0.5), so a
   pass or fail can be attributed.
6. **Expected effect, said now:** with ≈ 5.5k completion tokens per answer (Spark's reasoning median 5,177), FT's
   tokens per correct part at 80-90% ≈ 6.4-7.2k vs bar (d) ≈ 7,105 (79-answer BX; the 90-answer value will be higher):
   verifier's sharper estimate: (mean 5,916 + 250) / 0.8 ≈ 7.7k > 7,105 at 80% (≈ 6.85k at 90%), so the token form of
   bar (d) LIKELY FAILS unless the pass rate is ≥ ~90%; the wall-clock form may decide; bar (c) stays easy; the "many times
   cheaper" headline weakens to "≈ 2.8-3× fewer tokens than B-max, no manual, one try".

7. **Training stop rule (verifier T2, before R3 training):** if train.json shows `stopped_at_deadline: true` or fewer
   optimizer steps than planned, /vol/r3/merged is NOT dev-checked; training is re-run. Cap $5 (ceiling; expected spend
   ≈ $1.3-1.8, H200 timeout ≈ 40 min). Output name `r3` → dev session with FORGE_MODEL_NAME=r3.
8. **Memory rule (verifier T3):** on mem_stop (nothing saved, ≈ $0.3-0.4 lost) do not retry the same settings; retry once at
   max_tokens 8,192 (drops ≈ 36) with the user's yes.
9. **User yes (2026-10-30, "okay in modal and base"):** after R3 training, the dev re-check (FORGE_MODEL_NAME=r3) and the
   base Glimmer arm-A control, both on Modal.
10. **Reading the base control (verifier D3a, written before the runs):** the 80% gate is read on FT alone (complete 60,
    budget_stopped false). The control A is read per job: FT − A pass rate; FT < A overall means training hurts; FT ≥ A + 10
    points means training helps; in between = no clear effect. Both disclosed. The served model path must be /vol/r3/merged
    (checked before GO).

## Rule-card check (pre-registered 2026-10-30 before the runs; superintel §c + verifier C3)
Old dev set (4th look, disclosed; the card was written from R3 dev crashes). Arms: R3 + card, A + card, k = 3.
- Main signal = crashes (any non-empty run_error) of R3 + card: <= 8 → manual-gap diagnosis holds; 9-14 → unclear (say
  so); >= 15 → diagnosis wrong (the card must be trained in, not only served).
- Pass rates within ±10 points = no clear difference (paired SE ≈ 6-9). A + card pass rate = expected generator yield.
