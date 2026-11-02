"""Round P2c: total cap + one free live try per visitor + tries counter.

HTTP tests use FastAPI's TestClient against the REAL app built by
``app.backend.webapp.make_app`` with fakes injected. No Modal, no network,
no model.
"""

import math
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:  # pragma: no cover -- fastapi is installed in .venv
    HAS_FASTAPI = False

from app.backend import budget, config, limits, webapp

needs_fastapi = pytest.mark.skipif(
    not HAS_FASTAPI,
    reason="P2c-test needs fastapi==0.115.6 and httpx installed "
           "(.venv already has them; pip install fastapi==0.115.6 httpx)")

ROOT = Path(__file__).resolve().parent.parent.parent
MODAL_WEB = ROOT / "deploy" / "modal_web.py"
JOB = "An L-shaped mounting bracket. Overall size 80 x 30 x 45 mm."
GOOD_CODE = "```python\nresult = box\n```"
GOOD_MEASURE = {"bbox": [0, 0, 0, 80, 30, 45], "volume": 1000.0,
                "solids": 1, "area": 10.0,
                "com": [40.0, 15.0, 22.5], "valid": True}
BUILT = {"brep_bytes": b"BREP", "measure": dict(GOOD_MEASURE),
         "log": "", "run_error": None}


class FakeModel:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, messages, body, timeout):
        self.calls.append(True)
        step = self.script[min(len(self.calls) - 1, len(self.script) - 1)]
        return step[1], step[2]


class FakeBox:
    def __init__(self, results):
        self.results = list(results)

    def __call__(self, code):
        return dict(self.results[-1])


def make_deps(tries_store=None, wall=None):
    t = wall if wall is not None else [1_700_000_000.0]
    if tries_store is None:
        tries_store = {}
    deps = {
        "model": FakeModel([("return", GOOD_CODE, 6.0),
                            ("return", "DONE", 1.0)]),
        "box": FakeBox([BUILT]),
        "convert": lambda brep: (b"STL:" + bytes(brep), b"STEP"),
        "warmer": lambda _ip: None,
        "containers": lambda: 100,  # warm: status never fires a warm-up here
        "leads": {},
        "files": {},
        "tries": tries_store,
        "money": budget.Budget(now=lambda: t[0]),
        "rates": limits.RateState(now=lambda: t[0]),
        "lead_rates": limits.LeadRate(now=lambda: t[0]),
        "now": lambda: t[0],
        "build_limit_s": 600.0,
    }
    return deps, tries_store


# ------------------------------------------------------- config defaults
def test_p2c_config_defaults():
    assert config.TOTAL_CAP_USD == 15
    assert config.DAILY_CAP_USD == 15  # only the total binds unless set
    assert config.MAX_LIVE_TRIES_PER_VISITOR == 1
    assert config.EST_TRY_USD == pytest.approx(0.30)
    assert config.TRIED_MESSAGE == (
        "You've used your free live try. You can watch the recorded "
        "demo as many times as you like.")


def test_p2c_modal_web_bakes_new_names():
    src = MODAL_WEB.read_text()
    assert '"TOTAL_CAP_USD"' in src and '"EST_TRY_USD"' in src
    assert '"MAX_LIVE_TRIES_PER_VISITOR"' in src
    baked = src[src.find("_BAKED_ENV"):]
    assert "TOTAL_CAP_USD" in baked and "EST_TRY_USD" in baked
    assert "MAX_LIVE_TRIES_PER_VISITOR" in baked
    assert 'os.environ.get("TOTAL_CAP_USD", "15")' in src
    assert 'os.environ.get("EST_TRY_USD", "0.30")' in src
    assert 'os.environ.get("MAX_LIVE_TRIES_PER_VISITOR", "1")' in src
    assert 'os.environ.get("DAILY_CAP_USD", "15")' in src
    assert "homegrown-tries" in src


# ------------------------------------------------------- total cap (unit)
def test_total_spend_sums_all_days():
    t = [1_700_000_000.0]
    money = budget.Budget(now=lambda: t[0])
    money._spend[budget.day_key(t[0])] = 6.0
    money._spend[budget.day_key(t[0] + 86400.0)] = 7.0
    assert money.total_spent() == pytest.approx(13.0)
    assert not money.is_capped()


def test_total_cap_across_two_days_pauses():
    t = [1_700_000_000.0]
    money = budget.Budget(now=lambda: t[0])
    # Neither day hits the daily cap alone, but together they pass $15.
    money._spend[budget.day_key(t[0])] = 10.0
    money._spend[budget.day_key(t[0] + 86400.0)] = 10.0
    assert money.total_spent() == pytest.approx(20.0)
    assert money.is_capped()
    state, message = money.warm_status(container_warm=True)
    assert state == "paused"
    assert message == config.PAUSED_MESSAGE


def test_total_exactly_at_cap_pauses():
    t = [1_700_000_000.0]
    money = budget.Budget(now=lambda: t[0])
    money._spend[budget.day_key(t[0])] = 7.5
    money._spend[budget.day_key(t[0] + 86400.0)] = 7.5
    assert money.is_capped()


def test_restore_merges_every_day_and_snapshot_roundtrips():
    t = [1_700_000_000.0]
    money = budget.Budget(now=lambda: t[0])
    money.restore({budget.day_key(t[0]): 4.0,
                   budget.day_key(t[0] + 86400.0): 9.0,
                   "bogus": "not-a-number"})
    assert money.total_spent() == pytest.approx(13.0)
    snap = money.snapshot()
    assert snap[budget.day_key(t[0])] == pytest.approx(4.0)
    money.restore({budget.day_key(t[0]): 1.0})  # smaller never wins
    assert money.snapshot()[budget.day_key(t[0])] == pytest.approx(4.0)


