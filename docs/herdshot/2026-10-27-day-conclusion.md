# HerdShot: conclusion of Oct 27 (day 2 of the hackathon)

Labels: **verified** (checked, with source) / **hypothesis** (not checked yet) / **decision** (a choice, by whom).

## Goal
Pick a hackathon project (submit by Nov 4, 18:00 CET) that is innovative, impactful and built on Meta's Muse models.
HerdShot's starting goal: protect AI agent teams from false facts.

## Relevant findings

### 1. Groupthink / lies in chat: does not happen when the evidence is in the team
- verified: **Test A** (Muse Spark 1.3, 70 runs, $22.92 Meta credit): 0% of honest agents privately believed the
  lie, in all 5 lie types → NO-GO. Every fact was checkable in a file, and agents checked.
  (reports/testA.md)
- verified: **A2** (Claude Haiku, 4 roles: researcher/builder/tester/lead; the researcher has an outdated document, the
  tester holds a clue; neutral prompts): 12.5% of teammates believed the stale value; with 2 agents pushing it
  (majority) also 12.5% → NO-GO, groupthink not shown. With no clue at all, 50% believed it (reasonable).
  (reports/a2.md, experiments/a2/PREREG.md)
- verified: A2 run 1 was void: 71/80 ballots empty because thinking used the whole token limit (400/200); fixed
  with 2000/1500 (run 1 kept in results/raw/a2-r1-invalid). Same bug as the Meta pilot (300 → 1200).
- verified: no agent message mentioned a trick, test or experiment (grep of all A2 run 1 messages).

### 2. Parallel work: agents break each other's work, with every model
- verified: **C1** (two agents change the same small file at once, then `git merge-file`, hidden tests):
  | Model | One agent alone | Two in parallel |
  |---|---|---|
  | Haiku | 15/16 | 4/16 |
  | Sonnet | 16/16 | 8/16 |
  | Opus | 13/16 | 4/16 |
  A stronger model does not fix it. (reports/c1-haiku.md, c1-sonnet.md, c1-opus.md)
- verified: every failure was visible (12/16 git text conflicts, the rest failed visible tests); 0 silent clashes →
  "detect clashes" adds nothing over merge + tests. (C1 PREREG rule: GAP-NOT-SHOWN)
- verified: **C2** (a Haiku "tech lead" writes a shared plan first): 7/16 vs 4/16 → USER-DECIDES (needed ≥12).
  The users task stayed 0/4 (both features change the same lines); config got worse (4 → 2); 5 calls vs 2.
  (reports/c2.md)
- caveat: agents rewrote whole files, which makes text conflicts likely; real agents make small edits that may merge
  cleanly but still be broken. Tasks were tiny (20–40 lines).

### 3. Outside research
- verified: CooperBench (arXiv 2601.13295): ~30% lower success together than alone (swarm wiki, swarm-failure-gaps.md).
- verified: competitors for parallel clashes: **STORM** (arXiv 2605.20563, May 2026: write-time conflict handling,
  +18.7 on Commit0-Lite) and **AgentRoom** (arXiv 2608.23740, Aug 2026: CRDT shared workspace with claim tools).
- verified: competitors near "stale facts": **STALE** (arXiv 2605.06527: benchmark, single agent's personal memory,
  best model 55.2%) and **LatticeMind** (arXiv 2608.08236: multi-agent memory store resolving conflicting claims at
  write time, 0.97 vs 0.61). Neither tracks or repairs the work already built on a wrong fact.
- verified: **Judgment Labs** (LinkedIn post by Alex Shan, sent by the user late Oct 27; 306 reactions, $32M seed+A,
  Greenoaks/Lightspeed): "continuous improvement platform for long-horizon agents": monitors signals in agent
  traces, background agents flag suspicious patterns, search, offline evals. It monitors and flags; it does not
  trace a wrong fact across a swarm or repair the work built on it. Shows strong market interest in long-horizon
  agent reliability; judges may see it as similar, so the pitch must state the difference.
