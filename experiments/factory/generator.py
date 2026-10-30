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


def text1(p):
    H = p["tf"] * 2 + p["Hc"]
    return (
        "Units: millimetres. Z is up. A spool (bobbin) on the Z axis, "
        "centred at X = 0, Y = 0. Bottom flange: diameter %s, Z from 0 "
        "to %s. Core: diameter %s, Z from %s to %s. Top flange: diameter "
        "%s, Z from %s to %s. A centre bore of diameter %s goes through "
        "everything along the Z axis. A wire slot %s wide cuts through "
        "the bottom flange along X: X from %s to %s, Y from %s to %s, "
        "Z from 0 to %s."
        % (num(p["Rf"] * 2), num(p["tf"]), num(p["Rc"] * 2),
           num(p["tf"]), num(p["tf"] + p["Hc"]), num(p["Rf"] * 2),
           num(p["tf"] + p["Hc"]), num(H), num(p["Rb"] * 2), num(p["sw"]),
           num(-p["Rf"] - 1), num(p["Rf"] + 1),
           num(p["sy"] - p["sw"] / 2), num(p["sy"] + p["sw"] / 2),
           num(p["tf"])))


def src1(p):
    H = p["tf"] * 2 + p["Hc"]
    return src(
        "b = _zcyl(%s, 0, 0, 0, %s)\n"
        "c = _zcyl(%s, 0, 0, %s, %s)\n"
        "t = _zcyl(%s, 0, 0, %s, %s)\n"
        "s = b.fuse(c, t)\n"
        "s = s.cut(_zcyl(%s, 0, 0, -1, %s))\n"
        "s = s.cut(_box(%s, %s, %s, %s, 0, %s))\n"
        "result = s\n"
        % (num(p["Rf"]), num(p["tf"]), num(p["Rc"]), num(p["tf"]),
           num(p["tf"] + p["Hc"]), num(p["Rf"]), num(p["tf"] + p["Hc"]),
           num(H), num(p["Rb"]), num(H + 1), num(-p["Rf"] - 1),
           num(p["Rf"] + 1), num(p["sy"] - p["sw"] / 2),
           num(p["sy"] + p["sw"] / 2), num(p["tf"])))


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
    body = "s = _box(0, %s, 0, %s, 0, %s)\n" % (
        num(p["L"]), num(p["W"]), num(p["H"]))
    for y in p["ys"]:
        body += "s = s.cut(_xcyl(%s, %s, %s, -1, %s))\n" % (
            num(p["rx"]), num(y), num(p["h1"]), num(p["L"] + 1))
    for x in p["xs"]:
        body += "s = s.cut(_ycyl(%s, %s, %s, -1, %s))\n" % (
            num(p["ry"]), num(x), num(p["h2"]), num(p["W"] + 1))
    body += "s = s.cut(_zcyl(%s, %s, %s, %s, %s))\nresult = s\n" % (
        num(p["rb"]), num(p["bx"]), num(p["by"]), num(p["zb"]),
        num(p["H"] + 1))
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


def text3(p):
    yc = p["W"] / 2 + p["gc"]
    return (
        "Units: millimetres. Z is up. A dovetail slide: a block X from 0 "
        "to %s, Y from 0 to %s, Z from 0 to %s. A dovetail groove runs "
        "along X for the whole length: opening width %s at the top face "
        "(Z = %s), floor width %s at depth (Z = %s), sides tilting "
        "outward by %s degrees from vertical, centred at Y = %s. Two "
        "end holes of diameter %s go through along Z at (X, Y) = (%s, "
        "%s) and (%s, %s)."
        % (num(p["L"]), num(p["W"]), num(p["H"]), num(p["wo"]),
           num(p["H"]), num(p["wb"]), num(p["H"] - p["gd"]), num(p["A"]),
           num(yc), num(p["dh"]), num(p["x1"]), num(p["W"] / 2),
           num(p["x2"]), num(p["W"] / 2)))


