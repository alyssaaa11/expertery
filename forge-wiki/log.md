# Forge wiki: log

## [2026-10-28 14:05] create | forge-wiki (user: "why are u using the project herdshot if is forge, u are mixing contexts")
- Moved the Forge pages out of ~/swarms/herdshot/herdshot-wiki: forge-design, forge-questions, forge-diagrams,
  final-pick-research, forge-plan, 6 diagrams, and the 4 final-pick raw reports. Links into HerdShot pages became plain
  path references. Forge lessons collected into wiki/lessons/lessons.md.

## [2026-10-28 14:15] create | glimmer-test-1-2026-10-28 (user: "do a test of glimmer"); Forge deploy script + secret forge-glimmer created

## [2026-10-28 14:40] update | forge-plan-2026-10-28 (first test: 15+15 jobs; Spark Open on Baseten credits)

## [2026-10-28 16:55] update | forge-diagrams (diagram 7 final plan) + forge-questions (Spark Open vs 1.3)

## [2026-10-28 17:45] update | lessons (overlap check, blind rebuild); first test prep: 33 jobs, self-test 33/33, blind 33/33, manual.md, RUNNER_SPEC.md

## [2026-10-28 18:00] update | forge-plan (Baseten $100 credit per user; card on file; check after dry run)

## [2026-10-28 17:25] update | forge-plan (Muse Code built runner, ~$0.51; e2e 33/33)

## [2026-10-28 17:55] update | forge-plan (dry run OK, spend ≈ $1.56) + lesson (modal app stop -y)

## [2026-10-28 18:50] create | first-test-2026-10-28 (main run results; decision = grey zone, waiting for the user)

## [2026-10-28 19:00] decision | first-test → GO (user, from grey zone)

## [2026-10-28 20:30] update | first-test (3 of B's failures are position-only; B2 cheap-fix arm proposed)

## [2026-10-28 21:00] create/update | status (START HERE), tools-and-services, value-and-market, factory-plan; lessons +8; superseded cost estimate and old schedule marked; first-test 'how the exam was built'; index rewritten (user: "put it in the wiki so nothing is forgotten")

## [2026-10-28 21:05] update | status (GitHub repo meta-hackathon, private, published by Muse Code, no leaks) + lesson (rules page)

## [2026-10-28 21:55] update | status (B2 cancelled by the user; private-tool AcmeCAD direction proposed)

## [2026-10-28 22:00] update | factory-plan (day-by-day plan for the AcmeCAD direction, proposed)
- 2026-10-28 22:30 decision: fictional space company Quillon Orbital Works, private tool Keel, company dashboard; draft spec company/SPEC.md (user review pending)
- 2026-10-28 22:20 verified: Muse Code built company/ (Keel, manual, 8 examples, dashboard); SELFTEST 35/35 re-run by Claude; 21 calls, ~$0.40 Meta; dashboard opened in Chrome. Note: request statuses (AI draft / Gauge PASS) are sample data until the assistant really runs.
- 2026-10-28 ~22:20 verified: Keel v2 built by Muse Code (~$0.80, selftest 88/88, spot-checks exact); v2 exam experiments/keel-exam-v2: selftest 90/90, blind rebuild 30/30; v1 exam kept as history. Verifier audit requested.
- 2026-10-28 23:14 verified: Keel v2 pilot (M1, M7, H9, Spark, k=1) 3/3 PASS, $0.03, no harness errors (results/keel-v2-pilot). 23:15 main run started (user yes).
- 2026-10-28 23:30 verified: Keel v2 main run: B Glimmer+manual 97.8%, C Spark 100% → rule 2 NO ROOM. Clean (0 harness/PermissionError). See [[keel-v2-baseline-2026-10-28]].
- 2026-10-28 23:39 filed: findings/quillon-keel-build-2026-10-28 (build method), 8 new lessons, tools-and-services evening facts.
- 2026-10-29 00:15 filed: decisions/night-prep-2026-10-28 (5 free night tasks: Spark context 1M from catalog, training recipe, verifier pre-review READY WITH FIXES, Tern/Skua drafts self-test 90/90, B2 sandbox spec), raw/training-recipe-research-2026-10-28.
- 2026-10-29 verified: coverage audit 83% (k=5) → Option A skipped by the user's noon rule. Page findings/coverage-audit-2026-10-29.
- 2026-10-29 decision (user): new goal = same quality, many times cheaper and faster, private. Page decisions/new-goal-2026-10-29.

