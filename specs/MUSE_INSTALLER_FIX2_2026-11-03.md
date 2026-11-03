# Muse Code fix round 2: Expertery v0 install dependencies (2026-11-03)

Found by Claude in the first real `expertery exam build` after `sh install.sh`: the uv tool env (Python 3.14, deps
only `modal`) fails at `expertery/cloud.py load_runner` → experiments/first-test/runner.py imports checks.py →
`import cadquery` → ModuleNotFoundError. The forge .venv works because it has cadquery 2.8.0 on Python 3.12 (system
Pythons ≥3.13 have no cadquery wheels; the cloud box pins cadquery==2.8.0, cadquery-ocp==7.9.3.1).

Fix (files: pyproject.toml, install.sh, docs/INSTALL.md, expertery/tests/* only; no Modal/network/model calls;
run `.venv/bin/python -m pytest expertery -q`):
1. pyproject.toml: requires-python ">=3.12,<3.13"; dependencies add "cadquery==2.8.0" and "cadquery-ocp==7.9.3.1"
   (same pins as the cloud box; read them from cloud_cq.pip_spec to confirm, do not change cloud_cq).
2. install.sh: `uv tool install --python 3.12 --editable "${REPO_DIR}"` (add `--reinstall` so re-running the script
   upgrades an existing install). Keep the uv/modal checks.
3. docs/INSTALL.md: say why (CadQuery runs locally only to load the factory's prompt/check modules; model-written code
   never runs locally, it runs in the cloud box).
4. Test: pyproject pins match cloud_cq's pip spec; install.sh contains `--python 3.12` and `--reinstall`.
Report: files changed + pytest summary line.
