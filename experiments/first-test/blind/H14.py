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

r = box(0,30,0,20,0,3).union(box(27,30,0,20,0,23)).union(box(27,57,0,20,20,23))
r = r.cut(cq.Workplane("XY").center(15,10).slot2D(15,5,0).extrude(3))
r = r.cut(cq.Workplane("XY").center(42,10).slot2D(15,5,0).extrude(3).translate((0,0,20)))
result = r
