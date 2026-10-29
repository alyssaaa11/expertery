# Option A retrieval-coverage audit (free): A is almost surely NO ROOM → skip A

**Summary**: The user's first noon kill test (decision 2026-10-29 morning). For each of the 30 draft exam jobs, do the 5
past designs that plain BM25 retrieves show every hidden-rule instance the job needs? **83% of jobs are fully covered**
(mean of 5 prototype libraries, range 73-90%) → by the pre-set rule (≥ 80% → skip A), **Option A is skipped**.

**Sources**: `experiments/option-a/audit/coverage_audit.py` (run with the forge venv; `--k 5|10|20`, `--verbose`);
rules `experiments/option-a/HIDDEN_STANDARDS.DRAFT.md`; jobs `experiments/option-a/jobs.DRAFT.py`.

**Last updated**: 2026-10-29

---

## Result (verified: command output, 2026-10-29)
| Top-k | Fully covered jobs, seeds 0-4 | Mean |
|---|---|---|
| 5 | 83, 90, 83, 83, 73 % | **83%** |
| 10 | 90, 93, 83, 83, 87 % | 87% |
| 20 | 97, 100, 93, 97, 97 % | 97% |
- Most-missed instances: Skua defaults on a few jobs (BM25 pulled Tern or no-programme designs through shared numbers),
  Tern tall-wall (> 30), Skua material override, long clip.
- decision (user's rule, set before the audit): coverage ≥ 80% → A almost surely NO ROOM → skip A. Do not grow the
  library to force a failure (user: that would rig the test).

## How it was done (method, so it can be repeated)
- The official library does not exist yet, so the script builds a **prototype library** of 300 request texts with
  rule-instance tags, following the coverage targets in the rule file (Tern 110 / Skua 110 / none 80; ≥ 8 designs per
  threshold side per programme, 3 exactly at each edge, overrides). Programs are not generated: retrieval sees only the
  request text, and coverage needs only which rules each design shows.
- Retrieval = plain BM25 (k1 1.5, b 0.75), lowercase alphanumeric tokens, numbers kept, no programme/family bonus
  (verifier drafts fix 1).
- "Covered" = every rule instance the job's reference uses appears in at least one retrieved design. This is lenient
  (the model must still infer the rule), but B-full (the whole library in the prompt) sees all rules anyway, so it
  points the same way.
- hypothesis: the real library would give a similar number, because it follows the same targets. Caveat: it is a
  prediction, not a model run.

## Pitch idea to keep (user, 2026-10-29)
If A is NO ROOM: a trained Glimmer with an empty prompt vs Glimmer + ~47k tokens of past designs = ~50× less input
per call, faster, and no library shipped. The same training run in Plan B can show it.
