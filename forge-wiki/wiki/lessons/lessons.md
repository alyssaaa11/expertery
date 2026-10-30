# Forge lessons

**Summary**: Reusable lessons from building Forge, each with how it was learned and how to check it again.

**Last updated**: 2026-10-30 (night)

---

- **Run the "cheap fix" baseline before building** (Oct 28). How learned: HerdShot test A died because agents that
  read the files rejected the lie (70/70); the final-pick research found the same risk for Forge (docs, skills or
  harness adaptation may close the gap without fine-tuning, 2607.08938). Check: list the cheapest non-novel fix as an
  arm of every first test, and stop if it already meets the bar. See [[final-pick-research-2026-10-28]].
- **A trivial test proves the referee, not the need** (Oct 28). How learned: the user asked "if you already made the
  cube, how do you know Forge is needed?" Check: first tests need easy, medium and hard levels, and the GO rule must
  look at medium and hard.
- **The too-easy / too-hard window** (Oct 28, reasoning, not yet measured): a teacher that never succeeds gives no
  training data, and one that always succeeds leaves no gap. Check: measure the teacher's pass rate and aim for
  about 30–70%.
- **Keep one project per directory, app, secret and wiki** (Oct 28). How learned: the user said "you are mixing
  contexts" when the Forge Glimmer test ran on HerdShot's Modal app, secret, storage and wiki. Check: before running
  anything, `grep -rn herdshot ~/projects/forge` should only find background references.
- **Check the setup before asking the user to do it** (Oct 28): `~/.modal.toml` already existed when I asked the user
  to run `modal setup`. Check: test the end state first (`modal profile current`, `modal app list`).
- **New system Python can lack wheels** (Oct 28): Python 3.15.2 has no CadQuery/OCP wheels. Fix and check:
  `uv venv --python 3.12`, then run a real build + measurement (20 mm cube = 7607.3 mm³).
- **Check whether model weights are gated before asking for a token** (Oct 28): Glimmer is not gated. Check:
  `curl -s https://huggingface.co/api/models/<id>` and read `gated`.
- **A free hello-world before paid GPU work** (Oct 28): Modal's square(42) (CPU, under a cent) proved login and remote
  runs. Check: `modal run get_started.py` prints 1764.
- **Meta's vLLM image needs `python` on PATH for Modal** (Oct 28). How learned: the first deploy failed during the
  image build ("unable to determine the version of Python", ~$0, no GPU started), and Modal's docs say images need
  `python` + `pip` on PATH. Fix: `setup_dockerfile_commands=['RUN ln -sf "$(command -v python3)" /usr/local/bin/python ...']`;
  the second deploy succeeded in 168 s. Check: `modal deploy` prints "App deployed".
- **Size, volume, area and centre of mass can all miss a moved feature** (Oct 28). How learned: the check self-test
  let 17 of 33 wrong parts pass (holes moved symmetrically keep all four numbers). Fix: compare the answer with the
  reference by overlap (volume of answer XOR reference ≤ 0.2%). B-rep booleans are exact, so correct answers score
  ~0.0%. Check: `experiments/first-test/selftest.py` prints `BAD: none`.
- **A blind rebuild finds unclear wording before it costs money** (Oct 28). How learned: a fresh agent built all 33
  parts from the text alone; all matched, but it flagged 5 wordings (curved vs flat notch, slot length end-to-end vs
  centre-to-centre), which were clarified. Check: score `blind/*.py` with `checks.score`.
- **`modal app stop` asks for confirmation and silently does nothing in a script** (Oct 28). How learned: after the dry run, `modal app list` still showed forge-glimmer deployed with 1 container; rerunning by hand printed "no interactive terminal detected". Fix: `modal app stop <app> -y`, print a warning if it fails, and check `modal app list` after every live run.
- **An independent verifier before a paid run pays for itself** (Oct 28). How learned: the verifier agent's pre-run
  audit found 2 real errors I had missed (contradictory GO/STOP rules, "16k window" wrong) and a cut-off risk. Raising
  max_tokens 8,000 → 16,000 then saved 3 answers in the main run (one per arm went over 8,000). Check: before every paid
  run, ask the verifier (`hivey --session default msg send verifier/master …`) and wait for GO.
- **Write decision rules as an ordered list, first match wins, in whole points** (Oct 28). How learned: "GO at +20" plus a
  "15–25 grey band that overrides" made GO impossible at 20–25 and let grey override STOP; a float edge (0.95 − 0.80 =
  0.1499) flipped a case. Check: probe the decision function on boundary cases (40/60, 40/65, 85/100, 80/95, 30/15).
- **Look at how a model fails, not only how often** (Oct 28). How learned: the user saw that H15 "looks correct"; shifting
  each failed part to line up with the reference showed 3 of 10 failures were position-only, not shape errors. Check:
  rebuild FAIL answers from calls.jsonl, align bounding boxes, recompute the overlap mismatch.
