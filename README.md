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
- Knowledge (wiki): `~/swarms/herdshot/herdshot-wiki/`. Start at `wiki/findings/forge-design-2026-10-28.md`, then
  `wiki/decisions/forge-plan-2026-10-28.md` and `wiki/findings/forge-questions-2026-10-28.md`.
- Glimmer on Modal (serving script): `~/projects/herdshot/deploy/modal_glimmer.py` (app `herdshot-glimmer`, Modal
  secret `herdshot-glimmer`).
- Research: `~/Research/2026-10-28-hackathon-final-validation/merged.md`.
- Agents that write specs: `~/swarms/herdshot/`.

## Check the setup
```bash
cd /tmp && ~/projects/forge/.venv/bin/python -I ~/projects/forge/scripts/check_cadquery.py
# expect: size mm: 20.0 20.0 20.0 and volume 7607.3 = expected
```
