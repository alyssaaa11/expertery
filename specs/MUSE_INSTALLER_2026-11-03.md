# Muse Code task: Expertery v0, an installable private factory with an exam agent (2026-11-03)

Repo: ~/projects/forge. Read README.md first (what Expertery is), then this spec. Build a command-line
product `expertery` that a company installs into ITS OWN Modal cloud account (private: its past work, exams and
trained model stay in its account). v0 supports one tool: CadQuery CAD.

Hard rules
- Do NOT change: experiments/brackets/** (frozen), examples/past-work-brackets/** (demo data), experiments/final/
  RULE_CARD.md, experiments/first-test/**, results/**, forge-wiki/**, README.md, app/**, deploy/modal_web.py.
- You MAY import/reuse (not rewrite) existing modules: experiments/final/cloud_cq.py (run_answer_in_box, the grader
  app `forge-cq-grader` and its `grade(exam, job_id, brep_bytes, reference=...)` / `measure_brep`),
  experiments/first-test/runner.py (SYSTEM_PROMPT, build_messages("A", text, ""), build_body),
  experiments/factory/teacher.py (SPARK_MODEL, SPARK_URL, MAX_TOKENS, TEMPERATURE, TOP_P),
  experiments/final/run_final_session.sh and run_base_session.sh, experiments/train/forge_train.py, deploy/modal_forge.py.
- No Modal, network or model call while you work. All tests use fakes. Run:
  `.venv/bin/python -m pytest expertery -q` and the existing `.venv/bin/python -m pytest experiments/final -q`.
- In any zsh/sh you write, always brace variables next to a colon: "${JOBS}:x", never "$JOBS:x" (zsh modifiers).

## Layout
- `pyproject.toml` at the repo root: name `expertery`, version 0.1.0, requires-python >=3.12, dependency `modal`,
  console script `expertery = expertery.cli:main`, package `expertery` only.
- `expertery/` package: `cli.py` (argparse, subcommands below), `config.py`, `exam_agent.py`, `cloud.py` (thin
  adapters over cloud_cq + session scripts; the repo root is the parent of the package dir; add the needed
  experiments dirs to sys.path inside the adapter, never at import time of cli.py), `tests/`.
- `install.sh` at the repo root: checks `uv` and `modal` exist, runs `uv tool install --editable "<repo dir>"`, then
  prints the next step (`expertery init`). It never asks for or prints secrets.
- `docs/INSTALL.md`: install, privacy model (what runs where), each command with an example, honest limits (v0:
  CadQuery only; practice-job generation still uses the factory scripts; train/serve need GPU money in the user's
  account).

## Commands
Every command that can spend money takes `--cap-dollars` (required, > 0) and `--dry-run` (prints the plan and the
estimated cost, spends nothing). Money: estimate each model call from tokens with the teacher's price constants if
present (else a constant in config.py with a comment), stop starting new calls when the next could pass the cap,
write spent_estimate to the output.

1. `expertery init [--dry-run]`: checks the Modal token works (`modal profile current` via subprocess), checks env
   for the reader key (EXPERTERY_READER_KEY, falling back to BASETEN_API_KEY; report present/missing, never print
   values), deploys the CAD box + grader into the current Modal account (the same deploy cloud_cq uses; find it in
   cloud_cq.py / its docstring), writes `~/.expertery/config.json` (tool "cadquery", reader url/model defaults =
   teacher SPARK_URL / SPARK_MODEL, overridable by EXPERTERY_READER_URL / EXPERTERY_READER_MODEL so a company can
   point at its own Spark Open or Glimmer server).
2. `expertery exam build <past-work-dir> --out <exam-dir> --cap-dollars X [--readers 2] [--workers 4] [--dry-run]`
   Past work = one folder per job: `request.txt` + `part.py` (CadQuery code that defines `result`). (`part.step`:
   print "not supported in v0" and mark the job SKIPPED.) For each job:
   a. Reference check: run part.py in the cloud box (run_answer_in_box); it must build one valid solid. Else status
      BROKEN_REFERENCE (with the error).
   b. Readers: the reader model (Meta Muse Spark Open) gets ONLY request.txt with the factory prompt
      (runner.build_messages("A", text, "") + build_body), `--readers` independent tries; extract the code block
      like the existing runner does; run each in the box; grade each against the reference with the cloud grader
      (exam "factory", reference = part.py source; 0.2% rule as today).
   c. All readers PASS → READY. Any reader fails → one more reader call ("explainer") that sees the request text,
      the reference part's measurements (bbox, volume, solids) and each failed reader's measurements or run error,
      but NEVER the reference code, and must return JSON {"phrase": ..., "why": ..., "suggested_request": ...}
      naming the wording a careful engineer could read two ways. Status FLAGGED with that suggestion. If the reply
      is not valid JSON → FLAGGED with suggestion null and the raw text kept.
   Outputs in exam-dir: `candidates.jsonl` (id, text, reference, status, reader verdicts, measurements, suggestion),
   `calls.jsonl` (every model call with tokens, seconds), `report.md` (one table: job, status, readers passed,
   phrase/why; totals; spent_estimate; the line "A FLAGGED job is not a model failure: the wording may be read two
   ways. A person decides."). Refuse to overwrite an exam-dir that has `exam.jsonl`.
3. `expertery exam review <exam-dir> [--accept-all | --keep-all]`: for each FLAGGED job shows original, phrase, why,
   suggestion and asks [a]ccept suggestion / [k]eep original / [d]rop job / [e]dit text (reads one line). Writes the
   decision + who/when (`"reviewer": "human"`, ISO time) into candidates.jsonl. --accept-all / --keep-all exist for
   scripts and tests (record "reviewer": "flag"). Accepted or edited texts are NOT re-checked automatically; report.md
   says "re-run `exam build` on edited jobs to re-check them".
4. `expertery exam lock <exam-dir>`: refuses while any FLAGGED job has no decision; writes `exam.jsonl` in the runner
   jobs-file format (id, family "past-work", level "unknown", text, reference) for READY + accepted/kept/edited jobs,
   and `FREEZE.txt` with the sha256 of exam.jsonl and the date. Refuses if exam.jsonl exists.
5. `expertery test --exam <exam.jsonl> --model trained|base --name <model-name> --out <dir> --cap-dollars X
   [--loop] [--k 3] [--dry-run]`: trained → run_final_session.sh with FORGE_MODEL_NAME=<name>, `--pilot ""`,
   `--run "${EXAM}:<sub>:FT:<k>"`; base → run_base_session.sh with `--run "${EXAM}:<sub>:A:<k>"`; `--loop` sets
   RUNNER_EXTRA="--bx-loop" (base + loop also needs FORGE_RULE_CARD; trained + loop must run without it; pass the
   env through exactly). After a trained run, redeploy deploy/modal_forge.py with the same FORGE_MODEL_NAME (the
   session script stops the app; a live product may depend on it). Prints the summary.json pass rate.
6. `expertery serve --name <model-name> [--dry-run]`: deploys deploy/modal_forge.py with FORGE_MODEL_NAME; prints the
   URL. (The web page is not part of v0.)
7. `expertery train --data <train_records.jsonl> --out <volume-subdir> --cap-dollars X [--dry-run]`: runs
   `forge_train.py r5 --data ... --out ... --cap-dollars ...` (the guarded entrypoint; never `modal run ...::train`).
   Help text says practice data comes from the factory scripts (experiments/factory, experiments/r5) in v0.
8. `expertery status`: config (no secrets), which Expertery apps are deployed in the account (`modal app list`),
   latest exam dirs found under the current folder.

## Tests (expertery/tests, all offline with fakes)
- exam build: READY / FLAGGED / BROKEN_REFERENCE / SKIPPED(step) paths with fake box, grader and reader; explainer
  never receives part.py text (assert it is absent from the messages); invalid explainer JSON → FLAGGED, null
  suggestion; cap stops new calls; dry-run makes zero calls; refuses an exam-dir with exam.jsonl.
- review: accept/keep/drop/edit recorded with reviewer and time; --accept-all.
- lock: refuses with undecided FLAGGED; writes runner-format rows that runner_final.load_factory_jobs_file accepts;
  FREEZE sha matches; refuses overwrite.
- test/serve/train/init: the exact subprocess argv and env built (mock subprocess), including "${...}:" safe specs,
  FORGE_RULE_CARD rules, and the redeploy after a trained test; no secret value ever in printed output.
- `python -m expertery.cli --help` lists all commands.

## Report back
Files added/changed, both pytest summary lines, and anything you could not do exactly as written.
