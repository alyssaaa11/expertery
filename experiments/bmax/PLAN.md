# Step 2 plan: baseline run of the no-training arms (DRAFT, frozen only after the verifier says GO)

Status: DRAFT by Claude, 2026-10-29. Needs: Muse Code build + tests, Claude's 30/30 reference check through the
sandbox, freeze by hash, verifier GO, then the user's yes (~$1.5).

## Question
How correct, how slow and how costly is Glimmer **without training**, in its plain, cheap and strongest fair forms, on
the 30 held-out CadQuery jobs of the first test? These numbers are the bar the trained Glimmer must clear
(forge-wiki/wiki/decisions/new-goal-2026-10-29.md).

## Exam touched once per arm (user rule: exam touched once)
Each arm runs on the 30 exam jobs **exactly once**: BR, B2 and BX now, the trained Glimmer once at the final exam.
Nothing in BR/B2/BX (prompt, examples, rounds, settings) may change after this run. That way the opponents are never
tuned on the exam, and the trained model's settings are chosen only on the dev set (~20 practice jobs). The final
report compares the trained Glimmer's single exam run with these frozen numbers.

## Arms (Glimmer only, same session and GPU; k = 1 per job, as in the first test)
| Arm | What | Role |
|---|---|---|
| BR | arm B again: manual + job | the floor (luck check against the first test's 67%) |
| B2 | manual + hint, one try | **cheap one-try arm** (user tweak 2) |
| BX | B2 + 3 solved examples + reasoning high + up to 3 rounds (error feedback, self-check on its own measurements) | **B-max**, the strongest fair opponent |
Spark Open is not re-run (30/30 in the first test; its cost per call is known: ≈ $0.011, 9-49 s).

## Measures (all from the server's usage fields and the runner's timing)
Pass rate (PASS ÷ (PASS + FAIL), whole points), model calls per job, tokens per job, summed latency per job, tokens and
latency per correct part, and $ per correct part = the arm's share of the run's metered Modal cost (by its share of
summed call latency) ÷ PASS. Position-only vs wrong-shape for every FAIL (b2-hint/analyze.py).

## Rules (first match wins)
0. INVALID > 5% in any arm → RUN INVALID (report it; no re-run without a new approval).
1. Any FAIL reason containing `harness` or a PermissionError from a legitimate CadQuery import → RUN INVALID (sandbox bug).
2. **B2 (one try) ≥ 90%** → STOP the training plan on CadQuery: a cheap one-try prompt leaves no room for a trained
   model to clearly beat it at the same cost. Report honestly.
3. Otherwise → the bar is set: trained Glimmer must reach ≥ BX − 5 points (paired bootstrap 95% CI reported), be
   ≥ 3× cheaper or faster per correct part than BX, and clearly beat B2 at about the same cost.
   Go to step 3 (factory), which needs the user's yes.

## Pilot (before the main run, same session)
Not on exam jobs (touch-once rule): the dry-run job E1 (mounting plate, never in the exam; `--jobs dry`), arms BR and
BX. It passes if E1 runs through the sandbox in both arms without INVALID or harness errors, BX makes ≥ 2 calls (any built
part gets the self-check message), and BX's `reasoning_len` is clearly longer than BR's (this checks that vLLM accepts
`chat_template_kwargs.reasoning_strength`; hypothesis, not yet tested). If reasoning_len does not change: report it, and
run BX without that key (decided with the user). Pilot answers are logged but never counted.

## Caps
Modal budget 2.50 (BX makes up to 90 calls with long prompts); the runner's NOT_RUN rule stops calls at the cap.
Expected ≈ $1.0-1.5 including the cold start (~4 min).

## Freeze (sha256 recorded here before the run)
runner.py, test_runner.py, sandbox_cq.sb, run_one_cq.py, hint.txt, bmax/examples.py, first-test/jobs.py,
first-test/checks.py, first-test/expected.json, first-test/manual.md, deploy/modal_glimmer.py.
