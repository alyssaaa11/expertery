"""SSE framing, heartbeat during a slow model, and the web secret grep."""

import asyncio
import json
from pathlib import Path

from app.backend import config, stream

WEB = Path(__file__).resolve().parent.parent / "web"


def test_encode_event_is_one_sse_data_frame():
    frame = stream.encode_event({"step": "write", "round": 1})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    assert "\n\n" not in frame.strip()
    assert json.loads(frame[len("data: "):]) == {"step": "write",
                                                 "round": 1}


def test_heartbeat_is_a_comment_frame():
    frame = stream.encode_heartbeat()
    assert frame.startswith(":")
    assert frame.endswith("\n\n")
    assert "data:" not in frame


def test_error_event_shape_and_cap():
    ev = stream.error_event("x" * 5000)
    assert ev["step"] == "error"
    assert len(ev["detail"]) == config.OUTPUT_CAP


def test_heartbeat_during_slow_model():
    async def slow():
        yield {"step": "write", "round": 1}  # first event is immediate
        await asyncio.sleep(0.06)  # ... then the model is slow
        yield {"step": "done", "round": 1}

    async def collect():
        out = []
        async for chunk in stream.with_heartbeat(slow(), interval=0.015):
            out.append(chunk)
        return out

    chunks = asyncio.run(collect())
    assert chunks[0].startswith("data: ")
    assert any(c.startswith(":") for c in chunks)  # heartbeat filled gaps
    assert chunks[-1].startswith("data: ")
    assert json.loads(chunks[-1][len("data: "):])["step"] == "done"


def test_no_secret_values_under_app_web():
    for path in sorted(WEB.iterdir()):
        if path.is_file():
            text = path.read_text(errors="replace")
            assert "VLLM_API_KEY" not in text, path.name
            assert "es_" not in text, path.name


def test_build_wall_clock_and_heartbeat_constants():
    assert config.BUILD_LIMIT_S == 600
    assert config.WEB_TIMEOUT_S >= 660
    assert config.HEARTBEAT_S <= 15
