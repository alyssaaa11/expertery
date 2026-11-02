"""P2b verifier fixes: ASGI routes (W1), money (W2/W3), deadline+slot (W4).

HTTP tests use FastAPI's TestClient against the REAL app built by
``app.backend.webapp.make_app`` with fakes injected. No Modal, no network,
no model. Tests that need fastapi/httpx skip with a clear install hint
when they are missing.
"""

import copy
import json
import time
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover -- fastapi is installed in .venv
    HAS_FASTAPI = False

from app.backend import budget, config, image_files, limits, loop, webapp

needs_fastapi = pytest.mark.skipif(
    not HAS_FASTAPI,
    reason="W1-test needs fastapi==0.115.6 and httpx installed "
           "(.venv already has them; pip install fastapi==0.115.6 httpx)")

ROOT = Path(__file__).resolve().parent.parent.parent
JOB = "An L-shaped mounting bracket. Overall size 80 x 30 x 45 mm."
CRASH_CODE = "```python\nresult = oops\n```"
GOOD_CODE = "```python\nresult = box\n```"
GOOD_MEASURE = {"bbox": [0, 0, 0, 80, 30, 45], "volume": 1000.0,
                "solids": 1, "area": 10.0,
                "com": [40.0, 15.0, 22.5], "valid": True}
CRASH = {"brep_bytes": None, "measure": None,
         "run_error": "NameError: name 'result' is not defined"}
BUILT = {"brep_bytes": b"BREP", "measure": dict(GOOD_MEASURE),
         "log": "", "run_error": None}


class FakeModel:
    """Scripted model: ("return", content, gpu) | ("raise", exc) |
    ("sleep", seconds, content, gpu). Records the per-call timeout."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, messages, body, timeout):
        self.calls.append({"messages": copy.deepcopy(messages),
                           "body": copy.deepcopy(body),
                           "timeout": timeout})
        step = self.script[min(len(self.calls) - 1, len(self.script) - 1)]
        if step[0] == "raise":
            raise step[1]
        if step[0] == "sleep":
            time.sleep(step[1])
            return step[2], step[3]
        return step[1], step[2]


class FakeBox:
    """Scripted box: list of run_answer_in_box-style dicts."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, code):
        self.calls.append(code)
        if not self.results:
            raise AssertionError("box called unexpectedly")
        return dict(self.results[min(len(self.calls) - 1,
                                     len(self.results) - 1)])


def make_deps(script=(("return", "DONE", 1.0),), box_results=(),
              build_limit_s=600.0, wall=None, containers=None):
    """Fake deps + handles for make_app. ``wall`` is a mutable [t]."""
    t = wall if wall is not None else [1_700_000_000.0]
    model = FakeModel(script)
    box = FakeBox(list(box_results))
    warmed = []
    money = budget.Budget(now=lambda: t[0])
    rates = limits.RateState(now=lambda: t[0])
    lead_rates = limits.LeadRate(now=lambda: t[0])
    deps = {
        "model": model,
        "box": box,
        "convert": lambda brep: (b"STL:" + bytes(brep), b"STEP"),
        "warmer": warmed.append,
        "containers": (lambda: None) if containers is None else containers,
        "leads": {},
        "files": {},
        "money": money,
        "rates": rates,
        "lead_rates": lead_rates,
        "now": lambda: t[0],
        "monotonic": time.monotonic,
        "build_limit_s": build_limit_s,
    }
    handles = {"model": model, "box": box, "warmed": warmed,
               "money": money, "rates": rates, "lead_rates": lead_rates,
               "wall": t, "deps": deps}
    return deps, handles


def events_from_sse(text):
    out = []
    for raw in text.split("\n\n"):
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                out.append(json.loads(line[len("data:"):]))
    return out


# ------------------------------------------------------------------ W1-test
@needs_fastapi
def test_get_root_serves_page():
    deps, _ = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "The AI expert" in resp.text


@needs_fastapi
def test_status_is_json():
    deps, _ = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        resp = client.get("/api/status")
        assert resp.status_code == 200
        assert resp.json()["state"] in ("ready", "waking")


