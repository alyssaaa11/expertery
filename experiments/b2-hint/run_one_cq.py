#!/usr/bin/env python3
"""Run one first-test model answer inside the b2-hint sandbox.

Invoked by experiments/first-test/runner.py as:
    <venv python> -I run_one_cq.py <scratch-dir>

Reads <scratch>/answer.py, executes it in a fresh namespace, requires a
variable `result`, exports it to <scratch>/answer.step with
cadquery.exporters.export, then prints one JSON line
`MEASURE {...}` (bounding box xmin..zmax, volume, number of solids) and
the step path. The runner uses MEASURE only for the BX self-check
message. No other output channel.
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


def main(argv):
    # Resolved: the sandbox matches the -D SCRATCH subpath literally, so
    # this must be the same fully-resolved path the runner passed.
    scratch = os.path.realpath(os.path.abspath(argv[1]))
    answer_path = os.path.join(scratch, "answer.py")
    step_path = os.path.join(scratch, "answer.step")
    with open(answer_path, encoding="utf-8") as f:
        src = f.read()
    ns = {}
    exec(compile(src, answer_path, "exec"), ns)
    if "result" not in ns:
        print("ERROR: no variable named 'result'", file=sys.stderr)
        return 2
    result = ns["result"]
    import cadquery as cq
    from cadquery import exporters as _ex

    shape = _to_shape(result, cq)
    bb = shape.BoundingBox()
    measure = {
        "xmin": round(bb.xmin, 2),
        "ymin": round(bb.ymin, 2),
        "zmin": round(bb.zmin, 2),
        "xmax": round(bb.xmax, 2),
        "ymax": round(bb.ymax, 2),
        "zmax": round(bb.zmax, 2),
        "volume": round(shape.Volume(), 1),
        "solids": len(shape.Solids()),
    }
    _ex.export(result, step_path)
    print("MEASURE " + json.dumps(measure), flush=True)
    print(step_path, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
