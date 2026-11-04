# Submission form text (DRAFT, 2026-11-04)

**Summary**: Copy-paste answers for the Cerebral Valley form. Replaces submission-draft-2026-10-30 (old name Forge,
Wonder as teacher, blanks). Every number is checked against the result files (pre-submission-review-2026-11-04).
Nothing here is submitted; the user submits.

**Status**: decision (user, 2026-11-04): deliver the project first, then enter the bonus prizes. Blanks: [VIDEO URL],
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
General AI invents functions your tool doesn't have. In our own runs, untrained Muse Glimmer 30B crashed 64 times on
CadQuery functions that don't exist. Expertery is a factory that turns Meta's open Glimmer into an expert on one
tool. Glimmer practises 2,000 jobs, a locked cloud box really builds every answer, and a strict referee keeps only the
correct ones. When Glimmer is stuck, Muse Spark Open gives one hint, never the code. Only proven answers become
lessons, so wrong answers never teach. After LoRA training, Glimmer needs no manual. On a hand-made 30-part CAD exam it
never saw, it scored 83% in one try (plain Glimmer: 53%) and 92% with its self-check loop. That ties the best setup
(94%, which needs a 3,240-word manual in every prompt) with 2.7× fewer tokens. Companies install it in their own cloud
account with one command, and an exam agent turns their past work into a locked test before they trust the model.

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
