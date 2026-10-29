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

## Arms (Glimmer only, same session and GPU; **k = 3 answers per job**, arms run one after another with the same workers)
| Arm | What | Role |
|---|---|---|
| BR | arm B again: manual + job | the floor (luck check against the first test's 67%) |
| B2 | manual + hint, one try | **cheap one-try arm** (user tweak 2) |
| BX | B2 + 3 solved examples + reasoning xhigh + up to 3 rounds (error feedback, self-check on its own measurements) | **B-max**, the strongest fair opponent |
Spark Open is not re-run (30/30 in the first test; its cost per call is known: ≈ $0.011, 9-49 s).

## Measures (all from the server's usage fields and the runner's timing)
Pass rate over all answers (PASS ÷ (PASS + FAIL), whole points) and pass@3; model calls per job; input, output and total
tokens per job; **tokens per correct part (primary cost measure)**; the arm's own wall-clock time (arms never share the
GPU); $ per correct part = arm wall-clock hours × $2.50 ÷ PASS. Position-only vs wrong-shape for every FAIL
(b2-hint/analyze.py). The trained Glimmer at the final exam runs the same way (k = 3, same workers, alone on the GPU).

## Rules (first match wins)
0. INVALID > 5% in any arm → RUN INVALID (report it; no re-run without a new approval).
1. Any FAIL reason containing `harness` or a PermissionError from a legitimate CadQuery import → RUN INVALID (sandbox bug).
2. **B2 (one try) ≥ 90%** → STOP the training plan on CadQuery: a cheap one-try prompt leaves no room for a trained
   model to clearly beat it at the same cost. Report honestly.
3. Otherwise → the bar is set, and these are the rules for the FINAL exam (pre-registered now; paired bootstrap over the
   30 jobs, 10,000 resamples, each job's pass rate over its 3 answers):
   - **as good as B-max** = trained − BX point estimate ≥ −5 points AND the 95% CI lower bound ≥ −15 points;
   - **clearly beats the one-try arm** = the 95% CI of trained − B2 lies entirely above 0;
   - **about the same cost as B2** = trained tokens per correct part ≤ 1.5 × B2's;
   - **much cheaper than B-max** = trained tokens per correct part ≤ BX's ÷ 3 (or wall-clock per correct part ≤ BX's ÷ 3);
   - the claim holds only if all four hold. "Within 5 points" is never called "better".
   - Luck check: if BR is outside 67% ± 20 points (the first test's B), say so in the report (not a stop rule).
   Go to step 3 (factory), which needs the user's yes.

## Honest disclosure
The B2 hint and the B-max solved examples were written after seeing the first test's failures on these 30 jobs (the
hint targets the position errors; the examples show centred boxes being moved). That can only help the no-training arms,
so it makes the comparison harder for the trained Glimmer, not easier. The examples themselves are new part families
(checked: experiments/bmax/examples.py).

## Pilot (before the main run, same session, not on exam jobs)
The dry jobs D1-D3 (`--jobs dry`, never in the exam), arms BR and BX, k = 1. It passes if every answer runs through the
sandbox without INVALID or harness errors, BX makes ≥ 2 calls on a built part, and BX's `reasoning_len` (xhigh) is
clearly longer than BR's (default). If BX hits the 16,000-token limit (cut off) on any pilot answer, switch BX to
"high" and record that. Pilot answers are logged but never counted.

## Caps and command
Modal cap 3.00 (k = 3: up to 90 BR + 90 B2 + 270 BX calls). Expected ≈ $1.5-2.5 including the cold start (~4 min).
Command (run_live.sh hardcodes --budget 5.0; the appended flag wins):
`experiments/first-test/run_live.sh main <out> --arms BR,B2,BX --k 3 --workers 8 --sandbox experiments/b2-hint/sandbox_cq.sb --budget 3.0`

## Freeze (sha256 recorded here before the run)
runner.py, test_runner.py, sandbox_cq.sb, run_one_cq.py, hint.txt, bmax/examples.py, first-test/jobs.py,
first-test/checks.py, first-test/expected.json, first-test/manual.md, first-test/run_live.sh, b2-hint/analyze.py,
deploy/modal_glimmer.py.