# ------------------------------------------------------- tries_left math
def test_tries_left_math():
    t = [1_700_000_000.0]
    money = budget.Budget(now=lambda: t[0])
    assert money.tries_left() == math.floor(15 / 0.30)
    assert isinstance(money.tries_left(), int)
    money._spend[budget.day_key(t[0])] = 15.0 - 0.30
    assert money.tries_left() == 1
    money._spend[budget.day_key(t[0])] = 15.0 - 0.29
    assert money.tries_left() == 0
    money._spend[budget.day_key(t[0])] = 99.0
    assert money.tries_left() == 0


# ------------------------------------------------------- TryState (unit)
def test_try_state_one_free_try_then_429():
    tries = limits.TryState()
    assert tries.check("1.2.3.4") is None
    tries.note("1.2.3.4")
    assert tries.count("1.2.3.4") == 1
    code, message = tries.check("1.2.3.4")
    assert code == 429
    assert message == config.TRIED_MESSAGE
    assert tries.check("5.6.7.8") is None  # another visitor unaffected


def test_try_state_restore_keeps_larger():
    tries = limits.TryState()
    tries.restore("1.2.3.4", 1)
    assert tries.check("1.2.3.4")[0] == 429
    tries.restore("1.2.3.4", 0)  # never forgets a persisted try
    assert tries.check("1.2.3.4")[0] == 429
    tries.restore("9.9.9.9", "bogus")  # bad values are ignored
    assert tries.check("9.9.9.9") is None


# ------------------------------------------------------- HTTP: one try
@needs_fastapi
def test_second_build_from_same_ip_is_429_tried():
    deps, _ = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        first = client.post("/api/build", json={"job": JOB})
        assert first.status_code == 200
        second = client.post("/api/build", json={"job": JOB})
        assert second.status_code == 429
        body = second.json()
        assert body["message"] == config.TRIED_MESSAGE
        assert body["reason"] == "tried"


@needs_fastapi
def test_another_ip_may_still_build_and_spoofed_first_hop_uses_last_hop():
    deps, _ = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        assert client.post("/api/build", json={"job": JOB}).status_code \
            == 200
        other = {"x-forwarded-for": "9.9.9.9"}
        assert client.post("/api/build", json={"job": JOB},
                           headers=other).status_code == 200
        # Same last-hop IP rule: the spoofable first hop is ignored.
        spoofed = {"x-forwarded-for": "spoofed, 9.9.9.9"}
        again = client.post("/api/build", json={"job": JOB},
                            headers=spoofed)
        assert again.status_code == 429
        assert again.json()["reason"] == "tried"


@needs_fastapi
def test_tries_survive_across_app_instances_sharing_the_store():
    tries_store = {}
    deps1, _ = make_deps(tries_store=tries_store)
    with TestClient(webapp.make_app(deps1)) as client:
        assert client.post("/api/build", json={"job": JOB}).status_code \
            == 200
    assert tries_store.get("testclient") == 1
    # A fresh process after a restart reloads the persisted count.
    deps2, _ = make_deps(tries_store=tries_store)
    with TestClient(webapp.make_app(deps2)) as client:
        assert client.get("/api/status").json()["you_tried"] is True
        denied = client.post("/api/build", json={"job": JOB})
        assert denied.status_code == 429
        assert denied.json()["reason"] == "tried"


# ------------------------------------------------------- HTTP: status
@needs_fastapi
def test_status_carries_tries_left_and_you_tried():
    deps, _ = make_deps()
    with TestClient(webapp.make_app(deps)) as client:
        fresh = client.get("/api/status")
        assert fresh.status_code == 200
        body = fresh.json()
        assert isinstance(body["tries_left"], int)
        assert body["tries_left"] == math.floor(15 / 0.30)
        assert body["you_tried"] is False
        client.post("/api/build", json={"job": JOB})
        after = client.get("/api/status").json()
        assert after["you_tried"] is True
        fresh_ip = client.get("/api/status",
                              headers={"x-forwarded-for": "9.9.9.9"}).json()
        assert fresh_ip["you_tried"] is False


@needs_fastapi
def test_total_cap_pauses_status_and_build_over_http():
    t = [1_700_000_000.0]
    deps, _ = make_deps(wall=t)
    money = deps["money"]
    money._spend[budget.day_key(t[0])] = 10.0
    money._spend[budget.day_key(t[0] + 86400.0)] = 10.0
    with TestClient(webapp.make_app(deps)) as client:
        paused = client.get("/api/status").json()
        assert paused["state"] == "paused"
        assert paused["message"] == config.PAUSED_MESSAGE
        assert paused["tries_left"] == 0
        assert paused["you_tried"] is False
        denied = client.post("/api/build", json={"job": JOB})
        assert denied.status_code == 429
        assert denied.json()["message"] == config.PAUSED_MESSAGE


# ------------------------------------------------------- page
def test_page_shows_approximate_counter_near_build_button():
    html = (ROOT / "app" / "web" / "index.html").read_text()
    assert 'id="triesnote"' in html
    assert html.find('id="triesnote"') > html.find('id="run"')
    js = (ROOT / "app" / "web" / "app.js").read_text()
    assert "free live tries left" in js
    assert "\u2248 " in js  # always approximate, never claimed exact
    assert "exact" not in js.lower() or "never exact" in js.lower()


def test_page_demo_mode_uses_localstorage_key_and_recorded_run():
    js = (ROOT / "app" / "web" / "app.js").read_text()
    assert "hg_tried" in js
    assert "localStorage" in js
    assert "Watch the recorded demo" in js
    assert "You've used your free live try." in js
    assert "recorded_run.json" in js
    assert "you_tried" in js
