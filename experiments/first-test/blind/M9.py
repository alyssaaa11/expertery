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

s, c = math.sin(math.radians(15)), math.cos(math.radians(15))
pts = [(45,5),(50,5),(50+70*s,5+70*c),(45+70*s,5+70*c)]
back = cq.Workplane("YZ").polyline(pts).close().extrude(80).translate((-40,0,0))
result = box(-40,40,0,60,0,5).union(box(-40,40,0,5,5,10)).union(back)
