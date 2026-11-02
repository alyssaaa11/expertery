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
    assert any("2 solids" in str(ev.get("detail", "")) for ev in plan)


def test_headline_and_no_mockup():
    html = (WEB / "index.html").read_text()
    assert "MOCKUP" not in html
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    assert "The AI expert" in text
    assert "your company gets to" in text
    assert "keep." in text


def test_copy_fixes():
    html = (WEB / "index.html").read_text()
    assert "30-part CAD exam (15 hard)" in html
    assert "second look; one try: 83.3%" in html
    assert "92% with its self-check loop" in html
    assert "~1 min" not in html
    assert "a few minutes" in html
    assert "Illustration" in html
    assert "https://github.com/alyssaaa11/expertery" in html
    assert 'href="#video"' in html
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
    assert "CONTACT_EMAIL" in js
    assert js.count("CONTACT_EMAIL") == 1
    assert "maxlength" in (WEB / "index.html").read_text().lower()
    assert "Self-check PASS" in js
    assert "Built (size not checked)" in js
    assert "Checks failed: see measurements" in js
    assert "Thanks, we read every answer." in js
    assert "three@0.160.0" in js or "three@0.160.0" in (WEB / "index.html").read_text()