## [2026-10-29] research | learning guide: training weights + verifiers
- Added raw: raw/knowledge/research-training-from-verified-data-2026-10-29.md, research-verifier-design-2026-10-29.md, research-cad-code-papers-2026-10-29.md (subagent reports, unedited)
- Created: wiki/findings/learn-training-and-verifiers-2026-10-29.md (3 key papers re-read in full: 2505.19713, 2605.07807, 2610.25812)
- Updated: wiki/status.md open questions 2 and 5; index.md
- 2026-10-29 12:32 verified: step-2 baseline: BR 87%, B2 88%, BX 95% (79/90 ran); Modal ≈ $4.5. Page findings/bmax-baseline-2026-10-29.
- 2026-10-29 13:49 verified: training smoke test (≈$1.06): train OK, 8k OOM, vLLM LoRA crash, merge OK, strict PASS. Page findings/training-smoke-2026-10-29.

## [2026-10-29 night] plan | training + final exam prepared, not run
- Created: experiments/final/PLAN.md, MUSE_SPEC.md; forge-wiki/wiki/assets/diagrams/forge-training-exam-plan.png, forge-how-training.png (assets/diagrams);
  findings/how-training-changes-weights-2026-10-30; decisions/submission-draft-2026-10-30, morning-brief-2026-10-30
- decision (user): budget $50; finish BX to 30 jobs (step 6a). Verifier: pre-build READY WITH 5 EDITS (applied 1861990),
  delta READY WITH 3 EDITS (applied 9602647).
- verified: Spark Open 816B/42B active, ≥ 700 GB VRAM (HF card); Mac 24 GB vs MLX Glimmer ≥ 48 GB recommended.
- Fresh direction review: 6/10, rebalance toward Impact + Demo. Lessons +8. README status refreshed.

## [2026-10-30] fix | diagrams visible in Obsidian + project page
- Moved the 2 new diagrams from attachments/ (HTML only, not shown in Obsidian) to wiki/assets/diagrams/ with PNGs (8, 9 in forge-diagrams); embedded in the training page; created wiki/project.md (one-page overview).

## [2026-10-30] explain | simple words
- Created wiki/forge-in-simple-words.md (story, word list) + 2 simple diagrams (10, 11 in forge-diagrams). Lesson added.

## [2026-10-30 ~09:30] save | before the user cleared the chat
- forge-in-simple-words: added the user's questions + answers (LoRA, the notebook, why freeze, one notebook vs pages, what is built).
- status: "Where we stopped" (factory first, demo last; Muse round 1 ready, NOT started; launch recipe; open recommendations).
- project: where we are. experiments/final/MUSE_ROUND1.md committed (not run).


## [2026-10-30] build | factory (Muse round 1) + learning loop + verifier
- verified: Muse round 1 (e24a9a7): cloud_cq box + grader, generator/make_jobs (200 jobs), teacher, patterns.py v0,
  exam guard on box, cached_tokens fix; ≈ $2.4. Claude re-checks all pass.
- decision (user): learning loop, suggest-and-approve (SPEC §4, 27e8800 missed the file; written in e24a9a7, verifier items dac893d).
- verified: verifier FAIL for pilot / GO for fix round (forge-factory-build-2026-10-30, 4/7/5); round 1b prompt ready, not launched.
- 2026-10-30 verified: Muse r1b (d304368, ≈ $0.96) fixed F1/F2/F4 + gallery; verifier FAIL for pilot (G1 text≠reference in
  4 families), GO for cheap Modal checks with filtered inputs. Round 1c prompt ready (00394af), not launched.

