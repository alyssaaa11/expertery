# Forge

**Teach a small open model to use a company's CAD tool as well as a big model with every trick, but many times
cheaper, faster and fully private.** Built with Muse Spark Open.

Meta Global AI Developer Hackathon 2026 · Indie track, Push the Frontier · kickoff Oct 26, build period Oct 27 - Nov 4,
official deadline Nov 4, 9 PM ET (our internal deadline: Nov 4, 18:00 CET).

## The idea in one minute
1. **A factory makes practice jobs** ("make a pipe tee: main tube 27.6 mm …") and a correct reference part for each one.
2. **A teacher answers them:** Muse Spark Open writes CadQuery code. Each answer runs in a locked cloud box (no network)
   and a strict **referee** compares the part with the reference. Only answers that pass are kept.
3. **A student learns:** Muse Glimmer 30B is LoRA-trained on the kept answers only.
4. **Fair final exam:** 30 frozen CAD jobs the factory never saw. The trained Glimmer must be about as correct as
   untrained Glimmer with every fair cheap fix (the "B-max" baseline, 95%), with much less time and fewer tokens per correct part.
   The decision rules were written down before any result ([`experiments/final/PLAN.md`](experiments/final/PLAN.md)).

Why it matters: companies with unreleased designs (automotive and industrial suppliers, any valuable company IP) often
may not send them to a cloud AI. A small model that runs on their own GPU and already knows their tool solves that.

## Current status (2026-10-30)
| Step | State | Evidence |
|---|---|---|
| Baselines on the 30-job exam | done: plain Glimmer 87%, Glimmer + hint 88%, Glimmer + every fair fix (B-max) 95% | [`forge-wiki/wiki/findings/bmax-baseline-2026-10-29.md`](forge-wiki/wiki/findings/bmax-baseline-2026-10-29.md) |
| Training pipeline smoke test | done: LoRA trains on one H100, merged model passes the strict referee | [`forge-wiki/wiki/findings/training-smoke-2026-10-29.md`](forge-wiki/wiki/findings/training-smoke-2026-10-29.md) |
| Factory (200 jobs, 10 families, cloud box, referee, learning loop) | built and checked; pilot next | [`experiments/factory/`](experiments/factory/), [`results/factory-gallery/index.html`](results/factory-gallery/index.html) |
| Factory main run, training, dev check, final exam | not run yet | [`experiments/final/PLAN.md`](experiments/final/PLAN.md) |

The one page with every claim and its source: [`forge-wiki/wiki/status.md`](forge-wiki/wiki/status.md). All numbers so
far: [`forge-wiki/wiki/findings/scoreboard.md`](forge-wiki/wiki/findings/scoreboard.md).

## Built during the hackathon (kickoff Oct 26, build period Oct 27 - Nov 4)
Everything in this repository was made during the hackathon. The first commit is from Oct 28. The one piece with an
older origin: `deploy/modal_glimmer.py` was adapted from the Modal deploy script of our earlier hackathon project
HerdShot, which was written on Oct 26 (kickoff day).
| Date | What was built |
|---|---|
| Oct 28 | Project setup; Glimmer served on Modal ([`deploy/modal_glimmer.py`](deploy/modal_glimmer.py), **adapted on Oct 28 from the HerdShot deploy script (written Oct 26)**, with its own app, secret and volumes); a fictional company tool "Keel" and its 30-job exam: Glimmer already scored 97.8%, so there was no room to improve and that direction was dropped |
| Oct 29 | Coverage audit; the main baseline (87% / 88% / 95%); training smoke test; FreeCAD gap test (no gap); "thinking" exam pilot (too easy, stopped) |
| Oct 30 | The factory: generator, teacher runner, cloud box and referee, learning loop, gallery; four repair rounds found by our own checks before any teacher money was spent |
| Oct 31 - Nov 4 | (planned) factory run, training, dev check, final exam, demo |

The full day-by-day log is in [`forge-wiki/log.md`](forge-wiki/log.md).

Note on the git history: early market notes (Oct 28) listed defence and medical companies as example customers. We
removed them on Oct 30 to follow the hackathon rules; Forge was never built for those uses. The history is kept as
proof of when each part was built.

