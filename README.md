# Forge

A private AI agent that becomes a pro at your company's tool. Muse Spark (the teacher) practises the tool, the real
results are checked automatically, and Glimmer (the student) is LoRA-trained on the correct attempts only. Each company
gets its own add-on file, running offline on its own servers.

Meta Global AI Developer Hackathon 2026 (Indie track, Push the Frontier). Submission due Nov 4, 18:00 CET.

Status (2026-10-28 evening): first test done. Real gap: Spark Open 30/30 vs Glimmer + manual 20/30 (grey zone by the
rule, user decided **GO**). Spent ≈ $3.5 of $30. Next: factory (see `forge-wiki/wiki/status.md`, read it first each day).

## Folders
| Folder | What goes in it |
|---|---|
| `forge-wiki/` | the project's knowledge base (Obsidian vault) |
| `deploy/` | Glimmer on Modal |
| `docs/diagrams/` | the 6 Archify diagrams (open the `.html` files in a browser) |
| `specs/` | specs our agents write; Muse Code writes the code from them (project rule) |
| `scripts/` | setup checks (`check_cadquery.py`) |
| `data/` | practice jobs and good examples (fake data only) |
| `results/` | test results and scoreboards |
| `.venv/` | Python 3.12 with CadQuery 2.8.0 (system Python 3.15 has no CadQuery build) |

## Diagrams, in reading order
1. `forge-explained`: what Forge is
2. `forge-pro-agent`: the design
3. `forge-use-cases`: who would use it
4. `forge-prepare`: the checklist before running
5. `forge-plan`: Oct 28 to Nov 4
6. `forge-factory`: what a company installs, and what leaves it

## Main tool
CadQuery (Python CAD, exports STEP for factories). Backup: OpenSCAD.

## Where the rest lives
All paths below were checked to exist on 2026-10-28.

### Forge knowledge: `forge-wiki/` (in this folder)
- Start at `forge-wiki/index.md`. Design: `wiki/findings/forge-design-2026-10-28.md`. Plan, budget and GO rules:
  `wiki/decisions/forge-plan-2026-10-28.md`. Q&A: `wiki/findings/forge-questions-2026-10-28.md`. First Glimmer run:
  `wiki/findings/glimmer-test-1-2026-10-28.md`. Lessons: `wiki/lessons/lessons.md`.

### Glimmer on Modal (Forge's own)
- `deploy/modal_glimmer.py`: app and secret `forge-glimmer`, volumes `forge-hf-cache` / `forge-vllm-cache`, one GPU at most.
- Server password: envsave `FORGE_GLIMMER_VLLM_API_KEY` (also stored in the Modal secret). Modal workspace `my-workspace`.
- Stop after every session: `modal app stop forge-glimmer`. Check spend: `modal billing summary`.
- Training example to base the LoRA spec on: https://modal.com/docs/examples/unsloth_finetune

### Hackathon rules
- Rubric, prizes, problem statement, deadlines: `~/.hivey/agent/hiveyAgent-wiki/wiki/user/meta-hackathon-2026.md`
- Overview across the user's projects: `~/Obsidian-wikis/master/wiki/knowledge/meta-hackathon-herdshot-2026.md`

### Meta model facts (learned in the earlier HerdShot project; background only)
- Muse Spark API (endpoint, prices, contributor tier, thinking eats max_tokens): `~/swarms/herdshot/herdshot-wiki/wiki/findings/meta-model-api.md`
- Muse models and tools (Glimmer, Spark Open on Baseten, Muse Code CLI): `~/swarms/herdshot/herdshot-wiki/wiki/findings/models-and-tools-2026-10-27.md`
- Keys (envsave names): `META_HERDSHOT_API_KEY` (Muse Spark; named for the earlier project, the same Meta account), `BASETEN_API_KEY` (Spark Open)

### Research and origin
- Merged research report: `~/Research/2026-10-28-hackathon-final-validation/merged.md` (raw copies in `forge-wiki/raw/knowledge/`)
- Where the idea came from: `~/agents/superintel/reports/hackathon-software-ideas_2026-10-28.md`

## Not researched yet (gaps)
- **SAM 3.1:** how to install and run it locally on this Mac, and what it adds beyond CadQuery's exact measurements.
  Needed before the result checker is designed.
- **Glimmer LoRA recipe:** the exact training settings and memory (Meta's post-training guide, Unsloth support for
  Glimmer). Needed for the Part B spec.
- **Muse Code headless use (`muse exec`):** flags, and whether it bills the Meta credit. Needed before the first build.

## Check the setup
```bash
cd /tmp && ~/projects/forge/.venv/bin/python -I ~/projects/forge/scripts/check_cadquery.py
# expect: size mm: 20.0 20.0 20.0 and volume 7607.3 = expected
```

## How this was built
The models doing the work are Meta's: Muse Glimmer 30B (open weights, the student, served with vLLM on Modal) and
Muse Spark Open (open weights, the teacher, on Baseten).

Who wrote what:
| Part | Written by | Examples |
|---|---|---|
| Product code (runners, sandbox, company tool Keel, dashboard, tests) | **Muse Code** (Meta's coding agent), from written specs | `experiments/first-test/runner.py`, `test_runner.py`, `experiments/b2-hint/run_one_cq.py`, `sandbox_cq.sb`, `company/keel/`, `experiments/keel-exam-v2/runner.py` |
| Specs and plans (what to build, decision rules written before each run) | Claude (Anthropic), as a planning assistant | `*SPEC*.md`, `PLAN.md` files, `experiments/bmax/BMAX_SPEC.md` |
| Exams, references and solved examples (test content) | Claude, on purpose: the checker should not be the AI being tested, and Meta's models must not see the answers before a test | `experiments/*/jobs.py`, `checks.py`, `experiments/bmax/examples.py`, `experiments/option-a/` drafts |
| Analysis and check scripts | Claude | `experiments/option-a/audit/coverage_audit.py`, `selftest*.py`, one-off checks of Muse Code's work |
| Independent review before every paid run | a separate Claude verifier agent | reports in `~/agents/verifier/reports/` |
| Wiki and coordination | Claude | `forge-wiki/` |

**Correction (2026-10-29):** Claude broke the project rule by writing a few scripts itself "to save time":
`experiments/smoke/train_smoke.py` and `score_answer.py` (training smoke test), `experiments/bmax/run_session.sh` and
`run_session_v2.sh` (run scripts), `experiments/bmax/glimmer_dashboard.py` (dashboard), and
`experiments/option-a/audit/coverage_audit.py` (an analysis). They are kept only as records of runs that already
happened; their results stand. Muse Code rebuilds the ones still needed from `experiments/train/MUSE_SPEC.md` (into
`experiments/train/` and `experiments/common/`), and from now on all code is written by Muse Code.

Commits made with Claude carry a "Co-Authored-By: Claude" line. Muse Code published this repository.
