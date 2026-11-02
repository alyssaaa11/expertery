Round P2c: total budget + one free live try per visitor + a "free tries left" counter (user decision, 2026-11-02).
Repo: ~/projects/forge. Read app/backend/*, deploy/modal_web.py, app/web/*, app/tests/* first.

User's words: "15 in total; on the page: try it, maximum one per try; if they tried once they [can't] do it another
time; show how many free tries are left."

Build (each with tests):
1. TOTAL cap: new config `TOTAL_CAP_USD` (default 15). Total spend = sum over ALL days in the spend store (persisted in
   the Modal Dict, mirrored like the daily spend). When total spend >= TOTAL_CAP_USD: status "paused" and build 429
   with the paused message. Keep `DAILY_CAP_USD` but change its default to 15 (so only the total binds unless set).
   Add both names to deploy/modal_web.py `_BAKED_ENV`.
2. One live try per visitor: new config `MAX_LIVE_TRIES_PER_VISITOR` (default 1). Count successful build STARTS per
   visitor IP (same last-hop IP rule) in a persisted Modal Dict `homegrown-tries` (in-process copy behind the lock, the
   Dict for persistence). Over the limit → 429 {"message": "You've used your free live try. You can watch the recorded
   demo as many times as you like.", "reason": "tried"}. The old per-hour IP limit stays as an extra guard.
3. Counter: `GET /api/status` adds `"tries_left": int` = max(0, floor((TOTAL_CAP_USD - total_spend) / EST_TRY_USD)),
   new config `EST_TRY_USD` (default 0.30), and `"you_tried": bool` for the caller's IP.
4. Page (app/web): near the Build button show "≈ N free live tries left" (from tries_left; "≈" always, never claim
   exact). If you_tried (or localStorage key `hg_tried` is set after the visitor's own live build), the Build button
   becomes "Watch the recorded demo" and plays recorded_run.json, with the line "You've used your free live try."
   The recorded demo is always available to everyone. Keep the design exactly; only add these small elements in the
   existing style.
Tests: total cap across 2 days pauses; second build from the same IP → 429 reason tried; another IP still allowed;
tries_left math; status you_tried; page shows the counter element and the localStorage key name; TestClient checks of
the new status fields; config defaults.

Rules: only change files under app/ and deploy/modal_web.py. Keep every earlier fix (static mount LAST, baked env,
FORGE_URL startup check, FTX self-check round in loop.py). No network, no Modal calls, no deploy, no model calls, no
git push, no pip install. Run `.venv/bin/python -m pytest -q app/tests` and `.venv/bin/python -m pytest -q
experiments/final experiments/r5` (must stay green). Report: diff summary, test results, deviations with reasons.