## Models and licences
| Model | Role | Licence / terms |
|---|---|---|
| Muse Glimmer 30B (`meta-models/Muse-Glimmer-30B`) | the student; trained with LoRA, served with vLLM on Modal | [Apache-2.0](https://huggingface.co/meta-models/Muse-Glimmer-30B) |
| Muse Spark Open (`meta-models/Muse-Spark-Open-816B-A42B`, via Baseten) | the teacher in the factory | [Muse Model License](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B/blob/main/LICENSE.md): allows training other models on its outputs ("Derivatives"); requires "Built with Muse Spark Open" |
| Muse Spark 1.3 (api.meta.ai) | Muse Code, the coding agent that wrote the code | Meta API terms |
| Muse Wonder (api.meta.ai) | optional backup teacher (`--escalate`); **never used for training data** | [Meta Model API Terms](https://dev.meta.ai/legal/terms-of-service) §10.1 forbid training competing models on outputs without Meta's written authorization, so Wonder outputs stay out of training |

## Who wrote what (honest version)
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
  (extra runner args for the R5 self-fix step).
- **Review:** a separate Claude verifier agent reviewed every step before money was spent.
- **Published by Alyssa** (all commits are hers; most carry a "Co-Authored-By: Claude" line).

## Run it
Needs macOS or Linux, Python 3.12, and for cloud steps a Modal account (and Baseten for the teacher).
```bash
git clone https://github.com/alyssaaa11/expertery.git forge && cd forge
python3.12 -m venv .venv && .venv/bin/pip install cadquery==2.8.0 cadquery-ocp==7.9.3.1 modal==1.6.3 pytest
.venv/bin/python -I scripts/check_cadquery.py          # expect: size mm 20.0 20.0 20.0, volume 7607.3
.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad experiments/train experiments/common
.venv/bin/python experiments/factory/make_jobs.py      # 200 jobs + the self-check table, offline
.venv/bin/python experiments/factory/gallery.py --out results/factory-gallery   # pictures of 10 parts
```
Cloud steps (cost money, need `modal setup` and your own keys in environment variables `BASETEN_KEY`,
`META_HERDSHOT_API_KEY`, `GLIMMER_URL`/`GLIMMER_KEY`; our `*_session.sh` wrappers read them from envsave): `experiments/final/cloud_cq.py --check-refs --exam factory`
(Modal CPU, cents), `experiments/factory/teacher.py --ids pilot --out <dir> --budget-dollars 1.2` (Baseten).
Every paid script refuses to run past its money cap.

## Folders
| Folder | What is in it |
|---|---|
| `experiments/factory/` | the factory: job generator, teacher runner, learning loop (`patterns.py`), gallery |
| `experiments/final/` | cloud box + referee (`cloud_cq.py`), the final plan and Muse specs |
| `experiments/first-test/` | the frozen 30-job exam and its referee (`checks.py`) |
| `experiments/bmax/`, `b2-hint/`, `freecad/`, `thinking/`, `keel-exam-v2/` | earlier tests, each with its frozen PLAN |
| `experiments/train/` | training pipeline (LoRA on Modal) with exam guard and money cap |
| `deploy/` | Glimmer on Modal |
| `company/` | the fictional company tool Keel (earlier direction) |
| `results/` | run results, Muse Code logs and diaries |
| `forge-wiki/` | the project's knowledge base (Obsidian vault): status, findings, decisions, lessons |
| `docs/diagrams/` | diagrams (open the `.html` files in a browser; `.png` copies) |

Training rule: never `modal run forge_train.py::train` directly; it bypasses the exam guard and the money cap.

## Licence
This repository's own code and docs: Apache-2.0, see [LICENSE](LICENSE).

**Trained models:** a Glimmer trained on Spark Open's answers is a "Derivative" under the Muse Model License. Any
trained weights or LoRA we share will ship with the Muse Spark Open LICENSE and Usage Policy, Glimmer's Apache-2.0
licence and Usage Policy, and the notice "Built with Muse Spark Open". No weights are in this repository.

**Third-party documentation included:**
- `experiments/first-test/manual.md` (and the copies used as prompts): excerpts of the CadQuery 2.8 documentation,
  Apache-2.0 (https://github.com/CadQuery/cadquery).
- `experiments/freecad/manual.md`: excerpts of the FreeCAD documentation (FreeCAD wiki), CC-BY-3.0
  (https://wiki.freecad.org), attributed to the FreeCAD documentation authors.
