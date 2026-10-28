# Forge questions answered (Oct 28 afternoon): privacy, tool choice, Glimmer test, cost, selling it

**Summary**: The user's questions about Forge on the afternoon of 2026-10-28, and the answers. Each company gets its
own private add-on. CadQuery was picked over OpenSCAD and other "open door" apps. The Glimmer test on Modal is needed
before anything else. The whole project should cost about $85–105. Forge can be sold without our credits because each
customer pays for its own computing. The selling part is not validated.

**Sources**: main session with the user, 2026-10-28 ~12:50–13:30. Commands and outputs are noted inline. Plan:
[[forge-plan-2026-10-28]]; design: [[forge-design-2026-10-28]]; diagrams: [[forge-diagrams]] (6, the factory).

**Last updated**: 2026-10-28

---

## 1. "If 2 companies use my agent, how is it private?"
- **Forge is the factory, not one shared agent** (decision of meaning, user's framing accepted). Every company starts
  from the same free Glimmer and gets its **own add-on file** (LoRA, a few hundred MB), trained only on its own tool
  and running on its own servers. Glimmer itself holds no company data, so A's add-on can't leak B's.
- Catch 1: if *we* host every company's agent (e.g. on our Modal), the data is separated but we could see it. The fully
  private version is self-hosted: the company runs Forge inside its own cloud or servers.
- Catch 2: the teacher, Muse Spark, is Meta's cloud API, so the practice jobs go through Meta. The rule is to use
  **fake practice data only**. Zero-cloud option (hypothesis, not tested): Spark Open self-hosted as the teacher.
- Pitch line: "Forge runs inside your company. You get your own trained Glimmer, and nobody else ever sees it."
- Diagram: forge-wiki/wiki/assets/diagrams/forge-factory.png. Company servers hold the control panel → tool sandbox → result
  checker (SAM 3.1 + measuring, with check self-test) → good examples → trainer (base Glimmer) → exam room → pro
  agent → employees. Only Muse Spark is outside.

## 2. Why CadQuery ("why not another app with an open door?")
- What Forge needs from a tool: controlled by code, results checked automatically, runs headless on a server, free and
  quick to set up.
| App | Door | Verdict |
|---|---|---|
| CadQuery | Python code | **main tool** (decision, user, 13:20): professional, exports STEP, less public data so a bigger gap, exact sizes from code |
| OpenSCAD | whole app is code | backup: easier, but popular, so Spark may already be good at it |
| FreeCAD | Python | big and slow to automate |
| Blender | Python | art tool, so "correct" is hard to check |
| KiCad | CLI | a later idea; harder to demo |
| Fusion 360 / Onshape | cloud API | paid and cloud-only, which breaks "private, offline" |
| SolidWorks | none here | Windows, paid licence |
- **Condition (hypothesis, measured on day 1):** Spark must succeed about 30–70% of the time. Near 0% means no good
  examples to train on (switch to OpenSCAD). Near 100% means there's no gap to show.
- verified: CadQuery 2.8.0 works here. A 20 mm cube with a 5 mm hole measured 20×20×20 mm and 7607.3 mm³ (= the
  formula), and STEP + STL export worked (`/tmp/cq-check/check.py`, 13:20).

## 3. Why test Glimmer on Modal first
- The whole of Forge depends on three things we have never run: Glimmer (~60 GB) starts on a Modal GPU, LoRA training
  works, and the trained add-on loads back. Finding a failure on Nov 1 would leave no time, and the Oct 29 day-1 test
  needs Glimmer running anyway (2 of its 3 arms).
- Part A (the script exists, `deploy/modal_glimmer.py`): deploy, ask 1 CadQuery-style question, note start time and cost,
  `modal app stop`. Part B: write a spec → Muse Code writes a tiny LoRA script (~10 fake examples, a few steps), save,
  reload, ask, stop. Pass: both answer, under about $5, nothing left running.
- decision (user, 13:20): **don't run Meta models yet; install only.** Neither part has run.
- Installs: nothing to install locally for the Glimmer test, because vLLM and the training stack run on Modal's side.

## 4. Total cost
- Superseded: the first estimate ($85–105) was replaced by the user's **$30 cap**. Real spend and the current
  budget are on [[status]]; the next stage's costs are in [[factory-plan-2026-10-29]].

## 5. "If I run out of credits, how can I sell it?"
- Customers pay for their own computing. We sell the software and the setup. The customer's GPUs (their Modal, AWS or
  servers) and Spark key are their cost, so our computing cost per customer is about $0.
- Ways to charge: licence or subscription (self-hosted, most private); a fixed price per trained agent (compute
  ~$15–60 per run, paid out of the customer's payment); a free core plus paid support and new tools.
- Credits matter only for the hackathon build and demo. A prize ($25K–$150K Indie) far exceeds them, and startup
  credit programs exist.
- **Not validated:** this is how to charge, not proof that companies would pay. Before treating Forge as a business,
  run the user's problem frameworks (future-problem-discovery + problem-acceleration protocol) after the hackathon.

## Setup state reached (verified, 2026-10-28)
- Modal CLI 1.6.3 (`uv tool install modal`); logged in as workspace my-workspace (`modal profile current`); hello-world
  returned 1764 (app ap-G9TskTFwCQyH89cXwLcc4U); secret then `herdshot-glimmer`; since 14:10 Forge uses its own secret `forge-glimmer` (envsave
  `FORGE_GLIMMER_VLLM_API_KEY`); Glimmer weights not gated (HF API `gated: False`). The user confirmed credits and
  a spending limit.

## 6. "Is Spark Open as smart as Muse Spark 1.3?" (2026-10-28 ~16:50)
- verified (PyTorch blog https://pytorch.org/blog/muse-spark-open/ and the Hugging Face model card): Spark Open shares
  the **same base model** as Muse Spark 1.3, with extra safety post-training because it runs without Meta's
  guardrails. 816B total / 42B active, 1M context, released Oct 15 2026. The licence requires "Built with Muse Spark
  Open" in products.
- hypothesis (one secondary source, MindStudio): Artificial Analysis Intelligence Index, Spark 1.3 = 48 vs Spark Open
  = 39, i.e. the open version is somewhat weaker. Artificial Analysis's own pages don't list Spark Open, and their
  scores were rescaled between articles, so the gap is not confirmed.
- What it means: the first test measures Spark Open on our own jobs, and the "C ≥ 30%" rule checks whether it is good
  enough to teach. Fallback if too weak: Muse Spark 1.3 on Meta credits (~$1.50), with the user's OK.
- Correction: the full Spark Open is ~537 GB even in NVFP4, so a company running the teacher itself needs several big
  GPUs. The small student (Glimmer) is the part any company can run cheaply.
