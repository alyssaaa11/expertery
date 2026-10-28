"""First-test exam: 30 CadQuery jobs (15 medium + 15 hard) plus 3 dry-run jobs, each with a reference part and two
deliberately wrong versions. Written before any model run (PLAN.md section 4); frozen once the self-test passes.

Every job text fixes all positions from the origin (millimetres, Z up), so a correct answer has exactly one shape.
A builder takes keyword overrides; the reference uses the defaults and each wrong version changes one thing.
"""
import math

import cadquery as cq
from cadquery import Solid, Vector


def box(x0, x1, y0, y1, z0, z1):
    return Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def cyl(r, p, d, h):
    """Cylinder of radius r starting at point p, going h along direction d."""
    return Solid.makeCylinder(r, h, Vector(*p), Vector(*d))


def zcyl(r, x, y, z0, z1):
    return cyl(r, (x, y, z0), (0, 0, 1), z1 - z0)


def slot_z(cx, cy, length, width, z0, z1):
    """Obround slot along X: straight part (length - width) plus two round ends, total length `length`."""
    half = (length - width) / 2
    s = box(cx - half, cx + half, cy - width / 2, cy + width / 2, z0, z1)
    s = s.fuse(zcyl(width / 2, cx - half, cy, z0, z1)).fuse(zcyl(width / 2, cx + half, cy, z0, z1))
    return s


def prism_xy(points, z0, z1):
    return cq.Workplane("XY").polyline(points).close().extrude(z1 - z0).translate((0, 0, z0)).val()


def _prism_yz(points, x0, x1):
    # Build in XY with (u, v) = (y, z), extrude along +Z by (x1 - x0), then map (u, v, t) -> (t, u, v).
    w = cq.Workplane("XY").polyline(points).close().extrude(x1 - x0).val()
    m = cq.Matrix([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])
    return w.transformGeometry(m)


def _prism_xz(points, y0, y1):
    # (u, v) = (x, z), extrude along +Z by (y1 - y0), map (u, v, t) -> (u, t, v).
    w = cq.Workplane("XY").polyline(points).close().extrude(y1 - y0).val()
    m = cq.Matrix([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]])
    return w.transformGeometry(m)


# ---------------------------------------------------------------- medium

def m1(wall_y0=7.0, hole_d=5.0):
    s = box(-20, 20, -10, 10, 0, 3).fuse(box(-20, 20, wall_y0, wall_y0 + 3, 0, 20))
    for x in (-15, 15):
        s = s.cut(zcyl(hole_d / 2, x, -1.5, 0, 3))
    return s


def m2(web_t=4.0, flange_z0=26.0):
    return box(0, 60, -15, 15, flange_z0, flange_z0 + 4).fuse(box(0, 60, -web_t / 2, web_t / 2, 0, flange_z0))


def m3(wall=2.0, floor=2.0):
    return box(-30, 30, -20, 20, 0, 30).cut(box(-30 + wall, 30 - wall, -20 + wall, 20 - wall, floor, 30))


def m4(lip_out=27.8, lip_h=5.0):
    s = box(-30, 30, -20, 20, 0, 2)
    ring = box(-lip_out, lip_out, -lip_out + 10, lip_out - 10, 2, 2 + lip_h)
    ring = ring.cut(box(-lip_out + 1.5, lip_out - 1.5, -lip_out + 11.5, lip_out - 11.5, 2, 2 + lip_h))
    return s.fuse(ring)


def m5(d2=15.0, l1=30.0):
    return zcyl(10, 0, 0, 0, l1).fuse(zcyl(d2 / 2, 0, 0, l1, l1 + 20)).fuse(zcyl(5, 0, 0, l1 + 20, l1 + 35))


def m6(pcd=45.0, hub_h=20.0):
    s = zcyl(30, 0, 0, 0, 8).fuse(zcyl(15, 0, 0, 8, 8 + hub_h)).cut(zcyl(10, 0, 0, 0, 8 + hub_h))
    for a in (0, 90, 180, 270):
        s = s.cut(zcyl(3, pcd / 2 * math.cos(math.radians(a)), pcd / 2 * math.sin(math.radians(a)), 0, 8))
    return s


