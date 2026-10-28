# Value and market: why Forge instead of just using the big model (Oct 28)

**Summary**: Answers to the user's questions after the first test: who would use Forge instead of a cloud big model,
what it costs per job, what an honest pitch can claim, the honest downsides, a space-company example, and how to
demonstrate a run that happened in the background. **Not validated with customers**: the market part is hypothesis.

**Sources**: main session 2026-10-28 ~19:00–21:00; cost numbers from `results/first-test-main/` (report.md, calls.jsonl)
and `modal billing summary`; Spark Open facts in [[tools-and-services]].

**Last updated**: 2026-10-28

---

## Why not just use the big model?
- If a company **can** send its work to a cloud model and doesn't mind the price, **it doesn't need Forge**: use the big
  model. (User agreed: "some companies will rent".)
- Forge is useful only where the big model **can't** be used, or is too costly:
| | Spark Open (teacher) | Glimmer + manual | Forge-trained Glimmer |
|---|---|---|---|
| Quality on our exam | 100% | 67% | **not measured yet** |
| Private / offline | cloud, or ~8 big GPUs to self-host (~537 GB) | 1 GPU | 1 GPU |
| Self-host price | ~$30/h (8 GPUs, estimate) | ~$2.50/h | ~$2.50/h |
- Pitch (decision of wording, hypothesis until training works): **"Forge gives the big model's skill to a small,
  private model a company can run on one GPU, without sending its designs anywhere."** Not "a skill nobody has".

## Cost per job (verified from the first test, rough)
- Spark Open on Baseten: $0.78 for 30 jobs → **~$0.026/job**.
- Glimmer on a busy rented A100: ~60 jobs in ~13 min at $2.50/h → **~$0.009/job** (~3× cheaper), but only while the GPU
  is busy. An idle GPU still costs $2.50/h, so the cloud is cheaper at low volume. Rough break-even: tens of
  thousands of jobs per month with a non-stop GPU (hypothesis).
- One-time training per tool: ~$10–15 (estimate for the factory run).

## Who would want Forge (hypothesis)
| Company | Choice | Why |
|---|---|---|
| Low volume, no secrets | cloud big model | simple, cheap at low use |
| High volume | Forge | ~3× cheaper per job when busy |
| Secret designs (aerospace, defence, medical, valuable IP) | Forge | not allowed to send data to the cloud: "allowed vs not allowed", not price |
| Offline sites (factory floor) | Forge | no cloud |
- The strongest reason is **privacy**; cost is second and only at high volume.

## Example: a space company (user question)
- Fits well: export-control rules (ITAR/EAR) often forbid sending designs to cloud AI; special tools (CAD scripting,
  orbit or stress simulators, internal CLIs); mistakes are expensive.
- Conditions for any tool: (1) controlled by code, (2) results checkable automatically (measure, simulate, test),
  (3) practice jobs can be generated without real secret data.
- The teacher must then also run inside (self-hosted Spark Open) or only see fake practice data.
- Limit of our evidence: CadQuery is public and the teacher already knows it. For a secret internal tool even the
  teacher may fail; Forge would need many teacher attempts filtered by the referee (not tested).

## The honest downside (explained simply to the user)
- Glimmer + manual already solves 2 of 3 jobs, so training can win at most +33 points (and part of it may be fixed
  by a prompt hint; see the B2 proposal in [[first-test-2026-10-28]]).
- The teacher scored 100%, so "the small model beats the big one" is impossible; the best case is "nearly matches it,
  privately and cheaply".

## How to demonstrate a background run
- Everything is in the log: every prompt, answer, code, measurement, verdict and time (`calls.jsonl`). Any part can
  be rebuilt exactly, for free, and a judge can check it.
- Prototype: `results/first-test-main/demo/replay.html` (3 jobs side by side, rebuilt from the log; the drawings are
  cropped and have no axes, so position errors are invisible. The real viewer needs a red overlay for mismatches).
- Demo plan (proposal, not built): (1) replay viewer with rotatable 3D parts, mismatch in red and the scoreboard
  filling; (2) a live moment of 1–2 jobs; (3) before/after: Glimmer + manual vs Forge-trained Glimmer, offline;
  (4) 3-minute video (HyperFrames). The viewer would be built by Muse Code alongside the factory.
