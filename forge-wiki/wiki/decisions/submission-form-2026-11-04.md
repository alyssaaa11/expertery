# Submission form text (DRAFT, 2026-11-04)

**Summary**: Copy-paste answers for the Cerebral Valley form. Replaces submission-draft-2026-10-30 (old name Forge,
Wonder as teacher, blanks). Every number is checked against the result files (pre-submission-review-2026-11-04).
Nothing here is submitted; the user submits.

**Status**: decision (user, 2026-11-04): deliver the project first, then enter the bonus prizes. Rewritten 2026-11-04 ~12:40 after agents-17 review (lead with the tie, label 53%, one-try 83% = rule card, Spark-answers finding, v0 builds only the exam). Blanks: [VIDEO URL],
[X POST URL] (after the video).

---

**Project name:** Expertery

**Tagline:** AI that knows your tool: a small open model trained only on answers a referee proved correct.

**Track:** Indie Developer · Push the Frontier

**Links:**
- Live demo: https://expertery.vercel.app
- GitHub: https://github.com/alyssaaa11/expertery (must be PUBLIC before submitting)
- Video (3 min): [VIDEO URL]

**Description (short):**
Expertery turns Meta's open Muse Glimmer 30B into a proven expert on one company tool. On a hand-made 30-part CAD exam
it never saw, the trained Glimmer **ties the best setup with no manual and 2.7× fewer tokens** (92% with its self-check loop vs 94%,
a statistical tie: −2.2 points, 95% CI −11 to +6); the best setup needs a 3,240-word manual in every prompt. In one try with no manual it scores 83%, which ties
plain Glimmer + a one-page rule card (85.6%); for scale, plain Glimmer with a short prompt scored 53% (one try, Oct 28).

How: Glimmer practises 2,000 CAD jobs, a locked cloud box really builds every answer, and a strict referee keeps only
the correct ones. When Glimmer is stuck, Muse Spark Open gives one hint, never the code. Only proven answers become
lessons, so wrong answers never teach. The unexpected finding: training Glimmer on Spark Open's answers made it worse
(38% and 48% vs 52% untrained, on our 60-job dev set); training on its own referee-checked answers worked.

The product: a company installs Expertery in its own cloud account with one command. In v0, an exam agent turns the
company's past work into a locked exam that a person reviews, and the model is tested on it before anyone trusts it.
Practice jobs still come from our CAD job generator; making practice jobs from a company's own past work is not built
yet.

**How it uses Meta AI:**
- **Muse Glimmer 30B (open weights)** is the student: LoRA-trained on 1,722 referee-checked lessons and served with
  vLLM. It runs live in the demo and in the product's self-check loop.
- **Muse Spark Open (open weights, on Baseten)** is the tutor: one short hint, no code, on the 76 jobs Glimmer could
  not solve (it solved 52 of the 54 usable hints). It is also the reader in the exam agent.
- **Muse Code** wrote the product code from written specs: the factory, cloud box, referee, training pipeline, live
  demo, installer and exam agent. It also pushed the repository. Every build round's log is in `results/`.

**Technical depth:**
- Rules written before every test, an exam run once and frozen with sha256, paired bootstrap 95% CIs, and a guard
  that checks no lesson touches the exam.
- Honest results: the original pre-registered claim ("as good as the best setup in one try") failed, and the README
  says so. The 92% is a labelled second look. Training on a bigger model's answers made Glimmer worse (38%, 48% vs 52%).
  Training on its own checked answers worked.
- An agentic self-check loop (write → build → measure → fix, up to 3 rounds) that never sees the answer. It rescued
  12 of 90 exam answers.

**Challenges:** Our first idea (HerdShot) died on day 2, when our own test showed agents already reject false facts.
The first two training rounds made the model worse. Studying where Glimmer itself failed (28 of 47 crashes came from
one missing function) turned it around.

**Bonus prizes entered:**
- Best Build on Meta Open Weights: Glimmer 30B is trained and runs live; Spark Open tutors and reads.
- Best Agentic Use-Case: the self-check loop and the exam agent.
- Most Viral: [X POST URL]
- Community Vote: share the gallery link after submitting.

**Team:** Alyssa Sancho (solo).

**Disclosure:** Claude (Anthropic) wrote the specs, the exams and referees, and small disclosed fixes; Claude is never
inside the product. Details: docs/WHO-WROTE-WHAT.md.
