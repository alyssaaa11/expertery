#!/usr/bin/env python3
"""Run one FreeCAD answer inside the cloud box (SPEC section 1).

Runs headless under `freecadcmd -c BOOTSTRAP` (see cloud_exec.py)
with env FC_SCRATCH=/work. The answer file (answer.py, written by the box caller)
is exec'd with ``ns = {"__name__": "__main__"}``; ``result`` must be a
``Part.Shape`` with at least one solid. ``import cadquery`` / ``OCP`` is
refused by an import hook. On success writes answer.step + measure.json
(bbox, volume, solids, isValid) into the scratch dir.

Exit codes: 0 = part written; 2 = answer error (missing result, wrong
type, refused import, exception during exec).

The verdict comes only from the cloud grader; measure.json is for logs.
This module imports FreeCAD/Part lazily so its pure helpers (hook,
exec, error strings) are unit-testable without FreeCAD, using a fake
Part module in tests.
"""

import json
import os
import sys

REFUSED_IMPORTS = ("cadquery", "OCP")

ERROR_NO_RESULT = "ERROR: no variable named 'result'"
ERROR_NOT_SOLID = "ERROR: result is not a Part solid"

ANSWER_NAME = "answer.py"
STEP_NAME = "answer.step"
MEASURE_NAME = "measure.json"


class RefusedImportError(ImportError):
    """Raised when answer code tries to import a refused module."""


class _RefuseImports:
    """Meta-path hook refusing cadquery / OCP (cheat route: FreeCAD can
    run CadQuery, so an answer could dodge the tool being tested)."""

    def __init__(self, refused=REFUSED_IMPORTS):
        self.refused = tuple(refused)

    def find_module(self, name, path=None):  # legacy protocol, freecadcmd py3.11 ok
        if (name or "").split(".")[0] in self.refused:
            return self
        return None

    def find_spec(self, name, path=None, target=None):
        if (name or "").split(".")[0] in self.refused:
            import importlib.machinery
            return importlib.machinery.ModuleSpec(name, self)
        return None

    def create_module(self, spec):
        raise RefusedImportError(
            "refused import: %s (answers must use the Part module)" % spec.name
        )

    def exec_module(self, module):
        raise RefusedImportError(
            "refused import: %s (answers must use the Part module)" % module.__name__
        )


def install_import_hook(refused=REFUSED_IMPORTS):
    """Install the cadquery/OCP refusal hook once; returns the hook."""
    for hook in sys.meta_path:
        if isinstance(hook, _RefuseImports):
            return hook
    hook = _RefuseImports(refused)
    sys.meta_path.insert(0, hook)
    return hook


def run_answer_source(source):
    """Exec answer source; returns (result, error).

    ``result`` is the raw ``result`` variable (or None); ``error`` is None
    on a clean exec, else a short "Type: message" string. A missing
    ``result`` variable is reported with ERROR_NO_RESULT here. Refused
    modules are masked from sys.modules during the exec, so the hook
    fires even where they happen to be importable.
    """
    ns = {"__name__": "__main__"}
    install_import_hook()
    masked = {}
    for name in list(sys.modules):
        if name in REFUSED_IMPORTS or name.startswith(
                tuple(r + "." for r in REFUSED_IMPORTS)):
            masked[name] = sys.modules.pop(name)
    try:
        exec(compile(source, ANSWER_NAME, "exec"), ns)  # noqa: S102 -- the box runs answers
    except RefusedImportError as e:
        return None, str(e)
    except Exception as e:  # noqa: BLE001 -- answer raised: api_error
        return None, "%s: %s" % (type(e).__name__, e)
    finally:
        sys.modules.update(masked)
    if "result" not in ns:
        return None, ERROR_NO_RESULT
    return ns["result"], None


def is_part_solid(result):
    """True when result is a Part.Shape with >= 1 solid.

    Real FreeCAD exposes ``Shape.Solids`` as a LIST attribute, not a
    method, so this uses ``len(shape.Solids)`` (a method object has no
    len: not a solid)."""
    try:
        import Part  # noqa: E402
    except ImportError:
        return False
    try:
        return isinstance(result, Part.Shape) and len(result.Solids) >= 1
    except Exception:  # noqa: BLE001 -- a broken shape is not a solid
        return False


def validate_result(result):
    """None when result is a Part solid, else the ERROR string."""
    if not is_part_solid(result):
        return ERROR_NOT_SOLID
    return None


def measure_shape(shape):
    """Log-only measurements: bbox faces, volume, solids, validity."""
    bb = shape.BoundBox
    return {
        "bbox": [float(bb.XMin), float(bb.YMin), float(bb.ZMin),
                 float(bb.XMax), float(bb.YMax), float(bb.ZMax)],
        "volume": float(shape.Volume),
        "solids": int(len(shape.Solids)),
        "valid": bool(shape.isValid()),
    }


def export_step(shape, path):
    """Write the part as STEP (the only thing the box hands back)."""
    shape.exportStep(path)


def run_one(scratch_dir):
    """Run <scratch>/answer.py; write answer.step + measure.json.

    Returns (ok, error). ok=True wrote both files; the grader decides.
    """
    with open(os.path.join(scratch_dir, ANSWER_NAME), encoding="utf-8") as f:
        source = f.read()
    result, error = run_answer_source(source)
    if error is not None:
        return False, error
    error = validate_result(result)
    if error is not None:
        return False, error
    step_path = os.path.join(scratch_dir, STEP_NAME)
    export_step(result, step_path)
    measure = measure_shape(result)
    with open(os.path.join(scratch_dir, MEASURE_NAME), "w", encoding="utf-8") as f:
        json.dump(measure, f)
    return True, None


def main(argv=None):
    scratch = os.environ.get("FC_SCRATCH", "/work")
    args = list(argv or [])
    if args:
        scratch = args[0]
    ok, error = run_one(scratch)
    if not ok:
        sys.stderr.write("%s\n" % (error or "answer failed"))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