## [2026-10-30 afternoon] factory ready (pending verifier) + repo readiness
- verified: Muse r1c (5edd84a) + r1d (ff7f3a4); cloud checks: REFS 200/200 + 30/30, regrade 199 same, blind rebuilds 10/10 + 10/10.
- decision (user): precise volumes in factory grader; no Wonder output in training; updates via hivey/Slack.
- Repo readiness 1-7 (f692227, 3f392d6), verifier reviewing.
- 2026-10-30 verified: factory pilot 19/20 (95%), $0.52, 0 patterns (6274420); main run proposed (160 jobs).
- 2026-10-30 verified: factory main 148/157 (94%) $4.38; training set 167 records; Muse round 2 built $2.40 (fd1d32c). Money ≈ $43.6.
- 2026-10-30 17:00 verified: dev check STOP: trained Glimmer 38.3% (23/60) at 0.2%; pilot D1-D3 0/3. Exam untouched.

## [2026-10-30 21:40] ingest | training experiments + diagnosis
- raw: second-opinion brief/answer, superintel task/answer (training diagnosis).
- Created: wiki/findings/training-experiments-2026-10-30.md. Updated: status (now), scoreboard §4, lessons (+6), index.
- verified: R1 38.3%, R3 48.3%, untrained 51.7% on dev; decision pending: cheap check, then self-distillation.

## [2026-10-30 22:40] save | before the user cleared the chat
- status NOW: rule-card check running (R3+card, then A+card), reading pre-registered, next steps, working rules.
- Claude small fix bb5e080 (FORGE_RULE_CARD) disclosed in README.

## [2026-11-01 16:45] update | R5 round (Oct 31 – Nov 1)
- new: findings/r5-own-answers-training-2026-11-01, decisions/r5-decisions-2026-10-31; indexed the 10-31 findings pages.
- status NOW rewritten: trained model ready, baselines 62/96 on R5D, next = FT test (user OK), Spark hints, final training.
- lessons +10 (card beats training, held-out check, own answers, filter dry-run, token caps, billing month, prompt ranges, announce runs, stand-in agents).
- scoreboard §4 (R5 held-out baselines).

## 2026-11-01 18:30
- r5 dev 94/100 (no card); Spark hints 54/76 usable, retries solved 52/54; r5f mix 1,742 (46 tutoring); r5f training started.
- new: findings/r5-final-spark-guided-2026-11-01; status NOW rewritten.

## 2026-11-02 00:10
- r5f training done (1,722 rows incl. 42 tutoring, 431 steps, loss 0.32, merged /vol/r5f/merged); guard took 2.5 h.
- saved older untracked records (Oct 29-30 checks, dashboards, watch script) to git.

## 2026-11-02 10:15
- dev 2: r5f 96/100 (crashes 1, hint mentions 0) → pre-registered pick = r5f for the exam.

## 2026-11-02 11:40
- EXAM (one-shot): r5f 75/90 = 83.3%; A+card 85.6%; B2 87.8%; BX 94.4%; bars a,b FAIL, c,d PASS. Status NOW rewritten.

## 2026-11-02 ~12:30
- superintel advice (~/agents/superintel/reports/forge-product-mode-advice_2026-11-02.md): product mode as DEMO only (~3 h, $1-2; retry+picker tops at pass@3 27/30, A+card also 27); checker = deterministic checks + Glimmer judge (not Jev: non-Meta); framing 53% -> 83% no manual, 3.4k tok/17 s vs 21.8k/44 s; optional FT inside BX fix loop as labelled second look; spend rest on video/README/install. Awaiting user decision.

## 2026-11-02 15:10
- SECOND LOOK FTX (r5f + BX fix loop): 83/90 = 92.2%, ≈ BX (−2.2 [−11.1, +5.6]) PASS; 2.7× fewer tokens; same time per answer.

## 2026-11-02 18:05
- decision (user): project renamed **Homegrown** (was Forge). Visible text (README title + note, wiki status/index note,
  video explainer source, factory diagram) renamed; internal code, Modal apps/volumes/secrets, env vars, file names and
  frozen exam files keep `forge` on purpose (no breakage; exam sha256 evidence valid). README full rewrite still to do.

## 2026-11-02 20:00
- new: decisions/submission-plan-2026-11-02 (all open items: product page plan, model access, video, bonus prizes, Impact options, form). Status TODO points to it.
- lessons +5 (loop value, generator-made test overstates, freeze vs later edits, guard time, uncommitted proof).

