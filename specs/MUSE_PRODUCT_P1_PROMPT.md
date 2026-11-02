Do ROUND P1 ONLY of the spec in specs/MUSE_PRODUCT_2026-11-02.md (read the whole spec first; P2 is context only, do
not build it now). Repo: ~/projects/forge.

Rules:
- Only create files under app/ (app/web/, app/tests/). Change nothing else. Do not touch experiments/, results/, data/,
  company/, deploy/, docs/, the wiki or any exam file.
- No network, no Modal, no model calls, no deploy, no git push. Do not start the dev server; Claude tests it in a browser.
- Copy the design from docs/product/mockup/index.html exactly (it is the user's approved design); only the listed
  changes (0-7) are allowed.
- Run: .venv/bin/python -m pytest -q app/tests  and also  .venv/bin/python -m pytest -q experiments/final experiments/r5
  (must stay green).
- End with the report the spec asks for: diff summary (files + one line each), the exact pytest commands and results,
  and anything you could not follow or decided differently, with the reason.
