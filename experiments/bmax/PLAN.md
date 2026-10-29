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

## Arms (Glimmer only, one GPU session; **k = 3 answers per job for B2 and BX, k = 1 for BR** (user, 2026-10-29: BR is only the luck check); arms run one after another with 8 workers)
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
(b2-hint/analyze.py). The trained Glimmer at the final exam runs the same way (k = 3, 8 workers, alone on the GPU).

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
Modal cap 3.00 (30 BR + 90 B2 + up to 270 BX calls, plus the pilot). Expected ≈ $1.3-2.2 including one cold start (~4 min).
Command: `experiments/bmax/run_session.sh <out>`: one deploy, the pilot (D1-D3, BR+BX, k=1), then it waits for Claude's
pilot check (`touch <out>/GO`, or `<out>/STOP`; 20 min max), then BR k=1 and B2+BX k=3 on the 30 exam jobs, then
stops the app. `--budget 3.0` for every runner call, all counting from the same GPU start.

## Freeze (sha256 recorded here before the run)
Frozen 2026-10-29 after the Muse Code fix session (pytest 73/73 outside Muse's shell; 30 blind refs 30/30 sandboxed = unsandboxed):
```
37f1b69fa1b7e949ac77f37ba2e3d8bfb161b5646fe272ddbd88a8b1b51bd533  first-test/runner.py
94081d2ff0bc20a84e995a2ae35910bf2e55ff091a22c455ce57d30a2a8a5548  first-test/test_runner.py
cd54e27cb112468c6bacced55047faf12aa1a1cd149437ea85600514b11aac20  b2-hint/sandbox_cq.sb
5072eb138a72977c8831c8b5a508c1914348fb3b1ce895e78cf5fbd59f152c31  b2-hint/run_one_cq.py
82ab6848505bb023db36196e76bbc586e4c265192bf7809feb9f4c4e7393fb82  b2-hint/hint.txt
083488b563289f64aead5f6e7e20a66cdf06a13ec0cc5e1b1f65487b31972daa  bmax/examples.py
7745fac5c63787ebb9c0df91f09262a07de5a6b0d9afd6200a04c949b436ef2b  first-test/jobs.py
3fc69f4baa0649d20210dc03e3a3143fa6f0bc28f15619d311e4f29c94e51c2a  first-test/checks.py
29996871e7bb0f2d443a9262d2de2df4a9ecadb8a693c4746723a07e04537420  first-test/expected.json
73efb01e3997f30688e6cfd318bdfbcb31bce50546b5aa24a5b871de17d600c8  first-test/manual.md
e2b1b87dbcaf59b0094298e0310bd5b6ed89c835bc2e9c5075b748926b76f872  bmax/run_session.sh
a8ed179266fe10ad951757482f15d61cd907e5697877bcf9b7357028a0756771  b2-hint/analyze.py
e1f88e6da0ca53bc3ff1754881da70f9c5a465dfdd83a7673d197e637947bd49  ../deploy/modal_glimmer.py
```
runner.py, test_runner.py, sandbox_cq.sb, run_one_cq.py, hint.txt, bmax/examples.py, first-test/jobs.py,
first-test/checks.py, first-test/expected.json, first-test/manual.md, bmax/run_session.sh, b2-hint/analyze.py,
deploy/modal_glimmer.py.