def m7(wall=3.0, floor=3.0):
    return box(0, 50, -15, 15, 0, 20).cut(box(0, 50, -15 + wall, 15 - wall, floor, 20))


def m8(pos=18.0, boss_h=10.0):
    s = box(-25, 25, -25, 25, 0, 3)
    for x in (-pos, pos):
        for y in (-pos, pos):
            s = s.fuse(zcyl(4, x, y, 3, 3 + boss_h))
    for x in (-pos, pos):
        for y in (-pos, pos):
            s = s.cut(zcyl(1.5, x, y, 0, 3 + boss_h))
    return s


def m9(angle=15.0, back_y=45.0):
    s = box(-40, 40, 0, 60, 0, 5).fuse(box(-40, 40, 0, 5, 5, 10))
    a = math.radians(angle)
    dy, dz = 70 * math.sin(a), 70 * math.cos(a)
    pts = [(back_y, 5), (back_y + 5, 5), (back_y + 5 + dy, 5 + dz), (back_y + dy, 5 + dz)]
    return s.fuse(_prism_yz(pts, -40, 40))


def m10(cb_d=11.0, cb_depth=6.5):
    return box(-20, 20, -20, 20, 0, 10).cut(zcyl(3.3, 0, 0, 0, 10)).cut(zcyl(cb_d / 2, 0, 0, 10 - cb_depth, 10))


def m11(gusset_leg=25.0, b_h=50.0):
    s = box(0, 50, -15, 15, 0, 4).fuse(box(0, 4, -15, 15, 0, b_h))
    g = _prism_xz([(4, 4), (4 + gusset_leg, 4), (4, 4 + gusset_leg)], -2, 2)
    return s.fuse(g)


def m12(groove_r=16.0, groove_z0=4.0):
    s = zcyl(20, 0, 0, 0, 12)
    ring = zcyl(20, 0, 0, groove_z0, groove_z0 + 4).cut(zcyl(groove_r, 0, 0, groove_z0, groove_z0 + 4))
    return s.cut(ring).cut(zcyl(4, 0, 0, 0, 12))


def m13(tab_x1=25.0, tab_hole_x=20.0):
    s = zcyl(8, 0, 0, 0, 8).fuse(box(0, tab_x1, 5, 8, 0, 8))
    s = s.cut(zcyl(5, 0, 0, 0, 8))
    return s.cut(cyl(2, (tab_hole_x, 5, 4), (0, 1, 0), 3))


def m14(knuckle_r=3.0, pin_r=1.5):
    s = box(0, 40, 0, 30, 0, 2).fuse(cyl(knuckle_r, (0, 0, 3), (1, 0, 0), 40))
    return s.cut(cyl(pin_r, (0, 0, 3), (1, 0, 0), 40))


def m15(post_x=40.0, hole_depth=8.0):
    s = box(-50, 50, -5, 5, 20, 30)
    for x in (-post_x, post_x):
        s = s.fuse(box(x - 5, x + 5, -5, 5, 0, 20))
    for x in (-post_x, post_x):
        s = s.cut(zcyl(1.65, x, 0, 0, hole_depth))
    return s


# ---------------------------------------------------------------- hard

def h1(boss_xy=(33.0, 18.0), hole_d=2.5):
    s = box(-40, 40, -25, 25, 0, 30).cut(box(-38, 38, -23, 23, 2, 30))
    bx, by = boss_xy
    for x in (-bx, bx):
        for y in (-by, by):
            s = s.fuse(zcyl(3, x, y, 2, 27))
    for x in (-bx, bx):
        for y in (-by, by):
            s = s.cut(zcyl(hole_d / 2, x, y, 2, 27))
    return s


def h2(pattern=((21, 10), (79, 10), (21, 59), (79, 59)), slot_ys=(25.0, 45.0)):
    s = box(0, 100, 0, 70, 0, 3)
    for x, y in pattern:
        s = s.fuse(zcyl(3, x, y, 3, 8))
    for x, y in pattern:
        s = s.cut(zcyl(1.35, x, y, 0, 8))
    for y in slot_ys:
        s = s.cut(slot_z(50, y, 20, 6, 0, 3))
    return s


