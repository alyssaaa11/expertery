# LLM Wiki: Forge

The knowledge base for **Forge**, the user's Meta hackathon project (Oct 26 – Nov 4, 2026). Forge trains a private
AI agent that becomes a pro at a company's tool: Muse Spark (the teacher) practises the tool, CadQuery checks the
real results, and Glimmer (the student) is LoRA-trained on the correct attempts only.

## Scope rules
- Forge only. HerdShot (the earlier project, dropped Oct 28) has its own wiki at `~/swarms/herdshot/herdshot-wiki`.
  Mention it only as background, by path, never with `[[links]]` into it.
- Knowledge only: no runnable code, no secrets. Code and results live in `~/projects/forge` (link them, don't copy).
- Label claims **verified** (with source) / **hypothesis** / **decision**.
- Every lesson says how it was learned and how to check it again.
- The budget is $30 max for the whole project (user, 2026-10-28). Record the real cost of every paid step.

## Folders
```
raw/knowledge/     -- immutable sources (research reports); never modify
wiki/findings/     -- facts learned and test results
wiki/decisions/    -- decisions with who/when/why
wiki/lessons/      -- reusable lessons
wiki/assets/       -- diagrams (PNG to embed, HTML to open)
index.md           -- catalog of every page
log.md             -- append-only operations log
```

## Workflow
New source → put it in `raw/`, write or update the `wiki/` pages it touches, add `[[links]]`, update `index.md`,
and append to `log.md` (`## [YYYY-MM-DD HH:MM] action | page`).
