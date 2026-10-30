# Round 2b (small, after round 2 finishes): verifier items not fully in the round 2 prompt
Source: ~/agents/verifier/reports/forge-muse-round2-prebuild-2026-10-30.md (E2, E3), m…261.
- E2 test: compare.py with 79 baseline + 11 step-6a fake BX records → bar (d) over all 90; refuse on a duplicate (job, rep)
  and when 6a is INCOMPLETE.
- E3 real guard: train_records.jsonl holds only {id,text,code}, so a `teacher` filter on it is a no-op. forge_train's
  loader cross-checks the run's calls.jsonl: keep only ids that have a PASS call with teacher == "spark"; print the
  dropped ids; outside the hashed set.
- After the factory main run: teacher.py refuses --escalate (decision, user 2026-10-30) and train records carry `teacher`.
Check round 2's report first: drop any item it already did.
