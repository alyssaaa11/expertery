"""Static checks for the Round P1 product page (no browser needed)."""

import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
VALID_STEPS = {"write", "build", "measure", "fix", "done", "error"}


def _events():
    data = json.loads((WEB / "recorded_run.json").read_text())
    if isinstance(data, dict):
        assert data.get("recorded") is True, "run must be marked recorded"
        return list(data["events"])
    return list(data)


def test_files_exist():
    for name in ("index.html", "styles.css", "app.js", "object.jpeg", "recorded_run.json"):
        assert (WEB / name).is_file(), name


def test_recorded_run_shape():
    plan = _events()
    assert len(plan) >= 5
    for ev in plan:
        assert ev["step"] in VALID_STEPS, ev
    assert plan[-1]["step"] == "done"
    assert plan[-1].get("recorded") is True
    assert plan[-1].get("verdict") == "PASS"
    # Real recorded run (live, 2026-11-02): every event is marked recorded.
    assert all(ev.get("recorded") is True for ev in plan)


def test_headline_and_no_mockup():
    html = (WEB / "index.html").read_text()
    assert "MOCKUP" not in html
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    assert "AI that" in text and "knows your tool." in text


def test_copy_fixes():
    html = (WEB / "index.html").read_text()
    # Proof card (user, 2026-11-02): one claim + "How we measured" link; the
    # full numbers (one try 83.3%, best setup 94%) stay in the README.
    assert "How we measured" in html and "#results" in html
    readme = (WEB.parents[1] / "README.md").read_text()
    assert "83%" in readme and "94%" in readme
    assert "92% with its self-check loop" in html
    assert "~1 min" not in html
    assert "a few minutes" in html
    assert "Illustration" in html
    assert "https://github.com/alyssaaa11/expertery" in html
    assert 'youtube.com/watch?v=po2wfzZXjtE' in html
    css = (WEB / "styles.css").read_text()
    assert "prefers-reduced-motion" in css
    assert "@media" in css
    assert "max-width" in css
    assert ".tab" in css  # corner tabs exist on desktop, hidden in the mobile query


def test_app_js_api_wiring():
    js = (WEB / "app.js").read_text()
    assert "/api/status" in js
    assert "/api/build" in js
    assert "/api/lead" in js
    assert "VLLM" not in js
    assert "es_" not in js
    assert "API_KEY" not in js
    assert "apikey" not in js.lower()
    assert "CONTACT_EMAIL" not in js  # placeholder removed (P2b privacy fix)
    assert "Deleted." in js  # delete-confirmation shown after a delete lead
    assert "maxlength" in (WEB / "index.html").read_text().lower()
    assert "Self-check PASS" in js
    assert "Built (size not checked)" in js
    assert "Checks failed: see measurements" in js
    assert "Thanks, we read every answer." in js
    assert "three@0.160.0" in js or "three@0.160.0" in (WEB / "index.html").read_text()
