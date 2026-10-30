"""Deterministic practice-job generator (factory SPEC section 1).

Ten NEW hard-style families (each job = 4-8 features placed by exact
relations; numbers vary per job within safe ranges; every job's text
gives every coordinate, like experiments/first-test/jobs.py texts).
Seed 20261029. Twenty jobs per family (200), ids F<family>-<n>.

Each family is a function params -> (text, reference_program_source).
Reference sources are self-contained answer-style programs (they assign
`result`); the grader executes them. Reference programs are trusted
generator code and may run locally (self-checks, tests).

Parameter ranges keep features from touching or overlapping by
accident: every range was picked so clearances hold for all sampled
values (the self-check builds all 200 and asserts one valid solid).

Round-first rule: each family's text/src pair shares one canonical set
of numbers, every value rounded to the printed precision BEFORE either
side uses it. The reference program is built from exactly the printed
numbers: diameters enter the program and radii exist only as
(diameter)/2 inside it; profile corners only as (centre +/- width/2);
overshoots only as (printed value + 1). make_jobs.py's TEXT=REF column
checks this per job (every non-small-integer literal in the reference
appears among the numbers printed in the text).
"""

import math
import random

SEED = 20261029
N_FAMILIES = 10
JOBS_PER_FAMILY = 20

PREAMBLE = """import cadquery as cq
from cadquery import Solid, Vector

def _box(x0, x1, y0, y1, z0, z1):
    return Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))

def _zcyl(r, x, y, z0, z1):
    return Solid.makeCylinder(r, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))

def _xcyl(r, y, z, x0, x1):
    return Solid.makeCylinder(r, x1 - x0, Vector(x0, y, z), Vector(1, 0, 0))

def _ycyl(r, x, z, y0, y1):
    return Solid.makeCylinder(r, y1 - y0, Vector(x, y0, z), Vector(0, 1, 0))
"""


def num(v):
    """Short exact number for texts and sources (ints stay ints)."""
    v = round(float(v), 1)
    if v == int(v):
        return str(int(v))
    return str(v)


def r1(rng, lo, hi):
    """One-decimal uniform sample (text and source share the value)."""
    return round(rng.uniform(lo, hi), 1)


def src(body):
    """A reference program source from a body block."""
    return PREAMBLE + body


# ------------------------------------------------------- 1. spool / bobbin


def gen1(rng):
    Rf = r1(rng, 18, 24)
    tf = r1(rng, 3, 5)
    Rc = r1(rng, 8, 11)
    Hc = r1(rng, 16, 24)
    Rb = r1(rng, 3, 5)
    sw = r1(rng, 3, 5)
    return {"Rf": Rf, "tf": tf, "Rc": Rc, "Hc": Hc, "Rb": Rb, "sw": sw,
            "sy": 0.0}


def _c1(p):
    """Canonical F1 numbers: every value rounded to the printed precision.

    text1 prints exactly these; src1 builds from exactly these (diameters
    enter the program, radii only as (diameter)/2 inside it)."""
    return {
        "Df": round(p["Rf"] * 2, 1),
        "Dc": round(p["Rc"] * 2, 1),
        "Db": round(p["Rb"] * 2, 1),
        "tf": round(p["tf"], 1),
        "zc1": round(p["tf"] + p["Hc"], 1),
        "H": round(p["tf"] * 2 + p["Hc"], 1),
        "sw": round(p["sw"], 1),
        "x0": round(-p["Rf"] - 1, 1),
        "x1": round(p["Rf"] + 1, 1),
        "y0": round(p["sy"] - p["sw"] / 2, 1),
        "y1": round(p["sy"] + p["sw"] / 2, 1),
    }


def text1(p):
    c = _c1(p)
    return (
        "Units: millimetres. Z is up. A spool (bobbin) on the Z axis, "
        "centred at X = 0, Y = 0. Bottom flange: diameter %s, Z from 0 "
        "to %s. Core: diameter %s, Z from %s to %s. Top flange: diameter "
        "%s, Z from %s to %s. A centre bore of diameter %s goes through "
        "everything along the Z axis. A wire slot %s wide cuts through "
        "the bottom flange along X: X from %s to %s, Y from %s to %s, "
        "Z from 0 to %s."
        % (num(c["Df"]), num(c["tf"]), num(c["Dc"]),
           num(c["tf"]), num(c["zc1"]), num(c["Df"]),
           num(c["zc1"]), num(c["H"]), num(c["Db"]), num(c["sw"]),
           num(c["x0"]), num(c["x1"]),
           num(c["y0"]), num(c["y1"]),
           num(c["tf"])))


def src1(p):
    c = _c1(p)
    return src(
        "b = _zcyl((%s)/2, 0, 0, 0, %s)\n"
        "c = _zcyl((%s)/2, 0, 0, %s, %s)\n"
        "t = _zcyl((%s)/2, 0, 0, %s, %s)\n"
        "s = b.fuse(c, t)\n"
        "s = s.cut(_zcyl((%s)/2, 0, 0, -1, (%s + 1)))\n"
        "s = s.cut(_box(%s, %s, %s, %s, 0, %s))\n"
        "result = s\n"
        % (num(c["Df"]), num(c["tf"]), num(c["Dc"]), num(c["tf"]),
           num(c["zc1"]), num(c["Df"]), num(c["zc1"]),
           num(c["H"]), num(c["Db"]), num(c["H"]), num(c["x0"]),
           num(c["x1"]), num(c["y0"]), num(c["y1"]), num(c["tf"])))


def wrong1(p):
    a = dict(p)
    a["sy"] = 4.0  # moved feature: the slot shifts sideways
    b = dict(p)
    b["Rb"] = round(p["Rb"] + 1.5, 1)  # wrong size: wider bore
    return [a, b]


