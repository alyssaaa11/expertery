# Submission plan: everything still missing (2026-11-02)

**Summary**: The research part is done (exam 83.3%, second look 92.2% vs 94.4%). What is missing is what judges can
touch: a live product, model access, the 3-minute video, the bonus-prize steps, Impact evidence and the form. This
page lists every open item, who does it, and the decisions still waiting for the user.

**Sources**: user review message 2026-11-02 evening (items 1-8); user answers in chat 2026-11-02 ("later, when all other
changes are fixed, we put the focus on the product"; "why?" on model access; "i dont have" an engineer contact);
rubric Impact 30 / Meta tooling 25 / Depth 20 / Demo 25 (kickoff slide, see project.md).

**Last updated**: 2026-11-02 20:00

---

## Deadlines
- verified (user): form due **Wed Nov 4, 9 PM ET = Nov 5, 03:00 CET**; own target **Nov 4, 18:00 CET**.
- verified (user review): Most Viral counts X engagement until **Nov 8**; judging Nov 5-9.

## Done today (2026-11-02)
- README rewritten (Homegrown name, factory, results, what did not hold, lessons, other tools, HerdShot Oct 26-28 with
  report copies in docs/herdshot, Modal/Baseten/Meta usage table, agent section, Oct 26 = after the 12:00 ET kickoff).
- GitHub description + 10 topics (Muse Code). HerdShot repo pushed (69 commits incl. Oct 27 experiments).
- NotebookLM explainer (7:19) kept OUT of the repo (user): ~/Videos/homegrown/. Still in one old commit (user asked
  nothing more; history rewrite not done).

## Open items
| # | Item | Who | Status / next step |
|---|---|---|---|
| 1 | **Live product page** "describe a part → build, check, fix → checked part + picture + STEP" | spec Claude, build Muse Code, test Claude, verifier | decision (user): **do it LAST**, after the other fixes. Plan below. |
| 2 | README section **"Run the trained model"** (page link + one command) | Claude | with item 1 |
| 3 | **Model access** during judging: Modal endpoint up Nov 5-9 (sleeps, pays per use, cap) and/or LoRA on Hugging Face with the Muse licence notice | user decides | user asked "why?" → explained (live check, Open Weights check, "a company can own it"). Undecided. HF needs the user's login (no HF token in envsave); publishing is public + permanent. |
| 4 | **3-minute video**, link at the top of the README | together | after item 1 so it can show the product. NotebookLM version is 7:19 and says "Forge"; a short version must say "92% *with the loop*". |
| 5 | **Most Viral** ($20k): X post with the demo; link in the form | Claude drafts, user approves | after video; `x-post-queue --account alyssa`; engagement counts to Nov 8 |
| 6 | **Open Weights** ($10k): a partner checks the model really runs | — | depends on item 3 (endpoint up during judging) |
| 7 | **Best Agentic** ($5k): the self-check loop described as the agent | Claude | **done** (README "The Homegrown agent") |
| 8 | **Community Vote** ($10k): share the gallery link | user | after submitting |
| 9 | **Impact (30%)**: a real person tries it + a short quote | user | user has no engineer contact. Options below. Never invent a quote. |
| 10 | Submission form | user | by Nov 4 18:00 CET; older draft: [[submission-draft-2026-10-30]] needs the new name + numbers |
| 11 | Old `forge` names in code | — | kept on purpose; README note explains it |

## Item 1: product page plan (hypothesis, not built)
- Page on Modal (CPU web app, sleeps when unused): text box + 3 example parts; live steps (write → build + measure →
  check → DONE or fix, ≤ 3 rounds); 3D picture, measurements, STEP/STL download, the code; below: factory diagram,
  results, GitHub + video links.
- Behind it: web app keeps the model key hidden → trained Glimmer r5f (deploy/modal_forge.py, A100, scale-down 300 s)
  → locked CAD box (cloud_cq) → same loop as the 92% second look (`do_bx_cloud_call`, `--bx-loop`).
- Protection: max builds per hour, daily spending cap, input length limit; "demo paused" when the cap is hit.
- Known weakness: cold start ~3-5 min after idle → page says "waking up the model"; wake it before recording.
- Cost: build ≈ $3 Meta credit, 3-4 h; use ≈ $2.50 per GPU hour of builds. Modal ≈ $72 of $90 used → ≈ $18 left;
  above $90 needs the user's OK.
- **Waiting for the user:** (a) open to anyone (best for Community Vote / X) or passcode (safest for money);
  (b) spending cap for Nov 5-9 (proposed $20).

## Item 9: Impact options (user has no engineer contact)
1. Hackathon Discord / community: post the live page, ask builders to try it (Claude drafts, user sends).
2. CadQuery community (Discord, GitHub discussions): the most relevant testers.
3. The X post doubles as a call for testers (also Most Viral).
4. Muse finds small engineering / 3D-printing businesses on Instagram/Facebook and drafts outreach (user approves).
5. Fallback without a quote: measured cost per correct part (2.7× fewer tokens), the privacy need, and a clearly
   labelled example user story in the video.
- decision (Claude's recommendation, not yet approved): product first, then 1 + 3 on Nov 3; 5 as backup.
- Rule: every public post needs the user's yes; no invented testimonials.
