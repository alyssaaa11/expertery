# Quillon Orbital Works and Keel: how the private-tool experiment was built (Oct 28)

**Summary**: Everything built on the evening of Oct 28 to test Forge on a tool no AI has seen: the fictional space
company Quillon Orbital Works, its private tool Keel (v1 → v2 → 2.1), the dashboard, the held-out exams, the
referee tolerance, the sandbox, the freeze by hash, and the five verifier rounds. The result of the test is in
[[keel-v2-baseline-2026-10-28]] (NO ROOM). Read this before building Option A ([[option-a-plan-2026-10-29]]),
which reuses all of it.

**Sources**: `company/SPEC.md` (v1 + v2 addendum), `company/` (keel, manual, examples, dashboard, selftest),
`experiments/keel-exam/` (v1 exam, history), `experiments/keel-exam-v2/` (PLAN frozen by sha256, jobs, referee,
runner, sandbox, blind/), Muse Code logs `results/muse-*.jsonl`, verifier reports
`~/agents/verifier/reports/forge-keel-exam-2026-10-28.md` and `forge-keel-v2-exam-2026-10-28.md`, git log 0261021..b9004c3.

**Last updated**: 2026-10-28

---

## Why (decisions)
- decision (user, ~22:00): after the first test, move from public CadQuery to a **non-public tool**, so no model
  could have learned it from the internet.
- decision (user, ~22:30): the company is a **space company making satellite parts** (confidential designs →
  needs an on-prem model, the Forge story), with an **internal dashboard like a real company**.
- decision (user, ~23:30): make the tool **more realistic** (v1 was close to plain CAD).

## What exists (verified)
| Piece | Where | Built by | Check |
|---|---|---|---|
| Company story + spec | `company/SPEC.md` | Claude | name "Quillon Orbital Works" web-searched: no real company |
| Keel 2.1 library | `company/keel/__init__.py` | Muse Code (v1 ~$0.40, v2 ~$0.80, 2.1 ~$0.20) | company selftest 92/92 |
| Manual 2.1.0 (~3.5k tokens) | `company/manual.md` | Muse Code | no exam job inside (verifier: max Jaccard 0.22) |
| 12 example parts | `company/examples/` | Muse Code | part numbers 0xxx–1xxx only |
| Offline dashboard | `company/dashboard/index.html` (double-click, Chrome) | Muse Code | no fetch/http; data shipped as `data.js`; statuses labelled sample data |
| v2 exam, 30 jobs | `experiments/keel-exam-v2/jobs.py` | Claude (not a Meta model) | selftest 90/90, blind rebuild 30/30 |
| Runner + sandbox | `experiments/keel-exam-v2/runner.py`, `sandbox.sb`, `run_one.py`, `run_live.sh` | Muse Code (~$2.75 over 4 sessions) | 63/63 tests, verifier GO at 74ae975 |

## Keel in one paragraph
Python recipe → exactly one CadQuery solid, so the first-test referee still judges it. Corner datum, edges named
north/south/east/west, holes only by company fastener code (table KF, -CB counterbore, -CS countersink), materials
change the standards (AL6061 wall 2.5 / fillet 1.0, TI6AL4V 3.0 / 1.5, SS316 2.0 / 0.5), FLIGHT class auto-fillets
and demands -CB/-CS, company mounts (PETREL-MOUNT-A/B, STAR-TRACKER-3, HARNESS-P2), wall holes (u from the west/
south end, z above the stock top), mirror (no pattern after it), and FRM requests dimensioned from the frame centre.
Since 2.1 cuts are applied after all walls and bosses, whatever the call order, and no cut removes material above
its local top.

## How the exam was made trustworthy (method, reusable for Option A)
1. Claude writes the jobs and reference programs; each job gets 2 deliberately wrong versions.
2. Self-test: references pass against themselves, wrong versions fail (90/90).
3. Tolerance from measurements, not a guess: correct answers written differently and STEP/BREP round trips match to
   ~1e-14; the smallest real error (missing fillet on a large plate) is ~0.006%. Referee overlap tolerance **1e-6**.
   The first try (0.01%, tuned on one small part) let 6 wrong parts pass (verifier).
4. Blind rebuild: a fresh helper with only the manual + request texts rebuilds every part; 30/30 exact, else fix the
   text (v1: 7 texts fixed; v2: M2 replaced as a near-copy of an example).
5. Fairness: a trap that contradicts the manual is a bug (hole-before-boss left the boss undrilled → Keel 2.1).
6. Verifier audit before any paid run; every finding fixed or answered.
7. Freeze by hash: sha256 of 9 files in PLAN §7; the runner refuses to start on any change. Re-freeze after every
   approved change (done twice tonight: rule-1 change, sandbox leak fix).

## The sandbox for model answers (verified on this Mac, 2026-10-28)
- `env -i HOME=<scratch> PATH=/usr/bin:/bin sandbox-exec -f sandbox.sb … 'ulimit -t 120; python run_one.py'`.
- Profile: allow default; deny network; deny reads under /Users/alyssa and the temp folders (/private/tmp,
  /private/var/folders, /tmp, /var/folders), then allow reads of the venv, the uv Python install
  (`~/.local/share/uv/python`, the venv's base interpreter sits there behind a symlink), `company/`, the answer's own
  scratch dir and `run_one.py`; deny writes except the own scratch dir and /dev/null.
- macOS ignores memory rlimits (setrlimit RLIMIT_AS/DATA/RSS fails), so the runner kills a child above 4 GB RSS.
- The child only writes `solid.brep`; the referee runs outside the sandbox.
- Leak found by the verifier: answer-key copies (and Claude task logs) in /private/tmp were readable → temp-folder
  read deny. Check: `test_sandbox_blocks_system_tmp_but_reference_passes`.

## Plan rules that came from the user (decisions, 2026-10-28)
- k = 3 samples per job per arm; decide on the mean; report pass@1 per sample and a paired bootstrap CI.
- All thresholds in percent of jobs/answers; INVALID gate > 5%; GO bar 25 points (same as the first test).
- Rule 1 (STOP) on teacher **pass@3**, not its mean: the factory keeps only referee-verified answers, so "can it solve
  the job at all" matters; report C mean (factory cost ≈ 1/mean tries per good example) and medium/hard pass@3 with an
  EASY-ONLY flag (hard < 20% or < half of medium).
- 3-job pilot before the main run; hard caps written in the plan (Modal $2.50 + 60 min for Glimmer, Baseten $4.00),
  sample-major order, unsent answers NOT_RUN, scoring on complete samples only.

## Cost of the evening (estimates from run.usage / runner token logs; Modal verified)
Muse Code ≈ $4.2 (company and Keel builds ≈ $1.4, runner ≈ $2.75); Keel v2 pilot $0.03 + main ≈ $1.5
(Modal ≈ $0.55 within $2.22 metered, covered by credits; Baseten ≈ $0.97). Project total ≈ $9.8 of $30.
