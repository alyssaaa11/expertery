# Forge in simple words (start here if a page uses words you don't know)

**Summary**: the whole project explained with a school comparison, two diagrams in everyday words, and a word list
that translates every technical word used in the other pages. Made 2026-10-30 because the user said "I don't
understand any diagram, the words I didn't see before".

**Last updated**: 2026-10-30

---

## The story
- **Glimmer** = a smart student. Knows a lot about drawing machine parts, but is slow and needs a thick instruction
  book open every time. It is small enough to live inside a company.
- **Spark** = the teacher. Much bigger and better, but too big for a company to keep in its own building.
- **The checker** = an examiner with the answer key. It builds each part and measures it; only perfect parts count.
- **Goal**: after practice, Glimmer gets as many right answers as before, but without the book, so it is much
  faster and cheaper.

## How Glimmer learns
![[assets/diagrams/forge-simple-how-glimmer-learns.png]]

## The plan from today to the exam
![[assets/diagrams/forge-simple-plan.png]]

## Word list (technical word → simple meaning)
| Word in other pages | Simple meaning |
|---|---|
| Model | the AI "brain" (Glimmer, Spark) |
| Weights | the billions of numbers inside the brain that hold what it knows |
| Training | practice that changes some of those numbers so it gets better |
| LoRA / patch / adapter | the small notebook added to the brain; only it changes in training |
| Merge | gluing the notebook into the brain for good |
| Loss | the "how wrong was the guess" score; lower is better |
| Gradient | the direction to change the notebook so the score gets better |
| Learning rate | how big each small change is |
| Epoch | one full pass through all the practice problems (we do 2) |
| Token | a small piece of a word; models read and write in tokens; more tokens = more cost and time |
| Prompt | what we send to the model: the instructions and the problem |
| Manual | the thick instruction book (about 5,700 tokens) put into every prompt today |
| Referee / grader / checker | the program that builds the part and measures it against the right answer |
| 1e-6 / 0.2% | how strict the checker is: 1e-6 = practically perfect; 0.2% = almost perfect |
| Teacher / student | Spark teaches, Glimmer learns |
| Factory | the machine that makes practice problems and keeps only perfect solutions |
| Dev set / dev check | the mock test: 20 problems Glimmer never practised on |
| Final exam | the real test: 30 problems kept hidden from training |
| k = 3 | each problem is answered 3 times, to reduce luck |
| B-max / BX | the old way at its best: Glimmer + book + hints + examples + retries (95% right) |
| B2 | Glimmer + book + one hint, one try (88% right) |
| FT | the trained Glimmer (fine-tuned) |
| Bars a-d | the 4 pass rules for the real exam, written before we see results |
| Pre-registered | rules written down before running, so we can't change them after |
| Bootstrap / CI | a way to measure how sure we are about a difference |
| GPU (A100, H100) | the rented computer chip that runs the model (about $2.50-4 per hour) |
| Modal / Baseten | the cloud companies where Glimmer and Spark run |
| Muse Code | Meta's coding agent; it writes all our programs |
| Verifier | another AI agent that checks every plan and result for mistakes |
| Cloud box / sandbox | a locked computer in the cloud where model-written code runs, never on your Mac |
| CadQuery / FreeCAD | the CAD programs (tools to draw machine parts with code) |

## Questions the user asked (Oct 30), with the answers
**What is LoRA?** The small notebook stuck onto Glimmer's brain ("Low-Rank Adaptation"). The brain (about 30 billion
numbers) is frozen; only the notebook (about 105 million numbers, 1 for every 300) learns. When Glimmer answers it uses
brain + notebook together: the brain gives its normal answer, the notebook adds a small correction. At the end the
notebook is glued in ("merge"), because the program that runs Glimmer crashed when loading it separately (test run).

**What is that notebook?** A file full of numbers, not words (in the test run: `adapter_model.safetensors`; about
200 MB this time, an estimate). Glimmer's brain is 52 layers of big tables of numbers; a word becomes a list of numbers
that passes through table after table. The notebook puts a small extra table next to each big table; the two results
are added. Each small table is really two very thin tables (6,700 × 16 and 16 × 20,000 instead of 6,700 × 20,000):
"16" = it can learn 16 kinds of adjustment per table. Enough for habits, too little to rewrite what Glimmer knows.
What it learned can't be read, only seen in Glimmer's answers (like bike riding living in your muscles).

**Why freeze the brain?**
1. Memory: changing a number needs 3-4 extra copies of notes; for 30 billion numbers that is hundreds of GB (several
   big GPUs). For the notebook only, it fits one rented GPU (even then, one 8,192-token example used all 80 GB).
2. Forgetting: ~150 CAD examples would overwrite other skills; Glimmer is already 87-95% right, so keep it safe.
3. Memorising: a whole brain could memorise 150 answers; the small notebook only has room for general habits.
4. Safe and cheap: empty notebook = exactly the old Glimmer; throw it away to undo; ~20 min, $2-3.

**Is each correct Spark solution a notebook?** No: there is ONE notebook. Each correct solution is one practice page
(~150 pages). Glimmer goes through all pages twice; every page makes a tiny change to the same notebook, so it learns
what the pages have in common (the general skill). More notebooks only make sense per company or per tool (Company A
and Company B each get their own notebook for the same Glimmer: Forge's privacy idea). Wrong solutions are thrown
away by the checker, because one wrong page teaches a wrong habit.

**Do we have to build the loop?** The learning loop is already built and tested (Oct 29 test run: "how wrong" score
1.03 → 0.33, the trained Glimmer solved a new problem in 3 seconds). Still to build: the practice-page maker
(factory), the locked cloud box + checker for CadQuery, the exam runner, the B-max finisher, the scoreboard, and
last the demo viewer.

## Where the technical versions are
[[how-training-changes-weights-2026-10-30]] (training with details), [[forge-diagrams]] (all diagrams), [[project]].
