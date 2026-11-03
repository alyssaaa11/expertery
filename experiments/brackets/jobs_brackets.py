"""Bracket workflow test: 20 mounting-bracket requests written the way an employee would ask for a part.

Exam content (Claude, 2026-11-03), like experiments/first-test/jobs.py: written before any model saw these jobs.
Every request ends with a placement line, so a correct answer has exactly one shape and the 0.2% referee can grade it.
No bracket family exists in the training data (experiments/r5/jobs_r5d.jsonl families 1-10).

Each job is a list of (op, expr) steps; the reference program is built from them.
  python jobs_brackets.py            -> writes jobs_brackets.jsonl (id, family, level, text, reference)
  python jobs_brackets.py --selftest -> builds every reference (1 solid, volume > 0) and checks that dropping any
                                        single step changes the part by more than 0.2%, so the referee sees every feature
Runs Claude's own reference code only (never model answers), in the forge .venv (cadquery 2.8.0).
"""
import json
import os
import sys

HEADER = '''import cadquery as cq
from cadquery import Solid, Vector

def _box(x0, x1, y0, y1, z0, z1):
    return Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))

def _zcyl(r, x, y, z0, z1):
    return Solid.makeCylinder(r, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))

def _xcyl(r, y, z, x0, x1):
    return Solid.makeCylinder(r, x1 - x0, Vector(x0, y, z), Vector(1, 0, 0))

def _ycyl(r, x, z, y0, y1):
    return Solid.makeCylinder(r, y1 - y0, Vector(x, y0, z), Vector(0, 1, 0))

def _prism_xz(points, y0, y1):
    w = cq.Workplane("XY").polyline(points).close().extrude(y1 - y0).val()
    m = cq.Matrix([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]])
    return w.transformGeometry(m)

def _prism_xy(points, z0, z1):
    return cq.Workplane("XY").polyline(points).close().extrude(z1 - z0).translate((0, 0, z0)).val()

def _zcone(r0, r1, x, y, z0, z1):
    return Solid.makeCone(r0, r1, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))

def _rounded_plate(lx, ly, t, r):
    return cq.Workplane("XY").box(lx, ly, t, centered=(True, True, False)).edges("|Z").fillet(r).val()
'''

T = "Millimetres, Z up. "

