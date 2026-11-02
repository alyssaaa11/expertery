"""P2 page fixes: 390 px hero fit and the fix-row end state (static)."""

from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


def _mobile_block():
    css = (WEB / "styles.css").read_text()
    start = css.find("@media (max-width:700px)")
    assert start != -1
    return css[start:]


def test_headline_uses_clamp_on_mobile():
    assert "clamp(" in _mobile_block()


def test_top_buttons_wrap_on_mobile():
    block = _mobile_block()
    assert ".top" in block and "flex-wrap" in block
    assert ".rightnav" in block


def test_pill_nav_scrolls_on_mobile():
    block = _mobile_block()
    assert ".navslot" in block
    assert "overflow-x:auto" in block.replace(" ", "")


def test_no_horizontal_scroll_on_mobile():
    block = _mobile_block()
    assert "overflow-x:hidden" in block.replace(" ", "")


def test_desktop_rules_untouched():
    css = (WEB / "styles.css").read_text()
    desktop = css.split("@media")[0]
    assert "h1{font-size:96px" in desktop
    assert "grid-template-columns:1.05fr 1fr" in desktop
    assert ".pillnav{display:flex" in desktop


def test_used_fix_row_becomes_done():
    js = (WEB / "app.js").read_text()
    assert 'rowByKey.fix.className = "done"' in js


def test_fix_note_text_kept():
    js = (WEB / "app.js").read_text()
    # showDone never rewrites the fix row's "fixed in round N" note.
    assert js.count("fixNote.textContent =") == 2  # reset + fix event only
