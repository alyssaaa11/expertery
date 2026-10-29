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
APPIMAGE_SHA_NAME = APPIMAGE_ASSET + "-SHA256.txt"
APPIMAGE_SHA_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/"
    + APPIMAGE_SHA_NAME
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


EXEC_APP_NAME = "forge-freecad"  # Modal app the boxes run under


def lookup_exec_app():
    """The Modal app handle for boxes (created on first lookup)."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot look up the app")
    return modal.App.lookup(EXEC_APP_NAME, create_if_missing=True)


def build_image():
    """Modal image: download the AppImage, verify SHA256, unpack with
    --appimage-extract, link freecadcmd on PATH, and print `freecadcmd`
    version 1.1.4. Lazy: no network or Modal call until the image builds
    remotely. `curl -fL` fails the build on an HTTP error (a 404 is not a
    checksum mismatch later)."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot build the box image")
    return (
        modal.Image.from_registry("debian:bookworm-slim")
        .run_commands(
            "apt-get update && apt-get install -y --no-install-recommends "
            "ca-certificates curl libgl1 libglib2.0-0 libx11-6 libxext6 "
            "libxrender1 libsm6 libice6",
        )
        .run_commands(
            "curl -fL -o /opt/%s %s" % (APPIMAGE_ASSET, APPIMAGE_URL),
            "curl -fL -o /opt/%s %s" % (APPIMAGE_SHA_NAME, APPIMAGE_SHA_URL),
            "cd /opt && grep %s %s | sha256sum -c -"
            % (APPIMAGE_ASSET, APPIMAGE_SHA_NAME),
            "cd /opt && ./%s --appimage-extract >/dev/null" % APPIMAGE_ASSET,
            "ln -s /opt/squashfs-root/usr/bin/freecadcmd "
            "/usr/local/bin/freecadcmd",
            "freecadcmd --version",
        )
        .add_local_file(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), RUN_SCRIPT),
            "/work/%s" % RUN_SCRIPT,
        )
    )


def build_sandbox(image=None):
    """Create one fresh sandbox for one answer (terminated after use).

    Modal requires the app, so the box is created under the forge-freecad
    app handle, not ad hoc."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot create a sandbox")
    app = lookup_exec_app()
    return modal.Sandbox.create(
        app=app, image=image or build_image(), **sandbox_kwargs())


NO_STEP_PREFIX = "the answer wrote no STEP"


def _read_stream(stream):
    """Best-effort text from a box process stream (stdout or stderr)."""
    try:
        if stream is not None and hasattr(stream, "read"):
            return stream.read() or ""
    except Exception:  # noqa: BLE001 -- logs are best-effort
        pass
    return ""


def run_answer_in_box(answer_code, sandbox=None, sandbox_factory=None):
    """Run one answer string in the box. Returns {"step_bytes",
    "measure", "log", "run_error"}; measure is logs-only, the grader
    decides.

    `sandbox` (a live or fake sandbox) or `sandbox_factory` (called with
    no args) is injected in tests; without either, a real Modal sandbox
    is created. STEP output over 20 MB raises ValueError. When the answer
    writes no STEP (run_one_fc exits 2 with its ERROR line on stderr),
    nothing raises: step_bytes/measure come back None and run_error holds
    run_one_fc's stderr (its ERROR line), for the runner's run_error.
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
            "freecadcmd", WORK_DIR + "/" + RUN_SCRIPT,
            env={"FC_SCRATCH": WORK_DIR},
            timeout=EXEC_TIMEOUT_S,
        )
        log = _read_stream(getattr(proc, "stdout", None))
        err_text = _read_stream(getattr(proc, "stderr", None)).strip()
        try:
            step_bytes = sandbox.filesystem.read_bytes(STEP_PATH)
        except (FileNotFoundError, KeyError):  # KeyError: test fakes
            detail = err_text or log.strip()
            run_error = NO_STEP_PREFIX + (": %s" % detail if detail else "")
            return {"step_bytes": None, "measure": None, "log": log,
                    "run_error": run_error}
        if len(step_bytes) > MAX_STEP_BYTES:
            raise ValueError(
                "STEP is %d bytes (over the %d-byte limit); refusing"
                % (len(step_bytes), MAX_STEP_BYTES))
        import json as _json

        measure = _json.loads(sandbox.filesystem.read_text(MEASURE_PATH))
        return {"step_bytes": step_bytes, "measure": measure, "log": log,
                "run_error": None}
    finally:
        if own:
            try:
                sandbox.terminate()
            except Exception:  # noqa: BLE001 -- terminate is best-effort
                pass


