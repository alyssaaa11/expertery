"""Thinking-jobs exam (Claude, 2026-10-29): 10 requests written like real company work orders (5 medium + 5 hard) plus
2 dry-run jobs. Unlike the first test, a request does NOT give the coordinates: the model must derive every size and
position from the goal plus the company standard NDS-1 (STANDARDS.md, given to the model in the prompt). Each job has
one reference part and two wrong versions that make a typical reasoning mistake (a rule ignored or misapplied).
Frozen once selftest.py passes.
"""
from cadquery import Solid, Vector


# Shape helpers copied from experiments/first-test/jobs.py (self-contained, so the grader image needs only this file).
def box(x0, x1, y0, y1, z0, z1):
    return Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def zcyl(r, x, y, z0, z1):
    return Solid.makeCylinder(r, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))


def slot_z(cx, cy, length, width, z0, z1):
    """Obround slot along X: total length `length`, width `width`."""
    half = (length - width) / 2
    s = box(cx - half, cx + half, cy - width / 2, cy + width / 2, z0, z1)
    return s.fuse(zcyl(width / 2, cx - half, cy, z0, z1)).fuse(zcyl(width / 2, cx + half, cy, z0, z1))

T = "Nimbus request (apply NDS-1). "


def plate_with_holes(x, y, t, centres, d):
    s = box(-x / 2, x / 2, -y / 2, y / 2, 0, t)
    for cx, cy in centres:
        s = s.cut(zcyl(d / 2, cx, cy, 0, t))
    return s


def corners(x, y, inset):
    return [(sx * (x / 2 - inset), sy * (y / 2 - inset)) for sx in (-1, 1) for sy in (-1, 1)]


def open_box(ix, iy, depth, wall):
    """Open-top enclosure with inside space ix * iy, `depth` tall above the floor; walls and floor `wall` thick."""
    s = box(-ix / 2 - wall, ix / 2 + wall, -iy / 2 - wall, iy / 2 + wall, 0, wall + depth)
    return s.cut(box(-ix / 2, ix / 2, -iy / 2, iy / 2, wall, wall + depth))


def boss(s, x, y, z0, z1, screw):
    s = s.fuse(zcyl(2.5 * screw / 2, x, y, z0, z1))
    return s.cut(zcyl(0.8 * screw / 2, x, y, z0, z1))


# ---------------------------------------------------------------- dry

def d1(hole_d=4.5, inset=8.0):
    return plate_with_holes(60, 40, 5, corners(60, 40, inset), hole_d)


def d2(wall=2.5, depth=20.0):
    return open_box(50, 30, depth, wall)


# ---------------------------------------------------------------- medium

def t1(hole_d=5.5, inset=10.0):
    return plate_with_holes(80, 50, 6, corners(80, 50, inset), hole_d)


def t2(cb_d=11.0, cb_depth=6.5, inset=12.0):
    s = plate_with_holes(100, 60, 12, corners(100, 60, inset), 6.6)
    for cx, cy in corners(100, 60, inset):
        s = s.cut(zcyl(cb_d / 2, cx, cy, 12 - cb_depth, 12))
    return s


def t3(clear=0.5, wall=2.5):
    return open_box(60 + 2 * clear, 40 + 2 * clear, 18, wall)


def t4(width=4.5, extra=10.0):
    s = box(-35, 35, -15, 15, 0, 4)
    for cx in (-22, 22):
        s = s.cut(slot_z(cx, 0, width + extra, width, 0, 4))
    return s


def t5(gap=0.3, lip_h=4.0):
    s = box(-33, 33, -23, 23, 0, 2.5)
    ox, oy = 61 / 2 - gap, 41 / 2 - gap
    ring = box(-ox, ox, -oy, oy, 2.5, 2.5 + lip_h).cut(box(-ox + 2.5, ox - 2.5, -oy + 2.5, oy - 2.5, 2.5, 2.5 + lip_h))
    return s.fuse(ring)


# ---------------------------------------------------------------- hard

