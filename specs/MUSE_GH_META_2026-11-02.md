# Muse Code task: set the GitHub description and topics (2026-11-02)

Repo: ~/projects/forge, GitHub repo alyssaaa11/expertery (PRIVATE). The user asked for this.
Use the `gh` CLI. Do exactly this, nothing else:
1. gh repo edit alyssaaa11/expertery --description "Homegrown: turn a small open model into a private expert on your tool, learning only from answers a referee proved correct. Muse Glimmer 30B on CAD: 53% to 83% alone, 92% with a self-check loop."
2. gh repo edit alyssaaa11/expertery --add-topic meta-hackathon --add-topic muse-glimmer --add-topic muse-spark --add-topic fine-tuning --add-topic lora --add-topic cadquery --add-topic cad --add-topic ai-agents --add-topic self-improving --add-topic modal
3. Verify: gh repo view alyssaaa11/expertery --json description,repositoryTopics,visibility and print it.
Rules: do not change visibility, files, branches or anything else. Report the verify output and any error verbatim.