# ------------------------------------------------------- 2. manifold block


def gen2(rng):
    L = r1(rng, 80, 110)
    W = r1(rng, 70, 100)
    H = r1(rng, 48, 60)
    nx = rng.choice([2, 3])
    ny = rng.choice([2, 3])
    rx = r1(rng, 4, 6)
    ry = r1(rng, 4, 5)
    rb = r1(rng, 4, 6)
    h1 = round(H * 0.3, 1)
    h2 = round(H * 0.7, 1)
    ys = [round(W * (i + 1) / (nx + 1) + rng.uniform(-1, 1), 1)
          for i in range(nx)]
    xs = [round(L * (j + 1) / (ny + 1) + rng.uniform(-1, 1), 1)
          for j in range(ny)]
    return {"L": L, "W": W, "H": H, "nx": nx, "ny": ny, "rx": rx,
            "ry": ry, "rb": rb, "h1": h1, "h2": h2, "ys": ys, "xs": xs,
            "bx": round(L - 14, 1), "by": round(W - 14, 1),
            "zb": round(h2 + ry + 3, 1)}


def text2(p):
    lines = [
        "Units: millimetres. Z is up. A manifold block: X from 0 to %s, "
        "Y from 0 to %s, Z from 0 to %s." % (num(p["L"]), num(p["W"]),
                                            num(p["H"]))]
    for i, y in enumerate(p["ys"]):
        lines.append(
            "Cross port %d along X: diameter %s, at Y = %s, Z = %s, "
            "X from -1 to %s." % (i + 1, num(p["rx"] * 2), num(y),
                                  num(p["h1"]), num(p["L"] + 1)))
    for j, x in enumerate(p["xs"]):
        lines.append(
            "Cross port %d along Y: diameter %s, at X = %s, Z = %s, "
            "Y from -1 to %s." % (j + 1, num(p["ry"] * 2), num(x),
                                  num(p["h2"]), num(p["W"] + 1)))
    lines.append(
        "Blind port from the top: diameter %s, centred at (X, Y) = (%s, "
        "%s), Z from %s to %s." % (num(p["rb"] * 2), num(p["bx"]),
                                   num(p["by"]), num(p["zb"]),
                                   num(p["H"] + 1)))
    return " ".join(lines)


def src2(p):
    # Diameters enter the program; radii only as (diameter)/2 inside it.
    # Overshoots are (printed value + 1), never a precomputed literal.
    Dx, Dy, Db = round(p["rx"] * 2, 1), round(p["ry"] * 2, 1), \
        round(p["rb"] * 2, 1)
    body = "s = _box(0, %s, 0, %s, 0, %s)\n" % (
        num(p["L"]), num(p["W"]), num(p["H"]))
    for y in p["ys"]:
        body += "s = s.cut(_xcyl((%s)/2, %s, %s, -1, (%s + 1)))\n" % (
            num(Dx), num(y), num(p["h1"]), num(p["L"]))
    for x in p["xs"]:
        body += "s = s.cut(_ycyl((%s)/2, %s, %s, -1, (%s + 1)))\n" % (
            num(Dy), num(x), num(p["h2"]), num(p["W"]))
    body += "s = s.cut(_zcyl((%s)/2, %s, %s, %s, (%s + 1)))\nresult = s\n" % (
        num(Db), num(p["bx"]), num(p["by"]), num(p["zb"]), num(p["H"]))
    return src(body)


def wrong2(p):
    a = dict(p)
    a["ys"] = [round(p["ys"][0] + 4, 1)] + list(p["ys"][1:])
    b = dict(p)
    b["rb"] = round(p["rb"] + 2, 1)
    return [a, b]


# ------------------------------------------------------- 3. dovetail slide


def gen3(rng):
    L = r1(rng, 70, 100)
    W = r1(rng, 44, 60)
    H = r1(rng, 24, 32)
    wo = r1(rng, 12, 16)
    gd = r1(rng, 8, 11)
    A = r1(rng, 15, 25)
    wb = round(wo + 2 * gd * math.tan(math.radians(A)), 1)
    dh = r1(rng, 5, 8)
    return {"L": L, "W": W, "H": H, "wo": wo, "gd": gd, "A": A,
            "wb": wb, "dh": dh, "x1": round(L * 0.25, 1),
            "x2": round(L * 0.75, 1), "gc": 0.0}


def _c3(p):
    """Canonical F3 numbers, rounded to the printed precision first.

    The groove is defined by its printed opening/floor widths and centre;
    the profile corners exist only inside the program as (centre +/- width/2).
    """
    return {
        "L": round(p["L"], 1),
        "W": round(p["W"], 1),
        "H": round(p["H"], 1),
        "wo": round(p["wo"], 1),
        "wb": round(p["wb"], 1),
        "A": round(p["A"], 1),
        "yc": round(p["W"] / 2 + p["gc"], 1),
        "zf": round(p["H"] - p["gd"], 1),
        "dh": round(p["dh"], 1),
        "x1": round(p["x1"], 1),
        "x2": round(p["x2"], 1),
    }


def text3(p):
    c = _c3(p)
    return (
        "Units: millimetres. Z is up. A dovetail slide: a block X from 0 "
        "to %s, Y from 0 to %s, Z from 0 to %s. A dovetail groove runs "
        "along X for the whole length: opening width %s at the top face "
        "(Z = %s), floor width %s at depth (Z = %s), sides tilting "
        "outward by %s degrees from vertical, centred at Y = %s. Two "
        "end holes of diameter %s go through along Z at (X, Y) = (%s, "
        "%s) and (%s, %s)."
        % (num(c["L"]), num(c["W"]), num(c["H"]), num(c["wo"]),
           num(c["H"]), num(c["wb"]), num(c["zf"]), num(c["A"]),
           num(c["yc"]), num(c["dh"]), num(c["x1"]), num(c["yc"]),
           num(c["x2"]), num(c["yc"])))