def h3(n=12, key_len=1.5):
    s = zcyl(20, 0, 0, 0, 8)
    for k in range(n):
        a = 2 * math.pi * k / n
        notch = box(16, 21, -1.5, 1.5, 0, 8).rotate(Vector(0, 0, 0), Vector(0, 0, 1), math.degrees(a))
        s = s.cut(notch)
    s = s.cut(zcyl(4, 0, 0, 0, 8)).cut(box(0, 4 + key_len, -1.5, 1.5, 0, 8))
    return s


def h4(hole_z=14.0, fin_h=15.0):
    s = box(-10, 10, -10, 10, 0, 4)
    for x0 in (-7.5, -1.5, 4.5):
        s = s.fuse(box(x0, x0 + 3, -10, 10, 4, 4 + fin_h))
    return s.cut(cyl(2.5, (-10, 0, hole_z), (1, 0, 0), 20))


def h5(hole_at=16.5, t=3.0):
    s = box(0, 30, 0, 30, 0, t).fuse(box(0, 30, 0, t, 0, 30)).fuse(box(0, t, 0, 30, 0, 30))
    s = s.cut(zcyl(2, hole_at, hole_at, 0, t))
    s = s.cut(cyl(2, (hole_at, 0, hole_at), (0, 1, 0), t))
    s = s.cut(cyl(2, (0, hole_at, hole_at), (1, 0, 0), t))
    return s


def h6(pocket_depth=7.0, mount_x=20.0):
    s = box(-25, 25, -20, 20, 0, 25).cut(zcyl(11, 0, 0, 25 - pocket_depth, 25)).cut(zcyl(5, 0, 0, 0, 25))
    for x in (-mount_x, mount_x):
        s = s.cut(zcyl(2.5, x, 0, 0, 25))
    return s


def h7(flats=10.0, depth=5.0):
    r = flats / 2 / math.cos(math.radians(30))
    hexpts = [(r * math.cos(math.radians(60 * k)), r * math.sin(math.radians(60 * k))) for k in range(6)]
    return zcyl(10, 0, 0, 0, 12).cut(prism_xy(hexpts, 12 - depth, 12)).cut(zcyl(2.75, 0, 0, 0, 12))


def h8(arm_t=2.0, hook_h=2.0):
    s = box(0, 20, 0, 10, 0, 5).fuse(box(20, 50, 0, 10, 5 - arm_t, 5))
    return s.fuse(_prism_xz([(50 - hook_h, 5), (50, 5), (50, 5 + hook_h)], 0, 10))


def h9(n=9, fin_t=1.5):
    s = box(-30, 30, -20, 20, 0, 4)
    centres = [-28 + 56 * i / (n - 1) for i in range(n)]
    for c in centres:
        s = s.fuse(box(c - fin_t / 2, c + fin_t / 2, -20, 20, 4, 24))
    return s


def h10(inner_r=12.5, hole_x=23.0):
    band = cyl(inner_r + 3, (0, -10, 0), (0, 1, 0), 20).cut(cyl(inner_r, (0, -10, 0), (0, 1, 0), 20))
    band = band.cut(box(-20, 20, -10, 10, -20, 0))  # keep the upper half only
    s = band
    for x0, x1 in ((-30.5, -13.0), (13.0, 30.5)):
        s = s.fuse(box(x0, x1, -10, 10, 0, 3))
    for x in (-hole_x, hole_x):
        s = s.cut(zcyl(2.5, x, 0, 0, 3))
    return s


def h11(hole_xz=(35.0, 28.0), pocket_depth=4.0):
    s = box(0, 40, 0, 30, 0, 8)
    for k in range(1, 4):
        s = s.fuse(box(10 * k, 40, 0, 30, 8 * k, 8 * k + 8))
    hx, hz = hole_xz
    s = s.cut(cyl(3, (hx, 0, hz), (0, 1, 0), 30))
    return s.cut(box(0, 10, 10, 20, 8 - pocket_depth, 8))


