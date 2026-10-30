"""Serve the trained Forge model (base + merged LoRA) with vLLM on Modal.

Same settings as deploy/modal_glimmer.py (A100-80GB, the same vLLM image
and flags, max-model-len 32768, max_containers 1, 5-minute scale-down,
secret forge-glimmer with VLLM_API_KEY), except:

- app ``forge-trained`` (stopped after every session: no idle GPU);
- the model path is /vol/<name>/merged from the ``forge-lora`` volume
  (<name> from env FORGE_MODEL_NAME, default ``final``);
- the served name is ``forge`` (what runner_final.py asks for).

    FORGE_MODEL_NAME=final modal deploy deploy/modal_forge.py
    modal app stop forge-trained   # after every session
"""

import os
import subprocess

import modal

MODEL_NAME = os.environ.get("FORGE_MODEL_NAME", "final")
MODEL_PATH = "/vol/%s/merged" % MODEL_NAME
SERVED_NAME = "forge"
GPU = "A100-80GB"
SCALEDOWN_S = 300
PORT = 8000
MINUTES = 60

# Modal needs `python` + `pip` on PATH; the vLLM image only ships `python3`
# (same fix as deploy/modal_glimmer.py).
image = modal.Image.from_registry(
    "vllm/vllm-openai:muse-glimmer",
    setup_dockerfile_commands=[
        'RUN ln -sf "$(command -v python3)" /usr/local/bin/python'
        ' && (python -m pip --version || python -m ensurepip)',
    ],
).entrypoint([])
# Bake the deploy-time name INTO the container: Modal re-imports this
# module inside the container where FORGE_MODEL_NAME is not set, so
# without this the server would fall back to /vol/final/merged.
image = image.env({"FORGE_MODEL_NAME": MODEL_NAME})
hf_cache = modal.Volume.from_name("forge-hf-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("forge-vllm-cache", create_if_missing=True)
lora_vol = modal.Volume.from_name("forge-lora", create_if_missing=True)

app = modal.App("forge-trained")


@app.function(
    image=image,
    gpu=GPU,
    scaledown_window=SCALEDOWN_S,
    timeout=30 * MINUTES,
    max_containers=1,  # one GPU at most: a hard ceiling on spend rate
    secrets=[modal.Secret.from_name("forge-glimmer")],
    volumes={"/root/.cache/huggingface": hf_cache,
             "/root/.cache/vllm": vllm_cache,
             "/vol": lora_vol},
)
@modal.concurrent(max_inputs=16)
@modal.web_server(port=PORT, startup_timeout=25 * MINUTES)
def serve():
    # Re-read the name inside the container (from the baked image env)
    # rather than trusting the deploy-time MODEL_PATH global.
    model_path = "/vol/%s/merged" % os.environ.get("FORGE_MODEL_NAME",
                                                   "final")
    print("SERVING %s" % model_path, flush=True)
    # VLLM_API_KEY from the secret makes vLLM require "Authorization: Bearer <key>"
    subprocess.Popen([
        "vllm", "serve", model_path,
        "--served-model-name", SERVED_NAME,
        "--host", "0.0.0.0", "--port", str(PORT),
        "--tensor-parallel-size", "1",
        "--max-model-len", "32768",
        "--enable-auto-tool-choice",
        "--tool-call-parser", "muse_glimmer",
        "--reasoning-parser", "muse_glimmer",
        "--generation-config", "auto",
    ])
