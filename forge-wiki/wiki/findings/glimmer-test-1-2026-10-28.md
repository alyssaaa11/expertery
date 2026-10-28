# Glimmer test 1 (Oct 28): does Glimmer run on Modal and write working CadQuery?

**Summary**: The first live run of Muse Glimmer 30B for Forge. It started on a Modal A100-80GB GPU, answered all
three questions, and wrote CadQuery code that ran. The cube was exactly right. The L-bracket had the right volume but
the wall hung off the edge of the base, and the automatic check caught it. Real cost: $0.57.

**Sources**: `~/projects/forge/results/glimmer-test-1/` (`run_test.py`, `results.json`, `run.log`, `run2.log`);
`modal billing summary` and `modal billing rates` (2026-10-28 ~14:10); `modal app list` (both apps stopped).

**Last updated**: 2026-10-28

---

## What ran (verified)
- User go-ahead: "do a test of glimmer to know if works well" (2026-10-28).
- Local first? No: the Mac had about 7.8 GB free (vm_stat) and Glimmer q4 needs about 15 GB, so the test ran on Modal.
- Attempt 1 (13:41) failed while building the image, before any GPU: "unable to determine the version of Python".
  Fix: link `python` to the image's `python3` (see [[lessons]]).
- Attempt 2: deployed in 168 s. The first answer took 459.5 s (cold start: model download + vLLM start). The app was
  stopped at 13:59:59.
- Note: this run still used the HerdShot app, secret and storage (`herdshot-glimmer`). The user flagged the mix-up, so
  Forge now has its own `~/projects/forge/deploy/modal_glimmer.py` (app/secret `forge-glimmer`, volumes `forge-*`).

## Results (verified, results.json)
| Job | Time | Tokens out (thinking chars) | Measured | Expected | Pass |
|---|---|---|---|---|---|
| hello | 459.5 s (cold start) | 235 (1,007) | "Hello!" | — | ok |
| cube 20 mm + 5 mm hole | 47.8 s | 1,311 (4,248) | 20×20×20 mm, 7607.3 mm³ | same | ✅ |
| L-bracket + 2 holes | 142.6 s | 3,845 (13,338) | 40×**23**×20 mm, 4322.2 mm³ | 40×20×20, 4322.2 | ❌ |
- The bracket error: Glimmer put the wall at y = 10–13 mm, just outside the base (y = −10 to 10), so the wall hangs off
  the edge instead of standing on it. The volume was still right, so a volume-only check would have passed it. The
  bounding-box check caught it.
- The expected values were verified first with a hand-built reference bracket (40×20×20 mm, 4322.2 mm³).

## Cost (verified, modal billing summary)
- Metered $0.57 (deployed apps $0.56 + egress $0.01), all covered by credits; billed $0.00.
- Rates: A100-80GB $2.50/h, H100 $3.95/h, A100-40GB $2.10/h.
- Forge budget used: **$0.57 of $30**.

## What it means (hypothesis)
- Glimmer works on Modal and writes runnable CadQuery. The pipeline idea (code → CadQuery → measure → pass/fail) works
  end to end.
- Glimmer fails on a medium job where it must place parts relative to each other: exactly the kind of gap Forge needs.
  This is one job, not evidence yet. The first test (40 jobs, 3 levels, Spark arm, Glimmer + manual arm) decides.
- Checks must cover shape, not only volume: bounding box at least, ideally the position of each feature.
- Thinking is long (13k characters for the bracket). Set max_tokens high (6000 was enough here) and count the time.
- The first Forge deploy downloads the weights again into the new `forge-hf-cache` volume: about 7 more GPU minutes
  (~$0.30).