@needs_fastapi
def test_build_streams_sse_and_stores_files():
    deps, h = make_deps(
        script=[("return", GOOD_CODE, 6.0), ("return", "DONE", 1.0)],
        box_results=[BUILT])
    with TestClient(webapp.make_app(deps)) as client:
        resp = client.post("/api/build", json={"job": JOB})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "data:" in resp.text
        events = events_from_sse(resp.text)
        assert events[0]["step"] == "write"  # first event before model work
        done = [e for e in events if e["step"] == "done"]
        assert len(done) == 1 and done[0]["verdict"] == "PASS"
        code_resp = client.get(done[0]["code_url"])
        assert code_resp.status_code == 200
        assert "result = box" in code_resp.text


@needs_fastapi
def test_lead_ok_and_files_unknown_404_and_dev_server_404():
    deps, h = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        lead = client.post("/api/lead",
                           json={"tool": "CAD", "email": "me@company.com"})
        assert lead.status_code == 200
        assert lead.json() == {"ok": True}
        assert h["deps"]["leads"]["leads"][0]["email"] == "me@company.com"
        assert client.get("/files/deadbeef.stl").status_code == 404
        assert client.get("/files/deadbeef.py").status_code == 404
        assert client.get("/dev_server.py").status_code == 404


def test_webapp_sends_no_model_request_for_status():
    src = (ROOT / "app" / "backend" / "webapp.py").read_text()
    assert "urllib" not in src
    assert "FORGE_URL" not in src
    assert "v1/models" not in src


# ------------------------------------------------------------------ W2 money
@needs_fastapi
def test_status_never_calls_model_and_throttles_warmups():
    deps, h = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        wall = h["wall"]
        first = client.get("/api/status").json()
        assert first["state"] == "waking"  # cold: nothing warm yet
        assert len(h["warmed"]) == 1  # one throttled warm-up fired
        before = h["money"].spent_today()
        for _ in range(4):  # polling never wakes anything by itself
            assert client.get("/api/status").json()["state"] == "waking"
        assert len(h["model"].calls) == 0
        assert len(h["warmed"]) == 1  # per-IP hour throttle held
        assert h["money"].spent_today() == before
        # Another IP within 10 min is held by the global throttle...
        other = {"x-forwarded-for": "9.9.9.9"}
        client.get("/api/status", headers=other)
        assert len(h["warmed"]) == 1
        # ...but after 10 min a new IP may fire, charged once more.
        wall[0] += 601.0
        client.get("/api/status", headers=other)
        assert len(h["warmed"]) == 2
        assert h["money"].spent_today() == pytest.approx(2 * config.WAKE_USD)


@needs_fastapi
def test_warm_until_ready_then_cold_again():
    deps, h = make_deps(
        script=[("return", GOOD_CODE, 6.0), ("return", "DONE", 1.0)],
        box_results=[BUILT])
    with TestClient(webapp.make_app(deps)) as client:
        wall = h["wall"]
        client.post("/api/build", json={"job": JOB})  # a real response
        assert client.get("/api/status").json()["state"] == "ready"
        assert h["warmed"] == []  # ready needs no warm-up
        wall[0] += config.SCALE_DOWN_S + 1.0  # scale-down window passed
        assert client.get("/api/status").json()["state"] == "waking"


@needs_fastapi
def test_container_count_warm_needs_no_request():
    deps, h = make_deps(containers=lambda: 2)
    with TestClient(webapp.make_app(deps)) as client:
        assert client.get("/api/status").json()["state"] == "ready"
        assert h["warmed"] == []
        assert h["model"].calls == []


