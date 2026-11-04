You're making the 3-minute submission video for **Expertery**, our entry in the Meta AI Developer Hackathon 2026 (Indie track, "Push the Frontier"; deadline Nov 4). Judges score **Impact 30% · Meta tools 25% · Demo (incl. this video) 25% · Technical depth 20%**. Aim for 2:45–2:55, 1080p, burned-in captions, text ≥ 28 px.

**What Expertery is (say this in the first 10 seconds):** a factory that turns Meta's open model (Muse Glimmer 30B) into an expert on one company tool. It practises in the tool, a referee keeps only answers that were proven right, and it learns only from those. Proven on CAD (CadQuery). Live: https://expertery.vercel.app. Tagline, said exactly 3 times (open, close, last frame): **"AI that knows your tool."**

**Hard rules (judges punish these):**
- Only real screen recordings of the real product. Never show a mock-up as real output, and never splice fragments into a run that didn't happen.
- Label every speed-up on screen ("real run, sped up 4×").
- Every number on screen carries its source in small text. Use only the numbers below, with exactly this wording.
- Never say "never leaves your company", "100%", "the first", or "replaces engineers". Privacy wording: "open model, can run on a GPU you control".

**Script beats:**
1. **0:00–0:10 Hook.** The rotating, checked part with a ✓ PASS badge. Voice: "One sentence in. A checked CAD part out. Expertery: AI that knows your tool."
2. **0:10–0:30 Problem (2026 evidence, one stat per ~5 s):**
   - "2026's best AI scores 0.59 out of 1 on real engineering CAD tasks, at about $11 per task." *(BenchCAD 2.0, Oct 12 2026; graded score, not a pass rate)*
   - "8 million SOLIDWORKS & 3DEXPERIENCE users." *(Dassault Systèmes, Jan 29 2026)*
   - "Compilation is not correctness: AI-written factory (PLC) code passes 11.92 points less often when actually run." *(CycleBench, arXiv 2610.28675, Oct 2026)*
   - Small caption under all three: "Different tests, not a direct comparison with our results."
3. **0:30–1:15 Demo.** Screen-record the live page: type the L-bracket request → stage labels WRITE → BUILD → MEASURE → FIX → DONE → 3D view, measurements, STEP download. Use the real recorded run (`app/web/recorded_run.json`, Nov 2: PASS in 120 s), labelled. Wake the model ~15 min before recording (cold start up to 14 min).
4. **0:45–1:00 Side by side (real exam outputs only): exam job H1.** Left: plain Glimmer's part, `results/first-test-main/demo/H1_A.svg`, labelled **"plain Glimmer, Oct 28 (earlier session)"**. Its mounting posts stick out on the wrong side. Right: the correct part, `H1_ref.svg`, labelled "the part we asked for". The trained model passed H1 on all 3 exam tries (`results/exam-2026-11-02/exam-FT/calls.jsonl`). If you want the trained model's own part instead of the reference, render its H1 code **only** through the locked sandbox runner (`experiments/b2-hint/run_one_cq.py`), never by running model code directly on the Mac. Backups if H1 doesn't read well on screen: M12, then H15.
5. **1:15–1:50 Proof (before → after), one card each:**
   - **62% → 96%** · "Same model, same 100 jobs it never trained on. Crashes 12 → 1." *(+34 pts, 95% CI +24 to +44; source: results/r5f-dev-ft-2026-11-02/compare_dev.json; small caption: "jobs from the same part families as training")*
   - **83% → 92%** on a hard hand-made exam (30 parts × 3 tries = 90 answers), thanks to its self-check loop. Hard parts 73% → 91%. *(results/exam2-ftx-2026-11-02/compare_ftx.json)*
   - "Same score as the best setup with a 5,700-word manual (92% vs 94%, a statistical tie), with **2.7× fewer tokens**." *(7,946 vs 21,823 tokens per correct part)*
6. **~1:50 Second wow: a real self-fix from the exam, job H2 try 1** (`results/exam2-ftx-2026-11-02/exam2-FTX/calls.jsonl`, job H2, rep 0):
   - **Round 1 crash:** show the real error from the `run_error` field. It ends in `.fillet(3)` → `StdFail_NotDone: BRep_API: command not done`. Caption: "It asked for 3 mm rounded edges the CAD kernel couldn't build."
   - **"Glimmer reads the error and rewrites its code"** → round 2 builds → round 3 done.
   - **Final part:** the real final code (48 lines, from the `bx_final` row) and its real measurements: 100 × 70 × 8 mm, volume 20,708.6 mm³, 1 solid, valid → **✓ PASS**.
   - The code from rounds 1–2 wasn't stored, so **don't show "before" code** and don't invent any. Backup: H14 rep 0 (same structure; its crash error is also in `run_error`).
   - Caption: "Real exam run · the self-check loop rescued 12 of 90 answers".
7. **2:00–2:30 Meta tools (25% of the score, own segment):** factory diagram (`docs/video/expertery-factory-diagram.png`), each box lighting up: Glimmer = the student (trained, LoRA, ~2 h on one GPU) · Spark Open = the tutor (hints only, never code; with hints Glimmer solved 52 of 54 stuck jobs) · Muse Code = wrote the factory, the cloud box and this page. Line: "Only answers the referee proved correct became lessons. Wrong answers never teach."
8. **2:30–2:50 Close:** "Proven on CAD. Next: any tool with a checkable answer: PLC code, chip design, SQL." Then the 3 takeaways (learns only from proven answers · no manual, same score, 2.7× fewer tokens · all Meta, open) → "Expertery: AI that knows your tool." → https://expertery.vercel.app

**Optional honesty card (10 s, builds trust):** "What didn't hold: it isn't faster (266 s vs 301 s per answer), and it still misses some hard parts."

Deliver: the MP4, the voice-over script with timings, and a list of every on-screen number with its source. Ask before using any number not in this prompt.
