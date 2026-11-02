# Muse Code task: Homegrown product page (live demo), 2026-11-02

Repo: ~/projects/forge. Two rounds, run as two separate Muse sessions. **Round P1 first; round P2 only
after P1 is checked.** Do not run any Modal, network or model call, and do not deploy. Claude deploys later, after the
user says yes. Do not touch `experiments/`, `results/`, `data/`, `company/`, the exam files or the wiki. You may only
import from `experiments/final/` (read-only).

The design is decided by the user. **Copy it; do not redesign it.** Source of truth:
`docs/product/mockup/index.html` (v3: full-screen, FYNSEC-style frame, Familjen Grotesk, teal #1fa39a, animations,
hex-nut + sprout logo) with its assets `object.jpeg`. Copy text, layout, colours and animations exactly. The only
changes are the ones listed below.

---

## Round P1: the page (frontend only)

Create `app/web/` with:
- `index.html`, `styles.css`, `app.js` (split from the mockup; no build step, no framework), `object.jpeg` (copy).
- `recorded_run.json`: one demo run in the event format below (use the mockup's L-bracket story: write → build →
  measure finds "2 solids, expected 1" → fix → PASS). Mark it `"recorded": true`. Claude will replace it later with a
  real recorded run.

Changes from the mockup:
1. Remove the yellow "MOCKUP" pill.
2. The 3D object keeps a small caption under it: "Illustration".
3. The demo panel calls the real API:
   - On "Build it": first `GET /api/status` → `{"state": "ready"|"waking"|"paused", "message": str}`.
     - `paused`: show the message ("Demo paused: today's budget is used up…"), then play `recorded_run.json`
       labelled "Recorded run". Show the GitHub and video links and the form.
     - `waking`: show "Waking up the model (about 1–3 min). Here is a recorded run meanwhile." Play the recorded run,
       then start the live run when it finishes.
     - `ready`: start the live run.
   - Live run: `POST /api/build` with JSON `{"job": text}`. The response is Server-Sent Events, one JSON object per
     event:
     `{"step":"write"|"build"|"measure"|"fix"|"done"|"error", "round":1..3, "detail":str, ...}`.
     The final `done` event carries `{"verdict":"PASS"|"CHECK FAILED", "measurements":{...}, "code":str,
     "stl_url":str, "step_url":str, "rounds":int, "seconds":float}`.
     Map the events onto the 5 existing step rows (same CSS classes as the mockup: on/done/fix). The timer shows
     "live run · N s", or "recorded run · N s" for the recording.
   - `done`: show the result row (PASS badge only when verdict is PASS; otherwise a neutral "Checks failed: see
     measurements" badge, never a fake PASS). Show the measurements as small chips, the code in a collapsible `<pre>`,
     and STL/STEP/code download links. Show a 3D view of the STL with three.js r160 from a pinned CDN URL
     (OrbitControls, steel material, slow auto-rotate, teal edges). If WebGL fails, hide the viewer.
   - `error` (HTTP 429/413/5xx or an error event): show the message from the server in the panel, never a stack trace.
4. Input: limit the textarea to 600 characters with a visible counter. The 3 example chips fill in full example jobs
   (write 3 realistic CadQuery jobs: L-bracket with 2 holes, flanged pipe adapter, electronics box with lid lip, each
   with all dimensions in mm).
5. Form: submits `POST /api/lead` with `{"tool":str,"email":str}`, then shows "Thanks, we read every answer." No
   other tracking, no cookies, no analytics.
6. Links: GitHub = https://github.com/alyssaaa11/expertery ; the video link stays `#video` (filled in later).
7. `prefers-reduced-motion` keeps working. The page must also work at 390 px width (stack the columns; hide the
   dark corner tabs on mobile).

Tests (`app/tests/test_web_static.py`, pytest, no browser needed):
- index.html, styles.css, app.js, object.jpeg and recorded_run.json exist; recorded_run.json parses, every event has a
  valid `step`, and it ends with `done` + `"recorded": true`.
- index.html contains the headline "The AI expert", "your company gets to", "keep." and no "MOCKUP".
- app.js references `/api/status`, `/api/build`, `/api/lead`, and contains no API key, no "VLLM", no "es_".

Also add `app/web/dev_server.py` (stdlib only): serves `app/web/` on localhost:8099 with a FAKE API (status ready, a
build that streams the recorded events with 0.8 s gaps, a lead that returns ok), so Claude can test the page in a
browser without any model.

---

## Round P2: the backend (Modal web app)

Create `deploy/modal_web.py` (Modal app name `homegrown-web`, CPU only, `min_containers=0`) and
`app/backend/` (pure-Python logic, importable and testable without Modal):

- **Serving:** a FastAPI ASGI app that serves `app/web/` at `/`, plus:
  - `GET /api/status`: `paused` if the daily budget is used up; otherwise `ready` if a cheap probe of the model
    endpoint (`GET {FORGE_URL}/v1/models`, 3 s timeout) answers, else `waking` (and fire one non-blocking warm-up
    request).
  - `POST /api/build`: SSE stream as in P1.
  - `POST /api/lead`: append `{"tool","email","ts"}` to a Modal Dict `homegrown-leads` (email ≤ 200 chars, tool ≤
    300 chars; reject otherwise). Never log emails to stdout.
  - `GET /files/<run_id>.(stl|step|py)`: files kept in a Modal Dict `homegrown-files` for 24 h.
- **The loop (same as the 92% second look, FTX):** the model is the trained Glimmer served by
  `deploy/modal_forge.py` (served name `forge`; URL from env `FORGE_URL`; key from the existing Modal secret
  `forge-glimmer`, env `VLLM_API_KEY`). Messages start from `runner_final.ft_messages(job)`. Then up to 3 model calls:
  after a crash append the assistant reply and `runner.bx_error_message(error)`; after a build append
  `runner.bx_self_check_message(measure)`; a reply without a code fence ("DONE") ends the loop. Build every request body exactly as the FTX arm does (`runner.build_bx_body`: 16,000 max tokens, the same
  temperature/top_p/top_k, and the same reasoning setting). Make the reasoning strength ONE setting, env `REASONING_STRENGTH`
  (allowed: "high" or "xhigh"; default "xhigh" = what the 92% second look used, verifier F1). The decision is open: the user
  asked whether "high" (what the model was trained on) is better or faster; a small check on factory practice jobs decides
  before deploy. Test: the body sent to the model carries exactly the configured value. Import these helpers (`runner` is experiments/first-test/runner.py, imported by runner_final.py the same way); do not copy-paste them. If an import is impossible
  without side effects, stop and report it instead of rewriting them.
- **The box:** each answer runs in `cloud_cq.run_answer_in_box(code)` (the locked Modal sandbox, app `forge-cq`).
  Measurements come from its measure output. The **verdict on the page is a no-reference self-check**, because a
  visitor's job has no reference part: PASS only if the part built, `solids == 1`, and the bounding-box extents
  match every dimension that the job text states explicitly as overall size, within 0.5%. Otherwise "CHECK FAILED"
  with the reasons. The function is `app/backend/selfcheck.py:self_check(job_text, measurements) -> (verdict, reasons)`.
  Keep it simple and conservative, and test it.
- **Files:** convert the built BREP to STL (tolerance 0.1 mm) and STEP inside the CPU web container (CadQuery 2.8.0,
  same pins as `cloud_cq.pip_spec()`). Never execute visitor-supplied or model code in the web container: only the
  sandbox runs code. The web container only reads the BREP that the sandbox returns.
- **Protection (all limits in one config block at the top of modal_web.py, read from env with these defaults):**
  - `MAX_JOB_CHARS=600` → 413.
  - Per IP: `MAX_BUILDS_PER_IP_HOUR=4` → 429 with "Please wait a bit…".
  - Global: `MAX_CONCURRENT_BUILDS=2` → 429 "Busy, try again in a minute".
  - **Daily budget:** `DAILY_CAP_USD=20` (the user's number; Claude may change it at deploy). Cost estimate per build
    = model GPU seconds × `GPU_USD_PER_S=0.000694` (A100-80GB ≈ $2.50/h) + `SANDBOX_USD_PER_BUILD=0.002`, plus a
    `WAKE_USD=0.25` charge each time the status probe finds the model cold. The spend is kept in a Modal Dict keyed by
    UTC date. At or over the cap, `/api/status` returns `paused` and `/api/build` returns 429 with the paused message.
  - A whole build has a 240 s wall-clock limit → error event "This part took too long; try a simpler one".
  - Model output and errors shown to visitors are capped at 4,000 characters and HTML-escaped by the page.
- No Claude, no other model, no analytics, no third-party calls except the three.js CDN in the page.

Tests (`app/tests/`, pytest, all with fakes; no Modal, no network):
- the loop with a fake model + fake box: crash → fix → build → PASS gives event order write, build, fix, write, build,
  measure, done; messages match the FTX rules exactly (round 1 == ft_messages(job)); max 3 model calls;
- `self_check`: correct box passes; 2 solids fail; wrong extent fails; a job with no stated overall size passes only
  on built + 1 solid, with reason "no overall size stated";
- limits: 601 chars → 413; 5th build from one IP in an hour → 429; a third concurrent build → 429; spend at the cap
  → status paused and build 429; the wake charge is added once per cold probe;
- `/api/lead` rejects a 201-char email; the lead is not printed to stdout;
- no secret value in any HTML/JS/JSON under app/web (grep for VLLM_API_KEY's env name and "es_").

## Report (each round)
Diff summary, the exact pytest command and result (`.venv/bin/python -m pytest -q app/tests` plus the existing
`experiments/final experiments/r5` suites, which must stay green), and anything you could not follow or decided
differently (with the reason).