@needs_fastapi
def test_cold_build_charged_wake_exactly_once():
    # Two full builds: the script replays per build (4 model calls total).
    deps, h = make_deps(
        script=[("return", GOOD_CODE, 6.0), ("return", "DONE", 1.0),
                ("return", GOOD_CODE, 6.0), ("return", "DONE", 1.0)],
        box_results=[BUILT, BUILT])
    with TestClient(webapp.make_app(deps)) as client:
        money = h["money"]
        client.post("/api/build", json={"job": JOB})  # cold start
        assert money.spent_today() == pytest.approx(
            7.0 * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD
            + config.IDLE_TAIL_USD + config.WAKE_USD)
        # A second IP (P2c: one free live try per visitor IP): the model
        # is still warm in the same burst, so no second wake-up is charged.
        other = {"x-forwarded-for": "9.9.9.9"}
        client.post("/api/build", json={"job": JOB},
                    headers=other)  # warm, same burst
        assert money.spent_today() == pytest.approx(
            14.0 * config.GPU_USD_PER_S + 2 * config.SANDBOX_USD_PER_BUILD
            + config.IDLE_TAIL_USD + config.WAKE_USD)


def test_budget_warm_helpers():
    t = [1_700_000_000.0]
    money = budget.Budget(now=lambda: t[0])
    assert not money.is_warm()
    assert money.warm_status()[0] == "waking"
    money.note_model_response()
    assert money.is_warm()
    assert money.warm_status()[0] == "ready"
    assert money.warm_status(container_warm=False)[0] == "ready"
    t[0] += config.SCALE_DOWN_S + 1.0
    assert not money.is_warm()
    assert money.warm_status()[0] == "waking"
    assert money.warm_status(container_warm=True)[0] == "ready"
    money.note_cold_build()
    assert money.spent_today() == pytest.approx(config.WAKE_USD)


# ------------------------------------------------------------------ W3 money
@needs_fastapi
def test_exception_build_still_charged():
    deps, h = make_deps(script=[("raise", RuntimeError("boom"))])
    with TestClient(webapp.make_app(deps)) as client:
        resp = client.post("/api/build", json={"job": JOB})
        assert resp.status_code == 200
        events = events_from_sse(resp.text)
        assert events[-1]["step"] == "done"
        assert events[-1]["verdict"] == "CHECK FAILED"
        # Cold start + sandbox + one idle tail, charged exactly once.
        assert h["money"].spent_today() == pytest.approx(
            config.WAKE_USD + config.SANDBOX_USD_PER_BUILD
            + config.IDLE_TAIL_USD, abs=1e-3)


@needs_fastapi
def test_no_code_done_still_charged():
    deps, h = make_deps(script=[("return", "the model sent no code", 2.5)])
    with TestClient(webapp.make_app(deps)) as client:
        events = events_from_sse(
            client.post("/api/build", json={"job": JOB}).text)
        assert events[-1]["step"] == "done"
        assert events[-1]["verdict"] == "CHECK FAILED"
        assert h["money"].spent_today() == pytest.approx(
            2.5 * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD
            + config.IDLE_TAIL_USD + config.WAKE_USD)


@needs_fastapi
def test_failed_later_call_seconds_are_charged():
    deps, h = make_deps(
        script=[("return", CRASH_CODE, 1.0),
                ("raise", RuntimeError("late failure"))],
        box_results=[CRASH])
    with TestClient(webapp.make_app(deps)) as client:
        events = events_from_sse(
            client.post("/api/build", json={"job": JOB}).text)
        assert events[-1]["step"] == "done"
        # The successful first call's seconds count, plus the failed one.
        assert h["money"].spent_today() == pytest.approx(
            1.0 * config.GPU_USD_PER_S + config.SANDBOX_USD_PER_BUILD
            + config.IDLE_TAIL_USD + config.WAKE_USD, abs=5e-2)


# ------------------------------------------------------------------ W4 slot
@needs_fastapi
def test_per_call_timeout_is_time_left_capped_at_600():
    deps, h = make_deps(script=[("return", "DONE", 0.0)],
                        build_limit_s=100.0)
    with TestClient(webapp.make_app(deps)) as client:
        client.post("/api/build", json={"job": JOB})
        (call,) = h["model"].calls
        assert 90.0 <= call["timeout"] <= 100.0


