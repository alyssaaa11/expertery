# Homegrown: teaching a small private AI model a new skill from its own checked work

Built for the Meta hackathon (Indie track, "Push the Frontier"), October 26 – November 4, 2026.

## The problem
Companies want an AI that is good at THEIR tools, but big general models are expensive, and sending private designs to
an outside model is a risk. The usual fix is a long manual pasted into every prompt (thousands of words each time).
Homegrown asks: can a small open model learn the skill itself, so it needs no manual and can run privately?

## The skill we chose
Writing CAD code: turning a text description of a mechanical part ("a spool with a 6.8 mm bore and a wire slot")
into CadQuery Python code that builds the exact 3D part. It is easy to check: the built part either matches the
correct part or it does not.

## The team (models and tools)
- Glimmer (Meta's open 30B model): the STUDENT. It writes every answer and is the model we train.
- Spark Open (Meta, on Baseten): the TUTOR. It only gives short hints, never code.
- The Referee: an exact geometry check (CadQuery). It builds the part and compares it with the correct part. It cannot
  be talked into accepting a wrong answer.
- Muse Code (Meta's coding agent): built the factory code from written specs.
- Claude: wrote the specs and plans and checked the results; it is never inside the product.

## The Homegrown factory, step by step
1. Job generator: makes 2,000 practice jobs in 10 part families (spools, pipe tees, brackets, funnels, bezels...),
   each with a hidden correct part. 100 extra jobs are locked away as a secret test.
2. First try: Glimmer, with a one-page rule card, writes code for all 2,000 jobs. A cloud box runs each program, and
   the Referee checks it. 1,882 are correct, 118 are wrong.
3. Self-fix: for the 118 wrong ones, Glimmer sees only its own error or its own part's measurements (never the correct
   answer) and tries again. 42 are fixed; 76 are still wrong.
4. Spark tutor: for the 76 hardest, Spark looks at the job and Glimmer's attempt and writes one short hint, no code
   (for example: "your slot runs from Z -1 to 4.2 instead of 0 to 3.2"). With the hint, Glimmer solved 52 of 54.
5. Lessons: only answers the Referee proved correct become lessons: 1,742 lessons, each with Glimmer's own thinking
   and code. A safety check confirmed that no lesson touches the secret exam. KEY IDEA: wrong answers never teach.
6. Training: a small add-on (LoRA) is trained on Glimmer with these lessons, about 2 hours on one cloud GPU, about $10.
   The trained model needs no manual and no rule card.
7. Tests on problems it never saw.

## The results (measured honestly, rules written down before each test)
- 100 secret practice-style jobs: plain Glimmer 62/100, trained Glimmer 96/100 (no card).
- The real exam: 30 hand-made parts (15 medium, 15 hard), never used to build anything, 3 tries each, run once:
  - Plain Glimmer: 53%
  - Trained Glimmer, one try: 83% (the official exam score)
  - Trained Glimmer with a self-check loop: 92% (a labelled second look)
  - The best setup before Homegrown (Glimmer + a 5,700-word manual + the same loop): 94%
- So with the loop, the trained model ties the best setup (92% vs 94%, within chance), with no manual and about 2.7 times
  fewer tokens per correct part.
- Honest limits: on one try it does not beat the manual; it is not faster per answer; the 92% is a second look at the
  same exam.

## Why the loop helps
The Homegrown box runs the part and measures it (size, volume, number of pieces). If the code crashes, Glimmer sees the error
and fixes it. If the measurements do not match the job, Glimmer fixes the part. Up to 3 rounds, then DONE. It never sees
the correct answer, so this works in a real product. In the exam, the loop rescued 12 answers: 4 after crashes and 8
after Glimmer noticed its part did not match.

## The Homegrown box (the product)
Describe a part in words. The trained Glimmer writes the code, the box builds and measures it, Glimmer fixes its own
mistakes, and you get a checked CAD part. Small, private, and cheap to run.

## What a company would do
Swap in its own tool and its own job generator, run the same factory, and get a private model trained on its own tool,
learning only from answers that a referee proved correct.