- **Grey zone means the user decides from the data, never a re-run to fish** (Oct 28). How learned: the main run landed
  grey (B 67% > 60% ceiling, gap 33); the user chose GO with stated reasons, recorded before any further spending. A new
  arm (B2) is only allowed as a pre-registered cheap-fix baseline, not to improve a number.
- **Lock the frozen files** (Oct 28): `chmod a-w` on jobs/expected/checks/manual/PLAN kept Muse Code and later scripts
  from changing the exam (selftest.py then failed only on writing expected.json, which is the intended guard).
- **Keep every prompt, answer and code in the log** (Oct 28): a background run can be demonstrated later by rebuilding
  every part from calls.jsonl for free (replay.html), and any judge can re-check it.
- **Muse Code has no free allowance; read its run.usage event for cost** (Oct 28). How learned: `muse usage` →
  no_allowance; the JSON stream's `run.usage` event gives the tokens (2 sessions ≈ $1.02). Cap it with
  `--max-model-steps` and choose `--model muse-spark-1.3` (Wonder costs ~5× more).
- **Use a fresh hivey session address when messaging agents in other sessions** (Oct 28). How learned: `hivey msg send
  verifier/master` failed ("no swarm named verifier") until `hivey --session default msg send verifier/master …`. Check:
  `hivey --session <s> swarm directory`.
- **Hackathon rules page says nothing on other AI assistants** (Oct 28). How learned: WebFetch of cerebralvalley.ai/e/meta-ai-developer-hackathon: "Official Rules will be published before the Hackathon begins"; it suggests Muse Code for coding. Decision (user): publish and build code with Muse Code, and state honestly in the README that Claude helped plan. Check the official rules again before submitting.
- **Archify reruns: use a new `--out-dir`** (Oct 28): a second `finalize` into the same folder failed with
  `viewer/evidence-path-conflict`. Check: rerun with `--out-dir <folder>/review-N`; never delete old evidence.
- **Set the referee tolerance from measured noise vs smallest real error, per exam** (Oct 28). How learned: the Keel
  exam self-test failed 4/90 because missing or wrong fillets (0.019–0.18% overlap mismatch) passed the first test's
  0.2% tolerance; rebuilding H1 and H2 in a different order gave exactly 0.00000000% (Keel always builds identical
  geometry). Check: `experiments/keel-exam/selftest.py` (now 90/90 with 0.01%) and a script that prints `mismatch()`
  for wrong versions and for alternative correct programs; pick a tolerance well between the two.
- **Muse Code builds a whole small product fast and cheap from a precise spec** (Oct 28). How learned: company/SPEC.md
  → one `muse exec` session, 21 calls, ~$0.40, Keel + manual + 8 examples + offline dashboard, self-test 35/35
  re-run by Claude. Tell it platform traps up front (Chrome blocks fetch() on file://, so ship data as a script).
- **A tolerance tuned on one small part fails on big parts; tune it on the noise floor** (Oct 28). How learned: the
  verifier showed 0.01% let a missing fillet pass on large plates (0.006–0.009%), while correct reorderings and a STEP
  round trip match to ~2e-14. Check: compute `mismatch()` for alternative correct programs (noise) and for the
  smallest wrong versions on the LARGEST parts; set the tolerance between (now 1e-6).
- **A "trap" that contradicts the manual is unfair, not realistic** (Oct 28). How learned: verifier probes showed a
  hole called before its boss left the boss undrilled, while the manual says holes go "all the way down"; 7 jobs
  would FAIL manual-faithful answers. Fix: Keel 2.1 applies cuts after all walls/bosses. Check: build the same part
  in two call orders and require 0.0% mismatch, unless the manual documents the order (mirror, pattern).
- **Run the cheapest baseline before building a factory** (Oct 28). How learned: the Keel v2 baseline ($1.5) showed
  Glimmer + a short complete manual already at 97.8% (NO ROOM), which saved the ~$12 factory. Check: before any
  teacher run or training, measure small model + manual vs teacher on the held-out exam with frozen rules.
- **A sandbox for untrusted answers on macOS: sandbox-exec + env -i + ulimit -t + an RSS watchdog** (Oct 28). How
  learned: test scripts inside the profile (socket, reads of exam files and ~/.zshrc, sibling writes, env keys);
  `resource.setrlimit` RLIMIT_AS/DATA/RSS all fail on macOS. The verifier then found answer-key copies readable in
  /private/tmp. Check: `experiments/keel-exam-v2/test_runner.py` sandbox tests; profile in [[quillon-keel-build-2026-10-28]].
- **Freeze by hash, and re-freeze after every approved change** (Oct 28). How learned: Keel changed twice in one
  evening; the runner refuses when a sha256 in PLAN §7 differs. Check: `runner.py --print-hashes`, then
  `runner.freeze_check()` must pass before a paid run.
- **A spec changed after a build does not reach the built code: diff the code against the final plan** (Oct 28). How
  learned: the runner was built from the spec before the verifier's cap notes; reading `pairs = [...]` and the cap
  loop found 4 gaps (job-major order, $3 cap, Modal cap stopping both arms, no complete-sample scoring).
- **Always give the verifier the exact commit hash** (Oct 28). How learned: it re-checked 9fdb42a (no sandbox fix)
  while the fix sat in 74ae975, and reported NO-GO for a problem already fixed.
- **Grep results case-sensitively and read the context before raising an alarm** (Oct 28). How learned: 30 records
  "mentioned harness" — all were the mount name HARNESS-P2; the case-sensitive grep for harness errors and
  PermissionError found 0.
- **Check `date` before writing times into notes** (Oct 28). How learned: I wrote "2026-10-29 ~00:20" at 22:45 on
  Oct 28 into status and PLAN and had to correct them. Check: run `date` when stamping.
- **Muse Code cost grows with session length, mostly cached re-reads** (Oct 28). How learned: run.usage of 7 sessions:
  small fix ~$0.17–0.33, library build ~$0.40–0.80, the 1,400-line runner (65 calls, 7.4M cached tokens) ~$1.7.
  Check: cap `--max-model-steps`, keep specs precise, split big jobs.
- **A per-call budget is not a session budget** (Oct 29). How learned: the step-2 baseline passed `--budget 3.0` to
  each runner call in one GPU session; the runner's guard counts only from its own start (runner.py ~1182, `t_start`;
  `gpu_start` is used only for reporting), so the session ran ~10:45-12:28 ≈ $4.3 instead of stopping at $3. Neither
  Claude nor the verifier caught it (both read the flag, not the guard code). Check: before a multi-call session, read
  where the guard's clock starts; pass each call the budget LEFT (experiments/bmax/run_session_v2.sh), and leave margin
  for in-flight answers (up to ~400 s each ≈ $0.3).

