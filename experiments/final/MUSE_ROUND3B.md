# Muse Code round 3b: the in-train format check must abort (verifier B1, forge-r3-build-2026-10-30)
A factory run is LIVE (teacher.py): do not edit anything in experiments/factory/, experiments/final/cloud_cq.py,
run_cq_box.py, or anything under results/. All rules in experiments/final/MUSE_SPEC.md "Rules" apply.
Edit only experiments/train/forge_train.py and its tests:
- The in-train FORMAT_CHECK (≈ line 1142, printed before training) must ABORT the run (raise, no optimizer step, no
  adapter saved, the cost still reported) when any of thinking_first / answer_after_thinking / prompt_matches_ft is
  False for the first training record that has reasoning. Records without reasoning: unchanged behaviour.
- Test: a fake failing render aborts before the first optimizer step; a passing one continues.
Done when: pytest (experiments/train experiments/final experiments/factory experiments/common dashboard) passes and
`forge_train.py smoke --cap-dollars 2.0` still prints CAP REFUSED. Report: files changed, pytest line.
