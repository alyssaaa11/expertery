"""Shared constants for the expertery package.

Price fallbacks mirror experiments/factory/teacher.py (COST_IN_PER_M,
COST_CACHED_PER_M, COST_OUT_PER_M, IN_FLIGHT_COST). cloud.py prefers the
teacher's live constants when that module is importable and uses these
only when it is not.
"""

import os

TOOL = "cadquery"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".expertery")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

READER_KEY_ENV = "EXPERTERY_READER_KEY"
READER_KEY_FALLBACK_ENV = "BASETEN_API_KEY"
READER_URL_ENV = "EXPERTERY_READER_URL"
READER_MODEL_ENV = "EXPERTERY_READER_MODEL"

# Fallback model-call prices ($/M tokens), matching teacher.py.
COST_IN_PER_M = 1.25
COST_CACHED_PER_M = 0.15
COST_OUT_PER_M = 4.25
# Fallback reserve for one not-yet-made call, matching teacher.py.
IN_FLIGHT_COST = 0.075

TOL_VERDICT = 0.002  # 0.2%: the grading yardstick, as in cloud_cq.


def estimate_cost(usage, cost_in=COST_IN_PER_M,
                  cost_cached=COST_CACHED_PER_M,
                  cost_out=COST_OUT_PER_M):
    """Dollar cost of one model call from its usage dict."""
    usage = usage or {}
    try:
        prompt = float(usage.get("prompt_tokens", 0) or 0)
    except (TypeError, ValueError):
        prompt = 0.0
    try:
        completion = float(usage.get("completion_tokens", 0) or 0)
    except (TypeError, ValueError):
        completion = 0.0
    try:
        details = usage.get("prompt_tokens_details") or {}
        cached = float(details.get("cached_tokens", 0) or 0)
    except (TypeError, ValueError):
        cached = 0.0
    try:
        cached = max(cached, float(usage.get("cached_tokens", 0) or 0))
    except (TypeError, ValueError):
        pass
    uncached = max(0.0, prompt - cached)
    return (uncached * cost_in + cached * cost_cached
            + completion * cost_out) / 1e6
