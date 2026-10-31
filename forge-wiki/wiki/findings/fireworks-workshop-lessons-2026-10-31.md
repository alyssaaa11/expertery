# Fireworks workshop: training lessons for Forge (2026-10-31)

**Summary**: Lessons for Forge from the hackathon's Fireworks workshop (Sinan Ozdemir, 2026-10-28). Free Glimmer SFT on
Fireworks, how much data a generative task needs, and sweeping the reasoning effort. Related: [[spark-vs-glimmer-2026-10-31]],
[[training-experiments-2026-10-30]], [[status]].
Source: ~/transcripts/Meta-Global-AI-Developer-Hackathon-Live-Session-Fireworks-AI-Workshop-2026-10-28.txt (read in full).

## Facts
- verified: **Glimmer 30B SFT is free on Fireworks until 2026-11-30** (UI + Serverless Training API, LoRA, data stays
  local and only batches are sent, zero data retention). Sources: transcript [00:05:43]-[00:07:48]; fireworks.ai/blog/train-muse-glimmer-for-free;
  fireworks.ai/pricing. The cookbook page docs.fireworks.ai/fine-tuning/training-api/cookbook/muse-glimmer still says 10/31 (probably stale).
- verified: the fine-tuned model can be downloaded, but **only after asking Fireworks support for permission** (they scan
  it first) (transcript [01:01:00]). Our "runs privately" goal needs the weights, so ask early.
- verified: serverless *inference* of Glimmer on Fireworks was deprecated on 2026-09-25; on-demand deployments still exist (search result, changelog).
- verified (data size rule of thumb, transcript [01:02:02]): 50-100 examples show signal; a few hundred for
  classification/extraction; **thousands for generative tasks**; tens of thousands for genuinely new capabilities. Our
  code generation is generative, so 154-167 examples were about 10× too few.
- verified (transcript [00:31:17]-[00:37:28]): **more reasoning is not always better**. Models can talk themselves out
  of a right answer. Sweep the effort levels (Glimmer: low / medium / high / xhigh) on the eval and pick the best for
  the cost. Forge has only ever used "high".
- verified: pass@1 is the realistic headline metric; pass@k assumes you can pick the good answer. Forge has the
  referee, so pass@3 + referee is a real product mode. State it as such.
- verified: keep a short system prompt (dozens to ~100+ tokens) that shows "the shape of the task" even when training (transcript [00:50:46]).
- verified: routing between two models often gives a system that is cheaper and better than either alone (transcript [00:09:53]).
  For Forge: Glimmer first, the referee checks, and Spark only on the failures.

## What it changes (decision pending, user)
1. Train on Fireworks for free instead of Modal: saves ≈ $2-5 per training and allows more runs. It also counts as
   partner tooling. Before relying on the downloaded weights, ask support for download permission.
2. Self-distillation must aim for 1,000+ correct examples (factory jobs are free to make; Glimmer + card answers ≈ $0.02 each on Modal at 8 workers, so 1,000 correct ≈ 1,500 tries ≈ $30 > the ≈ $16 left; either aim for 500-700 or first test more parallel workers per GPU to lower the cost per answer).
3. Cheap first test: base Glimmer + card at low / medium / high on the dev jobs. If medium is as good, answers are much
   cheaper and faster without any training (this serves the "many times cheaper" goal directly).
