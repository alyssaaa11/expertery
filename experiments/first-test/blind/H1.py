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

r = box(-40,40,-25,25,0,30).cut(box(-38,38,-23,23,2,30))
pts = ((33,18),(-33,18),(-33,-18),(33,-18))
for x,y in pts:
    r = r.union(zcyl(6,x,y,2,27))
for x,y in pts:
    r = r.cut(zcyl(2.5,x,y,2,27))
result = r
