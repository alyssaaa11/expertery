# Forge

A private AI agent that becomes a pro at your company's tool. Muse Spark (the teacher) practises the tool, the real
results are checked automatically, and Glimmer (the student) is LoRA-trained on the correct attempts only. Each company
gets its own add-on file, running offline on its own servers.

Meta Global AI Developer Hackathon 2026 (Indie track, Push the Frontier). Submission due Nov 4, 18:00 CET.

Status (2026-10-28): setup done; Glimmer test 1 ran on Modal (cube ✅, L-bracket ❌, $0.57 of the $30 budget). Next:
the spec for the first test program (Muse Code builds it).

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
