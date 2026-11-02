"""Single config block for the Homegrown web backend (verifier S3/S4/S5/F1).

Every limit lives here, read from the environment with the spec defaults.
`deploy/modal_web.py` imports these names; tests assert the defaults.
"""

import os


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name, default):
    try:
        return int(float(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return int(default)


def _env_str(name, default):
    value = os.environ.get(name, default)
    return str(value) if value is not None else default


# --- visitor input -------------------------------------------------------
MAX_JOB_CHARS = _env_int("MAX_JOB_CHARS", 600)  # longer -> HTTP 413
LEAD_EMAIL_MAX = 200  # longer emails are rejected
LEAD_TOOL_MAX = 300  # longer tool answers are rejected
OUTPUT_CAP = 4000  # chars of model output / errors shown to visitors

# --- rates ---------------------------------------------------------------
MAX_BUILDS_PER_IP_HOUR = _env_int("MAX_BUILDS_PER_IP_HOUR", 4)  # 5th -> 429
MAX_CONCURRENT_BUILDS = _env_int("MAX_CONCURRENT_BUILDS", 2)  # 3rd -> 429

# --- money ---------------------------------------------------------------
DAILY_CAP_USD = _env_float("DAILY_CAP_USD", 20)
GPU_USD_PER_S = _env_float("GPU_USD_PER_S", 0.000694)  # A100-80GB ~ $2.50/h
SANDBOX_USD_PER_BUILD = _env_float("SANDBOX_USD_PER_BUILD", 0.002)
IDLE_TAIL_USD = _env_float("IDLE_TAIL_USD", 0.21)  # 300 s scale-down, once/burst
WAKE_USD = _env_float("WAKE_USD", 0.45)  # each actually-fired warm-up
BURST_GAP_S = 300.0  # no build for this long ends a burst
SCALE_DOWN_S = 300.0  # model stays warm this long after a real response
WARMUP_GLOBAL_S = 600.0  # at most one warm-up per 10 min globally
WARMUP_IP_S = 3600.0  # at most one warm-up per hour per IP
MAX_LEADS_PER_IP_HOUR = _env_int("MAX_LEADS_PER_IP_HOUR", 5)  # 6th -> 429

# --- model ---------------------------------------------------------------
# ONE reasoning-strength setting (verifier F1). "xhigh" is what the 92%
# second look used; "high" is what the model trained on. A small check on
# factory practice jobs decides before deploy.
REASONING_CHOICES = ("high", "xhigh")


def reasoning_strength():
    """The configured reasoning strength (env REASONING_STRENGTH)."""
    value = _env_str("REASONING_STRENGTH", "xhigh")
    if value not in REASONING_CHOICES:
        raise ValueError(
            "REASONING_STRENGTH must be one of %r, got %r"
            % (REASONING_CHOICES, value)
        )
    return value


# --- time ----------------------------------------------------------------
BUILD_LIMIT_S = _env_float("BUILD_LIMIT_S", 600)  # whole-build wall clock
WEB_TIMEOUT_S = _env_float("WEB_TIMEOUT_S", 720)  # Modal fn must stay > limit
HEARTBEAT_S = 15.0  # SSE heartbeat comment at least this often
PROBE_TIMEOUT_S = 3.0  # GET {FORGE_URL}/v1/models timeout
FILE_TTL_S = 24 * 3600.0  # run files kept for 24 h

BUILD_TIMEOUT_MESSAGE = "This part took too long; try a simpler one"
PAUSED_MESSAGE = "Demo paused: today's budget is used up. Here is a recorded run instead."
BUSY_MESSAGE = "Busy, try again in a minute"
RATE_MESSAGE = "Please wait a bit before building again"
