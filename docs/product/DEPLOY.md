# Expertery live demo: go-live steps (NOT run yet; user said "no go yet", 2026-11-02)

Decisions (user, 2026-11-02 evening): $15 TOTAL (no daily cap), 1 live try per visitor IP (user changed from 2, 2026-11-02 ~22:00), counter estimate $0.60/try
(verifier note), reasoning xhigh until the high-vs-xhigh check. Verifier GO on 7cb32a2
(~/agents/verifier/reports/forge-web-p2c-2026-11-02.md). Modal used ≈ $72 of the user's $90 (modal billing summary,
Oct 37.47 + Nov 34.49, checked 2026-11-02 ~21:30).

Each step needs the user's yes right before it.

1. Model (sleeps when unused; GPU only runs on requests):
   FORGE_MODEL_NAME=<r5f model name from forge-wiki status> modal deploy deploy/modal_forge.py
   → note the URL of app forge-trained (…modal.run).
2. Website (from the repo root, so the file list resolves):
   FORGE_URL=<url from step 1> TOTAL_CAP_USD=15 DAILY_CAP_USD=15 MAX_LIVE_TRIES_PER_VISITOR=1 EST_TRY_USD=0.60 \
   REASONING_STRENGTH=xhigh modal deploy deploy/modal_web.py
   → check the startup log line "homegrown-web config: {...}" shows these values.
3. One real test build by Claude (counts inside the $15); check verdict badge, 3D view, downloads, counter.
4. Give the user the link. Check `modal billing summary` daily during judging (Nov 5-9).
To stop everything: modal app stop homegrown-web && modal app stop forge-trained

## Done 2026-11-02 (~22:45)
- Model: `FORGE_MODEL_NAME=r5f modal deploy deploy/modal_forge.py` → <model URL from modal deploy>
- Website engine: run the deploy with the project venv (`.venv/bin/python -m modal deploy deploy/modal_web.py`; the
  plain `modal` CLI lacks CadQuery) with the env above plus `ALLOWED_ORIGINS=https://expertery.vercel.app`.
  Engine URL: <engine URL from modal deploy>
- Public page (user: no Modal/Gmail name in the address): Vercel project `homegrown-factory` →
  **https://expertery.vercel.app**. Build: copy app/web/{index.html,styles.css,app.js,object.jpeg,
  recorded_run.json} to a folder named homegrown-factory, set `<meta name="hg-api" content="<engine URL>">` in
  index.html, then `vercel deploy --prod --yes` there.
- First real build: PASS 80 × 30 × 45 mm in 120 s; cold start 14 min. Re-deploying the engine keeps the counters
  (Modal Dicts).

## Renamed 2026-11-03 (~12:50): address https://expertery.vercel.app
- Vercel project is still named `homegrown-factory` (internal); domain `expertery.vercel.app` added, the old
  `homegrown-factory.vercel.app` domain removed (user: don't keep the old one). Engine redeployed with the same baked
  settings and `ALLOWED_ORIGINS=https://expertery.vercel.app` (preflight: new origin 200, old origin 400).