## [2026-11-03 00:20] create | wiki/findings/live-demo-2026-11-02.md
Live demo launched (Vercel page + Modal engine), first real build, settings, money, page decisions. Updated status.md
(NOW + TODO), decisions/submission-plan-2026-11-02.md (items 1-2 done), lessons.md (+8 lessons with how learned),
index.md.

## [2026-11-03 11:30] create | public copy ~/projects/homegrown (user: "i want to keep the other things so i should do a duplicate")
- decision (user): keep this repo complete and private; publish a slim duplicate instead.
- verified: `~/projects/homegrown-publish/make_public_copy.sh` rebuilds it from this repo: full dated history (353 commits)
  with the NotebookLM video, the personal email (also as commit author → GitHub noreply), `~/` and the Modal
  workspace name scrubbed (check in the script prints 0); one cleanup commit removes `remove.txt` paths (1791 → 480
  files); `fix_readme.py` fixes README links. Kept tests 475 passed, 1 skipped (2026-11-03 11:27).
- lesson (how learned): `b2-hint/`, `bmax/` and `smoke/` look like dead ends but the exam runner and training pipeline
  read them; removing them broke 13 tests. Check: rebuild with tests, never trust a path list by name alone.
- lesson (how learned): CAD sandbox tests fail with "Operation not permitted .venv/pyvenv.cfg" when `.venv` is a
  symlink to another repo's venv; the sandbox only reads the repo's own `.venv`. Fix: `cp -cR` (copy-on-write).
- Next: re-run the script after the last forge commit; GitHub repo creation + push via Muse Code after the user's yes.

## [2026-11-03 evening] create | docs/video/pitch-expertry-2026-11-03.md (winning-pitch skill)
- decision (user, 2026-11-03): pitch uses the name **Expertry** (page headline "AI that knows your tool."); **no founder
  sentence**; format = 3-min video script + 10-slide live deck.
- verified: every number in the script traced to results/exam2-ftx-2026-11-02/compare_ftx.json (92.2 vs 94.4, CI
  [−11.1, +5.6], 7,946 vs 21,823 tokens, 266 vs 301 s) and README (1,742 lessons, 52/54, L-bracket run 120 s).
- lesson (how learned): the first draft said "Muse Code wrote the referee"; README "Who wrote what" (line ~185) shows the
  exam referee was written by Claude on purpose, Muse wrote the factory/cloud box. Check: grep README "Who wrote what"
  before any authorship line in a pitch.
- open: Expertry vs "homegrown" in the URL/README/diagram/form; bracket test AX arm not run; 53% baseline is k=1 from an
  earlier session. Self-review 85/100.
- decision (user, 2026-11-03, v2): "the main is that i trained a model" → pitch rebuilt: training is the headline,
  the self-check loop is one product beat. Lead number = dev 62 → 96 (compare_dev.json, +34 [24, 44]); exam alone 83.3
  (tie with card 85.6; −11.1 vs full manual); 6.5× fewer tokens (compare_bars.json). 53% baseline and wall-clock/$
  dropped. Self-review 87/100.

## [2026-11-03 11:50] decision | project renamed Homegrown → Experty (user, README scope only for now)
- verified: README in 518f364 says Experty; name note covers Forge → Homegrown → Experty; URLs, file names, live page
  (homegrown-factory.vercel.app) keep old names. Public copy rebuilt (480 files, 475 tests passed, links OK).
- open: live page text and its address still say Homegrown (page is Muse-built; change via Muse Code if the user wants).

## [2026-11-03 12:10] decision | name spelled **Expertry** (matches the live site title); README no longer mentions Homegrown (user)
- Supersedes the 11:50 "Experty" entry (typo in chat; the live site says Expertry 7×, checked with curl).
- verified: 3312198: README note says only "first called Forge"; diagram files renamed docs/video/expertry-factory.*, PNG
  re-captured (headless Chrome, 2048×1320, scale 1); only the live address keeps "homegrown". Public copy rebuilt, links OK.
- open: the live page HTML has `<meta name="hg-api">` = the Modal URL containing the workspace name (visible in page source).

## [2026-11-03 13:05] decision + deploy | name **Expertery**; live page https://expertery.vercel.app (user)
- Supersedes the 12:10 "Expertry" entry. Name check by digital-marketer: "Expertery" free (.com/.ai/.io unregistered);
  "Expertry" is a German HR-software company.