def src3(p):
    yc = p["W"] / 2 + p["gc"]
    y0, y1 = yc - p["wb"] / 2, yc + p["wb"] / 2
    y2, y3 = yc - p["wo"] / 2, yc + p["wo"] / 2
    zf = p["H"] - p["gd"]
    return src(
        "prof = cq.Workplane(\"YZ\").polyline([(%s, %s), (%s, %s), "
        "(%s, %s), (%s, %s)]).close().extrude(%s).val()\n"
        "s = _box(0, %s, 0, %s, 0, %s)\n"
        "s = s.cut(prof)\n"
        "s = s.cut(_zcyl(%s, %s, %s, -1, %s))\n"
        "s = s.cut(_zcyl(%s, %s, %s, -1, %s))\n"
        "result = s\n"
        % (num(y0), num(zf), num(y1), num(zf), num(y3), num(p["H"]),
           num(y2), num(p["H"]), num(p["L"]), num(p["L"]), num(p["W"]),
           num(p["H"]), num(p["dh"] / 2), num(p["x1"]),
           num(p["W"] / 2), num(p["H"] + 1), num(p["dh"] / 2),
           num(p["x2"]), num(p["W"] / 2), num(p["H"] + 1)))


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


def text4(p):
    x0, y0, x9, y9 = _slot_points(p)
    return (
        "Units: millimetres. Z is up. A cam plate: a disk of diameter %s, "
        "Z from 0 to %s, centred at X = 0, Y = 0. An eccentric bore of "
        "diameter %s goes through along Z, centred at (X, Y) = (%s, 0). "
        "A slot %s wide cuts through along Z: its centreline runs from "
        "(%s, %s) to (%s, %s)."
        % (num(p["R"] * 2), num(p["T"]), num(p["rb"] * 2), num(p["ex"]),
           num(p["sw"]), num(x0), num(y0), num(x9), num(y9)))


def src4(p):
    return src(
        "d = _zcyl(%s, 0, 0, 0, %s)\n"
        "d = d.cut(_zcyl(%s, %s, 0, -1, %s))\n"
        "slot = _box(%s, %s, %s, %s, -1, %s)\n"
        "slot = slot.rotate(Vector(0, 0, 0), Vector(0, 0, 1), %s)\n"
        "result = d.cut(slot)\n"
        % (num(p["R"]), num(p["T"]), num(p["rb"]), num(p["ex"]),
           num(p["T"] + 1), num(p["ex"] - p["rb"]), num(p["R"] + 1),
           num(-p["sw"] / 2), num(p["sw"] / 2), num(p["T"] + 1),
           num(p["th"])))


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
    return src(
        "main = _xcyl(%s, 0, 0, 0, %s)\n"
        "branch = _ycyl(%s, %s, 0, -1, %s)\n"
        "flange = _xcyl(%s, 0, 0, -6, 0)\n"
        "s = main.fuse(branch, flange)\n"
        "s = s.cut(_xcyl(%s, 0, 0, -1, %s))\n"
        "s = s.cut(_ycyl(%s, %s, 0, -2, %s))\n"
        "s = s.cut(_xcyl(%s, 0, 0, -7, 1))\n"
        "result = s\n"
        % (num(p["Rm"]), num(p["Lm"]), num(p["Rb2"]), num(p["xb"]),
           num(p["Lb"]), num(p["Rf2"]), num(p["rm"]), num(p["Lm"] + 1),
           num(p["rb2"]), num(p["xb"]), num(p["Lb"] + 1), num(p["rm"])))


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


