#!/usr/bin/env python3
"""Run one cloud CadQuery answer inside the box (MUSE_SPEC section 1).

Invoked in the box as:
    <python> run_cq_box.py <scratch-dir>

Reads <scratch>/answer.py, executes it with ``__name__ == "__main__"``,
requires a variable ``result`` (same rule as runner.run_code: a
Workplane gives its solid), exports it to the fixed path
<scratch>/answer.brep as **BREP** (exact; not STEP), writes the
measurements to the fixed path <scratch>/measure.json, then prints one
JSON line ``MEASURE {...}`` and the brep path. The runner reads only the
two fixed files and ignores stdout for them.
"""

import json
import os
import sys


def _to_shape(result, cq):
    if isinstance(result, cq.Workplane):
        vals = [v for v in result.vals() if isinstance(v, cq.Shape)]
        if len(vals) == 1:
            return vals[0]
        return cq.Compound.makeCompound(vals)
    if isinstance(result, cq.Assembly):
        return result.toCompound()
    return result


def measure(shape):
    """checks.measure-style dict (bbox, volume, area, com, solids, valid)."""
    import cadquery as cq

    s = _to_shape(shape, cq)
    bb = s.BoundingBox()
    com = cq.Shape.centerOfMass(s)
    return {
        "bbox": [round(v, 3) for v in
                 (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "volume": round(s.Volume(), 3),
        "area": round(s.Area(), 3),
        "com": [round(com.x, 3), round(com.y, 3), round(com.z, 3)],
        "solids": len(s.Solids()),
        "valid": bool(s.isValid()),
    }


def main(argv):
    scratch = os.path.realpath(os.path.abspath(argv[1]))
    answer_path = os.path.join(scratch, "answer.py")
    brep_path = os.path.join(scratch, "answer.brep")
    with open(answer_path, encoding="utf-8") as f:
        src = f.read()
    ns = {"__name__": "__main__"}
    exec(compile(src, answer_path, "exec"), ns)
    if "result" not in ns:
        print("ERROR: no variable named 'result'", file=sys.stderr)
        return 2
    result = ns["result"]
    import cadquery as cq
    from cadquery import exporters as _ex

    shape = _to_shape(result, cq)
    m = measure(shape)
    _ex.export(shape, brep_path, exportType="BREP")
    with open(os.path.join(scratch, "measure.json"), "w",
              encoding="utf-8") as f:
        json.dump(m, f)
    print("MEASURE " + json.dumps(m), flush=True)
    print(brep_path, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
