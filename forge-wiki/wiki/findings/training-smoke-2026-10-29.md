# Training smoke test (2026-10-29): training works; vLLM LoRA crashes, the merge fallback works

**Summary**: verified (results/smoke-2026-10-29/*.json, results/smoke-run*.log). Muse Glimmer 30B bf16 LoRA trains on one
H100 (loss 1.03 → 0.33 in 8 short steps, ~0.5 s per step at ~300 tokens), but an **8,192-token step runs out of memory**
(peak 80.2 GB). The adapter saves. **vLLM's LoRA loading crashes** (lora_shrink AssertionError, the known vLLM bug
53254; our image v0.26.1rc1 is older than the fix). **The merge fallback works**: the merged model serves as `forge` and
answered a new job in 3 s, 84 tokens, no reasoning text, correct format, **PASS with the strict referee (1e-6)**.
Smoke cost ≈ **$1.06** (Modal metered 6.76 → 7.82), under the $1.5 cap; all apps stopped.

**Sources**: `experiments/smoke/train_smoke.py` (test harness written by Claude), `score_answer.py`,
`results/smoke-2026-10-29/{train,merge,serve_merged}.json`, logs `results/smoke-run{,2,3,4}.log`.

**Last updated**: 2026-10-29

---

## Answers to the user's checklist (verified unless marked)
| Question | Answer |
|---|---|
| Fits in memory? | Short examples yes. 8,192 tokens: **no** (OOM, peak 80.2 GB of 80 on H100). |
| Loss going down? | Yes: 1.03, 0.94, 0.97, 0.50, 0.36, 0.35, 0.40, 0.33 (8 steps, 8 examples). |
| Seconds per step | ~0.4-0.6 s at 260-500 tokens (first step 3.8 s warm-up). Model load 27 s from the volume. |
| Adapter saved? | Yes: forge-lora volume `smoke/` (adapter_model.safetensors, adapter_config.json). |
| vLLM loaded it? | **No** as LoRA (crash). **Yes** after merging (`/vol/merged`, merge 165 s on H100, vLLM ready in 255 s). |
| Answer format? | Yes: one Python code block, 84 output tokens, 0 reasoning, finish_reason stop, 3 s. Strict referee: **PASS**. |
| Actual $ | ≈ $1.06 (4 Modal runs: a harness bug run, train+serve, serve-only diagnosis, merge+serve). |

## What it means for the real run (hypothesis)
- **Length:** keep training examples ≤ 4,096 tokens (short prompt + code answer; Spark's answers fit), or use an H200
  (141 GB, $4.54/h) if longer ones matter. Not yet tested: memory at 2-4k tokens; the real run must log peak memory at
  step 1 and stop early if it is close to the limit.
- **Serving:** plan on merge + serve merged (adds ~3 min of H100 ≈ $0.2 and a 56 GB copy in the forge-lora volume), or
  test a newer vLLM image for LoRA. Merging also removes the LoRA latency cost.
- **Cost guess for the real run:** ~200 examples × ~2-3k tokens × 2.5 epochs; at a few seconds per example ≈ 30-45 min on
  an H100 ≈ $2-3, + merge ≈ $0.2. To be confirmed by step 1 of the real run.
- **Early sign for the cheaper claim:** the trained model answered with no reasoning in 84 tokens (B2 used ~10.7k tokens
  per correct part). One easy job only, 8 training examples: not evidence of quality yet.

## Bugs met (lessons)
- A Modal function returned `torch.__version__` (a TorchVersion object); the local side has no torch, so unpickling the
  return failed. Return plain types (json round trip) and print the result in the container log too.
- Keep the whole vLLM log, not only the tail: the root cause sits above the final RuntimeError.