def src3(p):
    c = _c3(p)
    return src(
        "prof = cq.Workplane(\"YZ\").polyline([((%s) - (%s)/2, %s), "
        "((%s) + (%s)/2, %s), ((%s) + (%s)/2, %s), ((%s) - (%s)/2, %s)])"
        ".close().extrude(%s).val()\n"
        "s = _box(0, %s, 0, %s, 0, %s)\n"
        "s = s.cut(prof)\n"
        "s = s.cut(_zcyl((%s)/2, %s, %s, -1, (%s + 1)))\n"
        "s = s.cut(_zcyl((%s)/2, %s, %s, -1, (%s + 1)))\n"
        "result = s\n"
        % (num(c["yc"]), num(c["wb"]), num(c["zf"]),
           num(c["yc"]), num(c["wb"]), num(c["zf"]),
           num(c["yc"]), num(c["wo"]), num(c["H"]),
           num(c["yc"]), num(c["wo"]), num(c["H"]), num(c["L"]),
           num(c["L"]), num(c["W"]), num(c["H"]),
           num(c["dh"]), num(c["x1"]), num(c["yc"]), num(c["H"]),
           num(c["dh"]), num(c["x2"]), num(c["yc"]), num(c["H"])))


def wrong3(p):
    a = dict(p)
    a["gc"] = 3.0  # moved feature: the groove shifts sideways
    b = dict(p)
    b["dh"] = round(p["dh"] + 2, 1)  # wrong size: bigger end holes
    return [a, b]


# ------------------------------------------------------- 4. cam plate


def gen4(rng):
    R = r1(rng, 28, 36)
    T = r1(rng, 8, 12)
    rb = r1(rng, 6, 9)
    ex = r1(rng, 6, R - rb - 6)
    sw = r1(rng, 4, min(6, rb))
    th = r1(rng, 15, 75)
    return {"R": R, "T": T, "rb": rb, "ex": ex, "sw": sw, "th": th}


def _slot_points(p):
    c, s = math.cos(math.radians(p["th"])), math.sin(math.radians(p["th"]))
    r0, r9 = p["ex"] - p["rb"], p["R"] + 1
    return (round(r0 * c, 1), round(r0 * s, 1),
            round(r9 * c, 1), round(r9 * s, 1))


def _c4(p):
    """Canonical F4 numbers, rounded to the printed precision first.

    The slot is defined by its printed centreline endpoints, its printed
    width, and square ends; the program rebuilds it from exactly those
    (length and angle exist only inside the program, derived from the
    printed endpoints)."""
    x0, y0, x9, y9 = _slot_points(p)
    return {
        "D": round(p["R"] * 2, 1),
        "T": round(p["T"], 1),
        "Db": round(p["rb"] * 2, 1),
        "ex": round(p["ex"], 1),
        "sw": round(p["sw"], 1),
        "x0": x0,
        "y0": y0,
        "x9": x9,
        "y9": y9,
    }


def text4(p):
    c = _c4(p)
    return (
        "Units: millimetres. Z is up. A cam plate: a disk of diameter %s, "
        "Z from 0 to %s, centred at X = 0, Y = 0. An eccentric bore of "
        "diameter %s goes through along Z, centred at (X, Y) = (%s, 0). "
        "A slot %s wide with square ends cuts through along Z: its "
        "centreline runs from (%s, %s) to (%s, %s)."
        % (num(c["D"]), num(c["T"]), num(c["Db"]), num(c["ex"]),
           num(c["sw"]), num(c["x0"]), num(c["y0"]),
           num(c["x9"]), num(c["y9"])))


def src4(p):
    c = _c4(p)
    return src(
        "import math\n"
        "d = _zcyl((%s)/2, 0, 0, 0, %s)\n"
        "d = d.cut(_zcyl((%s)/2, %s, 0, -1, (%s + 1)))\n"
        "dx = (%s) - (%s)\n"
        "dy = (%s) - (%s)\n"
        "slot = _box(0, math.hypot(dx, dy), -(%s)/2, (%s)/2, -1, "
        "(%s + 1))\n"
        "slot = slot.rotate(Vector(0, 0, 0), Vector(0, 0, 1), "
        "math.degrees(math.atan2(dy, dx)))\n"
        "slot = slot.translate(Vector(%s, %s, 0))\n"
        "result = d.cut(slot)\n"
        % (num(c["D"]), num(c["T"]), num(c["Db"]), num(c["ex"]),
           num(c["T"]), num(c["x9"]), num(c["x0"]), num(c["y9"]),
           num(c["y0"]), num(c["sw"]), num(c["sw"]), num(c["T"]),
           num(c["x0"]), num(c["y0"])))


def wrong4(p):
    a = dict(p)
    a["ex"] = round(p["ex"] + 3, 1)  # moved feature: bore shifts out
    b = dict(p)
    b["rb"] = round(p["rb"] + 1.5, 1)  # wrong size: bigger bore
    return [a, b]


# ------------------------------------------------------- 5. pipe tee fitting


