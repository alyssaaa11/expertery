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

r = box(-40,40,-25,25,0,2)
vents = [(x,y) for x in (-28,-20,-12,-4,4,12,20,28) for y in (-16,-8,0,8,16)]
r = r.cut(cq.Workplane("XY").pushPoints(vents).rect(4,4).extrude(2))
holes = [(sx*36, sy*21) for sx in (1,-1) for sy in (1,-1)]
r = r.cut(cq.Workplane("XY").pushPoints(holes).circle(1.5).extrude(2))
result = r
