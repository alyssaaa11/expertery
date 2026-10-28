"""Quillon Orbital Works self-test (SPEC section 6).

Builds every example part, scores each reference against itself with the
existing referee (experiments/first-test/checks.py, never modified here),
checks that two deliberately wrong variants per example FAIL, and checks the
three KeelError cases. Prints a summary line ``SELFTEST x/y PASS``.
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

_CHECKS = os.path.join(
    HERE, "..", "experiments", "first-test", "checks.py"
)
_spec = importlib.util.spec_from_file_location("qow_checks", os.path.abspath(_CHECKS))
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

    # The three KeelError cases.
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

    print(f"SELFTEST {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