def gen5(rng):
    Lm = r1(rng, 70, 100)
    Rm = r1(rng, 12, 16)
    wall = r1(rng, 3, 4)
    Rb2 = r1(rng, 10, min(14, Rm))
    wall2 = r1(rng, 3, 4)
    return {"Lm": Lm, "Rm": Rm, "rm": round(Rm - wall, 1), "Rb2": Rb2,
            "rb2": round(Rb2 - wall2, 1),
            "xb": round(Lm * rng.uniform(0.42, 0.58), 1),
            "Lb": r1(rng, 30, 50), "Rf2": round(Rm + rng.uniform(6, 8), 1)}


def text5(p):
    return (
        "Units: millimetres. A pipe tee. Main tube along X: outer "
        "diameter %s, inner diameter %s, X from 0 to %s, axis at Y = 0, "
        "Z = 0. Branch tube along Y: outer diameter %s, inner diameter "
        "%s, axis at X = %s, Z = 0, Y from -1 to %s (it joins the main "
        "tube). A flange at the X = 0 end: diameter %s, X from -6 to 0, "
        "with a centre hole of diameter %s."
        % (num(p["Rm"] * 2), num(p["rm"] * 2), num(p["Lm"]),
           num(p["Rb2"] * 2), num(p["rb2"] * 2), num(p["xb"]),
           num(p["Lb"]), num(p["Rf2"] * 2), num(p["rm"] * 2)))


def src5(p):
    # Diameters enter the program; radii only as (diameter)/2 inside it.
    # Bore overshoots are (printed value + 1), never precomputed literals.
    # Round 1d: the main bore and the flange centre hole are ONE coaxial
    # cut (the old two overlapping cuts are the same solid but their face
    # structure makes the default Volume() noisy). The branch bore starts
    # exactly at the printed branch end (-1): the old -2 start removed a
    # disc of main-tube wall the text never describes.
    Dm, dm = round(p["Rm"] * 2, 1), round(p["rm"] * 2, 1)
    Db2, db2 = round(p["Rb2"] * 2, 1), round(p["rb2"] * 2, 1)
    Df2 = round(p["Rf2"] * 2, 1)
    return src(
        "main = _xcyl((%s)/2, 0, 0, 0, %s)\n"
        "branch = _ycyl((%s)/2, %s, 0, -1, %s)\n"
        "flange = _xcyl((%s)/2, 0, 0, -6, 0)\n"
        "s = main.fuse(branch, flange)\n"
        "s = s.cut(_xcyl((%s)/2, 0, 0, (-6 - 1), (%s + 1)))\n"
        "s = s.cut(_ycyl((%s)/2, %s, 0, -1, (%s + 1)))\n"
        "result = s\n"
        % (num(Dm), num(p["Lm"]), num(Db2), num(p["xb"]),
           num(p["Lb"]), num(Df2), num(dm), num(p["Lm"]),
           num(db2), num(p["xb"]), num(p["Lb"])))


def wrong5(p):
    a = dict(p)
    a["xb"] = round(p["xb"] + 5, 1)  # moved feature: branch shifts
    b = dict(p)
    b["rm"] = round(p["rm"] + 1.5, 1)  # wrong size: thinner walls
    return [a, b]


# ------------------------------------------------------- 6. lattice panel


def gen6(rng):
    L = r1(rng, 110, 150)
    W = r1(rng, 36, 52)
    T = r1(rng, 4, 6)
    b = r1(rng, 5, 7)
    n = rng.choice([4, 5, 6])
    pitch = (L - 2 * b) / n
    wb = r1(rng, 10, min(16, pitch - 4))
    ht = round(W - 2 * b - 4, 1)
    yb = round(b + 2, 1)
    cx = [round(b + pitch * (i + 0.5), 1) for i in range(n)]
    return {"L": L, "W": W, "T": T, "b": b, "n": n, "wb": wb,
            "ht": ht, "yb": yb, "yt": round(W - b - 2, 1), "cx": cx,
            "dx": 0.0, "dw": 0.0}


def _tri6(p, i):
    cx = p["cx"][i] + (p["dx"] if i == 0 else 0.0)
    wb = p["wb"] + (p["dw"] if i == 1 else 0.0)
    if i % 2 == 0:  # point up: base at the bottom
        return [(round(cx - wb / 2, 1), p["yb"]),
                (round(cx + wb / 2, 1), p["yb"]),
                (cx, round(p["yb"] + p["ht"], 1))]
    return [(round(cx - wb / 2, 1), p["yt"]),
            (round(cx + wb / 2, 1), p["yt"]),
            (cx, round(p["yt"] - p["ht"], 1))]


def text6(p):
    lines = [
        "Units: millimetres. Z is up. A lattice panel: a plate X from 0 "
        "to %s, Y from 0 to %s, Z from 0 to %s. A row of %d triangular "
        "cut-outs through Z, alternating point-up and point-down, with "
        "a solid border of at least %s all round:"
        % (num(p["L"]), num(p["W"]), num(p["T"]), p["n"], num(p["b"]))]
    for i in range(p["n"]):
        v = _tri6(p, i)
        lines.append(
            "Triangle %d (%s): (%s, %s), (%s, %s), (%s, %s)."
            % (i + 1, "up" if i % 2 == 0 else "down", num(v[0][0]),
               num(v[0][1]), num(v[1][0]), num(v[1][1]), num(v[2][0]),
               num(v[2][1])))
    return " ".join(lines)


def src6(p):
    body = "s = _box(0, %s, 0, %s, 0, %s)\n" % (
        num(p["L"]), num(p["W"]), num(p["T"]))
    for i in range(p["n"]):
        v = _tri6(p, i)
        body += ("tri = cq.Workplane(\"XY\").polyline([(%s, %s), (%s, %s), "
                 "(%s, %s)]).close().extrude(%s).val()\n"
                 "s = s.cut(tri)\n"
                 % (num(v[0][0]), num(v[0][1]), num(v[1][0]),
                    num(v[1][1]), num(v[2][0]), num(v[2][1]),
                    num(p["T"])))
    return src(body + "result = s\n")