JOBS = [
    dict(id="B1", level="medium", text=T +
         "Wall bracket for a power supply. Base plate 60 wide (X), 40 deep (Y), 4 thick. An upright plate, also 60 wide "
         "and 4 thick, stands on the back edge of the base, flush with it, 50 tall overall from the bottom of the base. "
         "Two 5.5 mm holes (M5 clearance) go through the base, 20 either side of the centre line and 15 from the front "
         "edge. Two 5.5 mm holes go through the upright (along Y), 20 either side of the centre line, 35 above the "
         "bottom. Placement: centred on X = 0, front edge of the base on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-30, 30, 0, 40, 0, 4)"), ("add", "_box(-30, 30, 36, 40, 0, 50)"),
                ("cut", "_zcyl(2.75, -20, 15, -1, 5)"), ("cut", "_zcyl(2.75, 20, 15, -1, 5)"),
                ("cut", "_ycyl(2.75, -20, 35, 35, 41)"), ("cut", "_ycyl(2.75, 20, 35, 35, 41)")]),
    dict(id="B2", level="medium", text=T +
         "Shelf bracket for a 25 mm wide rail. Wall plate 80 tall, 25 wide, 5 thick; shelf arm 80 long, 25 wide, 5 "
         "thick, sticking out from the bottom of the wall plate so the two form an L. A 5 thick triangular gusset, "
         "centred on the width, fills the inside corner; its two short sides are 50 long, measured from the inside "
         "faces of the plate and the arm. One 4.5 mm screw hole goes through the wall plate on the centre line, 68 above "
         "the bottom. Two 4.5 mm holes go through the arm: one on the centre line 65 from the wall side, one 40 from the "
         "wall side and 8 off the centre line toward +Y. Placement: back face of the wall plate on X = 0, the arm "
         "pointing toward +X, centred on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(0, 5, -12.5, 12.5, 0, 80)"), ("add", "_box(0, 80, -12.5, 12.5, 0, 5)"),
                ("add", "_prism_xz([(5, 5), (55, 5), (5, 55)], -2.5, 2.5)"),
                ("cut", "_xcyl(2.25, 0, 68, -1, 6)"), ("cut", "_zcyl(2.25, 65, 0, -1, 6)"),
                ("cut", "_zcyl(2.25, 40, 8, -1, 6)")]),
    dict(id="B3", level="medium", text=T +
         "Offset (Z-shaped) bracket that lifts a sensor 30 mm off its mounting surface, bent from 3 thick plate, 30 wide "
         "(Y). Lower foot: 25 long along X, lying flat. Riser: goes straight up from the +X end of the foot (its outside "
         "face flush with the end of the foot) to 30 overall height. Top flange: 25 long, lying flat on top of the riser "
         "and pointing further toward +X (its outer end is 47 from the free end of the foot). One 6.5 mm hole goes "
         "through each flange along Z, in the middle of the width: in the foot 11 from its free end, in the top flange "
         "11 from its free end. Placement: free end of the foot on X = 0, width Y from 0 to 30, bottom on Z = 0.",
         steps=[("add", "_box(0, 25, 0, 30, 0, 3)"), ("add", "_box(22, 25, 0, 30, 0, 30)"),
                ("add", "_box(22, 47, 0, 30, 27, 30)"),
                ("cut", "_zcyl(3.25, 11, 15, -1, 4)"), ("cut", "_zcyl(3.25, 36, 15, 26, 31)")]),
    dict(id="B4", level="hard", text=T +
         "Flat mending plate to join two boards: 80 long (X), 20 wide (Y), 3 thick, with all four corners rounded to "
         "radius 5 when seen from above. Four countersunk screw holes in a row on the centre line, at 10 and 30 either "
         "side of the centre: each 4.5 mm through, with a 90° countersink that is 9 mm across at the top face. "
         "Placement: centred on X = 0 and Y = 0, bottom on Z = 0.",
         steps=[("add", "_rounded_plate(80, 20, 3, 5)")] +
               [("cut", "_zcyl(2.25, %d, 0, -1, 4)" % x) for x in (-30, -10, 10, 30)] +
               [("cut", "_zcone(2.25, 4.5, %d, 0, 0.75, 3)" % x) for x in (-30, -10, 10, 30)]),
    dict(id="B5", level="hard", text=T +
         "Adjustable angle bracket: two legs at 90° (an L seen from the side), each 40 long, 4 thick and 30 wide. Each "
         "leg has an adjustment slot through it, 12 long overall and 5.5 wide with round ends, running along the leg's "
         "length, centred 24 from the outside corner and in the middle of the width. Placement: outside corner on the "
         "origin; the horizontal leg runs along +X with its bottom on Z = 0, the vertical leg runs up along +Z with its "
         "outside face on X = 0; width Y from 0 to 30.",
         steps=[("add", "_box(0, 40, 0, 30, 0, 4)"), ("add", "_box(0, 4, 0, 30, 0, 40)"),
                ("cut", "_box(20.75, 27.25, 12.25, 17.75, -1, 5)"), ("cut", "_zcyl(2.75, 20.75, 15, -1, 5)"),
                ("cut", "_zcyl(2.75, 27.25, 15, -1, 5)"),
                ("cut", "_box(-1, 5, 12.25, 17.75, 20.75, 27.25)"), ("cut", "_xcyl(2.75, 15, 20.75, -1, 5)"),
                ("cut", "_xcyl(2.75, 15, 27.25, -1, 5)")]),
    dict(id="B6", level="medium", text=T +
         "U-shaped holder for a 36 mm wide module. Base 42 wide (X) by 25 deep (Y), 3 thick. Two side walls, 3 thick "
         "and 35 tall overall, stand on the left and right edges of the base for its full depth, leaving 36 between "
         "them. Each side wall has a 4.2 mm hole through it along X, in the middle of the depth, 28 above the bottom. "
         "Two 4.5 mm holes go through the base, 9 either side of the centre line, in the middle of the depth. "
         "Placement: centred on X = 0, front edge on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-21, 21, 0, 25, 0, 3)"), ("add", "_box(-21, -18, 0, 25, 0, 35)"),
                ("add", "_box(18, 21, 0, 25, 0, 35)"),
                ("cut", "_xcyl(2.1, 12.5, 28, -22, -17)"), ("cut", "_xcyl(2.1, 12.5, 28, 17, 22)"),
                ("cut", "_zcyl(2.25, -9, 12.5, -1, 4)"), ("cut", "_zcyl(2.25, 9, 12.5, -1, 4)")]),
    dict(id="B7", level="hard", text=T +
         "Right-angle mount for a NEMA 17 stepper motor. Face plate 44 wide (X), 4 thick (Y), 50 tall. Foot 44 wide, "
         "25 deep, 4 thick, along the bottom of the face plate, extending toward +Y from the face plate's back face. "
         "Through the face plate (along Y): a 22.5 mm hole for the motor's centre boss, on the centre line 28 above the "
         "bottom, and four 3.4 mm screw holes on a 31 mm square around it (15.5 left/right and up/down from the boss "
         "centre). Two 4.5 mm holes go through the foot, 14 either side of the centre line, 16 from the face plate's "
         "back face. Placement: centred on X = 0, back face of the face plate on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-22, 22, 0, 4, 0, 50)"), ("add", "_box(-22, 22, 0, 25, 0, 4)"),
                ("cut", "_ycyl(11.25, 0, 28, -1, 5)")] +
               [("cut", "_ycyl(1.7, %s, %s, -1, 5)" % (x, z)) for x in (-15.5, 15.5) for z in (12.5, 43.5)] +
               [("cut", "_zcyl(2.25, -14, 16, -1, 5)"), ("cut", "_zcyl(2.25, 14, 16, -1, 5)")]),
    dict(id="B8", level="medium", text=T +
         "Hanging bracket. Upright tab 30 wide (X) and 4 thick (Y) with a fully rounded top: straight sides from the "
         "bottom up to 40, then a half-circle of radius 15 on top. An 8 mm hole goes through the tab along Y at the "
         "centre of that half-circle. Foot 30 wide, 30 deep, 4 thick, at the bottom of the tab, extending toward +Y "
         "from the tab's back face. Two 4.5 mm holes go through the foot, 8 either side of the centre line and 20 from "
         "the tab's back face. Placement: centred on X = 0, back face of the tab on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-15, 15, 0, 4, 0, 40)"), ("add", "_ycyl(15, 0, 40, 0, 4)"),
                ("add", "_box(-15, 15, 0, 30, 0, 4)"),
                ("cut", "_ycyl(4, 0, 40, -1, 5)"), ("cut", "_zcyl(2.25, -8, 20, -1, 5)"),
                ("cut", "_zcyl(2.25, 8, 20, -1, 5)")]),
    dict(id="B9", level="hard", text=T +
         "Bracket that holds a sensor at 45°. Base 40 long (X), 20 wide (Y), 4 thick. An arm, 20 wide like the base, "
         "rises from the top of the base leaning toward +X at 45°: seen from the side (X-Z), the arm is the "
         "parallelogram with corners (X, Z) = (32, 4), (36, 4), (55.799, 23.799) and (51.799, 23.799). Two 4.5 mm holes "
         "go through the base along Z at (X, Y) = (10, 10) and (22, 10). Placement: base corner on the origin, base X "
         "from 0 to 40, Y from 0 to 20, bottom on Z = 0.",
         steps=[("add", "_box(0, 40, 0, 20, 0, 4)"),
                ("add", "_prism_xz([(32, 4), (36, 4), (55.799, 23.799), (51.799, 23.799)], 0, 20)"),
                ("cut", "_zcyl(2.25, 10, 10, -1, 5)"), ("cut", "_zcyl(2.25, 22, 10, -1, 5)")]),
    dict(id="B10", level="hard", text=T +
         "Heavy-duty angle bracket. Two 5 thick legs, each 50 long and 40 wide (Y), at 90°: the horizontal leg along "
         "+X, the vertical leg up along +Z, the outside corner on the origin. Two 4 thick triangular gussets close the "
         "inside corner, flush with the two side edges (Y from 0 to 4 and from 36 to 40); each gusset's short sides run "
         "35 along each leg, measured from the inside faces. Two 6.6 mm holes go through the horizontal leg at X = 30, "
         "Y = 13 and Y = 27; two 6.6 mm holes go through the vertical leg along X at Z = 30, Y = 13 and Y = 27.",
         steps=[("add", "_box(0, 50, 0, 40, 0, 5)"), ("add", "_box(0, 5, 0, 40, 0, 50)"),
                ("add", "_prism_xz([(5, 5), (40, 5), (5, 40)], 0, 4)"),
                ("add", "_prism_xz([(5, 5), (40, 5), (5, 40)], 36, 40)"),
                ("cut", "_zcyl(3.3, 30, 13, -1, 6)"), ("cut", "_zcyl(3.3, 30, 27, -1, 6)"),
                ("cut", "_xcyl(3.3, 13, 30, -1, 6)"), ("cut", "_xcyl(3.3, 27, 30, -1, 6)")]),
    dict(id="B11", level="medium", text=T +
         "Flat T-shaped joining plate, 4 thick. Top bar 80 long (X) by 20 high (Y). Stem 20 wide, hanging 50 down "
         "(toward -Y) from the middle of the bar. Three 5 mm holes: in the bar 10 from each end on its centre line, and "
         "in the stem on its centre line 10 from its bottom end. Placement: bottom edge of the bar on Y = 0 (bar Y from "
         "0 to 20), centred on X = 0, bottom face on Z = 0.",
         steps=[("add", "_box(-40, 40, 0, 20, 0, 4)"), ("add", "_box(-10, 10, -50, 0, 0, 4)"),
                ("cut", "_zcyl(2.5, -30, 10, -1, 5)"), ("cut", "_zcyl(2.5, 30, 10, -1, 5)"),
                ("cut", "_zcyl(2.5, 0, -40, -1, 5)")]),
    dict(id="B12", level="hard", text=T +
         "Triangular shelf support. Wall plate 60 tall and arm 60 long, both 4 thick and 20 wide (Y), forming an L with "
         "the arm along +X at the bottom. A 4 thick web, centred on the width, fills the whole triangle between them "
         "out to the arm's tip and the top of the wall plate: in X-Z its corners are (4, 4), (60, 4) and (4, 60). A 16 "
         "mm lightening hole goes through the web along Y at (X, Z) = (20, 20). Placement: back of the wall plate on "
         "X = 0, centred on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(0, 4, -10, 10, 0, 60)"), ("add", "_box(0, 60, -10, 10, 0, 4)"),
                ("add", "_prism_xz([(4, 4), (60, 4), (4, 60)], -2, 2)"),
                ("cut", "_ycyl(8, 20, 20, -3, 3)")]),
    dict(id="B13", level="hard", text=T +
         "Pivot (clevis) bracket. Base plate 40 (X) by 30 (Y), 5 thick. Two ears stand on it, each 4 thick (Y) and 20 "
         "wide (X), centred on X = 0: one at Y from 8 to 12, the other at Y from -12 to -8. Each ear has straight sides "
         "up to Z = 25 and a rounded top, a half-circle of radius 10 centred at Z = 25. A 6 mm pivot hole goes through "
         "both ears along Y at the centre of the rounded top. Two 4.5 mm holes go through the base at X = -15 and "
         "X = 15, Y = 0. Placement: base centred on X = 0 and Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-20, 20, -15, 15, 0, 5)"), ("add", "_box(-10, 10, 8, 12, 0, 25)"),
                ("add", "_box(-10, 10, -12, -8, 0, 25)"), ("add", "_ycyl(10, 0, 25, 8, 12)"),
                ("add", "_ycyl(10, 0, 25, -12, -8)"),
                ("cut", "_ycyl(3, 0, 25, -13, 13)"), ("cut", "_zcyl(2.25, -15, 0, -1, 6)"),
                ("cut", "_zcyl(2.25, 15, 0, -1, 6)")]),
    dict(id="B14", level="hard", text=T +
         "Wall-hung ledge with a keyhole. Back plate 40 wide (X), 3 thick, 60 tall; its wall side is Y = 0. Ledge 40 "
         "wide, 4 thick, at the bottom, sticking out 35 from the wall side. Keyhole through the back plate (along Y): a "
         "10 mm round opening centred 45 above the bottom, with a 5 wide slot going straight up from its centre to a "
         "round end whose centre is 55 above the bottom. A 4.5 mm hole goes through the ledge on the centre line, 25 "
         "from the wall side. Placement: centred on X = 0, wall side on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-20, 20, 0, 3, 0, 60)"), ("add", "_box(-20, 20, 0, 35, 0, 4)"),
                ("cut", "_ycyl(5, 0, 45, -1, 4)"), ("cut", "_box(-2.5, 2.5, -1, 4, 45, 55)"),
                ("cut", "_ycyl(2.5, 0, 55, -1, 4)"), ("cut", "_zcyl(2.25, 0, 25, -1, 5)")]),
    dict(id="B15", level="medium", text=T +
         "Floor flange for a 25.4 mm (1 inch) tube. Square plate 50 by 50, 5 thick. A round boss on top, 35 diameter, "
         "20 tall above the plate. The 25.4 mm tube bore goes through the boss and the plate. Four 5.5 mm holes go "
         "through the plate near the corners, 18 from the centre in both X and Y. Placement: centred on the Z axis, "
         "bottom on Z = 0.",
         steps=[("add", "_box(-25, 25, -25, 25, 0, 5)"), ("add", "_zcyl(17.5, 0, 0, 5, 25)"),
                ("cut", "_zcyl(12.7, 0, 0, -1, 26)")] +
               [("cut", "_zcyl(2.75, %d, %d, -1, 6)" % (x, y)) for x in (-18, 18) for y in (-18, 18)]),
    dict(id="B16", level="medium", text=T +
         "Omega (hat-shaped) strap to clamp a cable bundle, 15 wide (Y from 0 to 15) and 3 thick everywhere. Two flat "
         "feet: X from -30 to -16 and from 16 to 30, Z from 0 to 3. Two sides go up from the inner ends of the feet: X "
         "from -16 to -13 and from 13 to 16, up to Z = 20. A top bridge joins them: X from -16 to 16, Z from 17 to 20. "
         "Each foot has a 4.5 mm hole along Z at X = -23 and X = 23, in the middle of the width.",
         steps=[("add", "_box(-30, -16, 0, 15, 0, 3)"), ("add", "_box(16, 30, 0, 15, 0, 3)"),
                ("add", "_box(-16, -13, 0, 15, 0, 20)"), ("add", "_box(13, 16, 0, 15, 0, 20)"),
                ("add", "_box(-16, 16, 0, 15, 17, 20)"),
                ("cut", "_zcyl(2.25, -23, 7.5, -1, 4)"), ("cut", "_zcyl(2.25, 23, 7.5, -1, 4)")]),
    dict(id="B17", level="medium", text=T +
         "Flat triangular gusset plate, 5 thick: a right triangle with both short sides 80 long, the right angle on the "
         "origin and the short sides along +X and +Y. Three 6.6 mm holes go through it along Z at (X, Y) = (12, 12), "
         "(55, 12) and (12, 55). Bottom on Z = 0.",
         steps=[("add", "_prism_xy([(0, 0), (80, 0), (0, 80)], 0, 5)"),
                ("cut", "_zcyl(3.3, 12, 12, -1, 6)"), ("cut", "_zcyl(3.3, 55, 12, -1, 6)"),
                ("cut", "_zcyl(3.3, 12, 55, -1, 6)")]),
    dict(id="B18", level="hard", text=T +
         "L-bracket for M4 socket-head screws. Base 50 (X) by 30 (Y), 8 thick. Upright, also 50 wide and 8 thick, 40 "
         "tall overall, standing on the back edge of the base and flush with it. Two holes in the base, 15 either side "
         "of the centre line and 10 from the front edge: each 4.5 mm through, with an 8 mm counterbore 4.5 deep from the "
         "top face. Two plain 4.5 mm holes go through the upright along Y, 15 either side of the centre line, 30 above "
         "the bottom. Placement: centred on X = 0, front edge on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(-25, 25, 0, 30, 0, 8)"), ("add", "_box(-25, 25, 22, 30, 0, 40)"),
                ("cut", "_zcyl(2.25, -15, 10, -1, 9)"), ("cut", "_zcyl(2.25, 15, 10, -1, 9)"),
                ("cut", "_zcyl(4, -15, 10, 3.5, 9)"), ("cut", "_zcyl(4, 15, 10, 3.5, 9)"),
                ("cut", "_ycyl(2.25, -15, 30, 21, 31)"), ("cut", "_ycyl(2.25, 15, 30, 21, 31)")]),
    dict(id="B19", level="hard", text=T +
         "Perforated mounting strap, 2 thick and 12 wide (Y). Flat part 120 long along X. At the +X end a tab turns up "
         "90° for the full width: 2 thick (X from 118 to 120), up to Z = 20. Six 4 mm holes go through the flat part "
         "along its centre line at X = 10, 30, 50, 70, 90 and 110, and one 4 mm hole goes through the tab along X, on "
         "the centre line, 13 above the bottom. Placement: X from 0 to 120, centred on Y = 0, bottom on Z = 0.",
         steps=[("add", "_box(0, 120, -6, 6, 0, 2)"), ("add", "_box(118, 120, -6, 6, 0, 20)")] +
               [("cut", "_zcyl(2, %d, 0, -1, 3)" % x) for x in (10, 30, 50, 70, 90, 110)] +
               [("cut", "_xcyl(2, 0, 13, 117, 121)")]),
    dict(id="B20", level="medium", text=T +
         "L-bracket with a cable notch. Base 60 (X) by 40 (Y), 5 thick. Upright 60 wide, 5 thick, 45 tall overall, "
         "standing on the back edge of the base and flush with it. A rectangular cable notch, 10 wide and 15 deep, is "
         "cut down from the top edge of the upright in the middle of its length. Two 5.5 mm holes go through the base, "
         "10 from each side and 15 from the front edge; two 5.5 mm holes go through the upright along Y, 10 from each "
         "side and 30 above the bottom. Placement: base corner on the origin, X from 0 to 60, front edge on Y = 0, "
         "bottom on Z = 0.",
         steps=[("add", "_box(0, 60, 0, 40, 0, 5)"), ("add", "_box(0, 60, 35, 40, 0, 45)"),
                ("cut", "_box(25, 35, 34, 41, 30, 46)"),
                ("cut", "_zcyl(2.75, 10, 15, -1, 6)"), ("cut", "_zcyl(2.75, 50, 15, -1, 6)"),
                ("cut", "_ycyl(2.75, 10, 30, 34, 41)"), ("cut", "_ycyl(2.75, 50, 30, 34, 41)")]),
]


