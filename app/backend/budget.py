"""Daily money budget and warm-up throttle (pure part of verifier S4).

Cost per build = model GPU seconds x GPU_USD_PER_S + SANDBOX_USD_PER_BUILD,
plus the idle tail after the last build of a burst (IDLE_TAIL_USD, charged
once per burst: a build that starts a new burst -- no build in the last
BURST_GAP_S -- carries it) and WAKE_USD each time a warm-up is actually
fired. Warm-ups are throttled: at most one per 10 minutes globally and one
per hour per IP. Spend is kept keyed by UTC date; at or over the cap the
API reports paused and refuses builds.

Warmth is learned WITHOUT any request to the model (verifier W2): the last
real model response sets ``warm_until`` = response time + SCALE_DOWN_S
(the 300 s scale-down). A build that starts while not warm is a cold start
and is charged WAKE_USD once. The web layer may additionally treat a
positive container count (Modal ``get_current_stats``, best effort) as warm.

Tests drive this with a fake clock; ``deploy/modal_web.py`` mirrors the
numbers into a Modal Dict for persistence across restarts. The web layer
calls mutating methods from a worker thread, so they are lock-guarded.

Round P2c adds an ALL-TIME cap (``TOTAL_CAP_USD``, default $15): total
spend is the sum over every day bucket, and at or over the cap the API
reports paused and refuses builds. The daily cap stays as an extra guard.
"""

import datetime
import math
import threading
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
        self._mu = threading.Lock()
        self._spend = {}  # day_key -> dollars
        self._last_build = None  # unix seconds of the last charged build
        self._last_warmup = None  # unix seconds of the last fired warm-up
        self._ip_warmups = {}  # ip -> unix seconds of its last warm-up
        self._warm_until = None  # wall seconds; warm while now < this

    # -- spend ---------------------------------------------------------
    def spent_today(self):
        """Dollars charged in the current UTC day."""
        with self._mu:
            return self._spend.get(day_key(self._now()), 0.0)

    def total_spent(self):
        """Dollars charged over ALL days (the P2c total cap base)."""
        with self._mu:
            return sum(self._spend.values())

    def tries_left(self):
        """Rough free live tries left under the total cap (P2c counter).

        ``max(0, floor((TOTAL_CAP_USD - total) / EST_TRY_USD))``; always
        an int, never exact -- the page shows it with an "about" mark.
        """
        with self._mu:
            total = sum(self._spend.values())
        try:
            est = float(config.EST_TRY_USD)
        except (TypeError, ValueError):
            est = 0.0
        if est <= 0:
            return 0
        return max(0, math.floor((config.TOTAL_CAP_USD - total) / est))

    def snapshot(self):
        """A copy of the day -> dollars ledger (for Dict persistence)."""
        with self._mu:
            return dict(self._spend)

    def restore(self, spend):
        """Merge persisted day buckets in, keeping the larger per day."""
        try:
            items = dict(spend).items()
        except (TypeError, ValueError, AttributeError):
            return
        with self._mu:
            for key, value in items:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                if value > self._spend.get(key, 0.0):
                    self._spend[key] = value

    def is_capped(self):
        """True once the daily OR the all-time cap is reached."""
        return self.spent_today() >= config.DAILY_CAP_USD or \
            self.total_spent() >= config.TOTAL_CAP_USD

    def _add(self, dollars):
        key = day_key(self._now())
        self._spend[key] = self._spend.get(key, 0.0) + dollars
        return dollars

    def charge_build(self, gpu_seconds):
        """Charge one build; returns the dollars added.

        GPU seconds plus one sandbox fee, plus one idle tail when this
        build starts a new burst.
        """
        with self._mu:
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

    # -- warmth (no model request; verifier W2) ------------------------
    def is_warm(self):
        """True while the model is known warm from a recent response."""
        with self._mu:
            return self._warm_until is not None and \
                self._now() < self._warm_until

    def note_model_response(self):
        """Record a real model response: warm for one scale-down window."""
        with self._mu:
            self._warm_until = self._now() + config.SCALE_DOWN_S

    def note_cold_build(self):
        """Charge WAKE_USD once for a build that starts while not warm."""
        with self._mu:
            return self._add(config.WAKE_USD)

    # -- warm-ups ------------------------------------------------------
    def may_warmup(self, ip):
        """True when a warm-up for this IP may fire now (throttled)."""
        with self._mu:
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
        with self._mu:
            t = self._now()
            self._last_warmup = t
            self._ip_warmups[ip] = t
            return self._add(config.WAKE_USD)

    # -- status --------------------------------------------------------
    def warm_status(self, container_warm=False):
        """(state, message) with NO side effects and NO model request.

        Ready when a recent real response (or a positive container count
        learned without sending an input) says the model is up; otherwise
        waking. The caller decides (via may_warmup/note_warmup) whether to
        actually fire a throttled warm-up request.
        """
        if self.is_capped():
            return "paused", config.PAUSED_MESSAGE
        if self.is_warm() or container_warm:
            return "ready", "The model is ready"
        return ("waking",
                "Waking up the model (this takes a few minutes). "
                "Here is a recorded run meanwhile.")

    def status(self, probe_ok):
        """(state, message) with NO side effects.

        Kept for compatibility: a truthy probe is treated like a warm
        signal. The web layer no longer probes; it uses warm_status().
        """
        return self.warm_status(container_warm=bool(probe_ok))