## Oct 29 night (training + final exam preparation)
- **When a rule changes, grep for every place that breaks it** (Oct 29). How learned: writing the final-exam spec, I
  found the CadQuery path (factory spec, the training exam guard, first-test runner) still runs model code on the Mac
  via sandbox-exec, months-old code written before the "Mac is the office" rule. Check:
  `grep -rn "sandbox-exec\|run_code" experiments/` before any new runner; anything that runs answer code must use a
  Modal box.
- **A capped run leaves holes in a pre-registered comparison** (Oct 29). How learned: the verifier counted BX final
  answers per job: 0 on H13-H15, 1 on H12, so the 30-job paired bootstrap was undefined. Check: before writing compare
  rules, count finals per (arm, job); size workers so the slowest answers (BX hard up to 821 s) finish in one wave
  (11 answers → 12 workers), and STOP if a finishing run is incomplete.
- **Say where a saving comes from** (Oct 29). How learned: the verifier split tokens per correct part from calls.jsonl:
  B2 = 6,458 prompt + 4,205 completion, BX = 14,101 + 7,213. Most of a trained model's saving is the dropped 5.7k
  manual. Check: always report prompt vs completion and wall-clock/$ next to "tokens per correct part".
- **A bar computed on partial data moves when the data is completed** (Oct 29). How learned: verifier A2: bar (d)'s
  7,105 is over 79 BX answers; with 90 (hard answers average 22,303 vs 20,235) it loosens. Check: recompute every
  threshold from the final data and disclose the change.
- **Re-add the caps every time a step is added** (Oct 29). How learned: my PLAN said "≤ $13.5 caps + Muse"; the
  verifier summed $12.80 + Muse $2-4 = $14.8-16.8. Check: a caps table with a total row, recomputed on every edit.
- **Check the Mac's memory against the model card before promising an offline demo** (Oct 29). How learned:
  `sysctl -n hw.memsize` = 24 GB; the Glimmer MLX q4 is ~15 GB and its README recommends ≥ 48 GB (17.6 tok/s on a
  64 GB M5 Pro). Check: those two numbers before any local model plan.
- **Ask a fresh reviewer about direction, not only the verifier about rigor** (Oct 29). How learned: the verifier checks
  correctness; a fresh agent given only the files and the rubric scored the direction 6/10: proof-heavy, demo-light
  (Impact + Demo = 55%). Check: once per phase, give a fresh agent the status page + rubric, never my conclusion.
- **Check the hackathon's banned topics before choosing pitch examples** (Oct 29). How learned: I used
  "medical-device makers" as an example; the rules ban health/medical ideas
  (~/.hivey/agent/hiveyAgent-wiki/wiki/user/meta-hackathon-2026.md). Check: read that list before writing pitch text.
- **Diagrams must follow the wiki's picture convention** (Oct 30). How learned: the user could not find the training diagram: I saved HTML only in forge-wiki/attachments/, which Obsidian does not show. Check: every diagram = PNG + HTML in forge-wiki/wiki/assets/diagrams/, embedded with ![[...png]] on its page and listed in [[forge-diagrams]].

