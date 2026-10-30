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

## Where the technical versions are
[[how-training-changes-weights-2026-10-30]] (training with details), [[forge-diagrams]] (all diagrams), [[project]].
