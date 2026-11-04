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
| 1 | **Live product page** "describe a part → build, check, fix → checked part + picture + STEP" | spec Claude, build Muse Code, test Claude, verifier | **LIVE 2026-11-02: https://homegrown-factory.vercel.app** ([[live-demo-2026-11-02]]). |
| 2 | README section **"Run the trained model"** (page link + one command) | Claude | **done**: README "Try it live" + "Live demo" section |
| 3 | **Model access** during judging: Modal endpoint up Nov 5-9 (sleeps, pays per use, cap) and/or LoRA on Hugging Face with the Muse licence notice | user decides | user asked "why?" → explained (live check, Open Weights check, "a company can own it"). Undecided. HF needs the user's login (no HF token in envsave); publishing is public + permanent. |
| 4 | **3-minute video**, link at the top of the README | together | **Script + live deck drafted 2026-11-03: docs/video/pitch-expertry-2026-11-03.md (name Expertry, user).** After item 1 so it can show the product. NotebookLM version is 7:19 and says "Forge"; a short version must say "92% *with the loop*". |
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
- decision (user, 2026-11-02 evening): (a) **open to anyone who has the link**: no passcode, not listed or advertised beyond our own posts; the build limits and spending cap stay on.
- **Waiting for the user:**
  (b) spending cap for Nov 5-9 (proposed $20).

### Home page message (user, 2026-11-02 evening, dictated)
- decision (user): the home page must make a company owner think "I want this factory for my company".
- decision (user): the main selling point is **privacy**. A cloud assistant is very smart, but your company's private tools and data
  go to the provider. Homegrown trains a private, autonomous assistant that lives inside your company.
- decision (user): second point: the factory **keeps checking and improving itself**, so it doesn't decay over months.
- hypothesis (Claude): honesty limits. (1) Don't claim that Anthropic or any provider trains on company data: business API
  terms often say they don't. Say "your tools and data leave your building" instead. (2) "Improves by itself over months" is
  not tested. Proven: one factory run (practice jobs → teacher → strict referee → training). Say "built to re-run and
  re-check itself" and show the referee gate, not months of improvement.

- decision (user, 2026-11-02 evening): brand colour = **steel** (a strong, industrial colour, like GoPro's style; the
  dictation also said "teal"). The page must not look like generic AI ("this is not AI talking"): it must feel like a real
  industrial product that companies want in order to become more powerful.
- decision (user, 2026-11-02 later): brand colour = **teal** (main colour); steel/graphite only as the background and lines.
- hypothesis (Claude, exact shades not yet approved): graphite #1C2126 background, steel #8A96A3 / light steel #C9D1D9 text and
  lines, one teal accent #1FA39A for buttons and "PASS". No purple gradients, sparkles or glowing AI orbs. Use real
  rendered parts and the measurements as the visuals, with plain industrial type.

- decision (user, 2026-11-02 evening): page style = like the FYNSEC Dribbble shot (dark frame, light card, large refined type, 3D object), **with movement**; the logo must represent the product. Rejected: plain dark/steel v1 and cinematic factory-photo v2 ("too boring, too simple").
- hypothesis (Claude): mockup v3 at ~/projects/forge/docs/product/mockup/index.html (v1, v2 kept beside it): Gemini 3D object (bracket on teal glass layers, an illustration, not a Homegrown output), logo = hex nut with a teal sprout. digital-marketer review: docs/product/home-page-review-digital-marketer-2026-11-02.md.

### Product build log (2026-11-02 evening)
- decision (user, "ok"/"yes okay yes"): build with Muse Code; the demo is **live with a daily cap** (not recorded-only). The $20/day value still needs an explicit yes before deploy.
- verified: Muse P1 page (2c6a339, ~17 calls) matches mockup v3; Claude checked desktop, the demo flow and phone layout via headless Chrome/CDP (scripts in the job tmp, method: mobile emulation 390 px, element-overflow scan).
- verified: Muse P2 backend (2faf9d9, 62 calls). Claude fixes (disclosed): the loop continues after a build (FTX self-check round); phone CSS; static mount last.
- verified: verifier NO-GO W1-W4 (report ~/agents/verifier/reports/forge-web-backend-2026-11-02.md): mount order, status probe boots the A100, uncharged failed builds, timeout leaves model running. Muse P2b fix round running (specs/MUSE_PRODUCT_P2B_PROMPT.md).
- decision (user, 2026-11-02 ~21:15, supersedes the $20/day 'ok'): **$15 TOTAL** for the live demo (Modal; ~$72/$90 used per wiki count, recheck with `modal billing` before deploy); **1 free live try per visitor**, recorded demo always available; page shows '≈ N free live tries left' (Muse P2c). Earlier 'ok' (~21:00): DAILY_CAP_USD = 20 (superseded); run the high-vs-xhigh check (factory practice jobs, not the exam). Deploy starts with xhigh (the measured 92% setup) until the check says otherwise.
- decision (user, 2026-11-02 ~22:20): form leads stay ONLY in Modal storage (Dict homegrown-leads, created at first deploy); no email/Slack notification. Claude reads them on request and reports to the user's personal Gmail (address kept out of the repo, user).
- decision (user, 2026-11-02 ~22:00, replaces "2 tries"): **1 free live try per visitor IP**; $15 TOTAL, no daily cap; NOT going live yet ("no go yet"). Verifier GO on 7cb32a2. Steps: docs/product/DEPLOY.md.
- verified (modal billing summary, 2026-11-02): Oct $37.47 + Nov $34.49 ≈ $72 used, all credits, $0 billed.
- lesson (how learned): `envsave get` needs the es_ opaque key; two Muse launches failed with "empty API key" until the help text showed it. Check: `envsave get <name>` returns empty.

## Item 9: Impact options (user has no engineer contact)
1. Hackathon Discord / community: post the live page, ask builders to try it (Claude drafts, user sends).
2. CadQuery community (Discord, GitHub discussions): the most relevant testers.
3. The X post doubles as a call for testers (also Most Viral).
4. Muse finds small engineering / 3D-printing businesses on Instagram/Facebook and drafts outreach (user approves).
5. Fallback without a quote: measured cost per correct part (2.7× fewer tokens), the privacy need, and a clearly
   labelled example user story in the video.
- decision (Claude's recommendation, not yet approved): product first, then 1 + 3 on Nov 3; 5 as backup.
- Rule: every public post needs the user's yes; no invented testimonials.
