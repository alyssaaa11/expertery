import cadquery as cq
import math

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))

def zcyl(d, x, y, z0, z1):
    return cq.Workplane("XY").circle(d/2).extrude(z1-z0).translate((x, y, z0))

def xcyl(d, y, z, x0, x1):
    return cq.Workplane("YZ").circle(d/2).extrude(x1-x0).translate((x0, y, z))

def ycyl(d, x, z, y0, y1):
    # XZ plane normal is -Y; extrude then move so it spans y0..y1
    return cq.Workplane("XZ").circle(d/2).extrude(y1-y0).translate((x, y1, z))

r = box(-15,15,0,4,0,60).union(box(-5,5,4,34,25,30)).union(box(-5,5,29,34,30,45))
for z in (15,45):
    r = r.cut(ycyl(4,0,z,0,4))
    # 90 deg countersink: radius 4 at Y=4 down to radius 2 at Y=2 (extended 0.5 past the face)
    cone = cq.Solid.makeCone(2, 4.5, 2.5, cq.Vector(0,2,z), cq.Vector(0,1,0))
    r = r.cut(cq.Workplane("XY").add(cone))
result = r