def h12(n=18, d_flat=1.5):
    s = zcyl(15, 0, 0, 0, 15)
    for k in range(n):
        a = 2 * math.pi * k / n
        s = s.cut(zcyl(1.5, 15 * math.cos(a), 15 * math.sin(a), 0, 15))
    dhole = zcyl(3, 0, 0, 0, 15).cut(box(d_flat, 4, -4, 4, 0, 15))
    return s.cut(dhole)


def h13(hole_zs=(15.0, 45.0), tip_h=15.0):
    s = box(-15, 15, 0, 4, 0, 60)
    s = s.fuse(box(-5, 5, 4, 34, 25, 30)).fuse(box(-5, 5, 29, 34, 30, 30 + tip_h))
    for z in hole_zs:
        s = s.cut(cyl(2, (0, 0, z), (0, 1, 0), 4))
        s = s.cut(Solid.makeCone(4, 2, 2, Vector(0, 4, z), Vector(0, -1, 0)))
    return s


def h14(slot_len=15.0, upper_x0=27.0):
    s = box(0, 30, 0, 20, 0, 3).fuse(box(27, 30, 0, 20, 0, 23)).fuse(box(upper_x0, upper_x0 + 30, 0, 20, 20, 23))
    s = s.cut(slot_z(15, 10, slot_len, 5, 0, 3)).cut(slot_z(upper_x0 + 15, 10, slot_len, 5, 20, 23))
    return s


def h15(cols=8, vent=4.0):
    s = box(-40, 40, -25, 25, 0, 2)
    for i in range(cols):
        cx = -28 + 8 * i if cols == 8 else -24 + 8 * i
        for j in range(5):
            cy = -16 + 8 * j
            s = s.cut(box(cx - vent / 2, cx + vent / 2, cy - vent / 2, cy + vent / 2, 0, 2))
    for x in (-36, 36):
        for y in (-21, 21):
            s = s.cut(zcyl(1.5, x, y, 0, 2))
    return s


# ---------------------------------------------------------------- dry run (not scored)

def d1(hole_x=25.0, hole_d=4.0):
    s = box(-30, 30, -20, 20, 0, 5)
    for x in (-hole_x, hole_x):
        for y in (-15, 15):
            s = s.cut(zcyl(hole_d / 2, x, y, 0, 5))
    return s


def d2(rib_h=12.0, rib_x=0.0):
    return box(-20, 20, -10, 10, 0, 3).fuse(box(rib_x - 1.5, rib_x + 1.5, -10, 10, 3, 3 + rib_h))


def d3(boss_x=10.0, slot_x=28.0):
    s = box(0, 40, 0, 20, 0, 4).fuse(zcyl(5, boss_x, 10, 4, 14)).cut(zcyl(1.5, boss_x, 10, 0, 14))
    return s.cut(slot_z(slot_x, 10, 16, 6, 0, 4).rotate(Vector(slot_x, 10, 0), Vector(slot_x, 10, 1), 90))


T = "Millimetres, Z up. "

