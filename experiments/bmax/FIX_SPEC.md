# Fix spec for Muse Code: B-max + sandbox fixes (verifier report forge-bmax-2026-10-29, GO WITH FIXES)

Status: written by Claude 2026-10-29; needs the user's yes before Muse Code runs. Same rules as BMAX_SPEC.md (edit
only experiments/first-test/runner.py, test_runner.py, experiments/b2-hint/run_one_cq.py; never open blind/,
experiments/option-a/ or expected*.json contents; no network/model calls; no commit; existing arms' request bodies
must stay byte-identical).

1. **DONE detection** (verifier 2): a reply with **no Python code block** ends the loop (the model is satisfied),
   whatever its text ("DONE", "DONE.", "**DONE**", "Looks right"). Only a reply that contains a code block is run.
   Final = the most recent program that built.
2. **Failed call in round 2/3** (verifier 3): a network/HTTP failure or empty reply after round 1 ends the loop and
   keeps the most recent program that built (FAIL if none), exactly like a cut-off. Only round 1 can make a job INVALID.
3. **Self-check after a fixed crash** (verifier 8, my spec bug): after ANY build, if calls remain, send the self-check
   message. So crash → fixed build → self-check = 3 calls. Update the test that expected 2 calls.
4. **No trust in the answer's stdout** (verifier 6): `run_one_cq.py` always writes the solid to the fixed path
   `<scratch>/answer.step` and the measurements to `<scratch>/measure.json`; the runner reads only those two files
   (realpath must be inside the scratch dir) and ignores stdout for them. Run the answer with
   `ns = {"__name__": "__main__"}` (verifier 9). Test: an answer that prints a decoy `.step` path or a fake MEASURE
   line, or registers an atexit writer elsewhere, gets its real part scored.
5. **reasoning setting** (verifier 1): make BX's value a constant `BX_REASONING = "xhigh"` (Glimmer's default is
   already "high" per dev.meta.ai, so "high" adds nothing). Keep it in `chat_template_kwargs.reasoning_strength`.
6. **Fair timing and cost** (verifier 4, 5):
   - Add `--workers N` (default: today's value, so old behaviour is unchanged) and run the requested arms **one after
     another**, each with N workers, never mixed on the GPU at the same time. Record each arm's own wall-clock start
     and end.
   - Per arm, report: input tokens, output tokens, total tokens, calls; tokens per correct part (**primary cost
     measure**); the arm's own wall-clock seconds; and **$ per correct part = arm wall-clock hours × $2.50 ÷ PASS**
     (A100-80GB Modal rate). Latency per job = model call time only, the same definition for every arm.
   - Remove the even split of Modal cost; fix the stale "Arms A+B" note and the decision text when the arms are not
     B and C (point to experiments/bmax/PLAN.md).
7. **Samples per job** (verifier 7): add `--k K` (default 1 = today's behaviour): each job is run K times per arm in
   fresh conversations; report the pass rate over all answers and pass@K per arm, and save every answer.
8. Tests for each item (no network, fake post_fn). Run
   `~/projects/forge/.venv/bin/python -m pytest -q experiments/first-test/test_runner.py` until all pass. Note: the
   sandbox tests skip inside your shell; Claude re-runs them outside.
Finish with a short report: files changed, the pytest line, and anything you could not follow (and why).
