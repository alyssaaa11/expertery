# Keel v2 baseline test: PLAN (frozen)

Supersedes `experiments/keel-exam/` (v1 exam, kept as history: the user asked for a more realistic tool, 2026-10-28).

Status: **FROZEN** 2026-10-28 ~23:50 (hashes in section 7; verifier exam GO; blind rebuild 30/30; runner tests 62/62;
rule 1 on C pass@3 per the user).
The paid pilot and main run need the user's yes.

## 1. Question
On a private tool no model has seen (Keel 2.0, of the fictional Quillon Orbital Works), with only the company manual:
1. Can the teacher (Spark Open) do the work? If not, it cannot teach, and the factory stops here cheaply.
2. Is the small model (Glimmer) clearly worse? If Glimmer + manual is already good, training has nothing to add.

## 2. Arms (30 held-out exam jobs, k = 3 independent samples per job per arm = 90 answers per arm, no retries)
| Arm | Model | Gets |
|---|---|---|
| B | Muse Glimmer 30B on Modal (A100-80GB, vLLM, as in the first test) | Keel manual + request |
| C | Muse Spark Open on Baseten | Keel manual + request |
No arm A (Glimmer without the manual): it cannot know Keel's names, so it would score ~0 and cost money for nothing.
Same prompt for both, same sampling as the first test (temperature 1.0, top_p 0.95, top_k 64, max_tokens 16000).

## 3. Exam and referee (verified before the run)
- 30 jobs (15 medium, 15 hard) in `jobs.py`, written by Claude, not by a Meta model; realistic requests (materials, flight class, company mounts, FRM centre dimensions, wall holes, mirror) that need the manual v2. Part numbers differ from the
  manual's examples; no exam job may enter practice data later.
- Referee: `referee.py` (this folder) = first-test `checks.py` unchanged, overlap tolerance **1e-6** (0.0001%).
  Reason (verifier audit 2026-10-28): correct answers written differently and a STEP round trip match to ~2e-14;
  0.01% let a missing standard fillet PASS on large parts (0.006–0.009%). The runner must import `referee.py`.
- Keel 2.1 (verifier fix): cuts are applied after all walls and bosses whatever the call order, and no cut removes
  material above its local top. Exam references must be unchanged by this (checked by re-running the self-test).
- M2 replaced (verifier note 3: it was a near-copy of example PLT-1042); self-test and blind re-run.
- Self-test 90/90 (30 references pass, 60 wrong versions fail; smallest wrong-version mismatch 0.0133%, alternative correct programs 0.00000000%). Blind rebuild 30/30 (fresh helper, manual v2 + texts only; it hit and solved the mirror/pattern trap in H2, H15; notes in blind/NOTES.md, no text changes needed).

## 4. Decision rules (ordered, first match wins; all in percent of answers, compared in whole points)
Score of an arm = mean pass rate over its 90 answers (= mean over the 30 jobs of passes/3), in percent.
0. INVALID > 5% of answers in either arm (more than 4 of 90: cut off, empty, or network/HTTP failure after one
   retry) → **RUN INVALID**: fix the cause, rerun that arm; no decision from this run.
1. C pass@3 < 30% → **STOP**: the teacher cannot use an unseen tool from its manual; rethink (e.g. a richer manual).
   C pass@3 = share of the 30 jobs with at least one PASS among C's complete samples (pass@k over the complete
   samples if a cap left fewer than 3). Why (user, 2026-10-28): the factory keeps only referee-verified teacher
   answers, so what matters is whether Spark can solve a job at all, not its average; e.g. 5 of 10 jobs solved once
   in 3 tries = mean 17% but pass@3 50%, enough to make practice data.
2. B ≥ 80% → **NO ROOM**: Glimmer + manual is already good; training cannot show much; rethink the tool.
3. C − B ≥ 25 points and B ≤ 70% → **GO**: build the factory (practice generator → teacher run → training). Bar 25,
   the same as the first test.
4. Otherwise → **GREY**: report to the user, who decides.
Reported next to rule 1: C mean pass rate (sets the factory cost: tries needed per good example ≈ 1/mean) and C
pass@3 split medium vs hard; flag EASY-ONLY if C hard pass@3 < 20% or < half of C medium pass@3: practice data would be
easy-only. Rules 2–3 stay on the mean pass rate.
Also reported alongside (not part of the rules): pass@1 of each sample separately (samples 1, 2, 3 per arm); a paired
bootstrap 95% CI of C − B over the 30 jobs (10,000 resamples of jobs, seed 0, per-job score = passes/3); McNemar on
sample 1 (informational). INVALID answers count as not PASS in the score and are listed separately.

## 4b. Prompt and answer format (fixed)
- Messages: system = "You write programs for Keel, Quillon Orbital Works' private part-description tool. Units are
  millimetres. Follow the Keel manual exactly. The program must start with `import keel`, create the part with
  `p = keel.part(...)`, and end with `solid = p.finish()`. Reply with exactly one Python code block and nothing
  else."; user 1 = "Here is the Keel manual. Use it.\n\n" + `company/manual.md`; user 2 = the request text.
- Answer: the first fenced code block (```python or ```), else the whole reply. Run in a fresh subprocess with
  `company/` on the path and a 120 s timeout; the part is the variable `solid`. FAIL = it raises (incl. KeelError),
  `solid` is missing, or the referee fails it. INVALID = cut off by the token limit, empty reply, or network failure.

