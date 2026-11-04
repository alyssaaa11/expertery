# Positioning, pitch and submission decisions (2026-11-03)

**Summary**: What Expertery claims and how it is sold, decided with the user on Nov 3: lead with "learns only from
proven answers", not privacy or cost; name stays Expertery; a private factory sold as setup + licence.

**Sources**: main session 2026-11-03 (user messages quoted below); user's research screenshot "What hurts companies
most"; video review of ~/agents/hyperframes/videos/expertery-submission (19 frames captured 2026-11-03).

**Last updated**: 2026-11-04

---

## Claims
- decision (user, 2026-11-03): removed the page note "Proven on CAD so far. Final training run: about 2 hours and about
  $10 of GPU time." (bb6676e). Why: the $10 was only the final LoRA run; data generation cost ~$20 more.
- decision (Claude, corrected 2026-11-03): **privacy is not what makes Expertery unique** (a card + untrained Glimmer is
  just as private; many products promise privacy). The unique part: the model is trained only on answers a referee
  proved correct in your tool. The Oct 28 "privacy is the strongest reason" ([[value-and-market-2026-10-28]]) is
  superseded as a pitch lead.
- decision (Claude, proposed): headline "Your AI stops guessing how your tool works. It learns only from answers that
  were proven to work." + proof line "On CAD: 53% → 92% correct, no manual." Pain behind it: AI invents functions that
  don't exist; "almost right" output (user's research table).
- hypothesis: training's measured edge over a rule card is cost (exam: 3,352 vs 4,145 tokens per correct part; prompt
  16k vs 80k), not quality (83.3% vs 85.6%, a tie). "No expert needed" is NOT true for this run (the card made the
  training answers).

## Name
- decision (user, 2026-11-03): name **Expertery** everywhere user-facing (5478883); internal ids keep old names
  (homegrown-web, Modal Dicts, Vercel project homegrown-factory, forge-*). "Smelter" rejected: smelter.ai exists (AI,
  social listening) and a second rename a day before the deadline; smelting kept only as a metaphor.

## Business model (hypothesis, not validated with customers)
- Sell a private factory: install in the company's own cloud account (v0), later on-prem / offline. Paid as a setup fee
  per tool (adapting generator, sandbox, referee; building the exam) + yearly licence + support.
- Hardware: training needs one 80 GB GPU for ~2 h, rentable (~$10-30); daily use one GPU; the teacher (Spark Open,
  ~700 GB) is optional because Glimmer learns mostly from its own checked answers.
- Exams come from 30-100 past jobs (locked, never trained on); practice jobs (~2,000) come from a job generator with
  known answers (Muse Code wrote ours). A guard checks no practice job copies an exam job.

## Submission items
- verified (user): deadline Wed Nov 4, 9 PM ET = Thu Nov 5, 03:00 CET; own target Nov 4, 18:00 CET.
- verified: live demo spend $8.84 of its $15 total cap (Modal Dict homegrown-spend, 2026-11-03); Modal total ≈ $78 of
  $90 (Oct $37.47 + Nov $40.55). decision pending (user): keep the $15 cap for judging or raise it.
- Open Weights prize ($10k "Best Build on Meta Open Weight Models", third-party summaries only, official page not
  read): the model qualifies on substance; missing = downloadable weights. Hugging Face repos can be made private or
  deleted later (copies already downloaded stay). Proposed: gated repo + a fresh-download reproducibility check
  (fingerprint + 10 practice jobs, ≥ 8 pass). decision pending (user): publish or skip.
- Video review (Claude, 2026-11-03): numbers match NUMBERS.md; fix before submitting: lead the proof with the
  hand-made exam (83 → 92) not the easier 62 → 96; the demo crop cuts the page title; decide "Proven on CAD" on
  purpose. Face on camera not required (rules found say nothing); own voice recommended for hook and close.
