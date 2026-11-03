"""Installer env pins (no Modal, no network, no model calls).

The uv tool env must run on Python 3.12 with the same CadQuery pins as
the cloud box, so `expertery exam build` can load the factory's
prompt/check modules locally (model-written code still only runs in
the cloud box; system Pythons >=3.13 have no CadQuery wheels).
"""

import os
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))

CLOUD_CQ_PATH = os.path.join(REPO_ROOT, "experiments", "final", "cloud_cq.py")


def _load_cloud_cq():
    import importlib.util as _ilu

    spec = _ilu.spec_from_file_location("cloud_cq_pins", CLOUD_CQ_PATH)
    mod = _ilu.module_from_spec(spec)
    sys.modules.pop("cloud_cq", None)  # never import the real module
    spec.loader.exec_module(mod)
    return mod


def test_pyproject_requires_python_312_only():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["requires-python"] == ">=3.12,<3.13"


def test_pyproject_pins_match_cloud_box():
    cloud_cq = _load_cloud_cq()
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    for pin in cloud_cq.pip_spec():
        assert pin in deps


def test_install_sh_pins_python_and_reinstalls():
    with open(os.path.join(REPO_ROOT, "install.sh"), encoding="utf-8") as f:
        src = f.read()
    assert "--python 3.12" in src
    assert "--reinstall" in src
