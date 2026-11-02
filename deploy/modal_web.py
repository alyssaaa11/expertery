"""Homegrown live-demo web app (Round P2, spec specs/MUSE_PRODUCT_2026-11-02.md).

Modal app ``homegrown-web``: CPU only, ``min_containers=0``,
``max_containers=1`` (one process holds the rate counters behind an
asyncio lock; Modal Dicts are only persistence across restarts).

Deploy (Claude, after the user says yes; never from this session):

    modal deploy deploy/modal_web.py

Needs the Modal secret ``forge-glimmer`` (env ``VLLM_API_KEY`` inside the
container) and env ``FORGE_URL`` (the ``forge`` endpoint from
deploy/modal_forge.py). REASONING_STRENGTH ("high"|"xhigh", default
"xhigh") and the limits below are env-overridable at deploy.
"""

import asyncio
import json
import os
import sys
import threading
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import modal  # noqa: E402

from app.backend import budget as budget_mod  # noqa: E402
from app.backend import image_files as image_files_mod  # noqa: E402
from app.backend import limits as limits_mod  # noqa: E402
from app.backend import loop as loop_mod  # noqa: E402
from app.backend import stream as stream_mod  # noqa: E402

# ------------------------------------------------------------- config block
# All limits in one place, read from env with the spec defaults. These
# mirror app/backend/config.py exactly (app/tests/test_p2_config.py
# asserts they stay equal); the backend modules read the same env.
MAX_JOB_CHARS = int(os.environ.get("MAX_JOB_CHARS", "600"))
MAX_BUILDS_PER_IP_HOUR = int(os.environ.get("MAX_BUILDS_PER_IP_HOUR", "4"))
MAX_CONCURRENT_BUILDS = int(os.environ.get("MAX_CONCURRENT_BUILDS", "2"))
DAILY_CAP_USD = float(os.environ.get("DAILY_CAP_USD", "20"))
GPU_USD_PER_S = float(os.environ.get("GPU_USD_PER_S", "0.000694"))
SANDBOX_USD_PER_BUILD = float(os.environ.get("SANDBOX_USD_PER_BUILD", "0.002"))
IDLE_TAIL_USD = float(os.environ.get("IDLE_TAIL_USD", "0.21"))
WAKE_USD = float(os.environ.get("WAKE_USD", "0.45"))
BUILD_LIMIT_S = float(os.environ.get("BUILD_LIMIT_S", "600"))
WEB_TIMEOUT_S = float(os.environ.get("WEB_TIMEOUT_S", "720"))
HEARTBEAT_S = 15.0
PROBE_TIMEOUT_S = 3.0
FILE_TTL_S = 24 * 3600.0
LEAD_EMAIL_MAX = 200
LEAD_TOOL_MAX = 300
# REASONING_STRENGTH ("high"|"xhigh", default "xhigh") is read from the
# same env by app/backend/loop.py (config.reasoning_strength); the body
# sent equals runner.build_bx_body at the default.

FORGE_URL = os.environ.get("FORGE_URL", "")
FORGE_MODEL = "forge"

PAUSED_MESSAGE = "Demo paused: today's budget is used up. Here is a recorded run instead."
BUSY_MESSAGE = "Busy, try again in a minute"
RATE_MESSAGE = "Please wait a bit before building again"
TIMEOUT_MESSAGE = "This part took too long; try a simpler one"

# ------------------------------------------------------------- Modal pieces
app = modal.App("homegrown-web")


def _web_image():
    img = (
        modal.Image.from_registry("python:3.12-slim")
        .apt_install("libgl1", "libglib2.0-0", "libxrender1", "libx11-6",
                     "libxext6")
        .pip_install("cadquery==2.8.0", "cadquery-ocp==7.9.3.1",
                     "fastapi==0.115.6")
        .env({"PYTHONPATH": "/pkg"})  # remote imports of app.backend.*
    )
    for rel in image_files_mod.WEB_IMAGE_FILES:
        img = img.add_local_file(rel, "/pkg/" + rel)
    return img


leads_dict = modal.Dict.from_name("homegrown-leads", create_if_missing=True)
files_dict = modal.Dict.from_name("homegrown-files", create_if_missing=True)
spend_dict = modal.Dict.from_name("homegrown-spend", create_if_missing=True)

REMOTE_PKG = "/pkg"


# ------------------------------------------------------------- HTTP helpers
def _vllm_headers():
    return {"Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "")}


def probe_model():
    """Cheap readiness probe: GET {FORGE_URL}/v1/models (3 s timeout)."""
    if not FORGE_URL:
        return False
    try:
        req = urllib.request.Request(
            FORGE_URL.rstrip("/") + "/v1/models",
            headers={"Authorization": "Bearer "
                     + os.environ.get("VLLM_API_KEY", "")},
            method="GET")
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT_S) as resp:
            return 200 <= resp.status < 300
    except Exception:  # noqa: BLE001 -- any failure means "not ready"
        return False


