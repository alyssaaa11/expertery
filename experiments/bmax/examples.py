"""B-max solved examples (Claude, 2026-10-29). Three CadQuery jobs written in the same style as the first test,
deliberately NOT from the 30 exam jobs or their part families (exam list: experiments/first-test/jobs-list.md:
brackets, profiles, boxes, lids, shafts, flanges, channels, standoff plates, stands, counterbores, gussets, pulleys,
clips, hinges, handles, enclosures, gears, fins, housings, spacers with hex pockets, hooks, heat sinks, clamps,
stairs, knobs, Z-brackets). Used only as worked examples in the B-max prompt. verify() checks each one builds."""

EXAMPLES = [
    dict(
        text="A nameplate. Plate: X from 0 to 70, Y from 0 to 30, Z from 0 to 4. A rectangular recess in the top face, "
             "X from 5 to 65, Y from 5 to 25, 1 deep (Z from 3 to 4). Two 3.4 mm holes along Z through the plate, "
             "centred at (X, Y) = (10, 15) and (60, 15).",
        code='''import cadquery as cq
# Boxes are centred by default: build with centered=False so the corner sits at the origin, as the job says.
plate = cq.Workplane("XY").box(70, 30, 4, centered=False)
recess = cq.Workplane("XY").box(60, 20, 1, centered=False).translate((5, 5, 3))
holes = (cq.Workplane("XY").pushPoints([(10, 15), (60, 15)]).circle(3.4 / 2).extrude(4))
result = plate.cut(recess).cut(holes)''',
        bbox=((0, 0, 0), (70, 30, 4)),
    ),
    dict(
        text="A plus-shaped spacer. Two crossing bars, Z from 0 to 6: bar 1 X from 10 to 50, Y from 25 to 35; bar 2 "
             "X from 25 to 35, Y from 10 to 50. A 5 mm hole along Z through the centre of the cross at (30, 30).",
        code='''import cadquery as cq
# A centred box lands on its centre point: place each bar by moving its centre to the job's centre.
bar1 = cq.Workplane("XY").box(40, 10, 6).translate((30, 30, 3))
bar2 = cq.Workplane("XY").box(10, 40, 6).translate((30, 30, 3))
hole = cq.Workplane("XY").center(30, 30).circle(2.5).extrude(6)
result = bar1.union(bar2).cut(hole)
# Self-check: bounding box should be X 10..50, Y 10..50, Z 0..6.''',
        bbox=((10, 10, 0), (50, 50, 6)),
    ),
    dict(
        text="A tube with a cross hole. Tube along the X axis from X = 0 to X = 40, outer diameter 16, inner diameter "
             "10, axis at Y = 0, Z = 8. A 4 mm hole along Y through both walls at X = 20 (axis at Z = 8).",
        code='''import cadquery as cq
# A YZ workplane extrudes along +X; its origin is moved to the tube axis (Y = 0, Z = 8).
tube = (cq.Workplane("YZ", origin=(0, 0, 8)).circle(8).circle(5).extrude(40))
cross = (cq.Workplane("XZ", origin=(20, 10, 8)).circle(2).extrude(20))  # XZ normal is -Y: from Y = 10 to Y = -10
result = tube.cut(cross)''',
        bbox=((0, -8, 0), (40, 8, 16)),
    ),
]


def verify():
    import cadquery as cq
    for i, e in enumerate(EXAMPLES, 1):
        ns = {}
        exec(e["code"], ns)
        bb = ns["result"].val().BoundingBox()
        got = ((bb.xmin, bb.ymin, bb.zmin), (bb.xmax, bb.ymax, bb.zmax))
        ok = all(abs(a - b) < 1e-6 for p, q in zip(got, e["bbox"]) for a, b in zip(p, q))
        print(f"example {i}: {'OK' if ok else 'MISMATCH'} bbox={tuple(tuple(round(v, 3) for v in p) for p in got)} "
              f"solids={len(ns['result'].val().Solids())} valid={ns['result'].val().isValid()}")


if __name__ == "__main__":
    verify()
