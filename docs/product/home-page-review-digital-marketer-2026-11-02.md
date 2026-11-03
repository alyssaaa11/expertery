# Expertery home page: review by digital-marketer (2026-11-02)

Reviewed: `home-page-draft-2026-11-02.md` (v1) against `README.md`. This is advice only. The draft was not edited and nothing was posted.
Sources: the digital-marketer wiki (`~/Obsidian-wikis/digital-marketer`), cited as `[[page]]`. Neil Patel pages are
expert opinion, and Starter Story and creator pages are founder or speaker claims. When the wiki doesn't cover a point, I say so.
All honesty limits from the draft are kept, and I add four more (§5).

## Verdict in one paragraph

The direction is right: a private specialist, real parts instead of AI imagery, and "we publish what didn't work".
Three things would stop a company owner from thinking "I want this for my company":
1. The hero doesn't say what tool it works on.
2. The proof sits in block 5, which most visitors never reach.
3. Two lines claim more than the build shows: "never leaves your company", and "53% → 83%" shown without the rule card's 85.6%.

Fix those three, put the demo second, and make the last ask a qualifying "bring it to your tool" form, not a waitlist.

---

## (1) Hero and section order

**What the wiki says a hero must do.** Above the fold, a stranger has to learn three things: what it is, whether it's
for them, and whether to trust it. Proof goes right next to the claim it supports
([[np-why-98-of-websites-dont-make-money-its-not-the-design]]: "Specificity is trust. Vagueness is friction.").
"The bolder the claim, the closer the proof" ([[np-20-years-of-marketing-knowledge-in-10-minutes]]).
Neil Patel also says most visitors never scroll past the second or third block (speaker claim, no source given).
A one-liner should state what the product does before why it matters, avoid jargon, and describe the outcome rather than the tech ([[sm-best-way-to-launch-your-startup-yc]]).

**The current hero against those three questions:**

| Question | Current hero | Problem |
|---|---|---|
| What is it? | "Your own AI expert. Trained on your tools." | "AI expert" is generic. Nothing says which tools, and only CAD is proven. |
| Is it for me? | "your company" | It doesn't say which companies fit: ones whose tool gives answers you can check automatically. |
| Can I trust it? | "checks every part it builds" | There's no number. All the proof sits in block 5. |

**Three headline and subline options.** Each one keeps the honesty limits.

**A. Specialist + checked work (my pick).** It answers all three questions in the first block and is the most honest.
> **Your tool's own AI specialist. Trained only on work that passed inspection.**
> Expertery turns Meta's open Glimmer model into a specialist on one tool. It practises, a strict referee keeps only
> correct answers, and the finished model runs privately. Proven on CAD: 92% on a hand-made exam, close to the best
> setup's 94%, with no manual and 2.7× fewer tokens.

**B. Industrial (closest to the "steel, GoPro" brief).**
> **Build your AI the way you build parts: inspect everything.**
> Expertery writes practice jobs, runs every answer in a locked box, and trains Meta's open Glimmer only on what
> passes. The finished model runs privately and measures every part before it hands it over. Proven on CAD.

**C. Privacy-led, if Alyssa wants privacy first.**
> **The AI expert your company gets to keep.**
> Cloud assistants are smart, but your tools and data leave your building. Expertery trains an open Meta model on your
> tool, learns only from answers a referee proved correct, and the finished model runs where you choose.
> Proven on CAD: 92% on a hand-made exam with its self-check loop.

Next to any of them, put **one real rendered part** with its measurements and the teal PASS stamp. That's the
"real artifact, not a mockup" rule from our own posting system ([[small-account-posting-system]]).
Add a byline "Built on Meta's open models (Glimmer, Spark Open, Muse Code)" in the hero rather than the footer,
because Meta tooling is worth 25 rubric points and judges skim.

**Section order: recommended change.** The current order puts the mechanism (diagram) before the outcome (demo, proof).
An owner buys the outcome first, and the wiki puts the outcome demo above the fold
([[conversion-optimization]], from the SaaS video-funnel source: a demo showing specific results lowers the perceived risk).

| # | Draft v1 | Recommended |
|---|---|---|
| 1 | Hero | Hero (option A/B/C + one rendered part + PASS stamp + Meta byline) |
| 2 | Problem, 3 lines | **Live demo**, opening with a recorded run that plays immediately (see §5, wait time) |
| 3 | Factory diagram | **Proof, 3 numbers** + "What didn't hold" link |
| 4 | Live demo | Factory diagram (for the engineers and judges who want depth) |
| 5 | Proof | **New: "Your tool next: what it takes"** (see below) |
| 6 | Bring it to your company | CTA form (see §4) |
| 7 | Footer | Footer |

