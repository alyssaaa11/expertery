# Muse Code round 3c: serve the RIGHT trained model (verifier D1, forge-r3-dev-go-2026-10-30)
Nothing is running. All rules in experiments/final/MUSE_SPEC.md "Rules" apply. Edit only deploy/modal_forge.py,
experiments/final/run_final_session.sh and their tests.
- deploy/modal_forge.py reads FORGE_MODEL_NAME from os.environ at import; Modal re-imports the module inside the
  container where the variable is not set, so it serves /vol/final/merged. Pass the name INTO the container (e.g.
  `image.env({"FORGE_MODEL_NAME": MODEL_NAME})` evaluated at deploy time, or `modal.Secret.from_local_environ`), and log
  the served path at start-up ("SERVING /vol/<name>/merged").
- run_final_session.sh: after "ready", fetch `$URL/v1/models` (with the key) and print the served model's `root`; refuse
  the pilot (exit 1, app stopped by the trap) unless it equals /vol/$FORGE_MODEL_NAME/merged (default final).
- Tests: the deploy-time name reaches the container env (static check of the image/env construction); the session
  refuses on a root mismatch (fake curl/models response).
Done when: pytest (experiments/final experiments/train experiments/factory experiments/common dashboard) passes.
Report: files changed, pytest line.