@needs_fastapi
def test_timed_out_build_makes_no_further_call_and_holds_slot():
    deps, h = make_deps(
        script=[("sleep", 1.2, GOOD_CODE, 1.0)],
        box_results=[BUILT],
        build_limit_s=0.25)
    with TestClient(webapp.make_app(deps)) as client:
        resp = client.post("/api/build", json={"job": JOB})
        assert "took too long" in resp.text
        assert len(h["model"].calls) == 1  # the in-flight call, no new one
        assert h["box"].calls == []  # no box run after the deadline
        assert h["rates"].active == 1  # slot held while the worker runs
        deadline = time.time() + 10.0
        while h["rates"].active != 0 and time.time() < deadline:
            time.sleep(0.05)
        assert h["rates"].active == 0  # released when the worker ends
        assert len(h["model"].calls) == 1  # still no further call
        assert h["box"].calls == []
        assert h["money"].spent_today() > 0  # timeout path was charged


def test_loop_stops_before_new_work_past_deadline():
    t = [100.0]
    seen = []

    def _model(messages, body):
        seen.append(body)
        return GOOD_CODE, 1.0

    def _box(code):
        raise AssertionError("box must not run past the deadline")

    events = list(loop.run_job(JOB, _model, _box, clock=lambda: t[0],
                              deadline=99.0))
    assert seen == []
    assert events[-1]["step"] == "done"
    assert events[-1]["verdict"] == "CHECK FAILED"


# ------------------------------------------------------- small: lead + files
@needs_fastapi
def test_lead_rate_limit_five_per_hour():
    deps, _ = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        for i in range(5):
            resp = client.post(
                "/api/lead",
                json={"tool": "CAD", "email": "u%d@company.com" % i})
            assert resp.status_code == 200
        sixth = client.post("/api/lead",
                            json={"tool": "CAD", "email": "u6@company.com"})
        assert sixth.status_code == 429
        fresh = client.post("/api/lead",
                            json={"tool": "CAD", "email": "u6@company.com"},
                            headers={"x-forwarded-for": "9.9.9.9"})
        assert fresh.status_code == 200


def test_lead_rate_unit():
    t = [5000.0]
    leads = limits.LeadRate(now=lambda: t[0])
    for _ in range(config.MAX_LEADS_PER_IP_HOUR):
        assert leads.check("1.2.3.4") is None
        leads.note("1.2.3.4")
    code, _ = leads.check("1.2.3.4")
    assert code == 429
    assert leads.check("5.6.7.8") is None
    t[0] += 3601.0
    assert leads.check("1.2.3.4") is None


@needs_fastapi
def test_lead_delete_removes_everything_with_that_email():
    deps, h = make_deps()
    deps["leads"]["leads"] = [
        {"tool": "CAD", "email": "me@company.com", "ts": 1.0},
        {"tool": "SQL", "email": "Me@Company.com", "ts": 2.0},
        {"tool": "CAD", "email": "other@company.com", "ts": 3.0},
    ]
    with TestClient(webapp.make_app(deps)) as client:
        resp = client.post("/api/lead",
                           json={"tool": " Delete ",
                                 "email": "me@company.com"})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True, "deleted": 2}
        assert deps["leads"]["leads"] == [
            {"tool": "CAD", "email": "other@company.com", "ts": 3.0}]


def test_image_serves_only_the_five_page_files():
    assert set(image_files.WEB_FILES) == {
        "app/web/index.html",
        "app/web/styles.css",
        "app/web/app.js",
        "app/web/object.jpeg",
        "app/web/recorded_run.json",
    }
    assert "app/web/dev_server.py" not in image_files.WEB_IMAGE_FILES
    assert (ROOT / "app" / "web" / "dev_server.py").is_file()  # kept locally
    assert image_files.check_file_list() == []


def test_privacy_line_and_no_contact_placeholder():
    html = (ROOT / "app" / "web" / "index.html").read_text()
    assert "We only use your email to reply about Homegrown. " \
        "To delete it, send the form again with the same email and " \
        "the word delete as the tool." in html
    js = (ROOT / "app" / "web" / "app.js").read_text()
    assert "CONTACT_EMAIL" not in js