The 3-line problem block can go: option C already contains it, and options A/B imply it. If you keep it, keep it to
one line under the hero.

**The new block 5 answers the owner's last doubt at the moment it comes up** ([[np-why-98-of-websites-dont-make-money-its-not-the-design]]:
answer hesitation on the page, not in a footer FAQ). Everything in it comes from the README's "For other tools" section and is already verified:
- Three parts change for each tool: a job generator, a sandbox that runs answers, and a referee that decides right or wrong.
- The best exam is 30–100 of your own past jobs with known correct results, never shown to the factory.
- The final training run took about 2 hours and about $10 of GPU time (README, step 6).
- Status, said plainly: proven on CAD only.

## (2) Lead with privacy or the self-checking factory?

**Recommendation:** use the privacy need as the "is this for me?" line, and lead the proof with self-checking.
Option A does both in one block.

Reasons:
- Privacy says who the buyer is, but every local-LLM vendor already says "private AI". It isn't specific, and the wiki
  says specificity is what earns trust ([[np-why-98-of-websites-dont-make-money-its-not-the-design]]).
- Checked work is the part only Expertery can show: the referee, the exam, and "wrong answers never teach". It also comes with numbers.
- Privacy is where the honesty risk is (§5, first item). If the hero leads on privacy, the hero's main promise is the
  one the current build proves least.

Not in the wiki: there is no evidence comparing privacy-led and quality-led headlines for B2B AI buyers. This is my judgment.
To test it cheaply, use two versions of the X post (one per angle) and compare replies and clicks, without changing the page.

## (3) Steel + one teal accent, industrial, not "AI"

**Yes, with two fixes.**
- **Supported by the wiki:**
  - Readers punish the generic AI look. Neil Patel lists "AI slop" as a 2026 trend
    ([[np-the-8-trends-im-betting-my-entire-marketing-strategy-on-in-2026]]).
  - A 2026 X source says AI-slop posts bring "ghost followers" who never buy ([[x-twitter-marketing]]).
  - The designer-quality study in [[instagram-design-playbook]] found the same pattern: one display family and one
    accent colour (11 of 14 accounts used a bold grotesk). That study is Instagram, not web, so treat it as a pointer only.
  - Teal is already Alyssa's accent ([[alyssa-personal-brand]]), so the page and her posts will match.
- **The wiki's warning:** design isn't what converts. Clarity and proof are
  ([[np-20-years-of-marketing-knowledge-in-10-minutes]], [[np-why-98-of-websites-dont-make-money-its-not-the-design]]).
  Spend the effort on the hero copy and the demo, not the palette.
- **Contrast check** (WCAG ratios I computed from the hex values):

  | Pair | Ratio | Verdict |
  |---|---|---|
  | Light steel #C9D1D9 text on graphite #1C2126 | 10.5:1 | fine |
  | Steel #8A96A3 on graphite | 5.4:1 | fine for secondary text |
  | Teal #1FA39A on graphite | 5.2:1 | fine |
  | **White text on a teal button** | **3.1:1** | **fails AA for normal text** |
  | Graphite text on a teal button | 5.2:1 | use this |

- **GoPro as a reference:** what transfers is "show the real output, not the brand". GoPro sells with footage, so
  Expertery should sell with rendered parts, measurements and the code. Not in the wiki: industrial web design for
  engineering buyers. This point is my judgment.

## (4) Best CTA with no customers yet

**Use one primary CTA per screen, and change the ask as the visitor moves down the page.**

1. **Hero and demo: "Try it live" (primary).** Judges score the demo (25 points), and technical buyers try before they buy
   ([[developer-marketing]]). Make "See how the factory works" a text link rather than a second button, so the click isn't split
   ([[conversion-optimization]]: one call to action).
2. **Right after a demo part finishes: "Want this for your tool?"** This is the free-tool pattern: show the result first,
   then make the ask while the result is still on screen ([[conversion-optimization]], Greg Isenberg source).
3. **Bottom: a 3-field form, "Bring Expertery to your tool".** It asks which tool, whether they have ~30 past jobs with
   known correct results (yes / no / not sure), and an email address.
   - Don't use **"Contact us"**: it's vague and has no reason attached.
   - Don't use a **plain waitlist**: it shows interest, not commitment from a buyer ([[satellite-monitoring]],
     [[idea-validation]]: every validation case in the wiki counts money or a dated commitment). YC also warns that
     waitlists you sit on convert badly ([[sm-best-way-to-launch-your-startup-yc]]).
   - The form qualifies leads, gives you real Impact evidence ("N companies described their tool"; report only real
     counts), and gives you the list for discovery calls after the hackathon ([[sm-if-i-started-a-saas-in-2026-0-to-1000-users]]:
     50 calls aiming at prepayment).

