# Expertery pitch: 3-minute video script + live deck (draft v2, 2026-11-03)

Made with the `winning-pitch` skill. Status: **draft for the user's approval**; nothing recorded or published.

- decision (user, 2026-11-03): name **Expertery** in the pitch (page headline "AI that knows your tool.").
- decision (user, 2026-11-03): **no founder sentence**.
- decision (user, 2026-11-03): format = 3-minute video + a live deck that mirrors it.
- decision (user, 2026-11-03, v2): **the main story is "I trained a model"**. The self-check loop is a product
  feature (one beat), not the headline.
- Rubric (kickoff slide, wiki project.md): **Impact 30 · Meta tooling 25 · Demo incl. video 25 · Technical depth 20**.

## Numbers used (all verified)
| Claim | Number | Source |
|---|---|---|
| Unseen practice jobs, no manual | plain 62/100 → trained 96/100; +34 pts, 95% CI [+24, +44]; crashes 12 → 1 | results/r5f-dev-ft-2026-11-02/compare_dev.json |
| Hand-made exam, trained, no manual, 1 shot | 75/90 = 83.3% (medium 93.3, hard 73.3) | results/exam-2026-11-02/compare_ft_acard.json |
| Untrained + one-page rule card | 77/90 = 85.6%; trained − card = −2.2 [−12.2, +6.7] (tie) | same |
| Best manual setup (BX: manual + hint + examples + retries) | 85/90 = 94.4% (hard 91.1); trained − BX = −11.1 [−24.4, +1.1] | results/exam-2026-11-02/compare_bars.json |
| Tokens per correct part | trained 3,352 (prompt 215) vs BX 21,823 (prompt 14,151) = **6.5× fewer** | same |
| Product loop on the exam (FTX) | 83/90 = 92.2% vs BX 94.4%; −2.2 [−11.1, +5.6] (tie) | results/exam2-ftx-2026-11-02/compare_ftx.json |
| Factory | 2,000 jobs; Spark hints → 52/54 solved; 1,742 proven lessons; LoRA, 1 GPU, 6,993 s | README, results/train-r5f/train.json |
Not used: the 53% exam baseline (earlier session, 1 try, n = 30; too weak) and wall-clock/$ (pre-registered bar (d)
passed on tokens only).

## Rubric → asset map
| Criterion | Weight | Asset | Where |
|---|---|---|---|
| Technical depth | 20 | The training factory, referee gate, pre-registered tests with CIs | 0:28–1:50 |
| Meta tooling | 25 | Glimmer = the model I trained · Spark Open = tutor (hints only) · Muse Code = built the factory, cloud box and page | 0:28–1:15, slide 4 |
| Impact | 30 | Manual gone from every request (6.5× fewer tokens); open weights can run on a GPU you control; live page. Bracket test **pending** | 0:11, 1:50, close |
| Demo | 25 | Real factory run footage + real live-page run (Nov 2 L-bracket) | 0:28–1:15, 2:00–2:30 |

## Vertebrae (what a judge repeats an hour later)
1. **I trained Meta's Glimmer: 62% → 96% on unseen jobs, with no manual.**
2. **It learned only from answers a referee proved correct.** (Wrong answers never teach.)
3. **The manual is gone from every request: 6.5× fewer tokens per correct part.**

## Tagline
Used exactly 3 times: video open, close, first line of the post/description.

| Option | Innovation | Clarity | Memorability | Truth | Fit | /25 |
|---|---|---|---|---|---|---|
| **AI that knows your tool.** (page headline) | 3 | 5 | 4 | 5 | 5 | **22** |
| Trained, not prompted. | 4 | 4 | 5 | 5 | 4 | 22 |
| Wrong answers never teach. | 4 | 3 | 5 | 5 | 4 | 21 |

Recommended: keep **"AI that knows your tool."** (it matches the live page). "Trained, not prompted" stays as one
spoken line in the problem beat ("So I didn't prompt it. I trained it.").

## Video script (target 2:50; ≈ 365 words at ≤ 150 wpm)
Recording rules: real footage only; captions burned in; text ≥ 28 px at 1080p; a stage label per step; something
changes every 10–20 s; every speed-up labelled. **Wake the model ~15 min before recording** (cold start up to 14 min).

