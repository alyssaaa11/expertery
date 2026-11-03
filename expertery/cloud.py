"""Thin adapters over the repo's existing modules.

The repo root is the parent of this package's directory. The needed
experiments directories are added to sys.path inside these functions,
never at import time (importing this module, or cli.py, has no sys.path
side effects and needs no third-party packages).

Reusable pieces (never rewritten here):
- experiments/final/cloud_cq.py: run_answer_in_box, the grader app
  forge-cq-grader with grade(..., reference=...) / measure_brep.
- experiments/first-test/runner.py: SYSTEM_PROMPT, build_messages,
  build_body, extract_code.
- experiments/factory/teacher.py: SPARK_MODEL, SPARK_URL, MAX_TOKENS,
  TEMPERATURE, TOP_P, cost_of_usage, IN_FLIGHT_COST.
"""

import json
import os
import sys
import urllib.request

from . import config as _config


def repo_root():
    """The repo root: the parent of this package's directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_paths():
    """Add the needed experiments dirs to sys.path (call-time only)."""
    root = repo_root()
    for sub in ("experiments/final", "experiments/first-test",
                "experiments/factory"):
        path = os.path.join(root, sub)
        if path not in sys.path:
            sys.path.insert(0, path)


def load_runner():
    """Import experiments/first-test/runner.py (stdlib only at import)."""
    _ensure_paths()
    import runner  # noqa: E402
    return runner


def load_teacher():
    """Import experiments/factory/teacher.py (stdlib only at import)."""
    _ensure_paths()
    import teacher  # noqa: E402
    return teacher


def load_cloud_cq():
    """Import experiments/final/cloud_cq.py (modal import is lazy)."""
    _ensure_paths()
    import cloud_cq  # noqa: E402
    return cloud_cq


def reader_defaults():
    """(url, model) defaults from the teacher module."""
    teacher = load_teacher()
    return teacher.SPARK_URL, teacher.SPARK_MODEL


def reader_config():
    """Effective (url, model, key_present) for reader calls.

    URL/model default to the teacher's SPARK_URL / SPARK_MODEL and are
    overridable via EXPERTERY_READER_URL / EXPERTERY_READER_MODEL so a
    company can point at its own Spark Open or Glimmer server. The key
    itself is never returned, only whether one is configured.
    """
    url, model = reader_defaults()
    url = os.environ.get(_config.READER_URL_ENV, "") or url
    model = os.environ.get(_config.READER_MODEL_ENV, "") or model
    key = (os.environ.get(_config.READER_KEY_ENV, "")
           or os.environ.get(_config.READER_KEY_FALLBACK_ENV, ""))
    return url, model, bool(key)


def reader_key():
    """The reader API key (never printed or logged by callers)."""
    return (os.environ.get(_config.READER_KEY_ENV, "")
            or os.environ.get(_config.READER_KEY_FALLBACK_ENV, ""))


def cost_of_usage(usage):
    """Dollar cost of one reader call; teacher's prices when available."""
    try:
        teacher = load_teacher()
        return float(teacher.cost_of_usage(usage))
    except Exception:  # noqa: BLE001 -- fall back to config constants
        return _config.estimate_cost(usage)


def in_flight_cost():
    """Reserve for one not-yet-made call; teacher's when available."""
    try:
        teacher = load_teacher()
        return float(teacher.IN_FLIGHT_COST)
    except Exception:  # noqa: BLE001
        return float(_config.IN_FLIGHT_COST)


def extract_code(content):
    """First fenced code block (the runner's rule)."""
    return load_runner().extract_code(content)


def reader_messages(request_text):
    """Factory prompt: runner.build_messages("A", text, "")."""
    runner = load_runner()
    return runner.build_messages("A", request_text, "")


def reader_body(model, messages):
    """Request body for a reader call."""
    return load_runner().build_body(model, messages)


def post_reader(url, key, body, timeout=600.0):
    """POST one reader body with stdlib urllib. Returns parsed JSON."""
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def run_box(answer_code, box_fn=None):
    """Run answer code in the cloud box.

    Default is cloud_cq.run_answer_in_box (the locked box; one sandbox
    per answer). Tests inject box_fn(code) -> {"brep_bytes", "measure",
    "log", "run_error"}.
    """
    if box_fn is not None:
        return box_fn(answer_code)
    return load_cloud_cq().run_answer_in_box(answer_code)


def factory_grade_fn(jobs, grade_fn=None):
    """grade_fn(exam, job_id, brep) carrying each job's reference.

    Default wires the cloud grader exactly as runner_final.grade_fn_for
    does: factory jobs pass their reference along (the grader prefers
    the baked file for known ids), via cloud_cq.grade.remote.
    """
    if grade_fn is not None:
        return grade_fn
    cloud_cq = load_cloud_cq()

    def _remote(*args, **kwargs):
        return cloud_cq.grade.remote(*args, **kwargs)

    return cloud_cq.factory_grade_fn(jobs, _remote)


def cloud_cq_path():
    """Absolute path of the module init deploys (box + grader)."""
    return os.path.join(repo_root(), "experiments", "final", "cloud_cq.py")


def rule_card_path():
    """Absolute path of the frozen rule card (base + loop runs)."""
    return os.path.join(repo_root(), "experiments", "final", "RULE_CARD.md")


def final_session_script():
    """Absolute path of run_final_session.sh (trained runs)."""
    return os.path.join(repo_root(), "experiments", "final",
                        "run_final_session.sh")


def base_session_script():
    """Absolute path of run_base_session.sh (base runs)."""
    return os.path.join(repo_root(), "experiments", "final",
                        "run_base_session.sh")


def forge_train_path():
    """Absolute path of experiments/train/forge_train.py."""
    return os.path.join(repo_root(), "experiments", "train",
                        "forge_train.py")


def modal_forge_path():
    """Absolute path of deploy/modal_forge.py."""
    return os.path.join(repo_root(), "deploy", "modal_forge.py")