## (5) What hurts conversion or sounds like overclaiming

Ranked by risk. Items 1–4 are new honesty limits I'd add to the draft's list.

1. **"It never leaves your company" (hero).** As built, the factory and the live demo run on Modal, and the Spark
   teacher ran on Baseten (README, "Where Modal, Baseten and Meta were used"). A judge or buyer who reads the README will
   see the gap. Say what's true: "the finished model runs privately" or "runs where you choose". Use "runs entirely in your own
   cloud" only after someone checks it (hypothesis: possible, since every model in the factory is open, but it hasn't been tested, and the
   Glimmer/Spark Open licence terms haven't been checked).
2. **"53% → 83%" without the rule card.** The README shows plain Glimmer with a one-page rule card scoring **85.6%**,
   above the 83.3% one-try score. "53 → 83" suggests training made a 30-point gain that a card mostly matches. The
   claim that holds is the README's own: **92% with the loop, about as good as the best setup (94%), with no 5,700-word manual and 2.7×
   fewer tokens.** Make that the lead number. If 53% appears, put the card's 85.6% beside it and keep the k=1 footnote.
3. **"Checks every part it builds" next to "a strict referee keeps only correct work".** The referee compares parts
   with known answers during training only. The live box checks its own measurements against the numbers in the request,
   without a reference. Don't let the page suggest that delivered parts are verified correct (92% means about 1 in 12 exam parts was still
   wrong). Safe wording: "measures every part before it hands it over".
4. **"Factories decay over months" (draft's must-feel #2).** This framing invites the months-long self-improvement
   claim, which the draft itself forbids. Use "built to re-run and re-check itself" and drop "decay".
5. **Demo wait time.** With the loop, a hard exam part took about 266 s on average (README). A visitor who
   watches a spinner for 4 minutes leaves. Play a **recorded run** first (labelled "recorded run"), then let them start
   their own with live step updates (writing → building → measuring → fixing, round 1/3) and a time estimate. Hypothesis: simple
   parts are faster, so check this on the deployed demo.
6. **What happens when the spending cap is hit ("demo paused").** If the cap hits during judging (Nov 5–9), the main CTA leads nowhere.
   The paused state should show the recorded run, the 3-minute video, and the bring-it-to-your-tool form.
7. **"Trained on your tools" (plural)** when only CAD is proven. Use "your tool" and "Proven on CAD" in the hero, which
   is the README's own status line.
8. **Jargon for owners:** "tokens", "k=1", "STEP/STL", "LoRA". Keep them in the proof footnotes and in the demo's download
   buttons, not in headlines. Example: "2.7× fewer tokens per correct part (same model, so roughly 2.7× less compute)".
   The "roughly less compute" part is my inference and should be checked before it's used.
9. **Keep "we publish what didn't work too"**, and link it straight to the README's "What did not hold". With no testimonials (correctly), this is the strongest
   trust signal on the page ([[developer-marketing]]: under-promise, over-deliver, publish honest post-mortems).
10. **Traffic match.** The Most Viral X post will bring AI builders, not company owners. A page that shows the demo
    early works for both groups ([[np-20-years-of-marketing-knowledge-in-10-minutes]]: match the page to the traffic source).

## Not covered by the wiki (judgment, labelled)
- Privacy-led versus quality-led messaging for B2B AI buyers (§2).
- Industrial or engineering web aesthetics, and the GoPro reference (§3).
- What hackathon judges respond to. The rubric weights come from the draft, not the wiki.

## Claims in this review, by type
- verified: rule card 85.6%, one-try 83.3%, loop 92.2%, best setup 94.4%, 2.7× tokens, ~266 s per answer with the loop, ~2 h and ~$10
  training run, Modal and Baseten usage, "proven on CAD only" (source: `~/projects/forge/README.md`, read 2026-11-02).
- verified: contrast ratios (WCAG relative-luminance formula, computed from the draft's hex values).
- hypothesis: self-hosting the whole factory in a customer's cloud, the licence terms, demo speed on simple parts, and tokens ≈ compute.
- decision (Alyssa's, kept): the buyer is a company owner or engineering lead; the steel look; the demo is open with caps; no testimonials.
