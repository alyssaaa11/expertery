"""Serve Muse Glimmer 30B (Meta open weights) with vLLM on Modal, as an OpenAI-compatible endpoint, for Forge.

Recipe from dev.meta.ai/docs/muse-glimmer/vllm (official vLLM image and parsers), in Modal's web-server pattern.
Adapted on 2026-10-28 from the earlier HerdShot deploy script, with Forge's own app, secret and volumes, so the two
projects never share state.

    modal deploy deploy/modal_glimmer.py     # prints the endpoint URL
    modal app stop forge-glimmer             # after every session: no idle GPU left running

Budget: Forge has $30 max in total (user, 2026-10-28). max_containers=1 and a 5-minute scale-down cap the spend rate.
Needs the Modal secret `forge-glimmer` with VLLM_API_KEY (the endpoint rejects calls without it). Glimmer's weights
are not gated, so no HF token is needed. Create the secret from envsave (FORGE_GLIMMER_VLLM_API_KEY) and never write
the value to a file.
"""
import subprocess

import modal

MODEL = "meta-models/Muse-Glimmer-30B"
SERVED_NAME = "muse-glimmer"
GPU = "A100-80GB"
SCALEDOWN_S = 300
PORT = 8000
MINUTES = 60

# Modal needs `python` + `pip` on PATH; the vLLM image only ships `python3` (first deploy failed 2026-10-28:
# "unable to determine the version of Python"). Link the image's own Python so vLLM stays importable.
image = modal.Image.from_registry(
    "vllm/vllm-openai:muse-glimmer",
    setup_dockerfile_commands=[
        'RUN ln -sf "$(command -v python3)" /usr/local/bin/python'
        ' && (python -m pip --version || python -m ensurepip)',
    ],
).entrypoint([])
hf_cache = modal.Volume.from_name("forge-hf-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("forge-vllm-cache", create_if_missing=True)

app = modal.App("forge-glimmer")


@app.function(
    image=image,
    gpu=GPU,
    scaledown_window=SCALEDOWN_S,
    timeout=30 * MINUTES,
    max_containers=1,  # one GPU at most: a hard ceiling on spend rate
    secrets=[modal.Secret.from_name("forge-glimmer")],
    volumes={"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache},
)
@modal.concurrent(max_inputs=16)
@modal.web_server(port=PORT, startup_timeout=25 * MINUTES)
def serve():
    # VLLM_API_KEY from the secret makes vLLM require "Authorization: Bearer <key>"
    subprocess.Popen([
        "vllm", "serve", MODEL,
        "--served-model-name", SERVED_NAME,
        "--host", "0.0.0.0", "--port", str(PORT),
        "--tensor-parallel-size", "1",
        "--max-model-len", "32768",
        "--enable-auto-tool-choice",
        "--tool-call-parser", "muse_glimmer",
        "--reasoning-parser", "muse_glimmer",
        "--generation-config", "auto",
    ])
