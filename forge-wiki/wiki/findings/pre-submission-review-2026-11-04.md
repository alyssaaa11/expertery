# Pre-submission review (2026-11-04 09:30 CET)

**Summary**: Deep review before submitting Expertery. Research and numbers are solid (a judge-style spot-check matched
every number). What is missing is packaging: no rendered video, a public repo that is still private and behind, a
stale form draft, a dead video link on the live page, and README references to folders the public copy lacks.

**Sources**: commands run 2026-11-04 09:25-09:45 CET (below); independent judge-style review (Claude Sonnet subagent,
read-only, on ~/projects/expertery + live page); wiki status.md, submission-plan-2026-11-02.md,
positioning-and-pitch-2026-11-03.md; rules in ~/swarms/herdshot/HERDSHOT.md § Hackathon rules.

---

## Goal
Submit by Nov 4 18:00 CET (own target); hard deadline Nov 5 03:00 CET (9 PM ET). Rules: public repo that opens
logged-out, 3-min video of only what was built, bonus prizes called out in the form.

## Relevant findings
- verified: GitHub alyssaaa11/expertery is **PRIVATE**, last push 2026-11-03 12:48 UTC (`gh repo view`).
- verified: the public copy ~/projects/expertery stops at the README lesson commit (59593a6 in forge); forge has **14
  newer commits** (installer adf0af9, exam agent v0.2 abe554a, brackets fixes) → public README/repo lack the
  installer and exam agent (`git log`). remove.txt only drops company/ and dashboard/, so a rebuild includes them.
- verified: **no final video render**. ~/Videos/expertery/submission = v3 picture (2:21, 7 scenes), voice clips
  assets/voice/vo-00..28.wav (Nov 3 17:19) wired into index.html; REVIEW.md: "full MP4 render: not rendered yet";
  music not done. Own voice was the plan (VOICEOVER.md); hypothesis: the wav clips are a generated stand-in.
- verified: live page links "3-min video" to `#video` (app/web/index.html:100, :145), no element has id="video" → dead.
- verified: README cites experiments/keel-exam, thinking/, option-a/, freecad/ and results/blind-rebuild*; none exist in
  the public copy (they exist in forge). Judge also flagged README:273 freecad manual bullet.
- verified: README:14 says build period "Oct 27 - Nov 4"; rules and README:122 say Oct 26.
- verified (judge spot-check): 83.3/92.2/94.4, 3,352/7,946/21,823 tokens, CIs, 85.6% A+card, 62/96/96, 53% (16/30)
  all match their result files. app/tests has 109 tests, README says 106.
- hypothesis (judge): README headline mixes unlike numbers (53% = k=1 earlier session, short prompt; 92% = second
  look with the loop + xhigh). Label both; page index.html:69 shows 92% without "with the self-check loop".
- verified: README "lessons (1,742)" vs video "1,722 checked lessons" — both true (1,742 in the mix, 1,722 trained
  after 20 length drops); say which one in README.
- verified: live engine answers /api/status: state waking, **tries_left 9**, so ≈ $6 of the $15 cap is left
  for judging Nov 5-9 + Community Vote. Note: that status call fired one page-load warm-up (WAKE_USD charged).
- verified: Modal billing Nov $43.18 + Oct $37.47 ≈ **$80.6 of the $90** credit cap; $0 billed.
- verified: submission-draft-2026-10-30.md is stale (name Forge, Wonder as teacher, blanks). No X post drafted (~/X/posts).
- verified: page source meta hg-api shows the Modal URL with the workspace name (open since 11-03).
- judge scores (hypothesis, one reader): Impact 6, Meta tooling 8, Depth 8, Demo 5 (no video). No Streamlit,
  secrets or personal emails found.

## Open questions (user decides)
1. Voice: your own voice, or the existing clips?
2. Video host (YouTube unlisted/public) + link in README, page, form.
3. OK to rebuild + force-push the public copy, then switch it PUBLIC?
4. Live demo cap: keep $15 (9 tries) or raise (Modal room ≈ $9 under $90)?
5. Open Weights: publish the LoRA on Hugging Face or rely on the live endpoint?
6. X post text + approval (Most Viral counts to Nov 8).

## Next step (order)
1. Video: render MP4 → watch it once → upload → link. 2. README fixes (list above) in forge → rebuild public copy →
push → PUBLIC → logged-out check. 3. Fix page video link, redeploy Vercel. 4. Form text (new). 5. X post. 6. Submit
before 18:00 CET; never in the last hour.
