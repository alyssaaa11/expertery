# What Muse Code did: round r2

From results/muse-final-r2.jsonl.

> # Muse Code round 2: trained arm, BX finisher, serving, comparison (user yes 2026-10-30; verifier READY WITH 3 EDITS, applied: forge-muse-round2-prebuild-2026-10-30)

## Steps

- 1. read experiments/final/MUSE_SPEC.md
- 2. read experiments/final/PLAN.md
- 3. read experiments/final/cloud_cq.py
- 4. read experiments/final/cloud_cq.py
- 5. read experiments/train/forge_train.py
- 6. read experiments/train/forge_train.py
- 7. ran `ls experiments/final/ experiments/factory/ experiments/first-test/ deploy/ experiments/freecad/ experiments/train/ experiments/common/ 2>&1;` → exit 0
- 8. read experiments/train/forge_train.py
- 9. read experiments/final/MUSE_ROUND2.md
- 10. ran `wc -l experiments/first-test/runner.py experiments/freecad/runner_fc.py experiments/freecad/run_fc_session.sh deploy/modal_glimmer.py experi` → exit 0
- 11. read experiments/first-test/runner.py
- 12. read deploy/modal_glimmer.py
- 13. read experiments/freecad/run_fc_session.sh
- 14. read experiments/final/run_cq_box.py
- 15. read experiments/first-test/runner.py
- 16. read experiments/common/run_session.sh
- 17. read experiments/first-test/runner.py
- 18. ran `ls results/bmax-baseline-2026-10-29/main-B2BX/ results/bmax-baseline-2026-10-29/main-BR/ 2>&1; echo ---; head -c 2000 results/bmax-baseline-` → exit 0
- 19. ran `python3 -c "` → exit 0
- 20. ran `grep -n "train_records\|factory_version\|teacher\|escalate" experiments/factory/teacher.py | head -40; echo ---; ls experiments/factory/*.js` → exit 0
- 21. ran `sed -n 540,676p experiments/factory/teacher.py; echo ===; python3 -c "` → exit 0
- 22. read experiments/train/test_forge_train.py
- 23. read experiments/train/test_forge_train.py
- 24. read experiments/final/test_cloud_cq.py
- 25. ran `grep -n "cached_tokens_of\|def main\|add_argument\|FORGE_URL\|FORGE_KEY\|GLIMMER_URL\|jobs-file\|jobs_file\|--exam\|reserve\|RESERVE\|money ` → exit 0
- 26. ran `grep -n "escalate\|train_records\|factory_version\|teacher" experiments/train/forge_train.py | head; echo ---; sed -n 1,60p experiments/fact` → exit 0
- 27. ran `sed -n 300,360p experiments/freecad/runner_fc.py; echo ===; sed -n 1724,1886p experiments/freecad/runner_fc.py` → exit 0
- 28. read experiments/common/budget_left.py
- 29. ran `grep -n "MEASURE\|xmin\|bbox" experiments/b2-hint/run_one_cq.py | head; echo ---; grep -n "jobs_dev\|dev_jobs\|jobs-file\|jobs_file" experim` → exit 0
- 30. ran `sed -n 1,80p experiments/b2-hint/run_one_cq.py; echo ===; sed -n 1,50p experiments/factory/make_jobs.py; echo ===; grep -n "EXAMPLES\b" expe` → exit 0
- 31. ran `python3 -c "` → exit 0
- 32. wrote 4858 bytes to experiments/final/runner_final.py
- 33. edited lines 134-135: `return (boxed["brep_bytes"], None,`
- 34. ran `grep -n "Bearer" experiments/final/runner_final.py | head -3; ~/projects/forge/.venv/bin/python -c "import ast; ast.parse(open('experiments/` → exit 0
- 35. edited lines 213-216: `def out_of_money(cap_dollars, gpu_start, reserve=RESERVE, now=None):`
- 36. edited lines 349-351: `"measurements": measurements,`
- 37. edited lines 374-379: `content, finish_reason, usage, reasoning_len = "", None, {}, 0`
- 38. edited lines 560-563: `"fails": fails or [],`
- 39. edited lines 568-572: `"prompt_tokens_total": prompt_total,`
- 40. edited lines 728-734: `digest = (summary.get("server") or {}).get("image_digest")`
- 41. edited lines 858-864: `def bx_finals_in(records):`
- 42. edited : ``
- 43. edited lines 945-949: `with open(os.path.join(out_dir, "report.md"), "w",`
- 44. edited lines 1009-1015: `arms = tuple(p.strip() for p in str(args.arms).split(",") if p.strip())`
- 45. ran `cd ~/projects/forge && .venv/bin/python -c "import ast; ast.parse(open('experiments/final/runner_final.py').read()); print('syntax ok')" && ` → exit 0
- 46. wrote 8609 bytes to experiments/final/test_runner_final.py
- 47. edited lines 212-214: `assert exc.value.code == 2`
- 48. edited lines 372-393: `def test_fill_incomplete_writes_refused_summary(tmp_path):`
- 49. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py 2>&1 | tail -15` → exit 0
- 50. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py::test_no_keys_exits_2_with_variable_name 2>&1 | ` → exit 0
- 51. edited lines 210-214: `with pytest.raises(SystemExit) as exc:`
- 52. edited lines 255-258: `# Same observable failure as the local fake executor (the box's`
- 53. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py 2>&1 | tail -4` → exit 0
- 54. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py::test_bx_cloud_sends_same_messages_as_frozen_loo` → exit 0
- 55. ran `cd ~/projects/forge && .venv/bin/python -c "` → exit 0
- 56. ran `cd ~/projects/forge && .venv/bin/python -c "` → exit 0
- 57. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py::test_bx_cloud_sends_same_messages_as_frozen_loo` → exit 0
- 58. edited lines 294-296: `assert [r["event"] for r in cloud["bx_rounds"]] == \`
- 59. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py 2>&1 | tail -3` → exit 0
- 60. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py::test_bx_cloud_sends_same_messages_as_frozen_loo` → exit 0
- 61. ran `cd ~/projects/forge && .venv/bin/python -c "import cadquery; print(cadquery.__version__)" 2>&1 | head -2` → exit 0
- 62. ran `cd ~/projects/forge && .venv/bin/python -c "` → exit 0
- 63. edited lines 267-281: `def test_bx_cloud_sends_same_messages_as_frozen_loop(monkeypatch):`
- 64. edited lines 296-300: `frozen = runner.do_bx_call(`
- 65. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_runner_final.py 2>&1 | tail -3` → exit 0
- 66. wrote 2475 bytes to deploy/modal_forge.py
- 67. wrote 4656 bytes to experiments/final/run_final_session.sh
- 68. ran `cd ~/projects/forge && chmod +x experiments/final/run_final_session.sh && zsh -n experiments/final/run_final_session.sh && echo "zsh syntax ` → exit 0
- 69. wrote 5948 bytes to experiments/final/compare.py
- 70. edited lines 71-76: `if arm == "BX":`
- 71. edited lines 128-138: `def require_bx_complete(merged, jobs, reps):`
- 72. edited lines 152-165: `def wall_of_summary(summary, arm=None):`
- 73. edited line 162: `return float((timing or {}).get("seconds"))`
- 74. edited line 232: `# ------------------------------------------------------- decision`
- 75. edited lines 301-308: `if ft_tpc is None or b2_tpc is None or bx_tpc is None \`
- 76. wrote 7607 bytes to experiments/final/test_compare.py
- 77. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_compare.py 2>&1 | tail -6` → exit 0
- 78. edited lines 50-69: `def _world(tmp_path, ft_fail_jobs=()):`
- 79. edited lines 148-151: `def test_failing_world_claim_does_not_hold(tmp_path):`
- 80. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final/test_compare.py 2>&1 | tail -3` → exit 0
- 81. ran `cd ~/projects/forge && .venv/bin/python -c "` → exit 0
- 82. ran `cd ~/projects/forge && .venv/bin/python -c "` → exit 0
- 83. edited lines 282-308: `def refuses_escalate_run(path):`
- 84. edited lines 181-193: `def test_loader_accepts_jsonl_and_json_array(tmp_path):`
- 85. edited lines 202-207: `def test_loader_rejects_records_without_text_and_code(tmp_path):`
- 86. edited line 431: `def test_modal_forge_matches_glimmer_settings():`
- 87. ran `cd ~/projects/forge && .venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad experiments/train experiments` → exit 0
- 88. ran `cd ~/projects/forge && .venv/bin/python experiments/train/forge_train.py smoke --cap-dollars 2.0; echo "exit=$?"` → exit 0
- 89. ran `cd ~/projects/forge && git status --short 2>&1 | head -20` → exit 0

