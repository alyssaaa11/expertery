# Tools and services: what we learned using them for Forge

**Summary**: Practical, checked facts about every tool and service Forge uses: Modal (Glimmer on a GPU), Baseten
(Spark Open), Meta API + Muse Code, CadQuery, and the models. Read this before running anything paid.

**Sources**: commands and outputs in the Forge session of 2026-10-28 (noted inline); `~/projects/forge/deploy/
modal_glimmer.py`; `experiments/first-test/run_live.sh`; verifier report `~/agents/verifier/reports/forge-2026-10-28.md`.

**Last updated**: 2026-10-28 (evening additions marked Oct 28 eve)

---

## Modal (Glimmer on a GPU)
- verified (Oct 28 eve, results/keel-v2-main.log): cold start 4 min 16 s with the weights already in the volume;
  90 Glimmer answers (plus 90 Spark) in 523 s with 16 parallel; `modal billing summary` metered $2.22 total so far,
  billed $0.00 (credits).
- verified: CLI 1.6.3 installed with `uv tool install modal`; workspace **my-workspace**; login in `~/.modal.toml`.
- verified: Forge deploy = `~/projects/forge/deploy/modal_glimmer.py`: app + secret **forge-glimmer** (VLLM_API_KEY,
  also envsave `FORGE_GLIMMER_VLLM_API_KEY`, regenerated each live run), volumes `forge-hf-cache` / `forge-vllm-cache`,
  **A100-80GB**, max 1 container, 5-min scale-down, image `vllm/vllm-openai:muse-glimmer`.
- verified: the image needs `python` on PATH (a symlink in `setup_dockerfile_commands`); without it the deploy fails
  "unable to determine the version of Python".
- verified: `--max-model-len 32768`. Glimmer's native context is 131,072 (dev.meta.ai/docs/muse-glimmer/vllm);
  16,384 was only our old setting.
- verified: cold start ~7 min (download into the volume the first time, then load); ready check = poll `/v1/models`.
- verified: **`modal app stop <app> -y`**. Without `-y` it asks for confirmation and silently does nothing in scripts.
  Always check `modal app list` after a run.
- verified (verifier): Modal web requests are cut at 150 s with a 303 redirect; urllib follows ~5, so one call is
  capped at ~750 s. The longest Glimmer call in the main run was 410 s.
- verified: price A100-80GB $2.50/h, H100 $3.95/h (`modal billing rates`). Real spend: `modal billing summary` /
  `report`. The runner's own GPU estimate leaves out the cold start (~3× low).
- verified: Glimmer speed ~25 tokens/s per answer (dry run), about 60 jobs in 13 min with 16 parallel.

## Baseten (Spark Open, the teacher)
- verified (Oct 28 eve, results/keel-v2-main): with the ~3.9k-token Keel prompt, one Spark Open call ≈ $0.011 and
  5–10 s (90 calls ≈ $0.97 by the runner's token estimate; prompt caching shows up as cached_tokens 3,712).
- verified: `https://inference.baseten.co/v1`, model **`meta-models/muse-spark-open-1026`**, key envsave
  `BASETEN_API_KEY` (opaque ref in the `baseten-muse-spark` skill). The hackathon key works only with this model.
- verified (verifier): price $1.25/M in, $4.25/M out (cache reads $0.15/M).
- verified: accepts temperature, top_p and **top_k** (2-call probe, HTTP 200).
- verified: speed 9–49 s per job; max answer 12,768 tokens (so max_tokens must stay ≥ 16,000).
- Money: the user says the hackathon gave **$100 credit**. The dashboard (org "HerdShot", Billing and usage) showed
  $0.00 spend and no visible balance, with a **Visa card on file**. The hackathon key gets 403 on the billing API.
  Baseten docs say credits are applied to invoices before the card. Still to confirm after usage shows up.

## Meta API and Muse Code
- verified (Oct 28 eve): 7 more Muse Code sessions for the company, Keel and the runner ≈ $4.2 in total (see
  [[lessons]] on session cost). It follows specs well, reports deviations honestly, and respected "never open the
  exam files" in library work.
- verified: Meta key envsave `META_HERDSHOT_API_KEY` (opaque es_b6ZrOh9_…; the name is from the earlier project, same
  hackathon account). Meta credit $150 with the user's limit $90; spent $24.49 in HerdShot + ~$1.02 in Forge.
- verified: **Muse Code** (`muse` 1.4.14) has **no free allowance** (`muse usage` → no_allowance), so every run costs
  Meta credit. Headless recipe used:
  `envsave get <ref> | muse exec --api-key-stdin --model muse-spark-1.3 --effort medium --workspace <dir>
  --approval-mode never --disable-web-tools --max-model-steps 60–80 --no-foreign-personal-context --json --prompt-file <f>`
- verified: cost is read from the `run.usage` event in the JSON output (input, cached, output and reasoning tokens).
  Build runner: 24 calls, ~$0.44–0.51. Apply fixes: 41 calls, ~$0.51 (mostly cheap cached reads).
- verified: Muse Code respected read-only files, and reported honestly what it could not follow.
- Option not tested: `--base-url` could point Muse Code at another server (e.g. Baseten).

## CadQuery (the tool and the referee)
- verified: CadQuery 2.8.0 in `~/projects/forge/.venv` (uv, **Python 3.12**; system Python 3.15 has no wheels).
- verified: B-rep booleans are exact, so the overlap check (answer XOR reference ≤ 0.2% of the reference volume)
  gives ~0.0% for a correct part. Size, volume, area and centre of mass alone missed 17 of 66 wrong parts.
- verified: a STEP export → import round trip keeps the verdicts (verifier C5).
- verified: CadQuery `box()` is centred by default, which caused the position-only failures (H15 lid 1 mm low).
- `cadquery.importers` is not importable as a module in 2.8; use `cq.importers.importStep`.

## Models
- Muse **Glimmer** 30B dense, Apache-2.0, distilled from Spark, served as `muse-glimmer` from
  `meta-models/Muse-Glimmer-30B` (not gated on Hugging Face). Meta-recommended sampling: temperature 1.0, top_p 0.95,
  top_k 64.
- Muse **Spark Open**: same base model as Muse Spark 1.3 plus extra safety post-training (PyTorch blog, HF card);
  816B total / 42B active, 1M context, ~537 GB even in NVFP4 (so self-hosting needs ~8 big GPUs). The licence requires
  "Built with Muse Spark Open". The "39 vs 48 intelligence index" comes from one secondary blog and is unconfirmed.
- Local Glimmer q4 MLX exists at `~/models/muse-glimmer-30b-radixark-q4-mlx` (~15 GB). The Mac has 24 GB RAM (~8 GB
  free when checked), so it was not run locally.