def text7(p):
    yc = p["W"] / 2 + p["yc"]
    return (
        "Units: millimetres. Z is up. A T-slot rail: a bar X from 0 to "
        "%s, Y from 0 to %s, Z from 0 to %s. A T-shaped slot runs along "
        "X for the whole length, centred at Y = %s: a narrow opening %s "
        "wide from the top face (Z = %s) down to Z = %s, and a wider "
        "undercut %s wide from Z = %s down to the slot floor at Z = %s. "
        "Two end holes of diameter %s go through along Z at (X, Y) = "
        "(%s, %s) and (%s, %s)."
        % (num(p["L"]), num(p["W"]), num(p["H"]), num(yc), num(p["wn"]),
           num(p["H"]), num(p["z1"]), num(p["ww"]), num(p["z1"]),
           num(p["z0"]), num(p["dh"]), num(p["x1"]), num(p["W"] / 2),
           num(p["x2"]), num(p["W"] / 2)))


def src7(p):
    yc = p["W"] / 2 + p["yc"]
    pts = [(yc - p["ww"] / 2, p["z0"]), (yc + p["ww"] / 2, p["z0"]),
           (yc + p["ww"] / 2, p["z1"]), (yc + p["wn"] / 2, p["z1"]),
           (yc + p["wn"] / 2, p["H"]), (yc - p["wn"] / 2, p["H"]),
           (yc - p["wn"] / 2, p["z1"]), (yc - p["ww"] / 2, p["z1"])]
    prof = ", ".join("(%s, %s)" % (num(y), num(z)) for y, z in pts)
    return src(
        "prof = cq.Workplane(\"YZ\").polyline([%s]).close().extrude("
        "%s).val()\n"
        "s = _box(0, %s, 0, %s, 0, %s)\n"
        "s = s.cut(prof)\n"
        "s = s.cut(_zcyl(%s, %s, %s, -1, %s))\n"
        "s = s.cut(_zcyl(%s, %s, %s, -1, %s))\n"
        "result = s\n"
        % (prof, num(p["L"]), num(p["L"]), num(p["W"]), num(p["H"]),
           num(p["dh"] / 2), num(p["x1"]), num(p["W"] / 2),
           num(p["H"] + 1), num(p["dh"] / 2), num(p["x2"]),
           num(p["W"] / 2), num(p["H"] + 1)))


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


def _tabs8(p):
    cx, cy = p["L"] / 2, p["W"] / 2
    hw = p["tw"] / 2
    return [
        ("left", -p["td"], 3, cy - hw, cy + hw,
         -p["td"] / 2 + p["hx"], cy),
        ("right", p["L"] - 3, p["L"] + p["td"], cy - hw, cy + hw,
         p["L"] + p["td"] / 2, cy),
        ("bottom", cx - hw, cx + hw, -p["td"], 3, cx, -p["td"] / 2),
        ("top", cx - hw, cx + hw, p["W"] - 3, p["W"] + p["td"],
         cx, p["W"] + p["td"] / 2),
    ]


def text8(p):
    lines = [
        "Units: millimetres. Z is up. A bezel frame: a plate X from 0 "
        "to %s, Y from 0 to %s, Z from 0 to %s, with a rounded-rectangle "
        "window through Z: centre (%s, %s), %s by %s, corner radius %s."
        % (num(p["L"]), num(p["W"]), num(p["T"]), num(p["L"] / 2),
           num(p["W"] / 2), num(p["lw"]), num(p["ww"]), num(p["r"]))]
    for name, x0, x1, y0, y1, hx, hy in _tabs8(p):
        lines.append(
            "Tab %s: X from %s to %s, Y from %s to %s, Z from 0 to %s, "
            "with a %s mm hole through Z at (%s, %s)."
            % (name, num(x0), num(x1), num(y0), num(y1), num(p["T"]),
               num(p["thd"]), num(hx), num(hy)))
    return " ".join(lines)


