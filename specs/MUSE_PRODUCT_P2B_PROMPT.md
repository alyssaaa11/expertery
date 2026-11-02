Round P2b: fix the verifier's NO-GO findings on the Homegrown web backend. Read first:
specs/MUSE_PRODUCT_2026-11-02.md (the spec), ~/agents/verifier/reports/forge-web-backend-2026-11-02.md (the review),
then app/backend/*, deploy/modal_web.py, app/tests/*. Repo: ~/projects/forge. W1 (static mount order) is
already fixed by Claude in deploy/modal_web.py: keep it (mount "/" LAST).

Fix, each with tests:
W1-test: install nothing; if `fastapi` is importable, add FastAPI TestClient tests of the real ASGI app built by a
  factory function you extract from modal_web.web() (e.g. `app/backend/webapp.py: make_app(deps)`, with model, box,
  Dicts and clock injected; modal_web.web() just calls it). Tests: GET / 200 (the page), GET /api/status 200 JSON,
  POST /api/build streams SSE, POST /api/lead 200, /files 404 for unknown ids, GET /dev_server.py 404. If fastapi is
  not importable, mark these tests skipped with a clear reason and tell Claude which package to install
  (fastapi==0.115.6, httpx).
W2 (money): /api/status must never send a request to the model endpoint by itself. Learn "warm" WITHOUT a request:
  an in-process `warm_until` timestamp = last real model response time + 300 s (scale-down). Optionally also
  `modal.Function.from_name("forge-trained", "serve").get_current_stats()` (container count) behind a try/except,
  never required by tests. A cold model is only woken by (a) a throttled warm-up (≤ 1 per 10 min globally, ≤ 1 per hour
  per IP) or (b) a real build; charge WAKE_USD for every cold start of either kind (a build that starts while not warm
  is charged WAKE_USD once).
W3 (money): charge every build, also on timeout, exception, no-code done or a closed tab: accumulate model seconds
  as calls finish, and charge them + SANDBOX_USD_PER_BUILD + the idle-tail rule in one `finally`, exactly once.
W4: pass a deadline into the loop: each model call's timeout = min(600, time left until BUILD_LIMIT_S); no new model
  call or box run after the deadline; the concurrency slot is released only when the worker thread really ends.
  Test with a fake slow model that a timed-out build does not make a further call and that the slot stays taken until
  the worker ends.
Small:
- /api/lead: per-IP limit 5 per hour → 429.
- Privacy line: replace with "We only use your email to reply about Homegrown. To delete it, send the form again with
  the same email and the word delete as the tool." Implement it: a lead whose tool is exactly "delete" (case-insensitive,
  trimmed) removes every stored lead with that email and stores nothing; respond {"ok": true, "deleted": n}; the page
  shows "Deleted." Remove the CONTACT_EMAIL placeholder.
- Remove app/web/dev_server.py from the web image file list (keep the file in the repo for local tests) and make sure
  the image only serves index.html, styles.css, app.js, object.jpeg, recorded_run.json.

Rules: only change files under app/ and deploy/modal_web.py. No network, no Modal calls, no deploy, no model calls, no
git push, no pip install. Run `.venv/bin/python -m pytest -q app/tests` and `.venv/bin/python -m pytest -q
experiments/final experiments/r5` (must stay green). Report: diff summary, test commands and results, and anything
you could not follow or decided differently, with the reason.
