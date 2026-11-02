"""Daily money budget and warm-up throttle (pure part of verifier S4).

Cost per build = model GPU seconds x GPU_USD_PER_S + SANDBOX_USD_PER_BUILD,
plus the idle tail after the last build of a burst (IDLE_TAIL_USD, charged
once per burst: a build that starts a new burst -- no build in the last
BURST_GAP_S -- carries it) and WAKE_USD each time a warm-up is actually
fired. Warm-ups are throttled: at most one per 10 minutes globally and one
per hour per IP. Spend is kept keyed by UTC date; at or over the cap the
API reports paused and refuses builds.

Tests drive this with a fake clock; ``deploy/modal_web.py`` mirrors the
numbers into a Modal Dict for persistence across restarts.
"""

import datetime
import time

from . import config


def day_key(now=None):
    """UTC date string for today's spend bucket."""
    t = time.time() if now is None else now
    return datetime.datetime.fromtimestamp(
        t, tz=datetime.timezone.utc).strftime("%Y-%m-%d")


class Budget:
    """Spend ledger + warm-up throttle (one web process)."""

    def __init__(self, now=None):
        self._now = now or time.time
        self._spend = {}  # day_key -> dollars
        self._last_build = None  # unix seconds of the last charged build
        self._last_warmup = None  # unix seconds of the last fired warm-up
        self._ip_warmups = {}  # ip -> unix seconds of its last warm-up

    # -- spend ---------------------------------------------------------
    def spent_today(self):
        """Dollars charged in the current UTC day."""
        return self._spend.get(day_key(self._now()), 0.0)

    def is_capped(self):
        """True once today's spend is at or over the daily cap."""
        return self.spent_today() >= config.DAILY_CAP_USD

    def _add(self, dollars):
        key = day_key(self._now())
        self._spend[key] = self._spend.get(key, 0.0) + dollars
        return dollars

    def charge_build(self, gpu_seconds):
        """Charge one build; returns the dollars added.

        GPU seconds plus one sandbox fee, plus one idle tail when this
        build starts a new burst.
        """
        t = self._now()
        try:
            gpu = float(gpu_seconds or 0.0)
        except (TypeError, ValueError):
            gpu = 0.0
        cost = gpu * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD
        if self._last_build is None or \
                t - self._last_build > config.BURST_GAP_S:
            cost += config.IDLE_TAIL_USD  # one tail per burst
        self._last_build = t
        return self._add(cost)

    # -- warm-ups ------------------------------------------------------
    def may_warmup(self, ip):
        """True when a warm-up for this IP may fire now (throttled)."""
        t = self._now()
        if self._last_warmup is not None and \
                t - self._last_warmup < config.WARMUP_GLOBAL_S:
            return False
        last = self._ip_warmups.get(ip)
        if last is not None and t - last < config.WARMUP_IP_S:
            return False
        return True

    def note_warmup(self, ip):
        """Record an actually-fired warm-up and charge WAKE_USD."""
        t = self._now()
        self._last_warmup = t
        self._ip_warmups[ip] = t
        return self._add(config.WAKE_USD)

    # -- status --------------------------------------------------------
    def status(self, probe_ok):
        """(state, message) with NO side effects.

        Never wakes the model by itself: when the state is "waking" the
        caller decides (via may_warmup/note_warmup) whether to actually
        fire a warm-up request.
        """
        if self.is_capped():
            return "paused", config.PAUSED_MESSAGE
        if probe_ok:
            return "ready", "The model is ready"
        return ("waking",
                "Waking up the model (this takes a few minutes). "
                "Here is a recorded run meanwhile.")