## 4c. Sandbox for model answers (answers are untrusted Python run on this Mac)
Each answer runs in its own new scratch directory under the job temp folder, as
`env -i HOME=<scratch> PATH=/usr/bin:/bin sandbox-exec -f sandbox.sb /bin/sh -c 'ulimit -t 120; <venv python> run_one.py'`:
- `sandbox.sb` (verifier note 2, tested profile in `sandbox.reference.sb`): `(allow default) (deny network*)`;
  `(deny file-read* (subpath "/Users/alyssa"))` then allow reads only of the venv, the uv Python install
  (`~/.local/share/uv/python`, the venv's base interpreter lives there behind a symlink), `company/` and the answer's
  own scratch dir, plus `run_one.py` itself (the child must read it; found by Muse Code); `(allow file-read-metadata)`;
  `(deny file-write*)` then allow writes only to the answer's own
  scratch dir and /dev/null. Paths are passed with `-D NAME=<path>` and `(param "NAME")`.
- Clean environment (`env -i`): no API keys or other secrets. `company/` is put on sys.path by `run_one.py`.
- CPU: `ulimit -t 120` plus a 120 s wall-clock timeout (kill the process group). Memory: macOS ignores RLIMIT_AS/
  DATA (tested: setrlimit fails), so the runner polls the child's RSS every 0.5 s and kills it above 4 GB → FAIL
  ("memory").
- The child writes the finished solid as a BREP/STEP file into the scratch dir; the referee runs in the runner
  process on that file (the referee never runs untrusted code). The solid is kept for the replay viewer.
- verified 2026-10-28 ~23:00 with `sandbox.reference.sb`: Keel builds a part and writes solid.brep; reading
  expected.json and ~/.zshrc fails, writing into a sibling scratch dir fails, a socket connect fails (all
  PermissionError); the environment has no *KEY*/*TOKEN* variables.

## 4d. Pilot (before the full run)
3 jobs (M1, M7, H9), arm C only (Spark Open on Baseten), k = 1. It checks: the prompt and answer format, code
extraction, the sandbox, the solid hand-off and the referee. The pilot passes if all 3 answers are extracted and run
in the sandbox without INVALID or harness errors (whether the parts PASS does not matter). Pilot answers are logged
separately and never count. If the pilot fails: fix the harness (not the exam), rerun the pilot.

## 5. Cost (estimate) and hard caps
Runner by Muse Code ~$0.40 (+ ~$0.20 for the follow-up sandbox/cap changes); pilot ~$0.08; Modal ~$1.0–1.5 (cold
start ~7 min + 90 answers); Baseten ~$2.0–2.4 (90 answers) → **~$3.7–4.6**. Spent before this test ≈ $5.4 of $30.
Hard caps (the runner checks them before every new call and stops sending new calls at the cap; calls in flight
finish and are logged):
- Modal: `--budget 2.50` USD, estimated as wall-clock since deploy start × $2.50/h (includes the cold start), and
  a 60-minute wall-clock limit for the Glimmer arm.
- Baseten: `--budget-c 4.00` USD, computed from each response's usage tokens × $1.25/M in, $4.25/M out (full input
  price, so the estimate is on the high side; 4.00 leaves room above the ~$2.0–2.4 expected).
- Order: calls are sent sample-major (all 30 jobs of sample 1, then sample 2, then sample 3; jobs in a fixed order
  inside a sample), so a cap hit leaves complete samples.
- If a cap stops an arm early (verifier note 1): answers never sent are NOT RUN (not FAIL, not INVALID). The arm's
  score then uses only its complete samples (all 30 jobs answered); an incomplete last sample is reported but not
  scored. If either arm has no complete sample, the run is INCOMPLETE and no decision is made.
Stop check after the run: `modal app stop forge-glimmer -y`, then `modal app list` must show it stopped; record
`modal billing summary`; record the Baseten spend from the token log.

## 6. Runner (built by Muse Code from RUNNER_SPEC.md; first-test runner.py is reused as the base, not changed)
`experiments/keel-exam-v2/runner.py`: arms B and C, k = 3, the prompt and answer format of 4b, the sandbox of 4c, the
pilot of 4d, the caps of 5, the scoring and report of 4, the freeze check of 7. Logs every prompt, answer, code,
sandbox result, measurement and verdict to `results/keel-v2-<run>/calls.jsonl`.

## 7. Freeze by hash
Before the run, the sha256 of these files is written here and committed; the runner recomputes them at start and
refuses to run if any differs: `jobs.py`, `expected.json`, `referee.py`, `runner.py`, `sandbox.sb`, `run_one.py`
(this folder), `../first-test/checks.py`, `../../company/keel/__init__.py`, `../../company/manual.md`.
Hashes (re-frozen 2026-10-28 ~23:50 with `runner.py --print-hashes`, after the rule-1 change):
```text
fc6dfd1a44f0596fdb3a2bb43e672805b7a86490380a2e9df73768de93b58863  jobs.py
aa5eef7077e7f7bb8375132749eb612efe2a47a2fefa0d9693762e9289bbc981  expected.json
c340a5c3eced99ee1faad123df1ad89cf8385d7ffe0553fc57fad7fca5e33a2f  referee.py
f38613aa9156750debfb4d902a2a7ca6463ecae4f6404a0a395a50dba0fcb39a  runner.py
0d150bfbaea5a27c3128444c8220e99c460fb80503b6418c11dfe12c6a377396  sandbox.sb
51376492dfd791a39d19c42a7e2a2ac681e36697b80a09c33781f9cabca05524  run_one.py
3fc69f4baa0649d20210dc03e3a3143fa6f0bc28f15619d311e4f29c94e51c2a  ../first-test/checks.py
0c1d41e9b5289f94339f86e9b38d5b8f2618960ac4b22f643c4edcf04942dc18  ../../company/keel/__init__.py
583b71bcbaae8d2bd6786aee425b0284ba8f6d9cc8689cf853ab05be1baf25ee  ../../company/manual.md
```
