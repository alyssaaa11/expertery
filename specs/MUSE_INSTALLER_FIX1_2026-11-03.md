# Muse Code fix round 1: Expertery v0 (2026-11-03)

Found by Claude in the first real install (`sh install.sh` OK; `expertery init` failed):
`modal deploy experiments/final/cloud_cq.py` → "module 'cloud_cq' has no attribute 'app'". In cloud_cq the box app
(forge-cq) is looked up on demand (`lookup_exec_app`, create_if_missing) and the grader app is EPHEMERAL: callers
wrap work in `with cloud_cq.modal.enable_output(): with cloud_cq._app.run(): ...` (see runner_final.main around the
run_ftx_suite / run_ft_suite calls). The exam agent calls `cloud_cq.grade.remote` without that context, so the first
real `exam build` would fail too.

Fix (files: expertery/cli.py, expertery/cloud.py, expertery/exam_agent.py, expertery/tests/*, docs/INSTALL.md; nothing
else; no Modal/network/model calls; run `.venv/bin/python -m pytest expertery -q`):
1. `init`: remove the `modal deploy` step. Instead call `cloud_cq.lookup_exec_app()` once (creates the box app in the
   user's own account if missing) via a cloud.py adapter, print "box app forge-cq ready in your Modal account; the
   referee (grader) starts on demand during each run and stops after". --dry-run prints that plan. Keep the profile
   and key checks and the config write.
2. `exam build` (real run, i.e. not dry-run and no injected box_fn/grade_fn): run all jobs inside
   `with cloud_cq.modal.enable_output(): with cloud_cq._app.run():` (one context for the whole build, via a cloud.py
   helper `cloud_session()` that is a no-op contextmanager when fakes are injected).
3. Tests: init never runs `modal deploy` and calls the lookup adapter once; exam build enters cloud_session exactly
   once for a real run and never for dry-run / injected fakes.
4. docs/INSTALL.md: update the init description.
Report: files changed + pytest summary line.
