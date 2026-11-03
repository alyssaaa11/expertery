# Install Expertery v0

Expertery v0 is a command-line product a company installs into its OWN
Modal cloud account: its past work, exams and trained model stay in
that account. v0 supports one tool: CadQuery CAD.

## Install

Needs Python 3.12+, `uv`, and `modal` (run `modal setup` first).

```sh
./install.sh
expertery init
```

`install.sh` checks `uv` and `modal` exist, runs
`uv tool install --editable "<repo dir>"`, then prints the next step
(`expertery init`). It never asks for or prints secrets.

`expertery init` checks the Modal token works (`modal profile
current`), reports whether a reader key is configured
(`EXPERTERY_READER_KEY`, falling back to `BASETEN_API_KEY`;
present/missing only, values are never printed), deploys the CAD box +
grader apps (the same deploy `experiments/final/cloud_cq.py` defines)
into the current Modal account, and writes
`~/.expertery/config.json` (tool `cadquery`; reader url/model
defaults from the factory teacher, overridable via
`EXPERTERY_READER_URL` / `EXPERTERY_READER_MODEL` so a company can
point at its own Spark Open or Glimmer server).

## Privacy model (what runs where)

- Past work, exams and the trained model live in the company's own
  Modal account. Nothing leaves it except reader API calls.
- Reader calls (Meta Muse Spark Open by default, or the company's own
  server via `EXPERTERY_READER_URL`) see ONLY the request text, plus
  the reference part's measurements in the explainer call. They NEVER
  see reference code (`part.py` is only built in the company's cloud
  box and graded by its cloud grader).
- Reference programs are trusted company code and build inside the
  locked cloud box; model answers always run in a fresh locked
  sandbox, never on a laptop.

## Commands

All examples assume the demo past work in `examples/past-work-brackets`
(one folder per job: `request.txt` + `part.py`).

```sh
# 1. Turn past work into exam candidates ($ cap required).
expertery exam build examples/past-work-brackets --out results/my-exam \
  --cap-dollars 5 --readers 2 --workers 4

# 2. Decide every FLAGGED job (accept / keep / drop / edit).
expertery exam review results/my-exam
expertery exam review results/my-exam --accept-all   # scripts/tests

# 3. Lock the exam (writes exam.jsonl + FREEZE.txt).
expertery exam lock results/my-exam

# 4. Run the exam on the trained or the base model ($ cap required).
expertery test --exam results/my-exam/exam.jsonl --model trained \
  --name final --out results/my-run --cap-dollars 5 --k 3
expertery test --exam results/my-exam/exam.jsonl --model base \
  --name base --out results/my-run-base --cap-dollars 5 --loop

# 5. Serve the trained model.
expertery serve --name final

# 6. Train on practice records ($ cap required; guarded entrypoint,
#    never `modal run ...::train`). Practice data in v0 comes from
#    the factory scripts (experiments/factory, experiments/r5).
expertery train --data train_records.jsonl --out my-model --cap-dollars 20

# 7. Config, Modal apps, latest exam dirs.
expertery status
```

Every command that can spend money takes `--cap-dollars` (required,
> 0) and `--dry-run` (prints the plan and the estimated spend, spends
nothing). Money: each model call is costed from its tokens with the
teacher's price constants; no new calls start once the next could
pass the cap; `spent_estimate` is written to the output.

`exam review` accepts `--accept-all` / `--keep-all` for scripts and
tests (recorded with reviewer `"flag"`). Accepted or edited texts are
NOT re-checked automatically; `report.md` says to re-run
`exam build` on edited jobs to re-check them.

## Honest limits (v0)

- CadQuery only. `part.step` files are marked SKIPPED (not supported).
- Practice-job generation still uses the factory scripts
  (`experiments/factory`, `experiments/r5`); train/serve need GPU
  money in the user's own account.
- `exam build` refuses to overwrite an exam dir that has `exam.jsonl`;
  `exam lock` refuses while any FLAGGED job has no decision, and while
  any DEFERRED job (cap stopped new calls) is unfinished.
- A FLAGGED job is not a model failure: the wording may be read two
  ways. A person decides.
