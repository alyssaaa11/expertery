"""The Homegrown demo FastAPI app, built by a factory (verifier W1 seam).

``make_app(deps)`` builds the real ASGI app with everything external
injected; ``deploy/modal_web.py`` ``web()`` only builds the real deps and
calls it. No Modal, no network and no model call in this module: the model,
the box, the stores and the clocks all arrive via ``deps``.

``deps`` keys (all optional unless noted):

- ``model``: ``(messages, body, timeout) -> (content, gpu_seconds)``.
  Required for ``/api/build`` to run; without it builds answer 500.
  ``timeout`` is ``min(600, time left until the build deadline)``.
- ``box``: ``(code) -> run_answer_in_box-style dict``. Required too.
- ``convert``: ``(brep_bytes) -> (stl_bytes, step_bytes)``. When missing,
  only the ``.py`` file is kept.
- ``warmer``: ``(ip) -> None``. Fires one warm-up request; called
  synchronously, so the real one must return fast (spawn a thread).
- ``containers``: ``() -> int | None``. Container count learned WITHOUT
  sending the model an input (e.g. Modal ``get_current_stats``); ``None``
  means unknown. Never required.
- ``leads`` / ``files``: Modal-Dict-like stores (``get``/``[]``/``del``).
  Plain dicts work in tests.
- ``tries``: Modal-Dict-like store (``get``/``[]``) of per-IP successful
  live-build starts, persisted in the ``homegrown-tries`` Modal Dict.
  Plain dicts work in tests.
- ``money``: ``budget.Budget``. ``rates``: ``limits.RateState``.
  ``lead_rates``: ``limits.LeadRate``. ``try_state``: ``limits.TryState``.
- ``now``: wall-clock callable (for money/rates/file timestamps).
  ``monotonic``: steady-clock callable (for deadlines).
- ``build_limit_s``, ``file_ttl_s``, ``web_dir``.
- ``mirror``: ``(money) -> None`` (persist spend). ``reconcile``:
  ``(money) -> None`` (reload spend after a restart).

Money rules implemented here (verifier W2/W3/W4):

- ``/api/status`` never sends a request to the model. Warmth comes from
  the in-process ``warm_until`` (last real response + 300 s) and,
  optionally, the ``containers`` count. A cold model is only woken by a
  throttled warm-up (<= 1 per 10 min globally, <= 1 per hour per IP, each
  fired warm-up charged WAKE_USD) or by a real build (a build that starts
  while not warm is charged WAKE_USD once).
- Every build is charged exactly once in the worker thread's ``finally``:
  accumulated model seconds + sandbox fee + the idle-tail rule, on every
  exit path (done, timeout, exception, no-code done, closed tab).
- The whole generator runs in ONE worker thread with a deadline; the
  concurrency slot is released only when that thread really ends.
"""

import asyncio
import os
import threading
import time

from . import budget as budget_mod
from . import config
from . import limits as limits_mod
from . import loop as loop_mod
from . import stream as stream_mod

MODEL_CALL_MAX_S = 600.0  # one model call never gets longer than this
DELETE_TOOL = "delete"  # a lead with exactly this tool deletes by email


def request_ip(request):
    """Client IP: LAST X-Forwarded-For hop first, else the peer."""
    peer = ""
    try:
        peer = (request.client.host if request.client else "") or ""
    except Exception:  # noqa: BLE001
        peer = ""
    try:
        forwarded = request.headers.get("x-forwarded-for", "")
    except Exception:  # noqa: BLE001
        forwarded = ""
    return limits_mod.client_ip(forwarded, peer)


def _store_get(store, key, default=None):
    try:
        value = store.get(key)
    except Exception:  # noqa: BLE001 -- Dict is best-effort persistence
        return default
    return default if value is None else value


def _store_set(store, key, value):
    try:
        store[key] = value
    except Exception:  # noqa: BLE001 -- best effort only
        pass


def _store_del(store, key):
    try:
        del store[key]
    except Exception:  # noqa: BLE001 -- best effort only
        pass


