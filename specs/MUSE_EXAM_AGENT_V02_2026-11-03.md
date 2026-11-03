# Muse Code task: exam agent v0.2, fewer false flags, readable report, hard cap (2026-11-03)

Context: first real run (results/expertery-exam-brackets-2026-11-03b/report.md): 10 READY, 8 FLAGGED, 2 DEFERRED,
spent $1.57 over a $1.50 cap. About half the flags are reader mistakes, not wording (e.g. B4 is a CadQuery error in
the reader's code; B11 "5 mm diameter or radius?"). Files you may change: expertery/exam_agent.py, expertery/cloud.py,
expertery/cli.py, expertery/tests/*, docs/INSTALL.md. Nothing else. No Modal/network/model calls; run
`.venv/bin/python -m pytest expertery -q`.

1. Majority of readers (default --readers 2 stays):
   - all readers PASS → READY.
   - split (some PASS, some FAIL) → run ONE tie-break reader; READY if PASS is the majority of all tries, else go to 2.
   - majority FAIL → explainer (step 2).
   Record every try in candidates.jsonl as today.
2. Explainer must classify. Its JSON becomes {"kind": "wording" | "reader_mistake", "phrase": ..., "why": ...,
   "suggested_request": ...}. Prompt: it sees the request, the reference measurements and the failed tries'
   measurements or run errors (still NEVER the reference code) and the passing tries' count; it must answer
   "reader_mistake" when a careful engineer would read the text one way only (e.g. the failure is a code/API error or
   a misread of a clear number). "why" at most 20 words; "suggested_request" = the full request with the smallest
   wording change. kind "wording" → FLAGGED; kind "reader_mistake" → READY with note "reader mistake: <why>";
   invalid JSON → FLAGGED with suggestion null (as today).
3. Hard money cap: a call reserves its estimate (in_flight_cost) before it starts; may_start is true only when
   spent + reserved_in_flight + one more reserve ≤ cap; on finish, release the reserve and charge the real cost. With
   N workers the realised spend can never pass the cap (test with fake costs and concurrent workers).
   Jobs not started for money stay DEFERRED; report says how many and "re-run with a higher --cap-dollars".
4. report.md, readable first:
   - line 1: "**<n> ready · <m> need your decision · <d> not checked (money cap)**"
   - section "Need your decision": per FLAGGED job one block: job id, the phrase in quotes, why (≤20 words),
     "Suggested:" the changed sentence only (diff the suggested_request against the original and show the changed
     sentence), then "Run `expertery exam review <dir>` to accept, keep, edit or drop."
   - section "Ready": one line listing ids; jobs READY via "reader mistake" listed after with their short note.
   - section "Not checked": ids, if any.
   - footer: spent_estimate vs cap, reader model, number of model calls. No long paragraphs anywhere.
5. Tests: tie-break path (1 PASS + 1 FAIL → third call; READY on PASS, explainer on FAIL); reader_mistake → READY with
   note; wording → FLAGGED; report layout (first line format, sections, ≤20-word why kept/truncated); concurrent cap
   test never exceeds the cap; existing tests updated where the behaviour changed on purpose.
Report: files changed + pytest summary line.
