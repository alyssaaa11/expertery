"""Quillon Orbital Works self-test (SPEC section 6 + Keel v2 addendum V2.8).

Builds every example part, scores each reference against itself with the
Keel-exam referee (experiments/keel-exam/referee.py, tolerance 0.01%),
checks that two deliberately wrong variants per example FAIL, checks the
v1 KeelError cases, and checks every new v2 rule (materials, FLIGHT, -CS,
wall holes, mounts, mirror). Prints a summary line ``SELFTEST x/y PASS``.
"""

import importlib.util
import json
import os
import runpy
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import keel  # noqa: E402

_REFEREE = os.path.join(
    HERE, "..", "experiments", "keel-exam", "referee.py"
)
_spec = importlib.util.spec_from_file_location("qow_referee", os.path.abspath(_REFEREE))
checks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checks)

EXAMPLES = os.path.join(HERE, "examples")

# Two deliberately wrong variants per example, as (find, replace) on the source.
# Each replacement must match the example source exactly once.
VARIANTS = {
    "brk_0101.py": [
        ('p.hole("KF-M4", at=(6, 6))', 'p.hole("KF-M4", at=(7, 6))'),
        ('p.wall("north", 25)', 'p.wall("north", 23)'),
    ],
    "plt_0230.py": [
        ("at=(10, 10)", "at=(11, 10)"),
        ("p.stock(80, 60, 3)", "p.stock(80, 60, 4)"),
    ],
    "std_0044.py": [
        ("p.boss(at=(15, 15), dia=12, h=10)", "p.boss(at=(15, 15), dia=12, h=8)"),
        ('p.hole("KF-M4", at=(15, 15))', 'p.hole("KF-M4", at=(16, 15))'),
    ],
    "frm_0310.py": [
        ("L=80, W=60, depth=4", "L=80, W=60, depth=5"),
        ('p.wall("north", 12)', 'p.wall("north", 10)'),
    ],
    "clp_0012.py": [
        ("to=(40, 15), width=5", "to=(40, 15), width=6"),
        ('p.wall("west", 10)', 'p.wall("west", 8)'),
    ],
    "brk_0155.py": [
        ('p.wall("north", 20)', 'p.wall("north", 18)'),
        ("p.pattern(2, 1, 34, 0)", "p.pattern(2, 1, 35, 0)"),
    ],
    "plt_0277.py": [
        ('"KF-M4-CB", at=(8, 8)', '"KF-M4-CB", at=(9, 8)'),
        ("KF-M4-CB", "KF-M4"),
    ],
    "frm_0320.py": [
        ("to=(105, 20), width=6", "to=(105, 20), width=7"),
        ('p.wall("east", 15)', 'p.wall("east", 13)'),
    ],
    "brk_0142.py": [
        ('p.hole("KF-M4-CB", at=(6, 6))', 'p.hole("KF-M4-CB", at=(7, 6))'),
        ('p.wall("north", 25)', 'p.wall("north", 23)'),
    ],
    "frm_1031.py": [
        ("L=80, W=60, depth=4", "L=80, W=60, depth=5"),
        ('p.hole("KF-M5", at=(5, 5))', 'p.hole("KF-M5", at=(6, 5))'),
    ],
    "plt_1042.py": [
        ("origin=(10, 10)", "origin=(11, 10)"),
        ('finish="CS"', 'finish="CB"'),
    ],
    "std_1063.py": [
        ("origin=(30, 30)", "origin=(31, 30)"),
        ("p.fillet()", "p.fillet(r=1.5)"),
    ],
}

passed = 0
total = 0


def check(label, ok, detail=""):
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label} {detail}")


def build_file(path):
    ns = runpy.run_path(path)
    return ns["solid"]


def build_source(source, hint):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(source)
        tmp = f.name
    try:
        return build_file(tmp)
    finally:
        os.unlink(tmp)