def wrong6(p):
    a = dict(p)
    a["dx"] = 3.0  # moved feature: the first triangle shifts
    b = dict(p)
    b["dw"] = 3.0  # wrong size: the second triangle grows
    return [a, b]


# ------------------------------------------------------- 7. T-slot rail


def gen7(rng):
    L = r1(rng, 80, 120)
    W = r1(rng, 34, 46)
    H = r1(rng, 24, 34)
    wn = r1(rng, 8, 12)
    ww = round(wn + rng.uniform(8, 12), 1)
    sd = r1(rng, 12, 18)
    uh = r1(rng, 5, 8)
    return {"L": L, "W": W, "H": H, "wn": wn, "ww": ww, "sd": sd,
            "uh": uh, "z0": round(H - sd, 1),
            "z1": round(H - sd + uh, 1),
            "x1": r1(rng, 10, 14),
            "x2": round(L - rng.uniform(10, 14), 1),
            "dh": r1(rng, 5, 8), "yc": 0.0}


def _c7(p):
    """Canonical F7 numbers, rounded to the printed precision first.

    The slot is defined by its printed widths, centre and levels; the
    profile corners exist only inside the program as (centre +/- width/2).
    """
    return {
        "L": round(p["L"], 1),
        "W": round(p["W"], 1),
        "H": round(p["H"], 1),
        "wn": round(p["wn"], 1),
        "ww": round(p["ww"], 1),
        "yc": round(p["W"] / 2 + p["yc"], 1),
        "z0": round(p["z0"], 1),
        "z1": round(p["z1"], 1),
        "dh": round(p["dh"], 1),
        "x1": round(p["x1"], 1),
        "x2": round(p["x2"], 1),
    }


def text7(p):
    c = _c7(p)
    return (
        "Units: millimetres. Z is up. A T-slot rail: a bar X from 0 to "
        "%s, Y from 0 to %s, Z from 0 to %s. A T-shaped slot runs along "
        "X for the whole length, centred at Y = %s: a narrow opening %s "
        "wide from the top face (Z = %s) down to Z = %s, and a wider "
        "undercut %s wide from Z = %s down to the slot floor at Z = %s. "
        "Two end holes of diameter %s go through along Z at (X, Y) = "
        "(%s, %s) and (%s, %s)."
        % (num(c["L"]), num(c["W"]), num(c["H"]), num(c["yc"]),
           num(c["wn"]), num(c["H"]), num(c["z1"]), num(c["ww"]),
           num(c["z1"]), num(c["z0"]), num(c["dh"]), num(c["x1"]),
           num(c["yc"]), num(c["x2"]), num(c["yc"])))


def src7(p):
    c = _c7(p)
    yc, ww, wn = num(c["yc"]), num(c["ww"]), num(c["wn"])
    z0, z1, H = num(c["z0"]), num(c["z1"]), num(c["H"])
    lo_w = "(%s) - (%s)/2" % (yc, ww)
    hi_w = "(%s) + (%s)/2" % (yc, ww)
    lo_n = "(%s) - (%s)/2" % (yc, wn)
    hi_n = "(%s) + (%s)/2" % (yc, wn)
    pts = [(lo_w, z0), (hi_w, z0),
           (hi_w, z1), (hi_n, z1),
           (hi_n, H), (lo_n, H),
           (lo_n, z1), (lo_w, z1)]
    prof = ", ".join("(%s, %s)" % (y, z) for y, z in pts)
    return src(
        "prof = cq.Workplane(\"YZ\").polyline([%s]).close().extrude("
        "%s).val()\n"
        "s = _box(0, %s, 0, %s, 0, %s)\n"
        "s = s.cut(prof)\n"
        "s = s.cut(_zcyl((%s)/2, %s, %s, -1, (%s + 1)))\n"
        "s = s.cut(_zcyl((%s)/2, %s, %s, -1, (%s + 1)))\n"
        "result = s\n"
        % (prof, num(c["L"]), num(c["L"]), num(c["W"]), num(c["H"]),
           num(c["dh"]), num(c["x1"]), num(c["yc"]), num(c["H"]),
           num(c["dh"]), num(c["x2"]), num(c["yc"]), num(c["H"])))


def wrong7(p):
    a = dict(p)
    a["yc"] = 3.0  # moved feature: the slot shifts sideways
    b = dict(p)
    b["wn"] = round(p["wn"] + 3, 1)  # wrong size: wider opening
    return [a, b]


# ------------------------------------------------------- 8. bezel frame


def gen8(rng):
    L = r1(rng, 80, 110)
    W = r1(rng, 60, 90)
    T = r1(rng, 4, 6)
    bw = r1(rng, 12, 16)
    r = r1(rng, 6, 10)
    td = r1(rng, 10, 14)
    tw = r1(rng, 20, 30)
    thd = r1(rng, 5, td - 4)
    return {"L": L, "W": W, "T": T, "bw": bw,
            "lw": round(L - 2 * bw, 1), "ww": round(W - 2 * bw, 1),
            "r": r, "td": td, "tw": tw, "thd": thd, "hx": 0.0}


def _c8(p):
    """Canonical F8 numbers, rounded to the printed precision first."""
    return {
        "L": round(p["L"], 1),
        "W": round(p["W"], 1),
        "T": round(p["T"], 1),
        "lw": round(p["lw"], 1),
        "ww": round(p["ww"], 1),
        "r": round(p["r"], 1),
        "td": round(p["td"], 1),
        "tw": round(p["tw"], 1),
        "thd": round(p["thd"], 1),
        "hx": round(p["hx"], 1),
        "cx": round(p["L"] / 2, 1),
        "cy": round(p["W"] / 2, 1),
    }