def reference(steps):
    lines = [HEADER]
    first_op, first_expr = steps[0]
    assert first_op == "add"
    lines.append("s = %s" % first_expr)
    for op, expr in steps[1:]:
        lines.append("s = s.%s(%s)" % ("fuse" if op == "add" else "cut", expr))
    lines.append("s = s.clean()")
    lines.append("result = s")
    return "\n".join(lines) + "\n"


def build(steps):
    ns = {}
    exec(reference(steps), ns)
    return ns["result"]


def selftest():
    bad = 0
    for job in JOBS:
        s = build(job["steps"])
        n_solids = len(s.Solids())
        vol = s.Volume()
        ok = n_solids == 1 and vol > 0
        weakest = None
        for i in range(1, len(job["steps"])):
            other = build(job["steps"][:i] + job["steps"][i + 1:])
            diff = s.cut(other).Volume() + other.cut(s).Volume()
            frac = diff / vol
            if weakest is None or frac < weakest[0]:
                weakest = (frac, job["steps"][i][1])
            if frac <= 0.002:
                ok = False
        print("%-4s %-6s solids=%d vol=%9.1f weakest step %.4f (%s) %s" % (
            job["id"], job["level"], n_solids, vol, weakest[0], weakest[1], "OK" if ok else "FAIL"))
        bad += not ok
    print("selftest: %d/%d OK" % (len(JOBS) - bad, len(JOBS)))
    return bad == 0


def write_jsonl(path):
    with open(path, "w", encoding="utf-8") as f:
        for job in JOBS:
            f.write(json.dumps(dict(id=job["id"], family="bracket", level=job["level"], text=job["text"],
                                    reference=reference(job["steps"]))) + "\n")
    print("wrote %d jobs to %s" % (len(JOBS), path))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    write_jsonl(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs_brackets.jsonl"))