- verified (96ee6fa): site text, tests (app/tests 109 passed), README, diagram (re-captured) say Expertery.
- verified: Vercel domain expertery.vercel.app added via `vercel domains add`, old homegrown-factory.vercel.app removed
  via `vercel api DELETE /v9/projects/<id>/domains/<domain>` (user: don't keep the old one; it now returns 404).
  Engine homegrown-web redeployed with the same baked settings (read from `modal app logs homegrown-web`, line
  "homegrown-web config") + ALLOWED_ORIGINS=https://expertery.vercel.app; OPTIONS preflight new origin 200, old 400.
- lesson (how learned): `vercel domains rm` only knows custom domains; project *.vercel.app domains need the API.
  Check: `vercel api "/v9/projects/<id>/domains?teamId=<team>"` lists them.
- open: page source still shows the engine URL with the Modal workspace name (meta hg-api).

## [2026-11-03 afternoon] video draft v2 | ~/Videos/expertery/submission (HyperFrames, outside the repo)
- decision (user): the video must explain why it fits Push the Frontier and why it matters (I trained the weights):
  why, how, evidence, people. Done as a new 20 s "frontier" part (prompting = skill outside in a 5,700-word manual;
  training = skill inside the weights, 1,742 proven lessons) + a "who it's for" close (people who build in CAD, 8M
  SOLIDWORKS/3DEXPERIENCE users from the brief; next: tools with a checkable answer). Total 2:48.
- decision (user, demo-findings page): on-screen step labels say the benefit, not the step name (≤18 words).
- verified: `npx hyperframes check` 0 errors / 0 warnings; snapshots reviewed (method: `snapshot --at <t>` per scene,
  read the contact sheet, fix overlaps the layout audit misses inside the caption zone).
- open: screen recording, Expertery's own M12 render (paid cloud build), one real self-fix trace, voice-over, music.

## [2026-11-03 13:45] update | public duplicate renamed ~/projects/expertery (user)
- verified: make_public_copy.sh now builds ~/projects/expertery; in the copy, README clone line + app/web GitHub links
  point to github.com/alyssaaa11/expertery (the private repo stays meta-hackathon). 488 files, 357 commits, 475 tests passed.
- verified (gitleaks full history, 13:28): no real secrets; 47k hits are SVG/number noise, fake test emails, fixture "SECRET-ABC-123".
- open: the LIVE page (deployed from this repo's app/web) still links to the private meta-hackathon repo → 404 for
  judges. Fix after the public repo exists: point app/web links to github.com/alyssaaa11/expertery and redeploy Vercel.

## [2026-11-03 14:00] publish | private GitHub repo https://github.com/alyssaaa11/expertery (user: "private for now")
- verified: Muse Code (muse exec, --disable-sandbox, spec ~/projects/homegrown-publish/muse/PUSH_EXPERTERY_2026-11-03.md,
  log push-expertery.jsonl there) created it PRIVATE + pushed main; origin/main == local HEAD a40adfe; 6 calls, 149k in
  (99k cached) / 1.4k out tokens.
- open: (1) switch to PUBLIC before submitting (user's yes); (2) a rebuild by make_public_copy.sh rewrites the last
  commit → the next push to expertery needs --force (new repo, nobody depends on it; still ask); (3) live page GitHub
  links still point to private meta-hackathon.

## [2026-11-03 14:30] fix | no links to the private repo anywhere public (user: "dont link it to the private meta hackaton")
- verified: live page GitHub links → github.com/alyssaaa11/expertery (2879cc7, Vercel redeployed, curl shows 3 links, 0 meta-hackathon).
- verified: make_public_copy.sh also rewrites `alyssaaa11/expertery` → `alyssaaa11/expertery` in all history; rebuilt
  copy 475 tests passed; Muse Code pushed it with --force-with-lease over a40adfe → GitHub main == 5d4e089, still PRIVATE.
- lesson (how learned): filter-repo drops a commit that becomes empty after replace-text (2879cc7 vanished from the
  copy; 357 = 357 commits). Check: compare `rev-list --count` and grep the content, not only the commit list.

## 2026-11-03 competitor review
- verified: evaluated MARKOV (Glimmer GRPO, BFCL 0.63→0.725); see wiki/findings/competitor-markov-2026-11-03.md
- verified: read #push-the-frontier (121 msgs, read-only); see wiki/findings/competition-push-the-frontier-2026-11-03.md

## [2026-11-04 00:30] ingest | bracket test, Expertery v0 installer + exam agent, positioning decisions
- new: wiki/findings/bracket-workflow-test-2026-11-03.md, wiki/findings/expertery-installer-2026-11-03.md,
  wiki/decisions/positioning-and-pitch-2026-11-03.md; 4 lessons appended (zsh modifiers, shared model app, real
  install, reader separates wording from model errors); index updated.


## [2026-11-04 09:45] review | pre-submission deep review
- new: wiki/findings/pre-submission-review-2026-11-04.md (repo PRIVATE + 14 commits behind, no video render, dead
  #video link, README cites missing folders, stale form draft, 9 live tries left; all spot-checked numbers match).

## [2026-11-04 ~09:45] fix + publish | README/page numbers, public copy trimmed, Muse push, form draft (user)
- verified: README fixes (cea0b1d): manual = 3,240 words (≈ 5,700 tokens), not "5,700-word"; 83% (official) and 92%
  (second look, loop) labelled, 53% moved to a "for scale" line; lessons chain 1,882 + 42 → −228 card-quoting = 1,696
  → +46 tutoring = 1,742 → −20 too long = 1,722 trained; 109 app tests; money to Nov 4 (Modal ≈ $81, Baseten ≈ $16);
  installer section; HerdShot + "who wrote what" shortened (full list docs/WHO-WROTE-WHAT.md). Build period Oct 27 (user).
- verified: page wording (manual size, factory step 02 = "Glimmer tries / Spark hints", 92% labelled with the loop),
  app tests 109 passed, Vercel redeployed, curl shows the 3 new strings.
- verified: remove.txt + fix_readme.py extended (Muse logs of removed experiments, unfinished bracket test, v0
  exam-agent run); rebuilt copy 527 files, 373 commits, 475 + 39 tests passed, 0 private strings, README links OK.
- verified: Muse Code force-pushed (--force-with-lease over 5d4e089) → GitHub main = 5c542b4, still PRIVATE
  (spec homegrown-publish/muse/REPUSH_EXPERTERY_2026-11-04.md; 8 calls, 215k in / 161k cached).
- new: wiki/decisions/submission-form-2026-11-04.md (form text; blanks = video URL, X post URL).
- open: switch repo PUBLIC (user's yes); HerdShot's first commit is Oct 26 while the README build period says Oct 27;
  video voice + fixes; page "3-min video" link still #video until the video URL exists.
- verified: 2026-11-04 re-read both channels (read-only); update in competition-push-the-frontier-2026-11-03.md

## [2026-11-04 ~10:15] check | "new demo rule" (live product, no slides) NOT verified; official start Oct 26
- verified: cerebralvalley.ai/e/meta-ai-developer-hackathon.md (curl, ~10:15): "When: Oct 26, 12:00 PM – Nov 4, 9:00 PM
  (EST)"; "Oct 26: Hackathon begins with kickoff livestream"; "Oct 27 – Nov 4: Live workshops". No video-format rule
  on the public page. details/submit pages need login (curl returns the same 68,860-byte shell).
- open: #announcements not read (surfagent Chrome is not logged into Discord). User to check before the video is final.
- open: README says "build period Oct 27 - Nov 4" (user, 2026-11-04 morning); the official start is Oct 26 → asked user.
- lesson (how learned): `tr` is a shell function here (`mv "$@" ~/.Trash`; `type tr`); a `| tr -d '/'` in a pipe ran
  `mv -d / ~/.Trash`, which failed only because mv has no -d. Check: `type tr` before any pipe; use sed/python instead.

## [2026-11-04 ~10:55] video | v4 re-voiced and re-cut (user): ~/Videos/expertery/Expertery-submission-v4.mp4 (2:54)
- Peppy Stella (HeyGen orca, speed 1.1), music m1, impact-first story, "8 million users" removed (unverified source),
  frozen stretches 16 → 1 (voice over it). Details + checks: ~/Videos/expertery/submission-v4/REVIEW.md. Not uploaded.
