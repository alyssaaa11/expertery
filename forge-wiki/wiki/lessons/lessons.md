# Forge lessons

**Summary**: Reusable lessons from building Forge, each with how it was learned and how to check it again.

**Last updated**: 2026-10-28

---

- **Run the "cheap fix" baseline before building** (Oct 28). How learned: HerdShot test A died because agents that
  read the files rejected the lie (70/70); the final-pick research found the same risk for Forge (docs, skills or
  harness adaptation may close the gap without fine-tuning, 2607.08938). Check: list the cheapest non-novel fix as an
  arm of every first test, and stop if it already meets the bar. See [[final-pick-research-2026-10-28]].
- **A trivial test proves the referee, not the need** (Oct 28). How learned: the user asked "if you already made the
  cube, how do you know Forge is needed?" Check: first tests need easy, medium and hard levels, and the GO rule must
  look at medium and hard.
- **The too-easy / too-hard window** (Oct 28, reasoning, not yet measured): a teacher that never succeeds gives no
  training data, and one that always succeeds leaves no gap. Check: measure the teacher's pass rate and aim for
  about 30–70%.
- **Keep one project per directory, app, secret and wiki** (Oct 28). How learned: the user said "you are mixing
  contexts" when the Forge Glimmer test ran on HerdShot's Modal app, secret, storage and wiki. Check: before running
  anything, `grep -rn herdshot ~/projects/forge` should only find background references.
- **Check the setup before asking the user to do it** (Oct 28): `~/.modal.toml` already existed when I asked the user
  to run `modal setup`. Check: test the end state first (`modal profile current`, `modal app list`).
- **New system Python can lack wheels** (Oct 28): Python 3.15.2 has no CadQuery/OCP wheels. Fix and check:
  `uv venv --python 3.12`, then run a real build + measurement (20 mm cube = 7607.3 mm³).
- **Check whether model weights are gated before asking for a token** (Oct 28): Glimmer is not gated. Check:
  `curl -s https://huggingface.co/api/models/<id>` and read `gated`.
- **A free hello-world before paid GPU work** (Oct 28): Modal's square(42) (CPU, under a cent) proved login and remote
  runs. Check: `modal run get_started.py` prints 1764.
- **Meta's vLLM image needs `python` on PATH for Modal** (Oct 28). How learned: the first deploy failed during the
  image build ("unable to determine the version of Python", ~$0, no GPU started), and Modal's docs say images need
  `python` + `pip` on PATH. Fix: `setup_dockerfile_commands=['RUN ln -sf "$(command -v python3)" /usr/local/bin/python ...']`;
  the second deploy succeeded in 168 s. Check: `modal deploy` prints "App deployed".
- **Archify reruns: use a new `--out-dir`** (Oct 28): a second `finalize` into the same folder failed with
  `viewer/evidence-path-conflict`. Check: rerun with `--out-dir <folder>/review-N`; never delete old evidence.