def _tabs8(p):
    c = _c8(p)
    cx, cy = c["cx"], c["cy"]
    hw = round(c["tw"] / 2, 1)
    return [
        ("left", round(-c["td"], 1), 3, round(cy - hw, 1),
         round(cy + hw, 1), round(-c["td"] / 2 + c["hx"], 1), cy),
        ("right", round(c["L"] - 3, 1), round(c["L"] + c["td"], 1),
         round(cy - hw, 1), round(cy + hw, 1),
         round(c["L"] + c["td"] / 2, 1), cy),
        ("bottom", round(cx - hw, 1), round(cx + hw, 1),
         round(-c["td"], 1), 3, cx, round(-c["td"] / 2, 1)),
        ("top", round(cx - hw, 1), round(cx + hw, 1),
         round(c["W"] - 3, 1), round(c["W"] + c["td"], 1),
         cx, round(c["W"] + c["td"] / 2, 1)),
    ]


def text8(p):
    c = _c8(p)
    lines = [
        "Units: millimetres. Z is up. A bezel frame: a plate X from 0 "
        "to %s, Y from 0 to %s, Z from 0 to %s, with a rounded-rectangle "
        "window through Z: centre (%s, %s), %s by %s, corner radius %s."
        % (num(c["L"]), num(c["W"]), num(c["T"]), num(c["cx"]),
           num(c["cy"]), num(c["lw"]), num(c["ww"]), num(c["r"]))]
    for name, x0, x1, y0, y1, hx, hy in _tabs8(p):
        lines.append(
            "Tab %s: X from %s to %s, Y from %s to %s, Z from 0 to %s, "
            "with a %s mm hole through Z at (%s, %s)."
            % (name, num(x0), num(x1), num(y0), num(y1), num(c["T"]),
               num(c["thd"]), num(hx), num(hy)))
    return " ".join(lines)


def src8(p):
    c = _c8(p)
    cx, cy = num(c["cx"]), num(c["cy"])
    lw, ww, r = num(c["lw"]), num(c["ww"]), num(c["r"])
    T = num(c["T"])
    # Window corners exist only inside the program, as
    # (centre +/- size/2), with the corner radius added back.
    body = (
        "s = _box(0, %s, 0, %s, 0, %s)\n"
        "win = _box((%s) - (%s)/2 + (%s), (%s) + (%s)/2 - (%s), "
        "%s, %s, -1, (%s + 1))\n"
        "win = win.fuse(_box(%s, %s, (%s) - (%s)/2 + (%s), "
        "(%s) + (%s)/2 - (%s), -1, (%s + 1)))\n"
        % (num(c["L"]), num(c["W"]), T, cx, lw, r, cx, lw, r,
           "(%s) - (%s)/2" % (cy, ww), "(%s) + (%s)/2" % (cy, ww),
           T, "(%s) - (%s)/2" % (cx, lw), "(%s) + (%s)/2" % (cx, lw),
           cy, ww, r, cy, ww, r, T))
    for sx, sy in (("- (%s)/2 + (%s)" % (lw, r), "- (%s)/2 + (%s)" % (ww, r)),
                   ("+ (%s)/2 - (%s)" % (lw, r), "- (%s)/2 + (%s)" % (ww, r)),
                   ("- (%s)/2 + (%s)" % (lw, r), "+ (%s)/2 - (%s)" % (ww, r)),
                   ("+ (%s)/2 - (%s)" % (lw, r), "+ (%s)/2 - (%s)" % (ww, r))):
        body += "win = win.fuse(_zcyl((%s), (%s) %s, (%s) %s, -1, " \
            "(%s + 1)))\n" % (r, cx, sx, cy, sy, T)
    body += "s = s.cut(win)\n"
    for _name, x0, x1, y0, y1, hx, hy in _tabs8(p):
        body += "s = s.fuse(_box(%s, %s, %s, %s, 0, %s))\n" % (
            num(x0), num(x1), num(y0), num(y1), T)
        body += "s = s.cut(_zcyl((%s)/2, %s, %s, -1, (%s + 1)))\n" % (
            num(c["thd"]), num(hx), num(hy), T)
    return src(body + "result = s\n")


def wrong8(p):
    a = dict(p)
    a["hx"] = 3.0  # moved feature: the left tab hole shifts
    b = dict(p)
    b["lw"] = round(p["lw"] + 4, 1)  # wrong size: wider window
    return [a, b]


# ------------------------------------------------------- 9. ported cap


def gen9(rng):
    R = r1(rng, 24, 32)
    H = r1(rng, 36, 48)
    rp = r1(rng, 5, 8)
    hp = r1(rng, 13, 17)
    rr = r1(rng, round(R * 0.5, 1), R - 8)
    return {"R": R, "H": H, "rp": rp, "hp": hp, "rr": rr,
            "fz": round(hp + rp + 6, 1)}


def text9(p):
    return (
        "Units: millimetres. Z is up. A ported cap: a cylinder of "
        "diameter %s, Z from 0 to %s, centred at X = 0, Y = 0. A side "
        "port of diameter %s runs along X at (Y, Z) = (0, %s): blind, "
        "from the +X face to the centre. A top recess of diameter %s "
        "goes down from the top face to Z = %s."
        % (num(p["R"] * 2), num(p["H"]), num(p["rp"] * 2), num(p["hp"]),
           num(p["rr"] * 2), num(p["fz"])))