def expect_error(label, fn, *args, needle="", **kwargs):
    try:
        fn(*args, **kwargs)
    except keel.KeelError as e:
        check(label, needle in str(e), str(e))
    except Exception as e:  # noqa: BLE001
        check(label, False, f"wrong error type: {e!r}")
    else:
        check(label, False, "no error raised")


def same_shape(label, a, b):
    good, fails, _ = checks.score(a, b, checks.measure(b))
    check(label, good, f"fails={fails}")


def main():
    with open(os.path.join(EXAMPLES, "requests.json")) as f:
        requests = json.load(f)
    files = sorted(r["part"] for r in requests)

    for name in files:
        path = os.path.join(EXAMPLES, name)
        with open(path) as f:
            source = f.read()
        assert source.rstrip().endswith("solid = p.finish()"), f"{name} must end in solid = p.finish()"

        try:
            ref = build_file(path)
            m = checks.measure(ref)
            ok_build = m["solids"] == 1 and m["valid"]
        except Exception as e:  # noqa: BLE001
            ref, ok_build = None, False
            print(f"  build error {name}: {e!r}")
        check(f"{name} builds one valid solid", ok_build)

        if ok_build:
            expected = checks.measure(ref)
            good, fails, _ = checks.score(ref, ref, expected)
            check(f"{name} reference scores PASS against itself", good, f"fails={fails}")
        else:
            check(f"{name} reference scores PASS against itself", False, "no reference solid")

        for i, (find, repl) in enumerate(VARIANTS[name]):
            label = f"{name} wrong variant {i + 1}"
            if source.count(find) != 1:
                check(label, False, f"pattern {find!r} matches {source.count(find)}x, want 1x")
                continue
            try:
                bad = build_source(source.replace(find, repl), label)
            except Exception as e:  # noqa: BLE001
                check(label, False, f"variant did not build: {e!r}")
                continue
            good, fails, _ = checks.score(bad, ref, checks.measure(ref))
            check(label + " FAILs as expected", not good, "variant unexpectedly PASSED")

    # The three v1 KeelError cases.
    try:
        p = keel.part("ERR-1")
        p.stock(20, 20, 3)
        p.hole("M4", at=(10, 10))
        check("unknown fastener code raises KeelError", False, "no error raised")
    except keel.KeelError as e:
        check("unknown fastener code raises KeelError", "KF-M4" in str(e), str(e))

    try:
        p = keel.part("ERR-2")
        p.stock(20, 20, 3)
        p.stock(10, 10, 2)
        check("second stock() raises KeelError", False, "no error raised")
    except keel.KeelError as e:
        check("second stock() raises KeelError", True, str(e))

    try:
        p = keel.part("ERR-3")
        p.stock(20, 20, 3)
        p.hole("KF-M3", at=(10, 10))
        keel.render(p, os.path.join(tempfile.gettempdir(), "qow_unfinished.svg"))
        check("missing finish() raises KeelError", False, "no error raised")
    except keel.KeelError as e:
        check("missing finish() raises KeelError", "finish()" in str(e), str(e))

    # --- v2 rules ---
    # Materials: unknown code, minimum wall, per-material defaults.
    expect_error(
        "unknown material raises KeelError",
        keel.part, "ERR-M1", material="AL7075", needle="AL6061",
    )
    expect_error(
        "unknown part class raises KeelError",
        keel.part, "ERR-M2", cls="ORBITAL", needle="GSE",
    )

    def _wall_part(material, t):
        p = keel.part("W", material=material)
        p.stock(40, 40, 4)
        p.wall("north", 10, t=t)
        return p.finish()

    expect_error("wall below AL6061 minimum raises", _wall_part, "AL6061", 1.0, needle="minimum")
    expect_error("wall below TI6AL4V minimum raises", _wall_part, "TI6AL4V", 1.9, needle="2")
    same_shape("TI6AL4V default wall is 3.0", _ti_default_wall(), _wall_part("TI6AL4V", 3.0))

    # FLIGHT: plain hole rejected, auto fillet applied.
    def _flight_plain():
        p = keel.part("F1", material="AL6061", cls="FLIGHT")
        p.stock(40, 40, 4)
        p.hole("KF-M4", at=(10, 10))
        return p.finish()

    expect_error("FLIGHT plain hole raises", _flight_plain, needle="flight parts need -CB or -CS")

    def _flight_auto():
        p = keel.part("F2", material="TI6AL4V", cls="FLIGHT")
        p.stock(40, 40, 4)
        p.hole("KF-M4-CB", at=(10, 10))
        return p.finish()

    def _flight_explicit():
        p = keel.part("F3", material="TI6AL4V", cls="FLIGHT")
        p.stock(40, 40, 4)
        p.hole("KF-M4-CB", at=(10, 10))
        p.fillet(r=1.5)
        return p.finish()

    def _gse_no_fillet():
        p = keel.part("F4", material="TI6AL4V")
        p.stock(40, 40, 4)
        p.hole("KF-M4-CB", at=(10, 10))
        return p.finish()

    same_shape("FLIGHT auto fillet equals explicit standard fillet", _flight_auto(), _flight_explicit())
    auto, bare = _flight_auto(), _gse_no_fillet()
    good, fails, _ = checks.score(bare, auto, checks.measure(auto))
    check("FLIGHT auto fillet differs from no fillet", not good, "unexpectedly identical")

    def _flight_plain_mount():
        p = keel.part("F5", material="AL6061", cls="FLIGHT")
        p.stock(80, 60, 4)
        p.mount("PETREL-MOUNT-A", origin=(10, 10))
        return p.finish()

    expect_error("FLIGHT plain mount raises", _flight_plain_mount,
                 needle="flight parts need -CB or -CS")

    # Countersink: builds; differs from plain and from counterbore.
    def _cs_part(code):
        p = keel.part("CS", material="AL6061")
        p.stock(40, 40, 4)
        p.hole(code, at=(20, 20))
        return p.finish()

    cs, plain, cb = _cs_part("KF-M4-CS"), _cs_part("KF-M4"), _cs_part("KF-M4-CB")
    m = checks.measure(cs)
    check("countersunk hole builds one valid solid", m["solids"] == 1 and m["valid"])
    for other, tag in ((plain, "plain"), (cb, "counterbore")):
        good, fails, _ = checks.score(other, cs, checks.measure(cs))
        check(f"countersink differs from {tag} hole", not good, "unexpectedly identical")

    # Wall holes: positions on each edge; error cases.
    def _wall_hole_part(edge, u):
        p = keel.part("WH", material="AL6061")
        p.stock(60, 40, 4)
        p.wall(edge, 20)
        z = 10
        p.wall_hole(edge, "KF-M3", at=(u, z))
        return p.finish()

    for edge, u in (("north", 30), ("south", 30), ("east", 20), ("west", 20)):
        s = _wall_hole_part(edge, u)
        mm = checks.measure(s)
        check(f"wall_hole on {edge} builds one valid solid", mm["solids"] == 1 and mm["valid"])
    moved_n, moved_s = _wall_hole_part("north", 30), _wall_hole_part("north", 32)
    good, fails, _ = checks.score(moved_s, moved_n, checks.measure(moved_n))
    check("moved wall_hole FAILs as expected", not good, "variant unexpectedly PASSED")

    def _wh_no_wall():
        p = keel.part("WH-E1", material="AL6061")
        p.stock(60, 40, 4)
        p.wall_hole("north", "KF-M3", at=(30, 10))

    expect_error("wall_hole with no wall raises", _wh_no_wall, needle="no wall")

    def _wh_cb():
        p = keel.part("WH-E2", material="AL6061")
        p.stock(60, 40, 4)
        p.wall("north", 20)
        p.wall_hole("north", "KF-M3-CB", at=(30, 10))

    expect_error("wall_hole with -CB raises", _wh_cb, needle="plain KF code")

    def _wh_fit():
        p = keel.part("WH-E3", material="AL6061")
        p.stock(60, 40, 4)
        p.wall("north", 20)
        p.wall_hole("north", "KF-M3", at=(30, 19.5))

    expect_error("wall_hole outside the wall face raises", _wh_fit, needle="does not fit")

    def _wh_edge():
        p = keel.part("WH-E4", material="AL6061")
        p.stock(60, 40, 4)
        p.wall("north", 20)
        p.wall_hole("top", "KF-M3", at=(30, 10))

    expect_error("wall_hole on unknown edge raises", _wh_edge, needle="unknown edge")

    # Mounts: each builds; each equals its explicit holes; error cases.
    _MOUNT_CASES = [
        ("PETREL-MOUNT-A", (10, 10)),
        ("PETREL-MOUNT-B", (5, 5)),
        ("STAR-TRACKER-3", (40, 30)),
        ("HARNESS-P2", (10, 10)),
    ]
    for name, origin in _MOUNT_CASES:
        p = keel.part("M-" + name, material="AL6061")
        p.stock(80, 60, 4)
        p.mount(name, origin=origin)
        s = p.finish()
        mm = checks.measure(s)
        check(f"mount {name} builds one valid solid", mm["solids"] == 1 and mm["valid"])

        q = keel.part("M-" + name + "-ref", material="AL6061")
        q.stock(80, 60, 4)
        for code, (hx, hy) in keel._mount_holes(name, origin):
            q.hole(code, at=(hx, hy))
        same_shape(f"mount {name} equals its explicit holes", s, q.finish())

    def _mount_cs_ref():
        p = keel.part("MCS", material="AL6061")
        p.stock(80, 60, 4)
        p.mount("HARNESS-P2", origin=(10, 10), finish="CS")
        a = p.finish()
        q = keel.part("MCS-ref", material="AL6061")
        q.stock(80, 60, 4)
        q.hole("KF-M2-CS", at=(10, 10))
        q.hole("KF-M2-CS", at=(25, 10))
        same_shape("mount finish CS equals explicit -CS holes", a, q.finish())

    _mount_cs_ref()

    def _mount_bad_name():
        p = keel.part("M-E1", material="AL6061")
        p.stock(80, 60, 4)
        p.mount("PETREL-MOUNT-C", origin=(10, 10))

    expect_error("unknown mount raises", _mount_bad_name, needle="unknown mount")

    def _mount_bad_finish():
        p = keel.part("M-E2", material="AL6061")
        p.stock(80, 60, 4)
        p.mount("HARNESS-P2", origin=(10, 10), finish="gold")

    expect_error("unknown mount finish raises", _mount_bad_finish, needle="unknown mount finish")

    def _mount_pattern():
        p = keel.part("MP", material="AL6061")
        p.stock(80, 60, 4)
        p.mount("HARNESS-P2", origin=(10, 10))
        p.pattern(2, 1, 30, 0)
        return p.finish()

    def _mount_pattern_ref():
        q = keel.part("MP-ref", material="AL6061")
        q.stock(80, 60, 4)
        q.mount("HARNESS-P2", origin=(10, 10))
        q.mount("HARNESS-P2", origin=(40, 10))
        return q.finish()

    same_shape("pattern repeats the whole mount", _mount_pattern(), _mount_pattern_ref())

    # Mirror: equals explicit holes; walls untouched; pattern-after-mirror raises.
    def _mirrored():
        p = keel.part("MR", material="AL6061")
        p.stock(60, 40, 4)
        p.wall("north", 10)
        p.hole("KF-M4", at=(6, 6))
        p.mirror("ew")
        return p.finish()

    def _mirrored_ref():
        q = keel.part("MR-ref", material="AL6061")
        q.stock(60, 40, 4)
        q.wall("north", 10)
        q.hole("KF-M4", at=(6, 6))
        q.hole("KF-M4", at=(54, 6))
        return q.finish()

    same_shape("mirror ew equals explicit mirrored holes", _mirrored(), _mirrored_ref())

    def _mirrored_ns():
        p = keel.part("MRN", material="AL6061")
        p.stock(60, 40, 4)
        p.boss(at=(10, 10), dia=8, h=5)
        p.mirror("ns")
        return p.finish()

    def _mirrored_ns_ref():
        q = keel.part("MRN-ref", material="AL6061")
        q.stock(60, 40, 4)
        q.boss(at=(10, 10), dia=8, h=5)
        q.boss(at=(10, 30), dia=8, h=5)
        return q.finish()

    same_shape("mirror ns equals explicit mirrored boss", _mirrored_ns(), _mirrored_ns_ref())

    def _pattern_after_mirror():
        p = keel.part("MR-E1", material="AL6061")
        p.stock(60, 40, 4)
        p.hole("KF-M4", at=(6, 6))
        p.mirror("ew")
        p.pattern(2, 1, 10, 0)

    expect_error("pattern() after mirror() raises", _pattern_after_mirror, needle="after mirror()")

    def _mirror_bad_axis():
        p = keel.part("MR-E2", material="AL6061")
        p.stock(60, 40, 4)
        p.hole("KF-M4", at=(6, 6))
        p.mirror("diagonal")

    expect_error("unknown mirror axis raises", _mirror_bad_axis, needle="unknown mirror axis")

    # --- v2.1.0 rules: order-free build, no over-cut ---
    # A hole recorded before its boss still drills the boss (holes go all the
    # way down), and the result equals boss-before-hole exactly.
    def _boss_then_hole():
        p = keel.part("OF-1", material="AL6061")
        p.stock(60, 40, 4)
        p.boss(at=(30, 20), dia=12, h=8)
        p.hole("KF-M4", at=(30, 20))
        return p.finish()

    def _hole_then_boss():
        p = keel.part("OF-2", material="AL6061")
        p.stock(60, 40, 4)
        p.hole("KF-M4", at=(30, 20))
        p.boss(at=(30, 20), dia=12, h=8)
        return p.finish()

    same_shape("hole-before-boss equals boss-before-hole", _hole_then_boss(), _boss_then_hole())

    def _wall_hole_order(ref_first):
        p = keel.part("OF-3", material="AL6061")
        p.stock(60, 40, 4)
        if ref_first:
            p.wall("north", 10)
            p.hole("KF-M4", at=(30, 38))
        else:
            p.hole("KF-M4", at=(30, 38))
            p.wall("north", 10)
        return p.finish()

    same_shape("hole-before-wall equals wall-before-hole", _wall_hole_order(False), _wall_hole_order(True))

    # Pocket and counterbore next to a wall must leave the wall volume intact.
    import cadquery as cq  # noqa: E402

    p = keel.part("NC-1", material="AL6061")
    p.stock(60, 40, 4)
    p.wall("north", 10)  # default t=2.5: y in [37.5, 40], z in [4, 14]
    p.pocket(at=(10, 34), L=20, W=5, depth=2)  # overlaps wall plan by 1.5 mm
    p.hole("KF-M4-CB", at=(45, 34.5))  # CB disc overlaps wall; clearance does not
    s = p.finish()
    m_nc = checks.measure(s)
    check("pocket+counterbore near wall builds one valid solid",
          m_nc["solids"] == 1 and m_nc["valid"])
    wall_box = cq.Solid.makeBox(60, 2.5, 10, pnt=cq.Vector(0, 37.5, 4))
    kept = s.intersect(wall_box).Volume()
    check("pocket+counterbore leave the wall volume intact",
          abs(kept - wall_box.Volume()) / wall_box.Volume() < 1e-4,
          f"wall kept={kept:g} full={wall_box.Volume():g}")

    print(f"SELFTEST {passed}/{total} PASS")
    return 0 if passed == total else 1


def _ti_default_wall():
    p = keel.part("W-TI", material="TI6AL4V")
    p.stock(40, 40, 4)
    p.wall("north", 10)
    return p.finish()


if __name__ == "__main__":
    sys.exit(main())