JOBS = [
    # ---- medium
    dict(id="M1", level="medium", build=m1, wrong=[dict(wall_y0=10.0), dict(hole_d=6.0)],
         text=T + "An L-bracket. Base plate: X from -20 to 20, Y from -10 to 10, Z from 0 to 3. Wall: X from -20 to 20, "
              "Y from 7 to 10, Z from 0 to 20 (it stands on the back edge of the base, flush with it at Y = 10). "
              "Two 5 mm diameter holes go through the base plate along Z, centred at (X, Y) = (-15, -1.5) and (15, -1.5)."),
    dict(id="M2", level="medium", build=m2, wrong=[dict(web_t=6.0), dict(flange_z0=24.0)],
         text=T + "A T-profile bar, 60 long along X (X from 0 to 60). Its cross-section: a flange Y from -15 to 15, "
              "Z from 26 to 30, on top of a web Y from -2 to 2, Z from 0 to 26."),
    dict(id="M3", level="medium", build=m3, wrong=[dict(wall=3.0), dict(floor=4.0)],
         text=T + "An open-top box. Outside: X from -30 to 30, Y from -20 to 20, Z from 0 to 30. Walls are 2 thick and "
              "the floor is 2 thick (the hollow inside is X from -28 to 28, Y from -18 to 18, Z from 2 to 30)."),
    dict(id="M4", level="medium", build=m4, wrong=[dict(lip_out=29.0), dict(lip_h=3.0)],
         text=T + "A box lid with a lip. Plate: X from -30 to 30, Y from -20 to 20, Z from 0 to 2. On top of it a "
              "rectangular lip ring, Z from 2 to 7: its outside is X from -27.8 to 27.8, Y from -17.8 to 17.8, and its "
              "walls are 1.5 thick (hollow inside X from -26.3 to 26.3, Y from -16.3 to 16.3)."),
    dict(id="M5", level="medium", build=m5, wrong=[dict(d2=16.0), dict(l1=25.0)],
         text=T + "A stepped shaft on the Z axis (centred at X = 0, Y = 0): diameter 20 from Z = 0 to 30, then "
              "diameter 15 from Z = 30 to 50, then diameter 10 from Z = 50 to 65."),
    dict(id="M6", level="medium", build=m6, wrong=[dict(pcd=40.0), dict(hub_h=15.0)],
         text=T + "A flange on the Z axis. Disk: diameter 60, Z from 0 to 8. Hub on top: diameter 30, Z from 8 to 28. "
              "A 20 mm bore goes through everything along the Z axis. Four 6 mm holes go through the disk along Z, on a "
              "45 mm diameter circle, at (X, Y) = (22.5, 0), (0, 22.5), (-22.5, 0), (0, -22.5)."),
    dict(id="M7", level="medium", build=m7, wrong=[dict(wall=4.0), dict(floor=5.0)],
         text=T + "A U-channel, 50 long along X (X from 0 to 50). Outside of the cross-section: Y from -15 to 15, "
              "Z from 0 to 20. It is open at the top: the inside Y from -12 to 12, Z from 3 to 20 is empty for the "
              "whole length (side walls and bottom are 3 thick)."),
    dict(id="M8", level="medium", build=m8, wrong=[dict(pos=15.0), dict(boss_h=12.0)],
         text=T + "A plate with four standoffs. Plate: X from -25 to 25, Y from -25 to 25, Z from 0 to 3. Four round "
              "standoffs, diameter 8, Z from 3 to 13, centred at (X, Y) = (18, 18), (-18, 18), (-18, -18), (18, -18). "
              "Each standoff has a 3 mm hole along Z through the standoff and the plate (Z from 0 to 13)."),
    dict(id="M9", level="medium", build=m9, wrong=[dict(angle=25.0), dict(back_y=35.0)],
         text=T + "A phone stand. Base: X from -40 to 40, Y from 0 to 60, Z from 0 to 5. Front lip: X from -40 to 40, "
              "Y from 0 to 5, Z from 5 to 10. Back support: a slanted plate, X from -40 to 40, whose cross-section in "
              "the Y-Z plane is the parallelogram with corners (Y, Z) = (45, 5), (50, 5), (50 + 70 sin 15°, 5 + 70 cos 15°) "
              "and (45 + 70 sin 15°, 5 + 70 cos 15°): 5 thick, leaning back 15° from vertical, 70 long."),
    dict(id="M10", level="medium", build=m10, wrong=[dict(cb_d=13.0), dict(cb_depth=4.0)],
         text=T + "A counterbored plate. Plate: X from -20 to 20, Y from -20 to 20, Z from 0 to 10. A 6.6 mm hole goes "
              "through along the Z axis at the centre. From the top face, a counterbore of diameter 11 goes down 6.5 "
              "(from Z = 3.5 to 10), on the same axis."),
    dict(id="M11", level="medium", build=m11, wrong=[dict(gusset_leg=15.0), dict(b_h=40.0)],
         text=T + "A shelf bracket. Horizontal plate: X from 0 to 50, Y from -15 to 15, Z from 0 to 4. Vertical plate: "
              "X from 0 to 4, Y from -15 to 15, Z from 0 to 50. A triangular gusset in the corner, Y from -2 to 2, "
              "whose cross-section in the X-Z plane is the triangle with corners (X, Z) = (4, 4), (29, 4), (4, 29)."),
    dict(id="M12", level="medium", build=m12, wrong=[dict(groove_r=17.5), dict(groove_z0=2.0)],
         text=T + "A grooved pulley on the Z axis. Cylinder: diameter 40, Z from 0 to 12. A rectangular groove runs all "
              "around it: between Z = 4 and Z = 8, material is removed from radius 16 out to the outside (radius 20). "
              "An 8 mm bore goes through along the Z axis."),
    dict(id="M13", level="medium", build=m13, wrong=[dict(tab_x1=30.0), dict(tab_hole_x=15.0)],
         text=T + "A cable clip. Ring: outer diameter 16, inner diameter 10, centred on the Z axis, Z from 0 to 8. "
              "Tab: the block X from 0 to 25, Y from 5 to 8, Z from 0 to 8, joined to the ring (the ring's 10 mm hole "
              "stays fully open). A 4 mm hole goes through the tab along Y, centred at X = 20, Z = 4."),
    dict(id="M14", level="medium", build=m14, wrong=[dict(knuckle_r=4.0), dict(pin_r=1.0)],
         text=T + "A hinge leaf. Plate: X from 0 to 40, Y from 0 to 30, Z from 0 to 2. Knuckle: a cylinder of "
              "diameter 6 along X, X from 0 to 40, its axis at Y = 0, Z = 3. A 3 mm pin hole goes through the knuckle "
              "along the same axis."),
    dict(id="M15", level="medium", build=m15, wrong=[dict(post_x=35.0), dict(hole_depth=12.0)],
         text=T + "A drawer handle. Grip bar: X from -50 to 50, Y from -5 to 5, Z from 20 to 30. Two posts under it: "
              "X from -45 to -35 and X from 35 to 45, both Y from -5 to 5, Z from 0 to 20. Each post has a 3.3 mm "
              "screw hole going up from the bottom face along Z, 8 deep, centred at (X, Y) = (-40, 0) and (40, 0)."),
    # ---- hard
    dict(id="H1", level="hard", build=h1, wrong=[dict(boss_xy=(30.0, 15.0)), dict(hole_d=3.5)],
         text=T + "An electronics enclosure, open at the top. Outside: X from -40 to 40, Y from -25 to 25, Z from 0 "
              "to 30; walls and floor 2 thick (hollow inside X from -38 to 38, Y from -23 to 23, Z from 2 to 30). "
              "Inside, four screw bosses stand on the floor: cylinders of diameter 6, Z from 2 to 27, centred at "
              "(X, Y) = (33, 18), (-33, 18), (-33, -18), (33, -18). Each boss has a 2.5 mm hole along its axis from "
              "Z = 2 to 27 (it does not go through the floor)."),
    dict(id="H2", level="hard", build=h2, wrong=[dict(pattern=((21, 10), (79, 10), (21, 55), (79, 55))),
                                                 dict(slot_ys=(25.0,))],
         text=T + "A circuit-board mounting plate. Plate: X from 0 to 100, Y from 0 to 70, Z from 0 to 3. Four "
              "standoffs, diameter 6, Z from 3 to 8, centred at (X, Y) = (21, 10), (79, 10), (21, 59), (79, 59). Each "
              "has a 2.7 mm hole along Z through the standoff and the plate (Z from 0 to 8). Two cable slots go "
              "through the plate: each is a 20 long, 6 wide obround (rounded ends, long side along X), centred at "
              "(50, 25) and at (50, 45)."),
    dict(id="H3", level="hard", build=h3, wrong=[dict(n=10), dict(key_len=3.0)],
         text=T + "A gear blank on the Z axis. Disk: diameter 40, Z from 0 to 8. Twelve notches go through it along "
              "Z: each removes the material within 1.5 of a ray from the centre and at a distance of 16 or more from "
              "the centre (3 wide, 4 deep); the rays point at angles 0°, 30°, 60° … 330° from the +X axis. An 8 mm "
              "bore goes through the centre along Z, with a keyway: the box X from 0 to 5.5, Y from -1.5 to 1.5 "
              "(through Z) is also removed."),
    dict(id="H4", level="hard", build=h4, wrong=[dict(hole_z=12.0), dict(fin_h=12.0)],
         text=T + "A three-fin camera mount. Base: X from -10 to 10, Y from -10 to 10, Z from 0 to 4. Three fins stand "
              "on it, each Y from -10 to 10, Z from 4 to 19, at X from -7.5 to -4.5, from -1.5 to 1.5 and from 4.5 to "
              "7.5. A 5 mm hole goes through all three fins along X, its axis at Y = 0, Z = 14."),
    dict(id="H5", level="hard", build=h5, wrong=[dict(hole_at=12.0), dict(t=4.0)],
         text=T + "A three-way corner bracket made of three 3 thick plates meeting at the origin: plate 1 X from 0 to "
              "30, Y from 0 to 30, Z from 0 to 3; plate 2 X from 0 to 30, Y from 0 to 3, Z from 0 to 30; plate 3 X "
              "from 0 to 3, Y from 0 to 30, Z from 0 to 30. Each plate has one 4 mm hole through its thickness: "
              "plate 1 along Z at (X, Y) = (16.5, 16.5); plate 2 along Y at (X, Z) = (16.5, 16.5); plate 3 along X "
              "at (Y, Z) = (16.5, 16.5)."),
    dict(id="H6", level="hard", build=h6, wrong=[dict(pocket_depth=10.0), dict(mount_x=17.0)],
         text=T + "A bearing housing. Block: X from -25 to 25, Y from -20 to 20, Z from 0 to 25. A bearing pocket of "
              "diameter 22 goes down from the top face 7 deep (Z from 18 to 25) on the Z axis. A 10 mm hole goes "
              "through the block on the Z axis. Two 5 mm mounting holes go through along Z at (X, Y) = (-20, 0) and "
              "(20, 0)."),
    dict(id="H7", level="hard", build=h7, wrong=[dict(flats=12.0), dict(depth=7.0)],
         text=T + "A spacer on the Z axis. Cylinder: diameter 20, Z from 0 to 12. A hexagonal pocket goes down from "
              "the top face 5 deep (Z from 7 to 12): a regular hexagon centred on the axis, 10 across the flats, with "
              "two of its flats parallel to the X axis (at Y = -5 and Y = 5). A 5.5 mm hole goes through on the axis."),
    dict(id="H8", level="hard", build=h8, wrong=[dict(arm_t=3.0), dict(hook_h=3.0)],
         text=T + "A snap-fit hook, everything Y from 0 to 10. Block: X from 0 to 20, Z from 0 to 5. Flexible arm: "
              "X from 20 to 50, Z from 3 to 5. Hook at the tip: a triangular prism on top of the arm whose "
              "cross-section in the X-Z plane is the triangle (X, Z) = (48, 5), (50, 5), (50, 7) (a 45° ramp)."),
    dict(id="H9", level="hard", build=h9, wrong=[dict(n=8), dict(fin_t=2.0)],
         text=T + "A heat sink. Base: X from -30 to 30, Y from -20 to 20, Z from 0 to 4. Nine fins stand on it, each "
              "1.5 thick in X, Y from -20 to 20, Z from 4 to 24, with their centres at X = -28, -21, -14, -7, 0, 7, "
              "14, 21 and 28."),
    dict(id="H10", level="hard", build=h10, wrong=[dict(inner_r=11.0), dict(hole_x=20.0)],
         text=T + "A pipe saddle clamp, everything Y from -10 to 10. Band: the upper half (Z ≥ 0) of a tube along Y "
              "with inner diameter 25 and outer diameter 31, its axis at X = 0, Z = 0. Two feet, joined to the band: X from -30.5 to "
              "-13 and X from 13 to 30.5, Z from 0 to 3. Each foot has a 5 mm hole along Z at (X, Y) = (-23, 0) "
              "and (23, 0)."),
    dict(id="H11", level="hard", build=h11, wrong=[dict(hole_xz=(30.0, 20.0)), dict(pocket_depth=6.0)],
         text=T + "A stair block, Y from 0 to 30. Four steps, each 8 high: X from 0 to 40, Z 0 to 8; X from 10 to 40, "
              "Z 8 to 16; X from 20 to 40, Z 16 to 24; X from 30 to 40, Z 24 to 32. A 6 mm hole goes all the way "
              "through along Y, its axis at X = 35, Z = 28. A square pocket X from 0 to 10, Y from 10 to 20 goes down "
              "4 from the top of the lowest step (Z from 4 to 8)."),
    dict(id="H12", level="hard", build=h12, wrong=[dict(n=12), dict(d_flat=3.0)],
         text=T + "A grip knob on the Z axis. Cylinder: diameter 30, Z from 0 to 15. Eighteen grip grooves: remove 18 "
              "cylinders of diameter 3 running the full height along Z, centred on the 30 mm outer circle at angles "
              "0°, 20°, 40° … 340° from the +X axis. A D-shaped shaft hole goes through on the axis: a 6 mm circle "
              "with the part at X > 1.5 left solid (a flat at X = 1.5)."),
    dict(id="H13", level="hard", build=h13, wrong=[dict(hole_zs=(20.0, 40.0)), dict(tip_h=10.0)],
         text=T + "A wall hook. Back plate: X from -15 to 15, Y from 0 to 4, Z from 0 to 60 (Y = 0 is the wall side). "
              "Arm: X from -5 to 5, Y from 4 to 34, Z from 25 to 30. Tip: X from -5 to 5, Y from 29 to 34, Z from 30 "
              "to 45. Two screw holes go through the back plate along Y at (X, Z) = (0, 15) and (0, 45): each is a 4 "
              "mm hole with a 90° countersink on the front face (Y = 4), 8 mm across at that face."),
    dict(id="H14", level="hard", build=h14, wrong=[dict(slot_len=20.0), dict(upper_x0=30.0)],
         text=T + "A Z-bracket, everything Y from 0 to 20, 3 thick. Lower flange: X from 0 to 30, Z from 0 to 3. "
              "Web: X from 27 to 30, Z from 0 to 23. Upper flange: X from 27 to 57, Z from 20 to 23. Each flange has "
              "a slot through it along Z: a 15 long, 5 wide obround (rounded ends, long side along X), centred at "
              "(X, Y) = (15, 10) in the lower flange and (42, 10) in the upper flange."),
    dict(id="H15", level="hard", build=h15, wrong=[dict(cols=7), dict(vent=5.0)],
         text=T + "A vented lid. Plate: X from -40 to 40, Y from -25 to 25, Z from 0 to 2. Forty square vents, 4 by 4, "
              "go through it: a grid of 8 columns and 5 rows with centres at X = -28, -20, -12, -4, 4, 12, 20, 28 and "
              "Y = -16, -8, 0, 8, 16. Four 3 mm corner holes go through at (X, Y) = (±36, ±21)."),
    # ---- dry run only (not scored)
    dict(id="D1", level="dry", build=d1, wrong=[dict(hole_x=22.0), dict(hole_d=5.0)],
         text=T + "A mounting plate: X from -30 to 30, Y from -20 to 20, Z from 0 to 5, with four 4 mm holes through "
              "it along Z at (X, Y) = (±25, ±15)."),
    dict(id="D2", level="dry", build=d2, wrong=[dict(rib_h=15.0), dict(rib_x=5.0)],
         text=T + "A ribbed plate. Plate: X from -20 to 20, Y from -10 to 10, Z from 0 to 3. Rib on top: X from -1.5 "
              "to 1.5, Y from -10 to 10, Z from 3 to 15."),
    dict(id="D3", level="dry", build=d3, wrong=[dict(boss_x=14.0), dict(slot_x=24.0)],
         text=T + "A plate X from 0 to 40, Y from 0 to 20, Z from 0 to 4, with a round boss of diameter 10 on top at "
              "(X, Y) = (10, 10), Z from 4 to 14, and a 3 mm hole along Z through the boss and the plate. A slot goes "
              "through the plate along Z: a 16 long, 6 wide obround with its long side along Y, centred at (28, 10)."),
]