def src9(p):
    # Diameters enter the program; radii only as (diameter)/2 inside it.
    # The side port runs from the centre to ((diameter)/2 + 1).
    D, Dp, Dr = round(p["R"] * 2, 1), round(p["rp"] * 2, 1), \
        round(p["rr"] * 2, 1)
    return src(
        "s = _zcyl((%s)/2, 0, 0, 0, %s)\n"
        "s = s.cut(_xcyl((%s)/2, 0, %s, 0, ((%s)/2 + 1)))\n"
        "s = s.cut(_zcyl((%s)/2, 0, 0, %s, (%s + 1)))\n"
        "result = s\n"
        % (num(D), num(p["H"]), num(Dp), num(p["hp"]), num(D),
           num(Dr), num(p["fz"]), num(p["H"])))


def wrong9(p):
    a = dict(p)
    a["hp"] = round(p["hp"] + 4, 1)  # moved feature: port moves up
    b = dict(p)
    b["rr"] = round(p["rr"] + 3, 1)  # wrong size: wider recess
    return [a, b]


# ------------------------------------------------------- 10. funnel / hopper


def gen10(rng):
    Rb = r1(rng, 14, 18)
    Rt = r1(rng, 26, 34)
    H = r1(rng, 30, 44)
    t = r1(rng, 3, 4)
    tf = r1(rng, 6, 9)
    Rs = r1(rng, 7, 9)
    Hs = r1(rng, 12, 20)
    rs = round(Rs - rng.uniform(3, 4), 1)
    return {"Rb": Rb, "Rt": Rt, "H": H, "t": t, "tf": tf,
            "rrb": round(Rb - t * 1.5, 1), "rrt": round(Rt - t, 1),
            "Rs": Rs, "Hs": Hs, "rs": rs,
            "rw": r1(rng, 3, 5), "rh": r1(rng, 3, 5)}


def _c10(p):
    """Canonical F10 numbers, rounded to the printed precision first.

    The rim is defined by its printed inner/outer diameters (never a
    "width" that disagrees with them); the recess by its printed top and
    bottom diameters. Radii enter the program only as (diameter)/2.
    """
    return {
        "Db": round(p["Rb"] * 2, 1),
        "Dt": round(p["Rt"] * 2, 1),
        "H": round(p["H"], 1),
        "Drt": round(p["rrt"] * 2, 1),
        "Drb": round(p["rrb"] * 2, 1),
        "tf": round(p["tf"], 1),
        "zt": round(p["H"] + 1, 1),
        "Ds": round(p["Rs"] * 2, 1),
        "zsp0": round(-p["Hs"], 1),
        "Dbore": round(p["rs"] * 2, 1),
        "zb0": round(-p["Hs"] - 1, 1),
        "zb1": round(p["tf"] + 1, 1),
        "Dout": round((p["Rt"] + p["rw"]) * 2, 1),
        "Din": round((p["Rt"] - p["t"]) * 2, 1),
        "rh": round(p["rh"], 1),
    }


def text10(p):
    c = _c10(p)
    return (
        "Units: millimetres. Z is up. A funnel on the Z axis, centred at "
        "X = 0, Y = 0. Outer cone frustum: bottom diameter %s at Z = 0, "
        "top diameter %s at Z = %s. Inner cone recess from the top: top "
        "diameter %s at Z = %s, bottom diameter %s at Z = %s, leaving a "
        "floor %s thick. A cylindrical spout outside: diameter %s, Z "
        "from %s to 4. A bore of diameter %s runs through the spout up "
        "into the recess (Z from %s to %s). A top rim ring: inner "
        "diameter %s, outer diameter %s, %s tall, sitting on the top face "
        "(Z = %s)."
        % (num(c["Db"]), num(c["Dt"]), num(c["H"]),
           num(c["Drt"]), num(c["zt"]), num(c["Drb"]), num(c["tf"]),
           num(c["tf"]), num(c["Ds"]), num(c["zsp0"]),
           num(c["Dbore"]), num(c["zb0"]), num(c["zb1"]),
           num(c["Din"]), num(c["Dout"]), num(c["rh"]), num(c["H"])))


def src10(p):
    c = _c10(p)
    # Round 1d: the rim is its own ring (outer minus inner, Z H to H+rh)
    # fused onto the top face. The old inner cut started at (H - 1) and
    # removed body material below the top face that the text never
    # describes. No cutter reaches below Z = H except the recess and the
    # spout bore, both described by the text.
    return src(
        "body = Solid.makeCone((%s)/2, (%s)/2, %s, Vector(0, 0, 0), "
        "Vector(0, 0, 1))\n"
        "rec = Solid.makeCone((%s)/2, (%s)/2, (%s - %s), "
        "Vector(0, 0, %s), Vector(0, 0, 1))\n"
        "spout = _zcyl((%s)/2, 0, 0, %s, 4)\n"
        "s = body.fuse(spout)\n"
        "s = s.cut(rec)\n"
        "s = s.cut(_zcyl((%s)/2, 0, 0, %s, %s))\n"
        "rim = _zcyl((%s)/2, 0, 0, %s, (%s + %s))\n"
        "rim = rim.cut(_zcyl((%s)/2, 0, 0, %s, ((%s + %s) + 1)))\n"
        "s = s.fuse(rim)\n"
        "result = s\n"
        % (num(c["Db"]), num(c["Dt"]), num(c["H"]), num(c["Drb"]),
           num(c["Drt"]), num(c["zt"]), num(c["tf"]), num(c["tf"]),
           num(c["Ds"]), num(c["zsp0"]), num(c["Dbore"]),
           num(c["zb0"]), num(c["zb1"]), num(c["Dout"]),
           num(c["H"]), num(c["H"]), num(c["rh"]), num(c["Din"]),
           num(c["H"]), num(c["H"]), num(c["rh"])))


