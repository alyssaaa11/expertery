"""Server-Sent Events helpers (verifier S5).

The first data event goes out immediately and a ": heartbeat" comment goes
out at least every HEARTBEAT_S seconds so proxies do not cut the stream.
``deploy/modal_web.py`` drives ``with_heartbeat`` from asyncio; the pump
task means a slow model never blocks the heartbeat.
"""

import asyncio
import json

from . import config

HEARTBEAT_LINE = ": heartbeat"


def encode_event(payload):
    """One SSE data frame for a JSON event dict."""
    return "data: %s\n\n" % json.dumps(payload, separators=(",", ":"))


def encode_heartbeat():
    """One SSE comment frame (keeps the stream alive)."""
    return "%s\n\n" % HEARTBEAT_LINE


def error_event(detail):
    """An SSE event payload for a failed build."""
    text = str(detail or "Something went wrong building that part.")
    return {"step": "error", "detail": text[:config.OUTPUT_CAP]}


async def with_heartbeat(aiter, interval=None):
    """Yield SSE strings for an async event iterator, injecting heartbeats.

    Events are pulled by a background task into a queue, so waiting for
    the next event never cancels the producer: whenever `interval`
    seconds pass without an event, a heartbeat comment is yielded.
    """
    gap = config.HEARTBEAT_S if interval is None else interval
    queue = asyncio.Queue()
    finished = object()

    async def _pump():
        try:
            async for event in aiter:
                await queue.put(event)
        finally:
            await queue.put(finished)

    task = asyncio.ensure_future(_pump())
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=gap)
            except asyncio.TimeoutError:
                yield encode_heartbeat()
                continue
            if item is finished:
                return
            yield encode_event(item)
    finally:
        if not task.done():
            task.cancel()
