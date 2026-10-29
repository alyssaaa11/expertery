"""Cloud safety box for FreeCAD answers (SPEC section 1).

Why this file exists (user decision 2026-10-29): nothing Glimmer writes
may run on the Mac. Every answer runs in a fresh Modal Sandbox
(block_network=True, no secrets, no volumes, cpu 1, memory 1024-4096
MiB, 90 s box); one sandbox per answer, terminated after use.

Image: FreeCAD 1.1.4 for Linux from the official release asset
``FreeCAD_1.1.4-Linux-x86_64-py311.AppImage`` (GitHub release
2026-09-28): downloaded in the image build, SHA256-verified against the
release's SHA256 file, unpacked with ``--appimage-extract`` (no FUSE
needed). The build prints ``freecadcmd`` version 1.1.4 (the Mac manual's
version). No conda route: conda-forge has no 1.1.4 build (1.1.0, 1.1.3,
2026.09.16 only); a different FreeCAD version could change the result.
The image holds ONLY FreeCAD + run_one_fc.py: no references, no jobs
file, no expected.json, no cadquery (see IMAGE_FILES).

Flow: write answer.py with sb.filesystem.write_text, run
``freecadcmd /work/run_one_fc.py`` with sb.exec (env FC_SCRATCH=/work,
timeout 60 s inside the 90 s box, the baseline's speed limit), read back
/work/answer.step (bytes) + /work/measure.json, then sb.terminate().
STEP answers over 20 MB are refused. The verdict and failure tags come
only from the grader; measure.json is for logs (the box runs untrusted
code and must not score itself).

Modal is imported lazily so the config helpers (sandbox kwargs, image
file list) are unit-testable offline. Tests inject a fake sandbox; any
test that could reach a real Modal call monkeypatches it to raise.
"""

import os

FREECAD_VERSION = "1.1.4"
APPIMAGE_ASSET = "FreeCAD_1.1.4-Linux-x86_64-py311.AppImage"
APPIMAGE_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/"
    + APPIMAGE_ASSET
)
APPIMAGE_SHA_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/SHA256.txt"
)

CPU = 1
MEMORY_MIB = (1024, 4096)
SANDBOX_TIMEOUT_S = 90  # the box: one sandbox per answer
EXEC_TIMEOUT_S = 60  # the answer run inside it (the baseline's limit)
MAX_STEP_BYTES = 20 * 1024 * 1024  # STEP answers over 20 MB are refused

WORK_DIR = "/work"
ANSWER_NAME = "answer.py"
RUN_SCRIPT = "run_one_fc.py"  # experiments/freecad/run_one_fc.py, baked in
STEP_PATH = WORK_DIR + "/answer.step"
MEASURE_PATH = WORK_DIR + "/measure.json"

# The box image holds ONLY FreeCAD + run_one_fc.py.
IMAGE_FILES = [RUN_SCRIPT]

try:
    import modal
except ImportError:  # offline: config helpers still work; runs refuse
    modal = None


def sandbox_kwargs():
    """Keyword args for modal.Sandbox.create: no network, no secrets,
    no volumes, one cpu, 1-4 GiB, 90 s. No "secrets"/"volumes" keys."""
    return {
        "block_network": True,
        "cpu": CPU,
        "memory": MEMORY_MIB,
        "timeout": SANDBOX_TIMEOUT_S,
    }


def image_files():
    """Files baked into the box image besides FreeCAD itself."""
    return list(IMAGE_FILES)


def build_image():
    """Modal image: download the AppImage, verify SHA256, unpack with
    --appimage-extract, and print `freecadcmd` version 1.1.4. Lazy: no
    network or Modal call until the image builds remotely."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot build the box image")
    return (
        modal.Image.from_registry("debian:bookworm-slim")
        .run_commands(
            "apt-get update && apt-get install -y --no-install-recommends "
            "ca-certificates curl file libgl1 libx11-6 libxext6 libxrender1 "
            "libxt6 libsm6 libice6 libfuse2-t 2>/dev/null || true",
        )
        .run_commands(
            "curl -L -o /opt/%s %s" % (APPIMAGE_ASSET, APPIMAGE_URL),
            "curl -L -o /opt/SHA256.txt %s" % APPIMAGE_SHA_URL,
            "cd /opt && grep %s SHA256.txt | sha256sum -c -" % APPIMAGE_ASSET,
            "cd /opt && ./%s --appimage-extract >/dev/null" % APPIMAGE_ASSET,
            "/opt/squashfs-root/usr/bin/freecadcmd --version",
        )
        .add_local_file(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), RUN_SCRIPT),
            "/work/%s" % RUN_SCRIPT,
        )
    )


def build_sandbox(image=None):
    """Create one fresh sandbox for one answer (terminated after use)."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot create a sandbox")
    return modal.Sandbox.create(image=image or build_image(), **sandbox_kwargs())


def run_answer_in_box(answer_code, sandbox=None, sandbox_factory=None):
    """Run one answer string in the box. Returns {"step_bytes",
    "measure", "log"}; measure is logs-only, the grader decides.

    `sandbox` (a live or fake sandbox) or `sandbox_factory` (called with
    no args) is injected in tests; without either, a real Modal sandbox
    is created. STEP output over 20 MB raises ValueError.
    """
    own = False
    if sandbox is None:
        if sandbox_factory is not None:
            sandbox = sandbox_factory()
        else:
            sandbox = build_sandbox()
        own = True
    try:
        sandbox.filesystem.write_text(
            WORK_DIR + "/" + ANSWER_NAME, answer_code or "")
        proc = sandbox.exec(
            ["freecadcmd", WORK_DIR + "/" + RUN_SCRIPT],
            env={"FC_SCRATCH": WORK_DIR},
            timeout=EXEC_TIMEOUT_S,
        )
        log = ""
        try:
            log = proc.stdout.read() if hasattr(proc.stdout, "read") else ""
        except Exception:  # noqa: BLE001 -- logs are best-effort
            log = ""
        step_bytes = sandbox.filesystem.read_bytes(STEP_PATH)
        if len(step_bytes) > MAX_STEP_BYTES:
            raise ValueError(
                "STEP is %d bytes (over the %d-byte limit); refusing"
                % (len(step_bytes), MAX_STEP_BYTES))
        import json as _json

        measure = _json.loads(sandbox.filesystem.read_text(MEASURE_PATH))
        return {"step_bytes": step_bytes, "measure": measure, "log": log}
    finally:
        if own:
            try:
                sandbox.terminate()
            except Exception:  # noqa: BLE001 -- terminate is best-effort
                pass
