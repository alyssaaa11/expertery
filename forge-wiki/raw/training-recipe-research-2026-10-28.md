# Muse Glimmer 30B LoRA SFT on Modal - recipe (researched 2026-10-28, web only)

Labels: [V]=verified in a fetched source, [H]=hypothesis/my estimate, [D]=decision I recommend.

## 1. Meta guide, template, reasoning format
- [V] No Meta fine-tuning recipe on the HF card; BF16 weights are "for fine-tuning and research". https://huggingface.co/meta-models/Muse-Glimmer-30B . HF blog covers only TRL (LoRA SFT = 1x H100 bf16, microbatch 1 + checkpointing; full SFT = 8xH100): https://github.com/huggingface/blog/blob/main/muse-glimmer.md
- [V] Template "ATEM": turns `<|start|>{role}<|message|>...<|eot|>`; system block has recipients `self` (private reasoning) and `user` (answer); answer turn is `<|start|>assistant to=user<|message|>`. `reasoning_strength` low|medium|high|xhigh passed to `apply_chat_template` (default high; system line "Reasoning strength: X"). https://blog.dailydoseofds.com/p/fine-tune-meta-ais-muse-glimmer-100
- [V] Tool calls are XML-style ATEM, NOT JSON; reasoning is channel-scoped, not tag-wrapped; vLLM needs `--tool-call-parser muse_glimmer --reasoning-parser muse_glimmer` (underscore). https://github.com/vllm-project/vllm/pull/51655
- [D] Build training text ONLY with `processor.apply_chat_template` (never hand-roll), keep the same reasoning_strength you serve with, and mask loss to the final `assistant to=user` turn. Unsloth warns: mix reasoning-style and direct examples, don't train only on short answers. https://unsloth.ai/docs/models/muse-glimmer/train
- [H] Your target is plain code answers; simplest is to train answer-only (no `self` channel) and serve with low reasoning, or include a short `self` reasoning if your referee-verified data has it. Check one rendered example by eye.

## 2. Tool support
- Unsloth: [V] supported day-0 (FastModel, 4-bit `unsloth/Muse-Glimmer-30B-unsloth-bnb-4bit`), "1.5x faster, 50% less VRAM". Docs say 30B QLoRA 24GB, 16-bit LoRA >40GB. Loss masking via `train_on_responses_only` with instruction_part `<|start|>user<|message|>`, response_part `<|start|>assistant to=user<|message|>`. Gotcha [V]: the model is multimodal (use FastModel + processor); embed+lm_head ~26% of memory; `offload_embedding=True` single GPU only.
- HF TRL (+PEFT): [V] officially documented in HF blog (AutoModelForMultimodalLM / AutoProcessor, transformers >= recent). Adapters in the wild are scoped to language-model layers via PEFT.
- NVIDIA NeMo AutoModel (SFT+LoRA) and TorchTitan: [V] named by search summary/Meta. torchtune, Axolotl, LLaMA-Factory: [H] no Glimmer-specific evidence found; don't use.
- [D] Use TRL+PEFT in bf16 (least magic, matches HF blog, adapter format is plain PEFT for vLLM). Unsloth is the fallback/speed option.

## 3. Memory (A100/H100 80GB, seq 8k)
- [V] BF16 weights ~56 GB (29.6B params, 52 layers, hidden 6656, GQA 32/2 heads). Vision encoder ~1.8B included.
- [H] bf16 LoRA r=16, grad checkpointing, micro-batch 1, 8k: weights 56 + LoRA/opt ~2 + checkpointed acts ~6 + logits (8k x 200k vocab, fp32 ~6.5GB, several copies) => ~70-78 GB. Fits but tight, esp. on A100. Mitigate: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, cap max_length at 8192, chunked/fused CE loss (Liger) if available, freeze vision tower (target only language_model).
- [D] First try bf16 LoRA on H100; if OOM at smoke test -> QLoRA 4-bit (Unsloth bnb-4bit, ~21GB weights, plenty of headroom, even runs on A100-80 comfortably).

## 4. Hyperparameters (small SFT, ~250 examples)
- LoRA r=16, alpha=32 (Unsloth default alpha=r; alpha=2r is common; r=32 for harder agentic tasks), dropout 0, target all linear in language model: q,k,v,o,gate,up,down; regex-anchor to `.*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)` to skip the ViT. [V: Unsloth r16/alpha16, 2e-4; rest D]
- lr 1e-4 to 2e-4 cosine/linear, warmup 5-10 steps (2e-4 is Unsloth's; for 250 examples I'd use 1e-4 to limit forgetting [H]), 2-3 epochs, effective batch 8 (micro 1 x GA 8) => ~30 steps/epoch, ~75 total. bf16, AdamW (8-bit optional), weight decay 0.001-0.01, max_length 8192, no packing (avoids cross-contamination with 4k system prompt), completion-only loss (TRL `assistant_only_loss`/completion_only_loss or the Unsloth collator parts above).
- Eval: hold out ~20 verified examples, run referee on generations after epoch 2 and 3; pick the better.

