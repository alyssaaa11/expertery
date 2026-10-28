import cadquery as cq
part = cq.Workplane("XY").box(20, 20, 20).faces(">Z").workplane().hole(5)
bb = part.val().BoundingBox()
print("cadquery", cq.__version__)
print("size mm:", round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2))
print("volume mm3:", round(part.val().Volume(), 1), "(expected", round(8000 - 3.14159265 * 2.5**2 * 20, 1), ")")
cq.exporters.export(part, "cube.step"); cq.exporters.export(part, "cube.stl")
print("exported STEP + STL")