| Time | Voice-over | Screen | On-screen label / caption |
|---|---|---|---|
| **0:00–0:11** Hook | "Expertery: AI that knows your tool. I trained Meta's open Glimmer model on CAD. With no manual, it went from 62 to 96 percent on jobs it had never seen." (30 w) | Live page hero → a rendered part rotating → the 62 → 96 bars snap in | "Expertery · AI that knows your tool." · "62% → 96% · no manual · 100 unseen jobs" |
| **0:11–0:28** Problem | "Out of the box, Glimmer can't do this reliably. The usual fix is a manual pasted into every request: 5,700 words, every time. Or a big cloud model, and your designs leave your building. So I didn't prompt it. I trained it." (42 w) | The real BX prompt scrolling (manual text), prompt-token counter to 14,151 | "Manual in every request: ~5,700 words" · "14,151 prompt tokens per correct part (measured)" |
| **0:28–1:15** How I trained it (the factory) | "Here's the factory. Muse Code built a generator of 2,000 practice parts, each with a hidden correct answer. Glimmer tries every one. A locked cloud box builds its code, and a strict referee compares the result with the real part, within 0.2 percent. When Glimmer fails, it sees its own error and tries again. Still stuck? Meta's Spark Open gives one hint, never code; with those hints, Glimmer solved 52 of 54. Only answers the referee proved correct become lessons: 1,742, with Glimmer's own reasoning. Wrong answers never teach. Then: training, on one GPU, about two hours." (98 w) | Factory diagram lighting up step by step; real factory gallery (results/factory-gallery) with PASS/FAIL ticker; training loss curve 0.63 → 0.32 | Stage labels GENERATE / TRY / REFEREE / TUTOR / LESSONS / TRAIN · "Built entirely on Meta: Glimmer · Spark Open · Muse Code" · "Training: 1 GPU, ~2 h (real run, sped up)" |
| **1:15–1:50** Did it learn? | "Did it learn? On 100 practice jobs it never saw: 62 percent before training, 96 after, with no manual, and crashes dropped from 12 to 1. Then the hard test: 30 hand-made parts, written before training, three tries each. Trained, with no manual: 83 percent. That's level with the untrained model reading a rule card, and 11 points behind the best setup with the full manual, mostly on the hardest parts." (73 w) | Bars 62 → 96 with CI; then exam bars: trained 83.3 · card 85.6 · full manual 94.4, CI whiskers | "100 unseen practice jobs (same generator as training) · +34 pts, 95% CI [+24, +44]" · "Exam: 30 hand-made parts × 3 tries = 90 answers · frozen before training" · "vs card −2.2 [−12, +7] · vs full manual −11 [−24, +1]" |
| **1:50–2:00** Re-hook | "But look at what it sends. 215 prompt tokens per correct part, instead of 14,000. Six and a half times fewer tokens in total." (22 w) | Two prompt boxes side by side: tiny vs the scrolling manual; token bars 3,352 vs 21,823 | "Tokens per correct part: 3,352 vs 21,823 (measured) = 6.5× fewer" |
| **2:00–2:30** Put to work | "Then I put the trained model to work. Type a part: an L-bracket, 80 by 30 by 45 millimetres, two 6-millimetre holes. It writes the code, the box builds and measures it, and it fixes its own mistakes before you see the part. With that self-check, it reaches 92 percent on the exam, level with the full-manual setup." (57 w) | Live-page recorded run: typing → code → build → measurements → PASS → 3D view → STEP | "Real run, Nov 2 · 120 s, sped up 4×" · "With self-check: 92% vs 94%, −2.2 [−11, +6]" |
| **2:30–2:50** Close | "Expertery: AI that knows your tool. Trained only on proven answers. No manual, six and a half times fewer tokens. And it's Meta's open model, so it can run on a GPU you control. Proven on CAD. Try it live." (40 w) | Three vertebrae appear one by one → live page URL | Tagline · 3 vertebrae · URL · "Proven on CAD so far" |

## Live deck (10 slides; headings ≤ 7 words; one point each)
For a live final: play the recorded segments and narrate over them. At most **one** live call (the live page, model
already warm, run cleanly 5× in a row beforehand).

