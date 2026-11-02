Do ROUND P2 of the spec in specs/MUSE_PRODUCT_2026-11-02.md (read the whole spec first, including every verifier
edit S1-S7). Round P1 is done and committed: app/web/ (the page) and app/tests/test_web_static.py. Repo:
~/projects/forge.

Build:
- deploy/modal_web.py and app/backend/ (+ tests in app/tests/) exactly as P2 describes.
- Two small page fixes found in Claude's browser check of P1 (only these changes to app/web/):
  1. At 390 px width the hero headline, the top-right buttons and the pill nav overflow the screen. Make the hero fit:
     smaller headline (clamp), wrap or hide the top-right buttons, the pill nav scrolls horizontally or hides, no
     horizontal page scroll at 390 px. Desktop must stay pixel-identical.
  2. After a run ends, the "Fix if needed" row keeps its spinning fix icon. When the run is done, a used fix row
     becomes a done row (check style, text keeps "fixed in round N"); an unused fix row stays neutral.

Rules:
- Only create/change files under app/ and the new deploy/modal_web.py. Do not change deploy/modal_forge.py,
  deploy/modal_glimmer.py, experiments/, results/, data/, company/, docs/, the wiki or any exam file. Import helpers
  from experiments/ read-only, as the spec says. If something can't be done without changing them, stop and report.
- No network, no Modal calls (no `modal deploy`, `modal run`, `modal serve`), no model calls, no git push.
- Run: .venv/bin/python -m pytest -q app/tests  and  .venv/bin/python -m pytest -q experiments/final experiments/r5
  (must stay green). If FastAPI/sse libs are missing in .venv, write the tests so the pure logic in app/backend is
  tested without them, and list what Claude must install; do not pip install anything.
- End with the report: diff summary (files + one line each), the exact pytest commands and results, the full list of
  files that go into the web image, every config default, and anything you could not follow or decided differently,
  with the reason.
