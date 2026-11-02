"""Visitor protection limits (pure part of verifier S3).

The Modal web function keeps ONE process (``max_containers=1``) and holds
these counters in that process behind an asyncio lock (Modal Dict has no
atomic counter; the Dict is only persistence across restarts). This module
holds the pure rules so tests can drive them with a fake clock; the lock
itself lives in ``deploy/modal_web.py``.
"""

import threading
import time
import uuid

from . import config


def new_run_id():
    """A run id: 32 hex chars (uuid4)."""
    return uuid.uuid4().hex


def client_ip(x_forwarded_for, peer):
    """The client IP for limits.

    Takes the LAST hop added by Modal's proxy, never the first
    X-Forwarded-For entry (which a visitor can spoof). Falls back to the
    connection peer when no forwarding header is present.
    """
    hops = [h.strip() for h in str(x_forwarded_for or "").split(",")
            if h.strip()]
    if hops:
        return hops[-1]
    return peer or ""


def check_job(job_text):
    """None when the job may run, else (413, message)."""
    if job_text is None:
        return 413, "Send a job description first"
    if len(job_text) > config.MAX_JOB_CHARS:
        return (413, "That job is %d characters; the limit is %d"
                % (len(job_text), config.MAX_JOB_CHARS))
    if not str(job_text).strip():
        return 413, "Send a job description first"
    return None


def check_lead(tool, email):
    """None when the lead may be stored, else (400, message).

    Never logs or prints the email; the caller stores only the record.
    """
    tool = "" if tool is None else str(tool)
    email = "" if email is None else str(email)
    if len(email) > config.LEAD_EMAIL_MAX:
        return 400, "That email is too long"
    if len(tool) > config.LEAD_TOOL_MAX:
        return 400, "That answer is too long"
    if not email.strip() or "@" not in email:
        return 400, "Send a valid email"
    return None


def lead_record(tool, email, ts=None):
    """The stored lead dict (no logging here; the caller must not print it)."""
    if ts is None:
        ts = time.time()
    return {"tool": str(tool or ""), "email": str(email or ""),
            "ts": ts}


class RateState:
    """Per-IP hourly builds and global concurrency (one web process).

    The web layer releases a slot from a worker thread (verifier W4), so
    the counter is lock-guarded.
    """

    def __init__(self, now=None):
        self._now = now or time.time
        self._mu = threading.Lock()
        self._ip_hits = {}  # ip -> [unix seconds of accepted builds]
        self._active = 0

    def _prune(self, ip, t):
        recent = [h for h in self._ip_hits.get(ip, []) if t - h < 3600.0]
        self._ip_hits[ip] = recent
        return recent

    def check_ip(self, ip):
        """None when this IP may start a build, else (429, message)."""
        with self._mu:
            recent = self._prune(ip, self._now())
            if len(recent) >= config.MAX_BUILDS_PER_IP_HOUR:
                return 429, config.RATE_MESSAGE
            return None

    def note_build(self, ip):
        """Record an accepted build for the IP hourly count."""
        with self._mu:
            self._ip_hits.setdefault(ip, []).append(self._now())

    def try_acquire(self):
        """A concurrency slot, or (429, message) when full."""
        with self._mu:
            if self._active >= config.MAX_CONCURRENT_BUILDS:
                return 429, config.BUSY_MESSAGE
            self._active += 1
            return None

    def release(self):
        """Give a concurrency slot back (never below zero)."""
        with self._mu:
            self._active = max(0, self._active - 1)

    @property
    def active(self):
        """Currently held concurrency slots (for tests)."""
        with self._mu:
            return self._active


class TryState:
    """Per-IP successful live-build STARTS (one web process; P2c).

    At most MAX_LIVE_TRIES_PER_VISITOR starts per visitor IP (default 1:
    one free live try); further starts are rejected with 429. Counts live
    behind the web layer's lock; the ``homegrown-tries`` Modal Dict is
    only persistence across restarts (the web layer restores each IP's
    persisted count into this copy before checking).
    """

    def __init__(self):
        self._mu = threading.Lock()
        self._tries = {}  # ip -> successful build starts

    def count(self, ip):
        """Successful live-build starts recorded for this IP."""
        with self._mu:
            return self._tries.get(ip, 0)

    def restore(self, ip, n):
        """Merge a persisted count in, keeping the larger value."""
        try:
            n = int(n)
        except (TypeError, ValueError):
            return
        if n <= 0:
            return
        with self._mu:
            if n > self._tries.get(ip, 0):
                self._tries[ip] = n

    def check(self, ip):
        """None when this IP may start a live build, else (429, message)."""
        with self._mu:
            if self._tries.get(ip, 0) >= \
                    config.MAX_LIVE_TRIES_PER_VISITOR:
                return 429, config.TRIED_MESSAGE
            return None

    def note(self, ip):
        """Record a successful live-build start for this IP."""
        with self._mu:
            self._tries[ip] = self._tries.get(ip, 0) + 1


class LeadRate:
    """Per-IP lead posts (one web process; verifier privacy fix).

    At most MAX_LEADS_PER_IP_HOUR posts per IP per hour; the 6th (by
    default) is rejected with 429. Every POST counts, including delete
    requests and invalid ones.
    """

    def __init__(self, now=None, limit=None, window_s=3600.0):
        self._now = now or time.time
        self._limit = config.MAX_LEADS_PER_IP_HOUR \
            if limit is None else limit
        self._window = window_s
        self._hits = {}  # ip -> [unix seconds of lead posts]

    def check(self, ip):
        """None when this IP may post a lead, else (429, message)."""
        t = self._now()
        recent = [h for h in self._hits.get(ip, [])
                  if t - h < self._window]
        self._hits[ip] = recent
        if len(recent) >= self._limit:
            return 429, "Please wait a bit before sending again"
        return None

    def note(self, ip):
        """Record a lead post for the IP hourly count."""
        self._hits.setdefault(ip, []).append(self._now())