def wrong10(p):
    a = dict(p)
    a["Hs"] = round(p["Hs"] + 5, 1)  # moved feature: longer spout
    b = dict(p)
    b["Rt"] = round(p["Rt"] + 4, 1)  # wrong size: wider top
    return [a, b]


# ------------------------------------------------------- registry + runs


FAMILIES = {
    1: {"name": "spool (bobbin)", "gen": gen1, "text": text1,
        "src": src1, "wrong": wrong1,
        "near": "M5 stepped shaft (cylinders on one axis)",
        "why": "different: flanges, slot through a flange"},
    2: {"name": "manifold block", "gen": gen2, "text": text2,
        "src": src2, "wrong": wrong2,
        "near": "H6 bearing housing (block + bores)",
        "why": "different: orthogonal ports at set heights"},
    3: {"name": "dovetail slide", "gen": gen3, "text": text3,
        "src": src3, "wrong": wrong3,
        "near": "M2 T-profile (extruded profile)",
        "why": "different: cut groove with an angle"},
    4: {"name": "cam plate", "gen": gen4, "text": text4,
        "src": src4, "wrong": wrong4,
        "near": "M12 pulley / M6 flange (disk + bore)",
        "why": "different: eccentric bore, angled slot"},
    5: {"name": "pipe tee", "gen": gen5, "text": text5,
        "src": src5, "wrong": wrong5,
        "near": "H10 pipe clamp",
        "why": "different: two crossing bored tubes"},
    6: {"name": "lattice panel", "gen": gen6, "text": text6,
        "src": src6, "wrong": wrong6,
        "near": "H15 vented lid (pattern of cut-outs)",
        "why": "different: triangles, alternating orientation"},
    7: {"name": "T-slot rail", "gen": gen7, "text": text7,
        "src": src7, "wrong": wrong7,
        "near": "M7 U-channel",
        "why": "different: T-shaped undercut slot"},
    8: {"name": "bezel frame", "gen": gen8, "text": text8,
        "src": src8, "wrong": wrong8,
        "near": "H2 board plate",
        "why": "different: rounded window, outside tabs"},
    9: {"name": "ported cap", "gen": gen9, "text": text9,
        "src": src9, "wrong": wrong9,
        "near": "M3 open box / H1 enclosure",
        "why": "different: cylindrical, side port"},
    10: {"name": "funnel (hopper)", "gen": gen10, "text": text10,
         "src": src10, "wrong": wrong10,
         "near": "none close (no cones in the exam)",
         "why": "different"},
}


def job_id(family, n):
    """Job id: F<family>-<n>."""
    return "F%d-%d" % (family, n)


def generate_all(seed=SEED, per_family=JOBS_PER_FAMILY):
    """Generate every job: [{id, family, text, reference}]. Deterministic
    in seed: the same seed gives the same file."""
    rng = random.Random(seed)
    jobs = []
    for family in range(1, N_FAMILIES + 1):
        fam = FAMILIES[family]
        for n in range(1, per_family + 1):
            params = fam["gen"](rng)
            jobs.append({
                "id": job_id(family, n),
                "family": family,
                "text": fam["text"](params),
                "reference": fam["src"](params),
            })
    return jobs


def choose_dev_ids(jobs, seed=SEED, per_family=2):
    """Seed-chosen dev split: 2 ids per family (20). Deterministic."""
    rng = random.Random(seed)
    dev = []
    for family in range(1, N_FAMILIES + 1):
        ids = sorted(j["id"] for j in jobs if j["family"] == family)
        dev.extend(sorted(rng.sample(ids, per_family)))
    return sorted(dev)


def first_params(family):
    """The first job's params of a family under the fixed seed (for the
    per-family wrong-variant self-check)."""
    rng = random.Random(SEED)
    params = None
    for fam in range(1, family + 1):
        for _ in range(JOBS_PER_FAMILY):
            params = FAMILIES[fam]["gen"](rng)
            if fam == family:
                first = params
                break
    return first


def build_source(source):
    """Build a trusted reference source in-process (needs cadquery)."""
    ns = {"__name__": "__main__"}
    exec(compile(source, "<reference>", "exec"), ns)
    return ns["result"]


def shape_info(shape):
    """(n_solids, valid) for a built shape (needs cadquery)."""
    import cadquery as _cq

    if isinstance(shape, _cq.Workplane):
        vals = [v for v in shape.vals() if isinstance(v, _cq.Shape)]
        shape = vals[0] if len(vals) == 1 else _cq.Compound.makeCompound(
            vals)
    if isinstance(shape, _cq.Assembly):
        shape = shape.toCompound()
    return len(shape.Solids()), bool(shape.isValid())


def score_at_tight(answer_text_or_shape, ref_shape, source=None):
    """Score at TOL_DIFF = 1e-6 (needs cadquery + checks).

    `answer_text_or_shape` is a built shape, or a reference source to
    build first. The expected values are the reference's measurements.
    Returns (passed, fails).
    """
    import os as _os
    import sys as _sys

    _ft = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), "..", "first-test")
    if _ft not in _sys.path:
        _sys.path.insert(0, _ft)
    import checks as _checks

    if isinstance(answer_text_or_shape, str):
        answer = build_source(answer_text_or_shape)
    else:
        answer = answer_text_or_shape
    expected = _checks.measure(ref_shape)
    old = _checks.TOL_DIFF
    try:
        _checks.TOL_DIFF = 1e-6
        passed, fails, _m = _checks.score(answer, ref_shape, expected)
    finally:
        _checks.TOL_DIFF = old
    return passed, fails