| # | Heading | Content | Time |
|---|---|---|---|
| 1 | **AI that knows your tool.** | Expertery logo; "I trained Meta's Glimmer: 62% → 96%, no manual" | 0:00 |
| 2 | **Every request ships a manual** | The 5,700-word manual as a tall scroll; "14,151 prompt tokens per correct part"; "or your designs leave the building" | 0:11 |
| 3 | **So I trained it instead** | Factory diagram: 2,000 jobs → try → referee → tutor → lessons → train | 0:28 |
| 4 | **Built entirely on Meta** | Three columns: Glimmer (the model I trained) · Spark Open (tutor, hints only, 52/54) · Muse Code (built the factory) | 0:50 |
| 5 | **Wrong answers never teach** | Referee at 0.2%; 1,742 proven lessons; exam guard: 0 lessons touch the exam | 1:05 |
| 6 | **62% → 96%, no manual** | Bars + CI [+24, +44]; crashes 12 → 1; "100 unseen practice jobs" | 1:15 |
| 7 | **Hard exam: 83%, no manual** | Trained 83.3 · card 85.6 (tie) · full manual 94.4; CIs; n = 90 each | 1:30 |
| 8 | **6.5× fewer tokens per part** | Prompt 215 vs 14,151; total 3,352 vs 21,823 | 1:50 |
| 9 | **Put to work: it checks itself** | Recorded run clip; with self-check 92% vs 94% (tie) | 2:00 |
| 10 | **AI that knows your tool.** | 3 vertebrae · live URL · "Proven on CAD. Bring us your tool." | 2:30 |

"What didn't hold" is said inside slide 7 (11 points behind the full manual, mostly hard parts: 73% vs 91%) rather
than as its own slide, so the training story keeps the time. Full list in the README.

## Q&A backups
- **Who wrote the exam?** Not Muse Code and not the trained model: the exam parts and the exam referee were written
  separately (by Claude, disclosed in the README "Who wrote what"), so the AI being tested never writes its own test.
- **Isn't the 96% on easy jobs?** Yes, easier: same generator as the training jobs (different jobs, never trained on).
  That's why the hand-made exam exists; there it's 83% alone, 92% with the self-check.
- **Why not just use the rule card?** On the exam the card gives the same accuracy (85.6 vs 83.3, a tie). Training
  puts that knowledge in the weights: no card or manual to maintain and send with every request.
- **Why behind the full manual on hard parts?** 73% vs 91% on hard parts alone; the self-check loop closes most of it
  (hard 41/45 with the loop, same as the full-manual setup).
- **Could the exam leak into training?** Hand-written before training; a guard checked all 1,742 lessons, 0 refused;
  frozen by sha256 (results/exam-2026-11-02/FREEZE.txt).
- **Is it private?** The weights are open, so it *can* run on your own GPU; the demo runs on Modal for convenience.
- **Is it faster?** Not the claim. The win is no manual and fewer tokens.
- **Beyond CAD?** Not shown yet. Any tool with a checkable result fits the factory; CAD is the one proven.

## If the bracket test lands before recording
Pre-registered in experiments/brackets/PLAN.md (claim X = lower cost per usable part, no quality loss). Use the
plan's own wording, unchanged:
- X holds → add to 1:50–2:00 and slide 8: "On 20 employee-style bracket requests: same quality, N× cheaper per usable part."
- Q holds, CI crosses 1 → "same quality, cheaper on average, not significant on 20 jobs" (README only).
- Q fails → README only, reported as a loss.
State on 2026-11-03: FTX arm has 61 call lines in results/brackets-2026-11-03/FTX/calls.jsonl; AX arm not run.

## Self-review (review-rubric.md, 100 points)
| # | Criterion | Score | Reason |
|---|---|---|---|
| 1 | Fit to the rubric | 13/15 | Depth + Meta tooling carry the training story; Impact rests on tokens + open weights, no real user yet |
| 2 | What it is, fast | 9/10 | Name + "I trained… 62 → 96" in 11 s; "for companies" implied |
| 3 | Concrete problem | 8/10 | Real artifact (the manual, measured prompt tokens), no real person's request |
| 4 | Product working | 13/15 | Factory footage from 0:28, live part at 2:00 (later than ideal, by choice: training is the product story) |
| 5 | Credible numbers | 18/20 | Every number has baseline, n, CI, conditions; weak 53% dropped; the gap to the manual is said out loud |
| 6 | Memorability | 9/10 | Tagline 3×, 3 vertebrae at the close |
| 7 | Truthfulness | 9/10 | "can run", "proven on CAD", dev-set ease disclosed; URL still says "homegrown" |
| 8 | Delivery craft | 8/10 | ≈ 365 words, re-hook at 1:50; not yet rehearsed |
| | **Total** | **87/100** | Ready to record once the fixes below are decided |

Top 3 fixes:
1. **Impact:** finish the bracket test (AX arm + compare) or get one real tester's quote. Never invent one.
2. **Name mismatch:** URL, README, diagram and form still say Expertery.
3. **Footage:** the factory beat needs real footage (gallery, PASS/FAIL ticker, loss curve) cut before recording;
   check results/factory-gallery and results/train-r5f have what's needed.
