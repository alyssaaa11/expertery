# Who wrote what (full list)

The short version is in the [README](../README.md#who-wrote-what). Some folders named below (the Keel tool, the
FreeCAD and thinking tests, the Option A drafts, the blind rebuilds) are left out of the public repository's current
version to keep it short; they are in its git history, with their dates.

- **Product code** (factory, teacher runner, learning loop, gallery, cloud box and referee, runners, training pipeline,
  the Keel company tool and dashboard, their tests): written by **Muse Code** (Meta's coding agent) from written specs.
  Each build round's full event log and a readable diary are in [`results/`](results/) (`muse-*.jsonl`; diaries
  `muse-final-r1*.diary.md` for the factory rounds): every file Muse read, edited and ran. Muse Code cannot commit, so
  its work was committed by Alyssa.
- **Written by Claude (Anthropic), on purpose:** specs and plans (`*SPEC*.md`, `PLAN.md`), the wiki, and **all exam
  content and referees**, so the AI being tested never writes its own test:
  `experiments/first-test/` (`jobs.py`, `checks.py`, `expected.json`, `selftest.py`, `blind/`, `run_live.sh`),
  `experiments/keel-exam/` and `keel-exam-v2/` (`jobs.py`, `referee.py`, `selftest.py`, `score_blind.py`, `blind/`),
  `experiments/thinking/` (`thinking_jobs.py`, `selftest.py`, `hand/`), `experiments/option-a/` drafts,
  `experiments/bmax/examples.py`, `scripts/`, and the blind-rebuild answers in `results/blind-rebuild*`.
- **Also written by Claude (disclosed):** `deploy/modal_glimmer.py` (adapted from HerdShot, later edited by Muse Code),
  and a few early run scripts (`experiments/smoke/train_smoke.py`, `score_answer.py`,
  `experiments/bmax/run_session*.sh`, `glimmer_dashboard.py`, `experiments/option-a/audit/coverage_audit.py`). They
  are records of runs that already happened; Muse Code rebuilt the parts still in use.
- **Small fixes by Claude (disclosed, user decision 2026-10-30):** `experiments/final/runner_final.py` `ft_messages`
  (optional rule card in the system message via FORGE_RULE_CARD); `experiments/final/RULE_CARD.md` (content).
  2026-10-31 (verifier B3b/B6b): `cloud_cq.build_sandbox(lifetime_s=…)` + its use in `make_jobs.py` (the reused batch
  box lives up to 3 h instead of 90 s), and `forge_train.check_rule_card` strips the card like `ft_messages`; 2 tests. Also `experiments/final/run_base_session.sh`: a `.jsonl`
  jobs-file spec and a `WORKERS` env (default 8) for the R5 runs. `runner_final.load_factory_jobs_file` keeps each job's
  reference for grading only (verifier B7). `experiments/final/RULE_CARD.md` v2 (two lines added after the R5 pilot's
  crashes, user decision B; v1 kept as RULE_CARD_V1.md) and its sha256 constant in `forge_train.py`. `experiments/viewer/make_viewer.py` default_render_fn
  (drives one cloud sandbox from the Mac instead of calling the Modal Function directly). `run_base_session.sh` RUNNER_EXTRA env
  (extra runner args for the R5 self-fix step). The same `.jsonl` spec, WORKERS and RUNNER_EXTRA in
  `run_final_session.sh` (R5 dev step). `experiments/r5/compare_dev.py` (dev reading: reuses compare.py's paired
  bootstrap; reads results only).
- **Small fixes by Claude on Nov 1-2 (disclosed):** `experiments/r5/hints.py` (max_tokens 16,000, finish_reason stored,
  word-match code filter; verifier S1-S3); `experiments/r5/build_mix.py --keep-hint` (tutoring rows; user decision);
  `experiments/r5/RULE_CARD_V3_RETRY.md` (one card line, hinted retries only); `experiments/final/compare_ft_acard.py`
  and `experiments/final/compare_ftx.py` (pre-registered readings, reuse compare.py); data prep of
  `results/r5-hints-2026-11-01/hint_input.jsonl`. **Muse Code** built the FTX second-look arm (`--bx-loop`) from
  `specs/MUSE_FTX_2026-11-02.md` and pushed the repo to GitHub.
- **The live demo (Nov 2):** page, backend and Modal web app written by **Muse Code** in 4 rounds from
  `specs/MUSE_PRODUCT_2026-11-02.md` (logs `results/muse-product-p*.jsonl`); the page design (mockup in
  `docs/product/mockup/`) by Claude with Alyssa. **Small fixes by Claude (disclosed):** `app/backend/loop.py` (after a
  build the model sees its own measurements and may fix, the FTX rule; + 2 tests); `deploy/modal_web.py` (static page
  mounted after the API routes; deploy settings baked into the image; FORGE_URL startup check); phone CSS in
  `app/web/styles.css`; wording ("strict" removed), footer links and the real recorded run in `app/web/`;
  `app/web/dev_server.py` fake counters (local preview only, not deployed).
- **Review:** a separate Claude verifier agent reviewed every step before money was spent.
- **Published by Alyssa** (all commits are hers; most carry a "Co-Authored-By: Claude" line).
- **Small fixes by Claude on Nov 4 (disclosed):** README numbers and wording; live page wording in `app/web/index.html`
  (manual size, the factory's teacher step, the YouTube video link) and its static test.
