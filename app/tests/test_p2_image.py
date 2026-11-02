"""Web image file list, modal_web.py shape, and config parity.

No Modal, no network: modal_web.py is checked by source + py_compile so
the suite runs without fastapi installed.
"""

import py_compile
import re
from pathlib import Path

from app.backend import config, image_files

ROOT = Path(__file__).resolve().parent.parent.parent
MODAL_WEB = ROOT / "deploy" / "modal_web.py"


def test_every_listed_file_exists():
    missing = [p for p in image_files.WEB_IMAGE_FILES
               if not (ROOT / p).is_file()]
    assert missing == []


def test_forbidden_files_absent():
    assert image_files.check_file_list() == []
    assert image_files.check_file_list(
        ["experiments/first-test/expected.json"]) != []
    assert image_files.check_file_list(
        ["experiments/first-test/jobs.py"]) != []
    assert image_files.check_file_list(
        ["results/anything.jsonl"]) != []
    for path in image_files.WEB_IMAGE_FILES:
        assert "expected.json" not in path
        assert not path.endswith("/jobs.py")
        assert "/results/" not in path


def test_minimum_imports_listed():
    assert "experiments/first-test/checks.py" in image_files.WEB_IMAGE_FILES
    assert "experiments/common/budget_left.py" in image_files.WEB_IMAGE_FILES
    assert "experiments/final/runner_final.py" in image_files.WEB_IMAGE_FILES
    assert "experiments/final/cloud_cq.py" in image_files.WEB_IMAGE_FILES
    assert "experiments/final/run_cq_box.py" in image_files.WEB_IMAGE_FILES
    assert "experiments/first-test/runner.py" in image_files.WEB_IMAGE_FILES


def test_modal_web_compiles():
    py_compile.compile(str(MODAL_WEB), doraise=True)


def test_modal_web_shape():
    src = MODAL_WEB.read_text()
    assert 'modal.App("homegrown-web")' in src
    assert "max_containers=1" in src
    assert "min_containers=0" in src
    assert 'modal.Secret.from_name("forge-glimmer")' in src
    assert "FORGE_URL" in src
    assert "homegrown-leads" in src
    assert "homegrown-files" in src
    assert "cpu=1" in src or "cpu = 1" in src
    assert "gpu=" not in src  # CPU only
    assert "run_answer_in_box" in src  # the locked sandbox, not the grader
    # The explicit list lives in app/backend/image_files.py; the Modal
    # image consumes it file by file.
    assert "WEB_IMAGE_FILES" in src
    assert "add_local_file" in src
    for forbidden in ("expected.json", "jobs.py", "results/"):
        assert forbidden not in src, forbidden
    assert 'REASONING_STRENGTH", "xhigh"' in src or \
        "REASONING_STRENGTH" in src


def test_no_grader_in_modal_web():
    src = MODAL_WEB.read_text().lower()
    assert "grader" not in src
    assert "grade_shapes" not in src


def test_config_defaults_match_backend():
    src = MODAL_WEB.read_text()
    pairs = re.findall(
        r"^([A-Z_]+) = (?:int|float)\(os\.environ\.get\(\"([A-Z_]+)\", "
        r"\"([^\"]+)\"\)\)",
        src, re.MULTILINE)
    found = {name: default for _, name, default in pairs}
    for name in ("MAX_JOB_CHARS", "MAX_BUILDS_PER_IP_HOUR",
                 "MAX_CONCURRENT_BUILDS", "MAX_LEADS_PER_IP_HOUR",
                 "DAILY_CAP_USD", "GPU_USD_PER_S",
                 "SANDBOX_USD_PER_BUILD", "IDLE_TAIL_USD", "WAKE_USD",
                 "SCALE_DOWN_S", "BUILD_LIMIT_S", "WEB_TIMEOUT_S"):
        assert name in found, name
        assert float(found[name]) == float(getattr(config, name)), name
    assert "LEAD_EMAIL_MAX = 200" in src
    assert "LEAD_TOOL_MAX = 300" in src
