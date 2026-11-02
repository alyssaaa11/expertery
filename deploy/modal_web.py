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

The FastAPI app itself is built by ``app.backend.webapp.make_app`` (pure,
testable without Modal); ``web()`` below only builds the real deps
(model/box/stores/clocks) and calls it. The static page is mounted LAST
inside the factory so it never swallows /api/* and /files (verifier
blocker 2026-11-02; Claude order fix, kept).
"""

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

# ------------------------------------------------------------- config block
# All limits in one place, read from env with the spec defaults. These
# mirror app/backend/config.py exactly (app/tests/test_p2_config.py
# asserts they stay equal); the backend modules read the same env.
MAX_JOB_CHARS = int(os.environ.get("MAX_JOB_CHARS", "600"))
MAX_BUILDS_PER_IP_HOUR = int(os.environ.get("MAX_BUILDS_PER_IP_HOUR", "4"))
MAX_CONCURRENT_BUILDS = int(os.environ.get("MAX_CONCURRENT_BUILDS", "2"))
MAX_LEADS_PER_IP_HOUR = int(os.environ.get("MAX_LEADS_PER_IP_HOUR", "5"))
DAILY_CAP_USD = float(os.environ.get("DAILY_CAP_USD", "15"))
TOTAL_CAP_USD = float(os.environ.get("TOTAL_CAP_USD", "15"))
EST_TRY_USD = float(os.environ.get("EST_TRY_USD", "0.30"))
MAX_LIVE_TRIES_PER_VISITOR = int(os.environ.get("MAX_LIVE_TRIES_PER_VISITOR", "1"))
GPU_USD_PER_S = float(os.environ.get("GPU_USD_PER_S", "0.000694"))
SANDBOX_USD_PER_BUILD = float(os.environ.get("SANDBOX_USD_PER_BUILD", "0.002"))
IDLE_TAIL_USD = float(os.environ.get("IDLE_TAIL_USD", "0.21"))
WAKE_USD = float(os.environ.get("WAKE_USD", "0.45"))
SCALE_DOWN_S = float(os.environ.get("SCALE_DOWN_S", "300"))
BUILD_LIMIT_S = float(os.environ.get("BUILD_LIMIT_S", "600"))
WEB_TIMEOUT_S = float(os.environ.get("WEB_TIMEOUT_S", "720"))
HEARTBEAT_S = 15.0
FILE_TTL_S = 24 * 3600.0
LEAD_EMAIL_MAX = 200
LEAD_TOOL_MAX = 300
# REASONING_STRENGTH ("high"|"xhigh", default "xhigh") is read from the
# same env by app/backend/loop.py (config.reasoning_strength); the body
# sent equals runner.build_bx_body at the default.

FORGE_URL = os.environ.get("FORGE_URL", "")
FORGE_MODEL = "forge"

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
    # Bake the deploy-time settings INTO the container (Claude fix,
    # disclosed): Modal re-imports this module inside the container, where
    # the deploy shell's env is not set (same trap as modal_forge.py).
    baked = {k: os.environ[k] for k in _BAKED_ENV if os.environ.get(k)}
    if baked:
        img = img.env(baked)
    for rel in image_files_mod.WEB_IMAGE_FILES:
        img = img.add_local_file(rel, "/pkg/" + rel)
    return img


_BAKED_ENV = ("FORGE_URL", "REASONING_STRENGTH", "DAILY_CAP_USD",
              "TOTAL_CAP_USD", "EST_TRY_USD", "MAX_LIVE_TRIES_PER_VISITOR",
              "MAX_JOB_CHARS", "MAX_BUILDS_PER_IP_HOUR",
              "MAX_CONCURRENT_BUILDS", "MAX_LEADS_PER_IP_HOUR",
              "GPU_USD_PER_S", "SANDBOX_USD_PER_BUILD", "IDLE_TAIL_USD",
              "WAKE_USD", "SCALE_DOWN_S")


leads_dict = modal.Dict.from_name("homegrown-leads", create_if_missing=True)
files_dict = modal.Dict.from_name("homegrown-files", create_if_missing=True)
spend_dict = modal.Dict.from_name("homegrown-spend", create_if_missing=True)
tries_dict = modal.Dict.from_name("homegrown-tries", create_if_missing=True)

REMOTE_PKG = "/pkg"


# ------------------------------------------------------------- HTTP helpers
def _vllm_headers():
    return {"Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "")}


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
    """Mirror EVERY Dict day bucket into the in-process ledger (restarts).

    The total cap sums all days, so a restart must reload all of them,
    not just today's bucket. Falls back to today's bucket only when the
    Dict cannot be listed.
    """
    try:
        mny.restore(dict(list(spend_dict.items())))
        return
    except Exception:  # noqa: BLE001 -- try the today-only fallback
        pass
    try:
        today = budget_mod.day_key()
        kept = spend_dict.get(today) or 0.0
        mny.restore({today: kept})
    except Exception:  # noqa: BLE001 -- Dict is best-effort persistence
        pass


def _mirror_spend(mny):
    try:
        for key, value in mny.snapshot().items():
            spend_dict[key] = value
    except Exception:  # noqa: BLE001 -- best effort only
        pass


def _container_count():
    """Containers up for the trained serve function, without an input.

    Uses ``get_current_stats`` (no request to the model, so a scaled-down
    model is NOT booted by asking). ``None`` means unknown; the caller
    then relies on the in-process warm state only.
    """
    try:
        fn = modal.Function.from_name("forge-trained", "serve")
        stats = fn.get_current_stats()
    except Exception:  # noqa: BLE001 -- best effort only
        return None
    if not stats:
        return 0
    for key in ("num_active_containers", "active_containers",
                "num_containers", "containers"):
        try:
            value = stats.get(key) if isinstance(stats, dict) \
                else getattr(stats, key, None)
        except Exception:  # noqa: BLE001
            value = None
        if isinstance(value, (int, float)):
            return int(value)
    return None


@app.function(image=_web_image(), cpu=1, min_containers=0, max_containers=1,
              timeout=int(WEB_TIMEOUT_S),
              secrets=[modal.Secret.from_name("forge-glimmer")])
@modal.asgi_app()
def web():
    """Build the real deps and return the shared FastAPI app."""
    # Startup check + effective config log, no secrets (verifier, Claude fix).
    if not FORGE_URL:
        raise RuntimeError("FORGE_URL is empty in the container; deploy with "
                           "FORGE_URL set (it is baked into the image env)")
    print("homegrown-web config:", {k: os.environ.get(k, "(default)")
                                    for k in _BAKED_ENV})
    sys.path.insert(0, REMOTE_PKG)
    for _p in (REMOTE_PKG + "/experiments/final",
               REMOTE_PKG + "/experiments/first-test"):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    import cloud_cq  # noqa: E402 -- locked sandbox runner only

    from app.backend import webapp as webapp_mod  # noqa: E402

    # One process (max_containers=1): counters live here; the Modal Dicts
    # are only persistence across restarts.
    money = budget_mod.Budget()
    rates = limits_mod.RateState()
    lead_rates = limits_mod.LeadRate()

    def _model(messages, body, timeout):
        t0 = time.monotonic()
        data = post_chat(body, timeout=timeout)
        elapsed = time.monotonic() - t0  # model seconds estimate: latency
        content = (((data.get("choices") or [{}])[0].get("message")
                     or {}).get("content")) or ""
        return content, elapsed

    def _box(code):
        return cloud_cq.run_answer_in_box(code)

    def _warmer(_ip):
        body = {"model": FORGE_MODEL,
                "messages": [{"role": "user", "content":
                              "Reply with exactly the word DONE."}],
                "max_tokens": 16, "temperature": 0.0}

        def _send():
            try:
                post_chat(body, timeout=30)
            except Exception:  # noqa: BLE001 -- warm-ups are best effort
                pass

        threading.Thread(target=_send, daemon=True).start()

    return webapp_mod.make_app({
        "model": _model,
        "box": _box,
        "convert": convert_brep,
        "warmer": _warmer,
        "containers": _container_count,
        "leads": leads_dict,
        "files": files_dict,
        "tries": tries_dict,
        "money": money,
        "rates": rates,
        "lead_rates": lead_rates,
        "build_limit_s": BUILD_LIMIT_S,
        "file_ttl_s": FILE_TTL_S,
        "web_dir": REMOTE_PKG + "/app/web",
        "mirror": _mirror_spend,
        "reconcile": _reconcile_spend,
    })
