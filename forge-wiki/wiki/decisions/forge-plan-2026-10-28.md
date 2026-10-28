# Forge plan (Oct 28): use cases, preparation checklist, day-by-day plan

**Summary**: The working plan for Forge after the user said "lets start" (2026-10-28). It covers who would use Forge
(4 use cases, only the OpenSCAD demo gets built), what must be ready before anything runs (4-lane checklist with
today's status), and the Oct 28 → Nov 4 schedule with one stop-or-go test on Oct 29. The design is in
[[forge-design-2026-10-28]]; all diagrams in [[forge-diagrams]].

**Sources**: main session, 2026-10-28 ~12:40; diagrams (Archify finalize + visual-check pass, screenshots inspected):
~/agents/.archify/workflow-forge-use-cases-20261028-124109/forge-use-cases.html,
~/agents/.archify/workflow-forge-prepare-20261028-124109/forge-prepare.html,
~/agents/.archify/workflow-forge-plan-20261028-124109/forge-plan.html

**Last updated**: 2026-10-28

---

## Goal
- verified 14:10: **spent so far $0.57 of $30** (Glimmer test 1, `modal billing summary`). See [[glimmer-test-1-2026-10-28]].
- decision (user, 14:00): Forge never shares HerdShot's app, secret, storage or wiki. Its own: `deploy/modal_glimmer.py` (app + secret `forge-glimmer`, envsave `FORGE_GLIMMER_VLLM_API_KEY`, volumes `forge-hf-cache`/`forge-vllm-cache`), wiki `~/projects/forge/forge-wiki`.
- **decision (user, 2026-10-28 ~13:50): the budget for the whole Forge project is $30 maximum** (all paid spend: Modal + Meta). Why (user): if Forge fails, the rest of the credits must stay free for another project. So spend in stages and stop early: first test ≤ ~$9; nothing more is spent unless it says GO. This replaces the $85–105 estimate in [[forge-questions-2026-10-28]]. Proposed fit (hypothesis): Spark on the contributor tier ~$3–5; Modal smoke test ~$3, day-1 Glimmer arms ~$4, one QLoRA run ~$6–8, scoreboard + demo in one session ~$4; buffer ~$6–10. Cuts: 40 day-1 jobs, ~600 practice tries, one training run, no retry. Modal spending limit should be ≤ $25.
- verified 13:50: the Mac has 24 GB RAM, and a local Glimmer q4 MLX copy exists at `~/models/muse-glimmer-30b-radixark-q4-mlx` (~15 GB; its model card asks for 48 GB, per `herdshot/backends/local.py`). hypothesis: running Glimmer locally could make the day-1 and scoreboard Glimmer arms $0, but it may not fit or may be slow. Not run (user: no Meta models yet).
- Project directory (decision, user asked for one, 2026-10-28 13:45): **`~/projects/forge`** (README, docs/diagrams, specs, scripts, data, results, .venv with CadQuery); local git, not pushed. The old `~/projects/herdshot/forge/.venv` is left in place, unused.
- decision (user, 2026-10-28 ~13:20): **main tool = CadQuery only** (professional, exports STEP, less public data so a bigger gap, exact measurement from code). Backup: OpenSCAD, if Spark almost never succeeds. Condition: Spark must succeed about 30–70% of the time, enough for training data but not so much that there's no gap.
- decision (user): don't run Meta models yet; install only.
- verified 13:20: CadQuery 2.8.0 in `~/projects/forge/.venv` (uv, Python 3.12, because system Python 3.15 has no CadQuery wheels). Test: 20 mm cube with a 5 mm hole measured 20×20×20 mm, volume 7607.3 mm³ = expected; STEP + STL export OK (/tmp/cq-check/check.py).
- verified 13:15: the Modal hello-world run returned 1764 (app ap-G9TskTFwCQyH89cXwLcc4U).
- Goal: show that a small offline Glimmer, trained by Forge on checked practice, beats Spark + manual on one tool (CadQuery; it was OpenSCAD until 13:20).

![[assets/diagrams/forge-use-cases.png]]

## Use cases (hypothesis: ideas, not tested with customers)
| Who | Tool | Pro agent does | Why not a cloud AI |
|---|---|---|---|
| Hackathon demo (built) | OpenSCAD | designs parts that fit | small model beats big, offline |
| Factory / engineering | CAD / CNC programs | drafts parts, engineer reviews | designs stay secret |
| Software company | internal CLI / API | right command first try | cheap, private, relearns on change |
| Hospital / bank / lab | records or lab software | runs the tool for staff | must stay offline; practises on fake data |
- Common pattern: a tool the public AI doesn't know, a way to check results automatically, and data that must stay private.

![[assets/diagrams/forge-prepare.png]]

## Preparation checklist (status checked 2026-10-28 12:40)
1. Accounts and money: keys, plus Modal credits and a spending limit (both done; user said so, 2026-10-28 ~13:20, not checked in the dashboard).
   - verified: `META_HERDSHOT_API_KEY` and `BASETEN_API_KEY` are in envsave (`envsave list`).
   - Meta credit: about $65 left of $90 ($24.49 spent, per the money decision page; recheck before spending).
2. Install: verified: Modal CLI 1.6.3 installed with `uv tool install modal` (13:20); verified logged in as workspace my-workspace (`modal profile current`, `modal app list` works); Forge's Modal secret is `forge-glimmer` (VLLM_API_KEY; value also in envsave as FORGE_GLIMMER_VLLM_API_KEY). verified: Glimmer weights are not gated (HF API `gated: False`), so no HF token is needed. Still missing: `openscad`; cadquery is also not installed (optional).
   verified OK: Muse Code 1.4.14 (`muse --version`).
3. Test the checks first: 5 hand-made correct parts and 2 wrong versions of each. A check is kept only if it passes the
   correct part and fails both wrong ones.
4. Modal smoke test (~$3–5): serve Glimmer and get 1 answer, run a tiny fine-tune (save, reload, answer), then
   `modal app stop`.
- Ready for the day-1 test when all four lanes are green.

![[assets/diagrams/forge-plan.png]]

## Schedule (decision: proposed by main session; the user has not changed it)
| Day | Work |
|---|---|
| Oct 28 | prepare + plan (this page) |
| Oct 29 | day-1 test: about 60 jobs, arms Glimmer alone / Glimmer + manual / Spark + manual. No real gap → stop: harder tool or Team Doctor |
| Oct 30–31 | our agents write specs → Muse Code builds jobs generator, renderer, checks |
| Nov 1 | Spark generates data, LoRA tune on a Modal H100 (~$12) |
| Nov 2–3 | scoreboard on frozen unseen jobs; record the 3-minute video (before/after, offline) |
| Nov 4 | submit by 18:00 CET |
- GO rules (Oct 29): Spark + manual still fails often; checks catch wrong parts reliably; fine-tune + reload works on Modal.
- Rules: agents write specs and Muse Code writes code; unseen test jobs are frozen before training; report the real result.

## Open questions
- Did the user send the Modal credits form? Do they agree with this schedule?
- Next step: install the Modal CLI and OpenSCAD, then log in (`modal setup` needs the user's browser).
