# What Muse Code did: round r1c

Made from the raw event log results/muse-final-r1c.jsonl: every step Muse took, in order. Edits show the first new line (the log does not name the file).

## The prompt it got

> # Muse Code round 1c: job text = reference (verifier G1, forge-factory-fix-2026-10-30) — waits for the user's yes

## Its steps

- 1. ran `ls -R | head -n 200; echo ---; ls -la; cat experiments/final/MUSE_SPEC.md 2>/dev/null | head -n 300` → exit 0
- 2. read experiments/final/MUSE_ROUND1C.md
- 3. read experiments/factory/generator.py
- 4. read experiments/factory/make_jobs.py
- 5. read experiments/factory/patterns.py
- 6. read experiments/factory/gallery.py
- 7. read experiments/factory/generator.py
- 8. read experiments/train/forge_train.py
- 9. read experiments/train/forge_train.py
- 10. read experiments/factory/test_generator.py
- 11. read experiments/factory/test_patterns.py
- 12. read experiments/factory/test_gallery.py
- 13. ran `python3 - <<'EOF'` → exit 0
- 14. read experiments/factory/teacher.py
- 15. read experiments/factory/test_teacher.py
- 16. ran `ls experiments/train/; grep -n "guard\|app.run\|cloud_cq_context\|default_box_measure\|default_train_meas" experiments/train/test_forge_trai` → exit 0
- 17. ran `grep -n "measure_brep\|def run_answer_in_box\|_app" experiments/final/cloud_cq.py | head -n 30; echo ---; python3 -c "import cadquery; print` → exit 0
- 18. ran `ls .venv/bin/ 2>/dev/null | head; .venv/bin/python -c "import cadquery; print(cadquery.__version__)" 2>&1 | tail -1; .venv/bin/python -m pyt` → exit 0
- 19. read experiments/train/test_forge_train.py
- 20. ran `ls results/ | head -30; ls results/factory-gallery/ 2>/dev/null; grep -o 'viewBox="[^"]*"' results/factory-gallery/svgs/F1.svg 2>/dev/null; ` → exit 0
- 21. ran `.venv/bin/python -c "import modal; print('modal yes')" 2>&1 | tail -1; cat experiments/factory/split.json; head -3 experiments/factory/jobs.` → exit 0
- 22. ran `ls results/factory-gallery/svgs/ | head; F=$(ls results/factory-gallery/svgs/ | head -1); head -c 800 results/factory-gallery/svgs/$F; echo;` → exit 0
- **plan**: [ ] Baseline pytest over the 5 folders; [ ] generator.py: round-first + refs from printed numbers (all families, F4/F10 text fixes); [ ] make_jobs.py TEXT=REF self-check column; [ ] patterns.py: teacher API/HTTP error -> our_bug/harness + test; [ ] forge_train.py guard: single _app.run() for whole pass + test; [ ] gallery.py viewBox fit + test; [ ] Regenerate jobs/split/dev, rerun gallery, full pytest, report
- 23. ran `.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad experiments/train experiments/common 2>&1 | tail -5` → exit 0
- 24. ran `.venv/bin/python -c "` → exit 0
- **plan**: [x] Baseline pytest over the 5 folders; [ ] generator.py: round-first + refs from printed numbers (all families, F4/F10 text fixes); [ ] make_jobs.py TEXT=REF self-check column; [ ] patterns.py: teacher API/HTTP error -> our_bug/harness + test; [ ] forge_train.py guard: single _app.run() for whole pass + test; [ ] gallery.py viewBox fit + test; [ ] Regenerate jobs/split/dev, rerun gallery, full pytest, report
- 25. edited lines 74-106: `def _c1(p):`
- 26. edited lines 183-195: `def src2(p):`
- 27. edited lines 226-259: `def _c3(p):`
- 28. edited lines 311-333: `def _c4(p):`
- 29. edited lines 401-413: `def src5(p):`
- 30. edited lines 518-552: `def _c7(p):`
- 31. edited lines 602-613: `def _c8(p):`
- 32. edited lines 620-622: `def _tabs8(p):`
- 33. edited lines 638-676: `def text8(p):`
- 34. edited lines 719-727: `def src9(p):`
- 35. edited lines 759-794: `def _c10(p):`
- 36. edited lines 13-16: `Parameter ranges keep features from touching or overlapping by`
- 37. ran `.venv/bin/python - <<'EOF'` → exit 1
- 38. edited lines 566-572: `yc, ww, wn = num(c["yc"]), num(c["ww"]), num(c["wn"])`
- 39. ran `.venv/bin/python - <<'EOF'` → exit 0
- 40. ran `.venv/bin/python - <<'EOF'` → exit 0
- 41. edited lines 16-30: `import difflib`
- 42. edited lines 83-130: `def self_check(jobs, texts):`
- 43. edited lines 9-14: `Self-check (SPEC section 1): every reference builds one valid solid`
- 44. edited lines 88-97: `def test_self_check_table_ok_on_real_jobs():`
- 45. edited lines 120-130: `body = make_jobs.body_of(job["reference"])`
- 46. edited lines 50-51: `ID_RE = re.compile(r"F\d+-\d+$")`
- 47. edited lines 106-119: `if rec.get("verdict") == "PASS":`
- 48. edited lines 18-21: `Every FAIL or error gets a signature (category, key). Categories:`
- 49. edited lines 71-83: `def test_harness_is_our_bug(tmp_path):`
- 50. edited lines 104-112: `_fake_run(str(tmp_path / "run-a"), [`
- 51. read experiments/train/test_forge_train.py
- 52. edited lines 461-478: `_GUARD_CTX_DEPTH = 0`
- 53. edited lines 565-590: `if train_meas_fn is None and ref_meases:`
- 54. edited lines 437-453: `def test_guard_uses_box_measure_for_code_side():`
- 55. edited lines 93-98: `def export_svg(shape, path):`
- 56. edited lines 7-12: `import builtins`
- **plan**: [x] Baseline pytest over the 5 folders; [x] generator.py: round-first + refs from printed numbers (all families, F4/F10 text fixes); [x] make_jobs.py TEXT=REF self-check column; [x] patterns.py: teacher API/HTTP error -> our_bug/harness + test; [x] forge_train.py guard: single _app.run() for whole pass + test; [ ] gallery.py viewBox fit + test; [ ] Regenerate jobs/split/dev, rerun gallery, full pytest, report
- 57. edited lines 59-60: `def test_fit_viewbox_adds_margin_and_holds_drawing():`
- 58. ran `cd experiments/factory && ../../.venv/bin/python make_jobs.py 2>&1 | tail -20` → exit 0
- 59. ran `cat experiments/factory/split.json; echo ---; git -C ~/projects/forge status --short | head -20; git -C ~/projects/f` → exit 0
- 60. ran `.venv/bin/python experiments/factory/gallery.py 2>&1 | tail -3 && grep -c 'viewBox=' results/factory-gallery/index.html && grep -c 'class="c` → exit 0
- **plan**: [x] Baseline pytest over the 5 folders; [x] generator.py: round-first + refs from printed numbers (all families, F4/F10 text fixes); [x] make_jobs.py TEXT=REF self-check column; [x] patterns.py: teacher API/HTTP error -> our_bug/harness + test; [x] forge_train.py guard: single _app.run() for whole pass + test; [x] gallery.py viewBox fit + test; [ ] Regenerate jobs/split/dev, rerun gallery, full pytest, report
- 61. ran `.venv/bin/python -m pytest -q experiments/final experiments/factory experiments/freecad experiments/train experiments/common 2>&1 | tail -6` → exit 0
- 62. ran `sha256sum experiments/factory/jobs.jsonl experiments/factory/split.json experiments/factory/jobs_dev.jsonl; .venv/bin/python -c "` → exit 0
- 63. ran `.venv/bin/python - <<'EOF'` → exit 0
- 64. ran `.venv/bin/python - <<'EOF'` → exit 0
- **plan**: [x] Baseline pytest over the 5 folders; [x] generator.py: round-first + refs from printed numbers (all families, F4/F10 text fixes); [x] make_jobs.py TEXT=REF self-check column; [x] patterns.py: teacher API/HTTP error -> our_bug/harness + test; [x] forge_train.py guard: single _app.run() for whole pass + test; [x] gallery.py viewBox fit + test; [x] Regenerate jobs/split/dev, rerun gallery, full pytest, report