# ------------------------------------------------------- live check CLIs
# (Claude runs these against real Modal; never in unit tests.)


def check_image():
    """Build the box image, run `freecadcmd --version` in it, print that."""
    if modal is None:
        raise RuntimeError("modal is not installed; cannot check the image")
    sb = modal.Sandbox.create(
        app=lookup_exec_app(), image=build_image(), **sandbox_kwargs())
    try:
        proc = sb.exec("freecadcmd", "--version", timeout=60)
        out = (_read_stream(proc.stdout) + _read_stream(proc.stderr)).strip()
        print(out)
        return out
    finally:
        sb.terminate()


def rel_diff(a, b):
    """Relative difference |a-b|/|b| (None when b is 0)."""
    try:
        return abs(float(a) - float(b)) / abs(float(b)) if float(b) else None
    except (TypeError, ValueError):
        return None


def check_hand(answer_paths, exec_fn=None, grade_fn=None, expected=None):
    """Run hand-written answers in the box and grade each STEP.

    Prints one line per answer: `<name>: PASS` (or FAIL) plus the
    bbox/volume relative difference vs the Mac-made parts when `expected`
    ({name: {"bbox": [...], "volume": ...}}) is given. Returns the lines.
    `exec_fn`/`grade_fn` are injected in tests; by default the real box
    and the cloud grader (needs the grader app context) are used.
    """
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cloud_grade as _cloud_grade  # noqa: E402

    lines = []
    for path in answer_paths:
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            source = f.read()
        boxed = (exec_fn or run_answer_in_box)(source)
        verdict, extra = "FAIL", ""
        if boxed.get("step_bytes") is not None:
            graded = (grade_fn or _cloud_grade.grade.remote)(
                name, boxed["step_bytes"])
            verdict = graded.get("verdict", "FAIL")
            exp = (expected or {}).get(name)
            got = graded.get("measurements") or {}
            if exp and got:
                parts = []
                for key in ("bbox", "volume"):
                    if key in exp and key in got:
                        vals_e = exp[key] if isinstance(
                            exp[key], list) else [exp[key]]
                        vals_g = got[key] if isinstance(
                            got[key], list) else [got[key]]
                        diffs = [rel_diff(g, e) for g, e in
                                 zip(vals_g, vals_e)]
                        diffs = [d for d in diffs if d is not None]
                        if diffs:
                            parts.append("%s rel-diff %.2e" % (
                                key, max(diffs)))
                if parts:
                    extra = " (" + ", ".join(parts) + ")"
        else:
            extra = " (%s)" % (boxed.get("run_error") or NO_STEP_PREFIX)
        line = "%s: %s%s" % (name, verdict, extra)
        print(line)
        lines.append(line)
    return lines


def main(argv=None):
    """CLI: --check-image prints freecadcmd --version from the built image;
    --check-hand <answers...> grades hand answers in the box."""
    import argparse as _ap

    parser = _ap.ArgumentParser(description="FreeCAD cloud-box checks.")
    parser.add_argument("--check-image", action="store_true")
    parser.add_argument("--check-hand", nargs="*", default=None,
                        help="hand answer files to run in the box and grade")
    args = parser.parse_args(argv)
    if args.check_image:
        check_image()
        return 0
    if args.check_hand is not None:
        check_hand(args.check_hand or sorted(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "hand", n)
            for n in sorted(os.listdir(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "hand")))
            if n.endswith(".py")))
        return 0
    parser.error("need --check-image or --check-hand")
    return 2


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