## 5. Time + cost
- Prices [V, third-party aggregators, Modal page not fetched]: A100-80GB $2.50/h, H100 $3.95/h, H200 $4.54/h, B200 $6.25/h. https://www.beam.cloud/blog/modal-pricing-explained and others. CPU/RAM billed extra (~$0.1-0.2/h).
- [H] Tokens processed: 1.5M x 2.5 epochs = ~3.75M. FLOPs ~ 8 x 30e9 x 3.75M = 9e17 (LoRA + checkpointing). H100 at ~35% MFU (~350 TFLOPs) => ~45 min; A100 at ~40% (~125 TFLOPs) => ~2 h. Throughput assumption ~1.4k tok/s H100, ~0.5k tok/s A100.
- Add ~10 min model load (56GB from HF; cache in a Volume) + smoke test ~10 min.
- [H] Expected total: H100 ~1.0-1.3h = ~$4-5 (fits budget); A100 ~2.3h = ~$6 (borderline and tighter on memory). H100 recommended. QLoRA is ~1.3x slower per token.

## 6. Serving the adapter
- [V] vLLM Day-0 support; image `vllm/vllm-openai:muse-glimmer`. LoRA startup crash (AssertionError in lora_shrink, issue #53254, reported on NVFP4 base) was fixed by PR #53513 merged 2026-08-24 ("Add multimodal module mapping for Muse-Glimmer"). https://github.com/vllm-project/vllm/issues/53254 , /pull/53513. A reviewer bot warned about `enable_tower_connector_lora` stubs (leave it False). Issue noted adapters were only documented with transformers+peft until then; a follow-up NVFP4+LoRA illegal-memory bug (#48862) is quantized-only.
- [H] Unknown whether the `:muse-glimmer` image tag includes the Aug 24 fix. Test early; if it crashes, switch image to a newer `vllm/vllm-openai:nightly`/recent release or fall back to merge (below).
- Flags [D]: `--enable-lora --max-lora-rank 32 --lora-modules forge=/vol/adapter --tool-call-parser muse_glimmer --reasoning-parser muse_glimmer --enable-auto-tool-choice` (max-lora-rank must be >= trained r; values 8/16/32/64 supported). Your 32768 max-model-len stays. Request with `model="forge"`.
- QLoRA adapter on bf16 base: [H] works in principle (PEFT adapter weights are independent of the quantized base), with slight mismatch since trained against dequantized weights; test eval on bf16 base. bf16-trained adapter is the cleaner path.
- Merge vs adapter: adapter is cheaper to iterate; if vLLM LoRA is flaky, `merge_and_unload()` in bf16 (needs ~60GB CPU RAM or the GPU), save to Volume, serve as a normal model. Merging avoids vLLM LoRA bugs and a small LoRA latency penalty. Keep the processor/tokenizer files with it.
- Modal: official example https://modal.com/docs/examples/unsloth_finetune (Qwen 4B/14B; the fetched page did not show Volume code; pattern from Modal's Flux LoRA example https://modal.com/docs/examples/diffusers_lora_finetune: `modal.Volume`, mount at /vol, `volume.commit()` after save, `volume.reload()` in the server). Third-party A100-80GB Unsloth-on-Modal tutorial: https://aiengineering.academy/LLM/ServerLessFinetuning/FinetuneGemmaUnslothModalTutorial/ . Use a 2nd Volume for the HF cache (`HF_HOME=/cache`).

## 7. Risks, fallbacks, smoke test
Risks: (a) bf16 OOM at 8k -> shrink max_length to 6k, r=8, QLoRA. (b) vLLM LoRA crash -> newer image or merge. (c) template mismatch (hand-rolled prompt, missing `to=user`) silently ruins output -> render with apply_chat_template and diff against vLLM's rendering. (d) overfit on 250 examples -> lr 1e-4, 2 epochs, held-out referee eval. (e) Variants: only 30B BF16 + 4-bit quants/GGUF/drafter exist; no smaller Glimmer found [V]. (f) Multi-GPU: 2xH100 doubles cost/hour but halves time (same $); FSDP complexity not worth it. Set Modal timeout and budget alarm ($8 hard stop).

Smoke test (~$0.50-1): Modal H100, 10 steps, 8 examples, max_length 8192, save adapter to Volume, `volume.commit()`. Check: peak memory (`torch.cuda.max_memory_allocated`) < 76GB, loss decreases, tokens/s measured (rescale cost). Then start vLLM on A100-80GB with flags above, `--lora-modules forge=/vol/smoke`, send one real request with the full 4k system prompt, confirm it returns a program and that `/v1/models` lists `forge`. Only then launch the full run.

## Sketch (TRL + PEFT)
```python
# modal: gpu="H100", timeout=3*3600, volumes={"/vol": vol, "/cache": hfcache}
model = AutoModelForMultimodalLM.from_pretrained("meta-models/Muse-Glimmer-30B", torch_dtype=torch.bfloat16, attn_implementation="sdpa")
peft = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.0,
  target_modules=r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)", task_type="CAUSAL_LM")
cfg = SFTConfig(per_device_train_batch_size=1, gradient_accumulation_steps=8, num_train_epochs=2.5, learning_rate=1e-4,
  lr_scheduler_type="cosine", warmup_steps=8, bf16=True, gradient_checkpointing=True, max_length=8192,
  assistant_only_loss=True, output_dir="/vol/forge-lora", save_strategy="epoch", logging_steps=1)
SFTTrainer(model=model, args=cfg, train_dataset=ds, peft_config=peft, processing_class=processor).train()
```
Note [H]: assistant_only_loss needs a template with generation markers; if the Glimmer template lacks them, tokenize yourself and mask labels before the last `<|start|>assistant to=user<|message|>`.