def t6(boss_screw_factor=2.5, hole_xy=(31.5, 19.0)):
    s = open_box(71, 46, 25, 2.5)
    hx, hy = hole_xy
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * hx, sy * hy
            s = s.fuse(zcyl(boss_screw_factor * 3 / 2, x, y, 2.5, 8.5))
            s = s.cut(zcyl(0.8 * 3 / 2, x, y, 2.5, 8.5))
    return s


def t7(wall=4.0, counterbore=True):
    s = open_box(50, 30, 25, wall)
    s = s.cut(zcyl(3.4 / 2, 0, 0, 0, wall))
    if counterbore:
        s = s.cut(zcyl(6.5 / 2, 0, 0, wall - 3.5, wall))
    return s


def t8(inset=3.75, pilot_d=2.4):
    s = open_box(80, 50, 30, 2.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (40 - inset), sy * (25 - inset)
            s = s.fuse(zcyl(7.5 / 2, x, y, 2.5, 32.5))
            s = s.cut(zcyl(pilot_d / 2, x, y, 2.5, 32.5))
    return s


def t9(bore_d=31.0, cb_d=10.0, cb_depth=5.5):
    s = plate_with_holes(90, 90, 10, corners(90, 90, 10), 5.5)
    s = s.cut(zcyl(bore_d / 2, 0, 0, 0, 10))
    for cx, cy in corners(90, 90, 10):
        s = s.cut(zcyl(cb_d / 2, cx, cy, 10 - cb_depth, 10))
    return s


def t10(slot_extra=10.0, boss_d=7.5):
    s = box(-30, 30, -20, 20, 0, 5)
    for cx in (-20, 20):
        s = s.cut(slot_z(cx, 0, 4.5 + slot_extra, 4.5, 0, 5))
    s = s.fuse(zcyl(boss_d / 2, 0, 0, 5, 17))
    return s.cut(zcyl(2.4 / 2, 0, 0, 5, 17))


# ---------------------------------------------------------------- expert (added 2026-10-29: 3-6 rules chained each)

def e1(board_top=8.5, lid_inset=3.75):
    s = open_box(90, 60, 30, 2.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s = boss(s, sx * 26.5, sy * 16.5, 2.5, board_top, 3)
            s = boss(s, sx * (45 - lid_inset), sy * (30 - lid_inset), 2.5, 32.5, 3)
    return s


def e2(bore_d=41.0, m4_d=4.5, inset=12.0):
    s = plate_with_holes(120, 80, 8, corners(120, 80, inset), 6.6)
    for cx, cy in corners(120, 80, inset):
        s = s.cut(zcyl(11 / 2, cx, cy, 8 - 6.5, 8))
    s = s.cut(zcyl(bore_d / 2, 0, 0, 0, 8))
    for cx, cy in corners(46, 46, 0):
        s = s.cut(zcyl(m4_d / 2, cx, cy, 0, 8))
    return s


def e3(extra=10.0, along_x=True):
    s = open_box(60, 40, 20, 2.5)
    for cx in (-20, 20):
        if along_x:
            s = s.cut(slot_z(cx, 0, 5.5 + extra, 5.5, 0, 2.5))
        else:
            s = s.cut(slot_z(0, 0, 5.5 + extra, 5.5, 0, 2.5).rotate(Vector(0, 0, 0), Vector(0, 0, 1), 90)
                      .translate(Vector(cx, 0, 0)))
    return s


def e4(hole_c=16.5, wall=4.0):
    s = open_box(41, 41, 15, wall)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s = s.cut(zcyl(4.5 / 2, sx * hole_c, sy * hole_c, 0, wall))
    return s


def e5(bore_d=23.0, boss_f=2.5, cb_depth=4.5):
    s = plate_with_holes(80, 60, 6, corners(80, 60, 8), 4.5)
    for cx, cy in corners(80, 60, 8):
        s = s.cut(zcyl(8 / 2, cx, cy, 6 - cb_depth, 6))
    s = s.cut(zcyl(bore_d / 2, 0, 0, 0, 6))
    for cx in (-20, 20):
        s = s.fuse(zcyl(boss_f * 3 / 2, cx, 0, 6, 16))
        s = s.cut(zcyl(2.4 / 2, cx, 0, 6, 16))
    return s


def e6(t=4.0, gap=0.3):
    ox, oy = 70 / 2 + t, 40 / 2 + t
    s = box(-ox, ox, -oy, oy, 0, t)
    lx, ly = 35 - gap, 20 - gap
    ring = box(-lx, lx, -ly, ly, t, t + 4).cut(box(-lx + t, lx - t, -ly + t, ly - t, t, t + 4))
    return s.fuse(ring).cut(zcyl(5.5 / 2, 0, 0, 0, t))


# ---------------------------------------------------------------- calibration (pilot difficulty gate, not scored)

def c1(top=7.5, hole_xy=(21.0, 11.0)):
    s = open_box(51, 31, 15, 2.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s = boss(s, sx * hole_xy[0], sy * hole_xy[1], 2.5, top, 3)
    return s


def c2(bore_d=36.0, slot_len=14.5):
    s = plate_with_holes(100, 70, 10, corners(100, 70, 10), 5.5)
    for cx, cy in corners(100, 70, 10):
        s = s.cut(zcyl(10 / 2, cx, cy, 10 - 5.5, 10))
    s = s.cut(zcyl(bore_d / 2, 0, 0, 0, 10))
    for cx in (-30, 30):
        s = s.cut(slot_z(cx, 0, slot_len, 4.5, 0, 10))
    return s


def c3(clear=0.5, gap=0.3):
    ix, iy = 40 + 2 * clear, 25 + 2 * clear
    s = box(-ix / 2 - 2.5, ix / 2 + 2.5, -iy / 2 - 2.5, iy / 2 + 2.5, 0, 2.5)
    lx, ly = ix / 2 - gap, iy / 2 - gap
    ring = box(-lx, lx, -ly, ly, 2.5, 6.5).cut(box(-lx + 2.5, lx - 2.5, -ly + 2.5, ly - 2.5, 2.5, 6.5))
    return s.fuse(ring)


JOBS = [
    # ---- medium
    dict(id="T2", level="medium", build=t2, wrong=[dict(cb_d=10.0, cb_depth=5.5), dict(inset=6.0)],
         text=T + "A plastic clamp plate, 100 by 60, 12 thick, fixed by four M6 socket-head screws at the corners, "
              "with the screw heads sunk flush with the top face."),
    dict(id="T5", level="medium", build=t5, wrong=[dict(gap=0.0), dict(lip_h=3.0)],
         text=T + "A plastic lid for an enclosure whose outside is 66 by 46 and whose walls are 2.5 thick."),
    # ---- hard
    dict(id="T6", level="hard", build=t6, wrong=[dict(boss_screw_factor=2.0), dict(hole_xy=(32.0, 19.5))],
         text=T + "A plastic enclosure, open at the top, for a circuit board of 70 by 45. The board has an M3 "
              "mounting hole near each corner, 3.5 from both board edges, and is screwed onto four screw bosses "
              "that are 6 tall. The space inside the enclosure is 25 tall, measured from the floor."),
    dict(id="T7", level="hard", build=t7, wrong=[dict(wall=2.5), dict(counterbore=False)],
         text=T + "An aluminium housing, open at the top, whose inside space is 50 by 30 and 25 deep. In the middle "
              "of its floor is a hole for an M3 socket-head screw inserted from inside the housing, with its head "
              "sunk into the floor."),
    dict(id="T8", level="hard", build=t8, wrong=[dict(inset=3.0), dict(pilot_d=3.4)],
         text=T + "A plastic enclosure, open at the top, whose inside space is 80 by 50 and 30 deep, with lid-screw "
              "bosses for M3 screws."),
    dict(id="T9", level="hard", build=t9, wrong=[dict(bore_d=30.0), dict(cb_d=11.0, cb_depth=6.5)],
         text=T + "An aluminium flange plate, 90 by 90, 10 thick, for a pipe of 30 outside diameter that passes "
              "through its centre. It is fixed by four M5 socket-head screws at the corners, heads sunk flush."),
    dict(id="T10", level="hard", build=t10, wrong=[dict(slot_extra=5.0), dict(boss_d=6.0)],
         text=T + "A plastic sensor bracket: a base plate, 60 by 40, 5 thick, fixed by two mounting slots for M4 "
              "screws centred on the plate's centre line at X = -20 and X = 20. In the middle of the plate stands a "
              "screw boss for an M3 screw, 12 tall."),
    # ---- expert additions (2026-10-29): each chains 3-6 NDS-1 rules
    dict(id="E1", level="hard", build=e1, wrong=[dict(board_top=6.0), dict(lid_inset=6.0)],
         text=T + "A plastic enclosure, open at the top, whose inside space is 90 by 60 and 30 deep, with lid-screw "
              "bosses for M3 screws. A circuit board of 60 by 40 sits centred in it, screwed onto four screw bosses "
              "that are 6 tall; the board has an M3 mounting hole near each corner, 3.5 from both board edges."),
    dict(id="E2", level="hard", build=e2, wrong=[dict(bore_d=40.0), dict(inset=6.0)],
         text=T + "An aluminium motor adapter plate, 120 by 80, 8 thick, fixed to the machine by four M6 socket-head "
              "screws at the corners, heads sunk flush. A motor whose round body is 40 in diameter passes through "
              "the centre of the plate and is fixed by four M4 screws on a 46 by 46 square pattern centred on the "
              "plate."),
    dict(id="E3", level="medium", build=e3, wrong=[dict(extra=5.0), dict(along_x=False)],
         text=T + "A plastic enclosure, open at the top, whose inside space is 60 by 40 and 20 deep. It is fixed to "
              "a rail by two mounting slots for M5 screws in its floor, centred on the centre line at X = -20 and "
              "X = 20."),
    dict(id="E4", level="hard", build=e4, wrong=[dict(hole_c=12.5), dict(wall=2.5)],
         text=T + "An aluminium housing, open at the top, for a square module of 40 by 40. The space inside is 15 "
              "deep. The housing is fixed by four M4 screws at the corners, through its floor."),
    dict(id="E5", level="hard", build=e5, wrong=[dict(bore_d=22.0), dict(boss_f=2.0)],
         text=T + "A plastic sensor plate, 80 by 60, 6 thick, fixed by four M4 socket-head screws at the corners, "
              "heads sunk flush. Through its centre passes a cable gland of 22 outside diameter. On the plate's "
              "centre line at X = -20 and X = 20 stand two screw bosses for M3 screws, 10 tall."),
    dict(id="E6", level="medium", build=e6, wrong=[dict(t=2.5), dict(gap=0.15)],
         text=T + "A lid for an aluminium enclosure whose inside space is 70 by 40, with a hole for an M5 handle "
              "screw through the middle of the lid."),
    # ---- dry run (not scored)
    dict(id="D1", level="dry", build=d1, wrong=[dict(hole_d=4.0), dict(inset=4.0)],
         text=T + "A plastic mounting plate, 60 by 40, 5 thick, fixed by four M4 screws at the corners."),
    dict(id="D2", level="dry", build=d2, wrong=[dict(wall=2.0), dict(depth=22.5)],
         text=T + "A plastic open-top enclosure whose inside space is 50 by 30 and 20 deep."),
    # ---- calibration (level dry: run in the pilot as the difficulty gate, never scored)
    dict(id="C1", level="dry", build=c1, wrong=[dict(top=5.0), dict(hole_xy=(25.0, 15.0))],
         text=T + "A plastic enclosure, open at the top, for a circuit board of 50 by 30. The space inside is 15 "
              "tall. The board has an M3 mounting hole near each corner, 4 from both board edges, and is screwed "
              "onto four screw bosses that are 5 tall."),
    dict(id="C2", level="dry", build=c2, wrong=[dict(bore_d=35.0), dict(slot_len=9.5)],
         text=T + "An aluminium bearing plate, 100 by 70, 10 thick, for a shaft housing of 35 outside diameter "
              "passing through its centre. It is fixed by four M5 socket-head screws at the corners, heads sunk "
              "flush, and has two mounting slots for M4 screws on its centre line at X = -30 and X = 30."),
    dict(id="C3", level="dry", build=c3, wrong=[dict(clear=0.0), dict(gap=0.0)],
         text=T + "A plastic lid for an enclosure made for a circuit board of 40 by 25."),
]