def src8(p):
    cx, cy = p["L"] / 2, p["W"] / 2
    x0, x9 = cx - p["lw"] / 2, cx + p["lw"] / 2
    y0, y9 = cy - p["ww"] / 2, cy + p["ww"] / 2
    r = p["r"]
    body = (
        "s = _box(0, %s, 0, %s, 0, %s)\n"
        "win = _box(%s, %s, %s, %s, -1, %s)\n"
        "win = win.fuse(_box(%s, %s, %s, %s, -1, %s))\n"
        % (num(p["L"]), num(p["W"]), num(p["T"]), num(x0 + r),
           num(x9 - r), num(y0), num(y9), num(p["T"] + 1), num(x0),
           num(x9), num(y0 + r), num(y9 - r), num(p["T"] + 1)))
    for dx, dy in ((x0 + r, y0 + r), (x9 - r, y0 + r),
                   (x0 + r, y9 - r), (x9 - r, y9 - r)):
        body += "win = win.fuse(_zcyl(%s, %s, %s, -1, %s))\n" % (
            num(r), num(dx), num(dy), num(p["T"] + 1))
    body += "s = s.cut(win)\n"
    for _name, x0, x1, y0, y1, hx, hy in _tabs8(p):
        body += "s = s.fuse(_box(%s, %s, %s, %s, 0, %s))\n" % (
            num(x0), num(x1), num(y0), num(y1), num(p["T"]))
        body += "s = s.cut(_zcyl(%s, %s, %s, -1, %s))\n" % (
            num(p["thd"] / 2), num(hx), num(hy), num(p["T"] + 1))
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
    return src(
        "s = _zcyl(%s, 0, 0, 0, %s)\n"
        "s = s.cut(_xcyl(%s, 0, %s, 0, %s))\n"
        "s = s.cut(_zcyl(%s, 0, 0, %s, %s))\n"
        "result = s\n"
        % (num(p["R"]), num(p["H"]), num(p["rp"]), num(p["hp"]),
           num(p["R"] + 1), num(p["rr"]), num(p["fz"]),
           num(p["H"] + 1)))


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


def text10(p):
    return (
        "Units: millimetres. Z is up. A funnel on the Z axis, centred at "
        "X = 0, Y = 0. Outer cone frustum: bottom diameter %s at Z = 0, "
        "top diameter %s at Z = %s. Inner cone recess from the top: top "
        "diameter %s at Z = %s, leaving a floor %s thick (recess bottom "
        "at Z = %s). A cylindrical spout outside: diameter %s, Z from %s "
        "to 4. A bore of diameter %s runs through the spout up into the "
        "recess (Z from %s to %s). A top rim ring: %s wide, %s tall, "
        "sitting on the top face."
        % (num(p["Rb"] * 2), num(p["Rt"] * 2), num(p["H"]),
           num(p["rrt"] * 2), num(p["H"] + 1), num(p["tf"]),
           num(p["tf"]), num(p["Rs"] * 2), num(-p["Hs"]),
           num(p["rs"] * 2), num(-p["Hs"] - 1), num(p["tf"] + 1),
           num(p["rw"]), num(p["rh"])))


def src10(p):
    return src(
        "body = Solid.makeCone(%s, %s, %s, Vector(0, 0, 0), "
        "Vector(0, 0, 1))\n"
        "rec = Solid.makeCone(%s, %s, %s, Vector(0, 0, %s), "
        "Vector(0, 0, 1))\n"
        "spout = _zcyl(%s, 0, 0, %s, 4)\n"
        "s = body.fuse(spout)\n"
        "s = s.cut(rec)\n"
        "s = s.cut(_zcyl(%s, 0, 0, %s, %s))\n"
        "s = s.fuse(_zcyl(%s, 0, 0, %s, %s))\n"
        "s = s.cut(_zcyl(%s, 0, 0, %s, %s))\n"
        "result = s\n"
        % (num(p["Rb"]), num(p["Rt"]), num(p["H"]), num(p["rrb"]),
           num(p["rrt"]), num(p["H"] + 1 - p["tf"]), num(p["tf"]),
           num(p["Rs"]), num(-p["Hs"]), num(p["rs"]),
           num(-p["Hs"] - 1), num(p["tf"] + 1), num(p["Rt"] + p["rw"]),
           num(p["H"]), num(p["H"] + p["rh"]), num(p["Rt"] - p["t"]),
           num(p["H"] - 1), num(p["H"] + p["rh"] + 1)))


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
