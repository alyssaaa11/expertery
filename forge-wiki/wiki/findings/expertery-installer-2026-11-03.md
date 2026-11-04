# Expertery v0: installer and exam agent (2026-11-03)

**Summary**: Expertery became an installable command-line product (`sh install.sh` → `expertery`), installed into the
company's own Modal account, with an exam agent that turns past work into a locked exam. Built by Muse Code in 4
rounds; the exam agent's reader is Meta's Muse Spark Open. Second real run: 18 READY, 2 FLAGGED, $1.72.

**Sources**: specs/MUSE_INSTALLER_2026-11-03.md, MUSE_INSTALLER_FIX1/FIX2, MUSE_EXAM_AGENT_V02_2026-11-03.md;
commits adf0af9, 7440614, 63a4b25, abe554a; results/expertery-exam-brackets-2026-11-03b and -03c (report.md);
docs/INSTALL.md; diagram docs/diagrams/expertery-install/ (HTML + PNG, bd06aec).

**Last updated**: 2026-11-04

---

## What it is (plain words)
- A **CLI**, not an MCP: a person types `expertery init`, `exam build | review | lock`, `test`, `train`, `serve`,
  `status`. decision (user, 2026-11-03): an MCP server is "next", after the hackathon.
- Private by design: past work, exams and the trained model stay in the company's own Modal account; model-written
  code runs only in the locked cloud box; the reader (Spark Open) can also run on the company's own server.
- Exam agent: for each past job (request.txt + part.py), checks the finished part builds; Spark Open reads ONLY the
  request and builds it (2 tries, a 3rd as tie-break when they split); the referee compares with the real part; if most
  tries fail, an explainer (never sees the reference code) classifies "wording" (FLAGGED + a suggested sentence) or
  "reader mistake" (READY with a note). A person approves every flag (`exam review`); `exam lock` writes exam.jsonl + sha.

## Relevant findings
- verified: `sh install.sh` installs `expertery` in ~/.local/bin (uv tool env, Python 3.12, cadquery 2.8.0 pins);
  `expertery init` OK (box app looked up, config ~/.expertery/config.json). Tests: 39 (expertery) + 77 (final) pass.
- verified: run b (v0): 10 READY, 8 FLAGGED, 2 DEFERRED, est. $1.57 vs cap $1.50; B16 flagged with the right cause
  (sides' start height); about half the flags were reader mistakes (B4 = CadQuery error).
- verified: run c (v0.2): **18 READY, 2 FLAGGED (B7, B8: which side of Y = 0 the plate thickness goes), 0 deferred,
  est. $1.72 of $2.50, 49 calls**; B20 kept READY as a reader mistake. B16 was READY this time.
- hypothesis: results vary between runs (readers sample at temperature 1.0); 3+ readers would be steadier (~50% more cost).
- verified: cost: Muse Code ≈ $0.70 + $0.20 + $0.15 + $0.60 Meta credit (estimates from run.usage tokens); Spark Open
  ≈ $1.57 + $1.72 (estimates, Baseten).

## Open questions
- Practice-job generation from past work (a "generator agent") is not built; v0 uses the factory scripts.
- Running the trained model 4-bit on a small GPU is untested (say "designed to run on one GPU").

## Next step
- README "Install Expertery" section; optional 10 s clip of `exam build` + report in the video.
- Pitch line: "Installs with one command into your own cloud account. The exam agent turns your past work into a
  checked exam, separates unclear wording from model mistakes, and a person approves every change."