def post_chat(body, timeout):
    """POST one chat-completions body to the forge endpoint (blocking)."""
    req = urllib.request.Request(
        FORGE_URL.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers=_vllm_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def convert_brep(brep_bytes):
    """BREP -> (stl_bytes, step_bytes) inside the CPU web container.

    Reads ONLY the sandbox's BREP (never executes visitor or model code).
    STL uses 0.1 mm tolerance.
    """
    import tempfile

    from cadquery import exporters, importers

    with tempfile.NamedTemporaryFile(suffix=".brep", delete=False) as f:
        f.write(bytes(brep_bytes))
        brep_path = f.name
    stl_path = brep_path + ".stl"
    step_path = brep_path + ".step"
    try:
        shape = importers.importShape(
            importers.ImportTypes.BREP, brep_path).val()
        exporters.export(shape, stl_path, exportType="STL", tolerance=0.1)
        exporters.export(shape, step_path, exportType="STEP")
        with open(stl_path, "rb") as f:
            stl_bytes = f.read()
        with open(step_path, "rb") as f:
            step_bytes = f.read()
        return stl_bytes, step_bytes
    finally:
        for path in (brep_path, stl_path, step_path):
            try:
                os.unlink(path)
            except OSError:
                pass


def _reconcile_spend(mny):
    """Mirror today's Dict spend into the in-process ledger (restarts)."""
    try:
        today = budget_mod.day_key()
        kept = spend_dict.get(today) or 0.0
        if kept > mny.spent_today():
            mny._spend[today] = float(kept)  # noqa: SLF001 -- same process
    except Exception:  # noqa: BLE001 -- Dict is best-effort persistence
        pass


def _mirror_spend(mny):
    try:
        spend_dict[budget_mod.day_key()] = mny.spent_today()
    except Exception:  # noqa: BLE001 -- best effort only
        pass


def _request_ip(request):
    """Client IP: connection peer fallback, LAST X-Forwarded-For hop first."""
    peer = ""
    try:
        peer = (request.client.host if request.client else "") or ""
    except Exception:  # noqa: BLE001
        peer = ""
    return limits_mod.client_ip(
        request.headers.get("x-forwarded-for", ""), peer)


def _fire_warmup(mny, ip):
    """Fire one non-blocking warm-up request (throttled, charged on fire)."""
    body = {"model": FORGE_MODEL,
            "messages": [{"role": "user",
                          "content": "Reply with exactly the word DONE."}],
            "max_tokens": 16, "temperature": 0.0}
    mny.note_warmup(ip)
    _mirror_spend(mny)
    try:
        post_chat(body, timeout=30)
    except Exception:  # noqa: BLE001 -- warm-ups are best effort
        pass


@app.function(image=_web_image(), cpu=1, min_containers=0, max_containers=1,
              timeout=int(WEB_TIMEOUT_S),
              secrets=[modal.Secret.from_name("forge-glimmer")])
@modal.asgi_app()
def web():
    """The FastAPI app: static page + status/build/lead/files APIs."""
    import fastapi
    from fastapi.responses import JSONResponse, Response
    from fastapi.staticfiles import StaticFiles

    sys.path.insert(0, REMOTE_PKG)
    for _p in (REMOTE_PKG + "/experiments/final",
               REMOTE_PKG + "/experiments/first-test"):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    import cloud_cq  # noqa: E402 -- locked sandbox runner only

    api = fastapi.FastAPI()
    api.mount("/", StaticFiles(directory=REMOTE_PKG + "/app/web",
                               html=True), name="web")

    # One process (max_containers=1): counters live here behind this lock;
    # the Modal Dicts are only persistence across restarts.
    rates = limits_mod.RateState()
    money = budget_mod.Budget()
    state_lock = asyncio.Lock()

    @api.get("/api/status")
    async def status(request: fastapi.Request):
        ip = _request_ip(request)
        async with state_lock:
            _reconcile_spend(money)
            if money.is_capped():
                return {"state": "paused", "message": PAUSED_MESSAGE}
        ok = await asyncio.to_thread(probe_model)
        async with state_lock:
            state, message = money.status(ok)
            if state == "waking" and money.may_warmup(ip):
                threading.Thread(target=_fire_warmup, args=(money, ip),
                                 daemon=True).start()
                # The charge lands in note_warmup when the thread runs;
                # mirror again on the next request (single process).
            return {"state": state, "message": message}

    @api.post("/api/build")
    async def build(request: fastapi.Request):
        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            payload = {}
        job = (payload or {}).get("job", "")
        denied = limits_mod.check_job(job)
        if denied:
            return JSONResponse({"message": denied[1]}, status_code=denied[0])
        ip = _request_ip(request)
        async with state_lock:
            _reconcile_spend(money)
            if money.is_capped():
                return JSONResponse({"message": PAUSED_MESSAGE},
                                    status_code=429)
            denied = rates.check_ip(ip)
            if denied:
                return JSONResponse({"message": denied[1]},
                                    status_code=denied[0])
            denied = rates.try_acquire()
            if denied:
                return JSONResponse({"message": denied[1]},
                                    status_code=denied[0])
            rates.note_build(ip)
        run_id = limits_mod.new_run_id()

        def _model_call(messages, body):
            t0 = time.monotonic()
            data = post_chat(body, timeout=600)
            gpu_s = time.monotonic() - t0  # GPU-seconds estimate: latency
            content = (((data.get("choices") or [{}])[0].get("message")
                         or {}).get("content")) or ""
            return content, gpu_s

        final_box = {}  # the last built answer's BREP (never executed here)

        def _box_run(code):
            out = cloud_cq.run_answer_in_box(code)
            if out and out.get("brep_bytes") is not None:
                final_box["code"] = code
                final_box["brep"] = out["brep_bytes"]
            return out

        _END = object()

        async def _aiter():
            gen = loop_mod.run_job(job, _model_call, _box_run,
                                   model=FORGE_MODEL)
            while True:
                try:
                    ev = await asyncio.to_thread(next, gen, _END)
                except Exception as e:  # noqa: BLE001 -- never stack-trace
                    yield stream_mod.error_event("Build failed: %s" % e)
                    return
                if ev is _END:
                    return
                if ev["step"] == "done" and ev.get("code"):
                    try:
                        _store_run_files(
                            run_id, final_box.get("code", ev["code"]),
                            final_box.get("brep"))
                    except Exception:  # noqa: BLE001 -- files optional
                        pass
                    try:
                        money.charge_build(ev.get("gpu_seconds", 0))
                        _mirror_spend(money)
                    except Exception:  # noqa: BLE001
                        pass
                    ev = dict(ev, stl_url="/files/%s.stl" % run_id,
                              step_url="/files/%s.step" % run_id,
                              code_url="/files/%s.py" % run_id)
                yield ev

        async def _bounded():
            # First event goes out immediately; heartbeat at least every
            # HEARTBEAT_S; whole build limited to BUILD_LIMIT_S.
            try:
                async with asyncio.timeout(BUILD_LIMIT_S):
                    async for chunk in stream_mod.with_heartbeat(_aiter()):
                        yield chunk
            except TimeoutError:
                yield stream_mod.encode_event(
                    stream_mod.error_event(TIMEOUT_MESSAGE))
            finally:
                rates.release()

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
        denied = limits_mod.check_lead(tool, email)
        if denied:
            return JSONResponse({"message": denied[1]}, status_code=denied[0])
        record = limits_mod.lead_record(tool, email)  # never printed/logged
        try:
            seen = list(leads_dict.get("leads") or [])
        except Exception:  # noqa: BLE001
            seen = []
        seen.append(record)
        try:
            leads_dict["leads"] = seen
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True}

    @api.get("/files/{filename}")
    async def files(filename: str):
        name, dot, ext = filename.rpartition(".")
        if not dot or ext not in ("stl", "step", "py") or not name:
            return JSONResponse({"message": "Not found"}, status_code=404)
        try:
            blob = files_dict.get("%s.%s" % (name, ext))
        except Exception:  # noqa: BLE001
            blob = None
        if not blob or time.time() - blob.get("ts", 0) > FILE_TTL_S:
            try:
                del files_dict["%s.%s" % (name, ext)]
            except Exception:  # noqa: BLE001
                pass
            return JSONResponse({"message": "Not found"}, status_code=404)
        ctype = {"stl": "model/stl", "step": "application/step",
                 "py": "text/plain"}[ext]
        data = blob["bytes"]
        if isinstance(data, str):
            data = data.encode("utf-8")
        return Response(bytes(data), media_type=ctype)

    return api


def _store_run_files(run_id, code, brep_bytes):
    """Convert the sandbox BREP to STL/STEP and keep all three for 24 h.

    The web container only reads BREP bytes; model/visitor code is never
    executed here.
    """
    files_dict["%s.py" % run_id] = {
        "bytes": (code or "").encode("utf-8"), "ts": time.time()}
    if not brep_bytes:
        return
    stl_bytes, step_bytes = convert_brep(brep_bytes)
    files_dict["%s.stl" % run_id] = {"bytes": bytes(stl_bytes),
                                     "ts": time.time()}
    files_dict["%s.step" % run_id] = {"bytes": bytes(step_bytes),
                                      "ts": time.time()}
