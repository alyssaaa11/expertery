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

r = zcyl(40,0,0,0,8)
notch = box(0,25,-1.5,1.5,0,8).cut(zcyl(32,0,0,0,8))
for i in range(12):
    r = r.cut(notch.rotate((0,0,0),(0,0,1),30*i))
r = r.cut(zcyl(8,0,0,0,8)).cut(box(0,5.5,-1.5,1.5,0,8))
result = r