## Final report

Done. All round-2 builds are in place and verified.

Files changed (nothing committed):
- [runner_final.py](~/projects/forge/experiments/final/runner_final.py) (new, §3+§3b+N1): arm FT = arm-A messages/body with model `forge`; FT one-shot loop (box → grader); BX cloud loop mirroring frozen `do_bx_call`; `--fill-missing` (workers default 12, exit 3 + `INCOMPLETE: ask the user`); every record carries `grader: first-test|factory`; dev runs print the PLAN step-5 gate; vLLM digest in every summary.
- [test_runner_final.py](~/projects/forge/experiments/final/test_runner_final.py) (new, 14 tests): FT≡arm-A-except-model, BX message-list equality vs frozen loop with real scored shapes, fill-missing/INCOMPLETE, no-keys exit 2, §6 static checks.
- [modal_forge.py](~/projects/forge/deploy/modal_forge.py) (new, §6) + [run_final_session.sh](~/projects/forge/experiments/final/run_final_session.sh) (new, §6): dev pilot + GO/STOP, cap with reserve, trap stops `forge-trained`.
- [compare.py](~/projects/forge/experiments/final/compare.py) (new, §7+E2) + [test_compare.py](~/projects/forge/experiments/final/test_compare.py) (new, 10 tests): 4-input merge, duplicate/missing/INCOMPLETE refusals (exit 2), bootstrap bars at exact boundaries, 79-answer disclosure, BX wall = 3,050 s + 6a sans cold start.
- `experiments/train/forge_train.py` (E3 filter only) + `test_forge_train.py` (3 new tests; 1 existing loader test updated to the new contract).

Verification observed:
- `.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad experiments/train experiments/common` → **284 passed, 2 skipped**.
- `runner_final.py --jobs main --out X` with no keys → exit 2, `missing environment variables: FORGE_URL, FORGE_KEY`, no network.
- `forge_train.py smoke --cap-dollars 2.0` → `CAP REFUSED`, exit 2.
- Loader tests show `dropped_non_spark=2` and the `--escalate` ValueError.

Two deviations to know: (1) the pre-existing loader test asserted teacher-less records load — updated to the E3 contract (smoke examples now load as `[]`; tagging them `spark` would fabricate provenance, so with an adequate cap `run_smoke` would train on zero records — needs a follow-up decision); (2) `compare.py` also refuses when FT lacks a job or no arm has a PASS (needed for the bootstrap/denominators), and exits 1 when bars compute but the claim fails. Live-factory files under `results/` were not touched; scratch checks stayed in `/tmp`.
