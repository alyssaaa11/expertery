# Forge

A private AI agent that becomes a pro at your company's tool. Muse Spark (the teacher) practises the tool, the real
results are checked automatically, and Glimmer (the student) is LoRA-trained on the correct attempts only. Each company
gets its own add-on file, running offline on its own servers.

Meta Global AI Developer Hackathon 2026 (Indie track, Push the Frontier). Submission due Nov 4, 18:00 CET.

Status (2026-10-28): planning and setup done. No Meta models have run yet (user decision). Next: test the checks,
then the Glimmer test on Modal.

## Folders
| Folder | What goes in it |
|---|---|
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

### Hackathon rules
- Rubric, prizes, problem statement, deadlines, user decisions: `~/.hivey/agent/hiveyAgent-wiki/wiki/user/meta-hackathon-2026.md`
- Hackathon overview (all projects, models, money, lessons): `~/Obsidian-wikis/master/wiki/knowledge/meta-hackathon-herdshot-2026.md`

### Forge knowledge (wiki: `~/swarms/herdshot/herdshot-wiki/`)
- Design (start here): `wiki/findings/forge-design-2026-10-28.md`
- Plan, checklist, schedule, day-1 GO rules: `wiki/decisions/forge-plan-2026-10-28.md`
- Q&A (privacy, why CadQuery, why test Glimmer, cost, selling): `wiki/findings/forge-questions-2026-10-28.md`
- Why Forge was picked (two research reports merged, prior art, the risk paper 2607.08938): `wiki/findings/final-pick-research-2026-10-28.md`
- All diagrams with explanations: `wiki/findings/forge-diagrams.md`
- Lessons from all experiments (e.g. thinking eats max_tokens; run the cheap baseline first): `wiki/lessons/lessons.md`

### Models, keys and money
- Muse Spark API (endpoint, prices, contributor tier, quirks): `wiki/findings/meta-model-api.md`
- Models and tools (Muse family, Glimmer, Spark Open on Baseten, Muse Code CLI): `wiki/findings/models-and-tools-2026-10-27.md`
- Money decisions and spend so far: `wiki/decisions/money-2026-10-27.md`
- Cost limiter (shared ledger, Modal warm-idle charging): `wiki/findings/cost-limiter.md`; caps in `~/projects/herdshot/caps.toml`
- Keys (envsave names only): `META_HERDSHOT_API_KEY` (Muse Spark), `BASETEN_API_KEY` (Spark Open), `HERDSHOT_GLIMMER_VLLM_API_KEY` (Glimmer server password; also the Modal secret `herdshot-glimmer`)
- Modal: workspace `my-workspace`, CLI logged in, spending limit set by the user

### Code we reuse
- Glimmer on Modal (vLLM serving): `~/projects/herdshot/deploy/modal_glimmer.py`, backend `~/projects/herdshot/herdshot/backends/modal.py`
- Modal LoRA fine-tune example to base the training spec on: https://modal.com/docs/examples/unsloth_finetune

### Research and origin
- Merged research report (scores, sources, day-1 gate): `~/Research/2026-10-28-hackathon-final-validation/merged.md`
- Where the idea came from (superintel software-only search): `~/agents/superintel/reports/hackathon-software-ideas_2026-10-28.md`

### Agents
- The swarm that writes specs: `~/swarms/herdshot/` (its briefs still say Claude agents write code; update them before building)

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
