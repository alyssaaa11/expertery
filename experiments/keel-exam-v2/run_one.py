#!/usr/bin/env python3
"""Run one model answer inside the Keel v2 sandbox (PLAN.md 4c).

Invoked by runner.py as:
    <venv python> run_one.py <scratch-dir>

Puts <repo>/company on sys.path (absolute path computed from this file's
own location), executes <scratch>/answer.py with runpy.run_path, takes the
variable `solid` (must be a CadQuery Shape), writes `solid.brep`
(solid.exportBrep(...)) and `result.json` (ok / error text) into the scratch
dir. Nothing else.
"""

import json
import os
import runpy
import sys


def main(argv):
    # Resolved: the sandbox matches the -D SCRATCH subpath literally, so
    # this must be the same fully-resolved path the runner passed.
    scratch = os.path.realpath(os.path.abspath(argv[1]))
    answer_path = os.path.join(scratch, "answer.py")
    result_path = os.path.join(scratch, "result.json")
    brep_path = os.path.join(scratch, "solid.brep")
    here = os.path.dirname(os.path.abspath(__file__))
    company = os.path.abspath(os.path.join(here, "..", "..", "company"))
    sys.path.insert(0, company)
    try:
        import cadquery as cq

        ns = runpy.run_path(answer_path)
        if "solid" not in ns:
            raise NameError(
                "no variable named 'solid' "
                "(the program must end with solid = p.finish())"
            )
        solid = ns["solid"]
        if not isinstance(solid, cq.Shape):
            raise TypeError(
                "'solid' must be a CadQuery Shape, "
                f"got {type(solid).__name__}"
            )
        solid.exportBrep(brep_path)
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({"ok": True}, f)
        return 0
    except Exception as e:  # noqa: BLE001 -- the error text is the FAIL reason
        try:
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "error": f"{type(e).__name__}: {e}"}, f)
        except OSError:
            pass
        print(f"run_one: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