def make_app(deps=None):
    """Build the Homegrown FastAPI app from injected dependencies."""
    import fastapi  # noqa: E402 -- deferred so the module imports w/o it
    from fastapi.responses import JSONResponse, Response  # noqa: E402
    from fastapi.staticfiles import StaticFiles  # noqa: E402

    deps = dict(deps or {})
    wall = deps.get("now") or time.time
    mono = deps.get("monotonic") or time.monotonic
    money = deps.get("money") or budget_mod.Budget(now=wall)
    rates = deps.get("rates") or limits_mod.RateState(now=wall)
    lead_rates = deps.get("lead_rates") or limits_mod.LeadRate(now=wall)
    tries_state = deps.get("try_state") or limits_mod.TryState()
    tries_store = deps.get("tries")
    if tries_store is None:
        tries_store = {}
    model = deps.get("model")
    box = deps.get("box")
    convert = deps.get("convert")
    warmer = deps.get("warmer") or (lambda _ip: None)
    containers = deps.get("containers") or (lambda: None)
    leads = deps.get("leads")
    if leads is None:
        leads = {}
    file_store = deps.get("files")
    if file_store is None:
        file_store = {}
    build_limit = float(deps.get("build_limit_s", config.BUILD_LIMIT_S))
    file_ttl = float(deps.get("file_ttl_s", config.FILE_TTL_S))
    web_dir = deps.get("web_dir") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "web")
    mirror = deps.get("mirror") or (lambda _m: None)
    reconcile = deps.get("reconcile") or (lambda _m: None)
    state_lock = asyncio.Lock()

    def _containers_warm():
        """A positive container count means warm; unknown means not warm."""
        try:
            count = containers()
        except Exception:  # noqa: BLE001 -- best effort only
            return False
        try:
            return count is not None and float(count) > 0
        except (TypeError, ValueError):
            return False

    api = fastapi.FastAPI()
    # Allow the page hosted elsewhere (e.g. Vercel) to call this API directly
    # from the visitor's browser, so limits still see each visitor's own IP
    # (Claude fix 2026-11-02, disclosed). No cookies/credentials.
    origins = deps.get("allowed_origins")
    if origins is None:
        origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
    if origins:
        from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
        api.add_middleware(CORSMiddleware, allow_origins=list(origins),
                           allow_methods=["GET", "POST"],
                           allow_headers=["Content-Type"],
                           allow_credentials=False)

    def _tries_restore(ip):
        """Merge this IP's persisted try count into the in-process copy."""
        kept = _store_get(tries_store, ip, 0)
        try:
            kept = int(float(kept))
        except (TypeError, ValueError):
            kept = 0
        tries_state.restore(ip, kept)

    def _you_tried(ip):
        """True once this IP has used its free live try (or tries)."""
        _tries_restore(ip)
        return tries_state.count(ip) >= \
            config.MAX_LIVE_TRIES_PER_VISITOR

    def _tries_note(ip):
        """Record a successful live-build start, in-process + persisted."""
        _tries_restore(ip)
        tries_state.note(ip)
        _store_set(tries_store, ip, tries_state.count(ip))

    @api.get("/api/status")
    async def status(request: fastapi.Request):
        ip = request_ip(request)
        fire = False
        async with state_lock:
            reconcile(money)
            tried = _you_tried(ip)
            if money.is_capped():
                return {"state": "paused",
                        "message": config.PAUSED_MESSAGE,
                        "tries_left": money.tries_left(),
                        "you_tried": tried}
            # No model request here, ever (verifier W2): warmth comes from
            # the last real response, or the container count.
            state, message = money.warm_status(_containers_warm())
            if state == "waking" and money.may_warmup(ip):
                money.note_warmup(ip)  # WAKE_USD charged on every fire
                try:
                    mirror(money)
                except Exception:  # noqa: BLE001
                    pass
                fire = True
            payload = {"state": state, "message": message,
                       "tries_left": money.tries_left(),
                       "you_tried": tried}
        if fire:
            try:
                warmer(ip)
            except Exception:  # noqa: BLE001 -- warm-ups are best effort
                pass
        return payload

    @api.post("/api/build")
    async def build(request: fastapi.Request):
        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            payload = {}
        job = (payload or {}).get("job", "")
        denied = limits_mod.check_job(job)
        if denied:
            return JSONResponse({"message": denied[1]},
                                status_code=denied[0])
        if model is None or box is None:
            return JSONResponse({"message": "Build service not configured"},
                                status_code=500)
        ip = request_ip(request)
        async with state_lock:
            reconcile(money)
            if money.is_capped():
                return JSONResponse({"message": config.PAUSED_MESSAGE},
                                    status_code=429)
            _tries_restore(ip)
            denied = tries_state.check(ip)
            if denied:
                return JSONResponse({"message": denied[1],
                                     "reason": "tried"},
                                    status_code=denied[0])
            denied = rates.check_ip(ip)
            if denied:
                return JSONResponse({"message": denied[1]},
                                    status_code=denied[0])
            denied = rates.try_acquire()
            if denied:
                return JSONResponse({"message": denied[1]},
                                    status_code=denied[0])
            rates.note_build(ip)
            _tries_note(ip)
            # A build that starts while not warm boots the model: charge
            # WAKE_USD once (verifier W2). No request is sent to learn
            # this; warmth is in-process state plus container count.
            if not money.is_warm() and not _containers_warm():
                money.note_cold_build()
            try:
                mirror(money)
            except Exception:  # noqa: BLE001
                pass
        run_id = limits_mod.new_run_id()
        deadline = mono() + build_limit
        net = asyncio.get_running_loop()
        shelf = asyncio.Queue()
        finished = object()
        acct = {"gpu": 0.0}  # model seconds, accumulated as calls finish
        settled = {"charged": False}
        last = {}  # the last built answer's code + BREP (never run here)

        def _model_call(messages, body):
            # Each call gets what is left of the build (verifier W4).
            remaining = deadline - mono()
            if remaining <= 0:
                raise TimeoutError("build deadline exceeded")
            timeout = min(MODEL_CALL_MAX_S, remaining)
            t0 = mono()
            try:
                content, gpu_s = model(messages, body, timeout)
            except Exception:
                # A failed call still burned GPU time (verifier W3).
                acct["gpu"] += max(0.0, mono() - t0)
                raise
            try:
                money.note_model_response()  # a real response: warm now
            except Exception:  # noqa: BLE001
                pass
            try:
                acct["gpu"] += float(gpu_s or 0.0)
            except (TypeError, ValueError):
                acct["gpu"] += max(0.0, mono() - t0)
            return content, gpu_s

        def _box_run(code):
            out = box(code)
            try:
                if out and out.get("brep_bytes") is not None:
                    last["code"] = code
                    last["brep"] = out["brep_bytes"]
            except Exception:  # noqa: BLE001
                pass
            return out

        def _store_run(code, brep_bytes):
            _store_set(file_store, "%s.py" % run_id,
                       {"bytes": (code or "").encode("utf-8"),
                        "ts": wall()})
            if brep_bytes is None or convert is None:
                return
            try:
                stl_bytes, step_bytes = convert(brep_bytes)
            except Exception:  # noqa: BLE001 -- files are optional
                return
            try:
                _store_set(file_store, "%s.stl" % run_id,
                           {"bytes": bytes(stl_bytes), "ts": wall()})
                _store_set(file_store, "%s.step" % run_id,
                           {"bytes": bytes(step_bytes), "ts": wall()})
            except Exception:  # noqa: BLE001
                pass

        def _emit(event):
            try:
                net.call_soon_threadsafe(shelf.put_nowait, event)
            except Exception:  # noqa: BLE001 -- loop gone, nobody listens
                pass

        def _worker():
            # ONE thread runs the whole loop to the end (verifier W4): the
            # slot is released in this finally, so it stays taken while any
            # model call or box run is still going -- even after the HTTP
            # side has timed out or the tab was closed.
            try:
                gen = loop_mod.run_job(job, _model_call, _box_run,
                                       model="forge", clock=mono,
                                       deadline=deadline)
                for ev in gen:
                    if ev.get("step") == "done" and ev.get("code"):
                        try:
                            _store_run(last.get("code", ev["code"]),
                                       last.get("brep"))
                        except Exception:  # noqa: BLE001
                            pass
                        ev = dict(ev,
                                  stl_url="/files/%s.stl" % run_id,
                                  step_url="/files/%s.step" % run_id,
                                  code_url="/files/%s.py" % run_id)
                    _emit(ev)
            except Exception as err:  # noqa: BLE001 -- never a stack trace
                _emit(stream_mod.error_event("Build failed: %s" % err))
            finally:
                # Charge exactly once, on every exit path (verifier W3).
                if not settled["charged"]:
                    settled["charged"] = True
                    try:
                        money.charge_build(acct["gpu"])
                    except Exception:  # noqa: BLE001
                        pass
                    try:
                        mirror(money)
                    except Exception:  # noqa: BLE001
                        pass
                    rates.release()
                _emit(finished)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

        async def _queued():
            while True:
                item = await shelf.get()
                if item is finished:
                    return
                yield item

        async def _bounded():
            # First event goes out immediately; heartbeat at least every
            # HEARTBEAT_S; whole build limited to build_limit.
            try:
                async with asyncio.timeout(build_limit):
                    async for chunk in stream_mod.with_heartbeat(_queued()):
                        yield chunk
            except TimeoutError:
                yield stream_mod.encode_event(
                    stream_mod.error_event(config.BUILD_TIMEOUT_MESSAGE))

        return fastapi.responses.StreamingResponse(
            _bounded(), media_type="text/event-stream")

    @api.post("/api/lead")
    async def lead(request: fastapi.Request):
        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            payload = {}
        tool = (payload or {}).get("tool", "")
        email = (payload or {}).get("email", "")
        ip = request_ip(request)
        async with state_lock:
            denied = lead_rates.check(ip)
            if denied:
                return JSONResponse({"message": denied[1]},
                                    status_code=denied[0])
            lead_rates.note(ip)
        denied = limits_mod.check_lead(tool, email)
        if denied:
            return JSONResponse({"message": denied[1]}, status_code=denied[0])
        if str(tool).strip().lower() == DELETE_TOOL:
            # Delete: remove every stored lead with this email, store
            # nothing. Never logs or prints the email.
            want = str(email).strip().lower()
            try:
                seen = list(_store_get(leads, "leads", []) or [])
            except Exception:  # noqa: BLE001
                seen = []
            kept = [rec for rec in seen
                    if not isinstance(rec, dict) or
                    str(rec.get("email", "")).strip().lower() != want]
            removed = len(seen) - len(kept)
            _store_set(leads, "leads", kept)
            return {"ok": True, "deleted": removed}
        record = limits_mod.lead_record(tool, email)  # never printed/logged
        try:
            seen = list(_store_get(leads, "leads", []) or [])
        except Exception:  # noqa: BLE001
            seen = []
        seen.append(record)
        _store_set(leads, "leads", seen)
        return {"ok": True}

    @api.get("/files/{filename}")
    async def files(filename: str):
        name, dot, ext = filename.rpartition(".")
        if not dot or ext not in ("stl", "step", "py") or not name:
            return JSONResponse({"message": "Not found"}, status_code=404)
        blob = _store_get(file_store, "%s.%s" % (name, ext))
        if not isinstance(blob, dict) or \
                wall() - blob.get("ts", 0) > file_ttl:
            _store_del(file_store, "%s.%s" % (name, ext))
            return JSONResponse({"message": "Not found"}, status_code=404)
        ctype = {"stl": "model/stl", "step": "application/step",
                 "py": "text/plain"}[ext]
        data = blob.get("bytes")
        if data is None:
            return JSONResponse({"message": "Not found"}, status_code=404)
        if isinstance(data, str):
            data = data.encode("utf-8")
        return Response(bytes(data), media_type=ctype)

    @api.get("/dev_server.py")
    async def no_dev_server():
        # The local fake server stays in the repo for browser tests but is
        # NOT part of the web image: the image only serves index.html,
        # styles.css, app.js, object.jpeg and recorded_run.json.
        return JSONResponse({"message": "Not found"}, status_code=404)

    # Static page LAST, so it doesn't swallow /api/* and /files (verifier
    # blocker 2026-11-02; Claude's order fix, kept).
    api.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    return api
