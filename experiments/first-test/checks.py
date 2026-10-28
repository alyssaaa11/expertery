"""Measure a CadQuery result and compare it with a job's expected values (PLAN.md section 6)."""
import cadquery as cq

TOL_POS = 0.1      # mm, bounding-box faces
TOL_COM = 0.3      # mm, centre of mass
TOL_REL = 0.01     # 1 %, volume and surface area
TOL_DIFF = 0.002   # 0.2 % of the reference volume may differ (answer XOR reference); B-rep booleans are exact


def to_shape(result):
    if isinstance(result, cq.Workplane):
        vals = [v for v in result.vals() if isinstance(v, cq.Shape)]
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(result, cq.Assembly):
        return result.toCompound()
    return result


def measure(result):
    s = to_shape(result)
    bb = s.BoundingBox()
    com = cq.Shape.centerOfMass(s)
    return {
        "bbox": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "volume": round(s.Volume(), 3),
        "area": round(s.Area(), 3),
        "com": [round(com.x, 3), round(com.y, 3), round(com.z, 3)],
        "solids": len(s.Solids()),
        "valid": bool(s.isValid()),
    }


def compare(m, e):
    """Return the list of failed checks (empty list = PASS)."""
    fails = []
    if m["solids"] != 1:
        fails.append(f"solids={m['solids']}")
    if not m["valid"]:
        fails.append("invalid shape")
    if any(abs(a - b) > TOL_POS for a, b in zip(m["bbox"], e["bbox"])):
        fails.append("bbox")
    for k in ("volume", "area"):
        if abs(m[k] - e[k]) > TOL_REL * abs(e[k]):
            fails.append(k)
    if any(abs(a - b) > TOL_COM for a, b in zip(m["com"], e["com"])):
        fails.append("com")
    return fails


def mismatch(answer, reference):
    """Volume that is in one part but not the other, as a fraction of the reference volume.
    Catches any moved feature, even symmetric moves that keep size, volume, area and centre of mass."""
    a, r = to_shape(answer), to_shape(reference)
    inter = a.intersect(r).Volume()
    return (a.Volume() + r.Volume() - 2 * inter) / r.Volume()


def score(answer, reference, expected):
    """PASS if every check holds. Returns (passed, failed_checks, measurements)."""
    m = measure(answer)
    fails = compare(m, expected)
    try:
        d = mismatch(answer, reference)
    except Exception as e:  # a broken shape can't be intersected
        d, fails = None, fails + [f"mismatch error {e!r}"[:120]]
    m["mismatch"] = None if d is None else round(d, 5)
    if d is not None and d > TOL_DIFF:
        fails.append(f"mismatch {d:.1%}")
    return (not fails), fails, m