- hypothesis: ChatGPT Deep Research (mini, 8 min, 0 exportable sources, LOW): top unsolved problems are
  misalignment, bad task splitting, shared-state clashes, long-horizon decay, weak verification; all worse with
  length and agent count; not fixed by bigger models alone. Saved:
  ~/swarms/herdshot/herdshot-wiki/raw/knowledge/2026-10-27-unsolved-multiagent-problems-deep-research-mini.md
- verified: real fleet incidents (shared/knowledge/real-outbreaks.md): 5 cases, all honest stale/misread facts living
  in files and briefs (one rule file misled ~34 sessions); not lies in chat.

### 4. Direction (where the day ended)
- decision (user): Hivey Evolve rejected as not innovative or impactful enough.
- decision (user): the "team manager / router" (split or not, model per role) rejected: easy to build, not impactful.
- hypothesis (current lead): **HerdShot = repair what a swarm built on a fact that turned out to be wrong.** It
  follows a stale or wrong fact as it travels between agents, sessions and files over time, finds every piece of
  work built on it, and repairs it. Pitch: "Memory tools fix what an agent remembers. HerdShot fixes what a swarm
  built on it." The user's point: the competitors (STALE, LatticeMind) are about memory, not this.
- hypothesis: the problems that matter appear on complex, long-horizon tasks (user's point, supported by the deep
  research); short toy tasks are solved by today's models.
- warning: the swarm's earlier novelty note (HERDSHOT.md) lists "recall of work built on a lie" in ~7 existing
  projects; novelty must be the combination (swarm-level spread over time + recall + repair + real fleet + Muse).

## Money and limits
- Meta: $24.49 spent today (test A + pilots); budget locked at day = $0 (caps.toml, commit 225e579).
- Claude API credit: $1.44 spent, $98.56 left (claude-api-guard ledger). Key reference passed via
  CLAUDE_API_GUARD_KEY_ID; the guard's config file still has no key set.
- Claude plan: weekly limit at 85%+, resets Oct 28 09:00 (Europe/Madrid).
- Baseten: $0 spent. Codex (ChatGPT plan) built the A2/C1/C2 runners.

## Open questions
1. Is the "repair what was built on a wrong fact" idea new enough? Check the ~7 projects in the swarm's
   novelty notes (shared/knowledge/novelty.md) one by one.
2. How often does a stale fact really spread in the user's swarms, and how much work is built on it? Measure from
   the local logs (1,714 bus messages, 984 transcripts), free.
3. Does it hold on complex, long-horizon tasks with Muse models, not only toy tasks?
4. What is the surprising, visual demo (e.g. a real swarm replay where one stale fact spreads and is repaired)?

## Next step (Oct 28, after 09:00)
1. Novelty check against the ~7 projects + STALE + LatticeMind + Judgment Labs (about 30 min, free).
2. Count stale-fact spread in the real fleet logs (about 30 min, free, local).
3. If both pass: write pre-registered rules, then a first Muse test (needs the user's OK for Meta spend).
4. Decision deadline: Oct 29 evening.

## Housekeeping (not done, waiting for the user)
- Nothing from today is committed in ~/projects/herdshot: experiments/{a2,c1,c2}, tests/test_{a2,c1,c2}.py,
  reports/results for A2/C1/C2, results/pilot.json, viz/live/replay_testA_s0.jsonl. Tests pass (A2 4, C1 6, C2 9).
- Two local servers still run (dashboard :8790, replay :8792); harmless, can be stopped.
- The swarm wiki's coordinator still has to ingest the two raw files written today (wiki rule: only the coordinator
  writes wiki/). The HerdShot Mac Calendar and HERDSHOT-WEEK-PLAN.md still describe the old plan (test A gates).
- Fake-run outputs were moved to the job tmp folder, not left in the repo.