## Totals

- steps: {'bash': 20, 'read_file': 15, 'edit_file': 29}
- 57 model calls, ≈ $1.62

## Its final report

Done. Job text now states exactly what the reference builds in all 10 families.

Files changed
- [generator.py](~/projects/forge/experiments/factory/generator.py): every family shares one canonical number set rounded to the printed precision before text or reference uses it. References are built from printed numbers only: diameters enter and radii exist only as `(D)/2`, profile corners only as `(centre ± width/2)`, overshoots only as `(value + 1)`. F4 text says "square ends" and the slot is rebuilt from its printed centreline endpoints plus printed width. F10 text gives rim inner/outer diameters and recess bottom diameter. Seed, ids, families, 20 jobs each, and parameter ranges unchanged.
- [make_jobs.py](~/projects/forge/experiments/factory/make_jobs.py): new `TEXT=REF` column; per job every non-small-integer reference literal must appear among the text's numbers. Regenerated [jobs.jsonl](~/projects/forge/experiments/factory/jobs.jsonl), [jobs_dev.jsonl](~/projects/forge/experiments/factory/jobs_dev.jsonl); [split.json](~/projects/forge/experiments/factory/split.json) byte-identical.
- [patterns.py](~/projects/forge/experiments/factory/patterns.py): teacher API/HTTP call failure (INVALID, empty code, transport error) is `harness`/`our_bug`, checked before `no_code`.
- [forge_train.py](~/projects/forge/experiments/train/forge_train.py): guard holds `cloud_cq._app.run()` once per pass via a re-entrant `cloud_cq_context()`; per-record measures reuse it. `checks.py` and `cloud_cq.py` untouched.
- [gallery.py](~/projects/forge/experiments/factory/gallery.py): `fit_viewbox_to_drawing` fits the viewBox to the transformed path bbox with a 5% margin; rewrote [index.html](~/projects/forge/results/factory-gallery/index.html) (10 cards, 10 viewBoxes, each strictly holding its drawing).
- Tests added (16): TEXT=REF on all 200 jobs plus a 21.2-vs-21.3 negative test, the API-error `our_bug` test, the single-`app.run()` guard test, and three viewBox tests.

Verification
- `pytest: 251 passed, 2 skipped in 18.74s` over the same 5 folders (baseline was 235 passed + 2 skipped; +16 new, none removed).
- Self-check table: `VALID 20/20`, `WRONG-1/2 FAIL`, `OVERLAP < 0.5`, `TEXT=REF 20/20` in all 10 families, `SELF-CHECK OK`.
- sha256: jobs.jsonl `e40099c4…f695bf1ec`, split.json `57282ffd…737b8fd`, jobs_dev.jsonl `b32a6fa2…136344eb`. Dev ids unchanged (same 20 ids). `FACTORY_VERSION` is now `d2423ca86d46`.
- Spot checks: F3-1 floor is 21.2 centred at 27.8 in both text and reference; F4-1 slot is "5.9 wide with square ends"; F10-1 rim/recess diameters all printed.

Not followed / notes
- Nothing in the round was skipped. One judgment call: the TEXT=REF check exempts whole-number literals with |v| ≤ 8 (through-cut overshoots, origins). Integer design values above 8 are still checked, and every fractional literal must match within 1e-9, so all four verifier mismatch classes are caught.
- The `.obsidian/workspace.json` modification in git status is not mine; I left it alone.
