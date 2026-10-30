import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,131,0,43.1,0,5.8)
tris = [[(8.1,7.9),(23.5,7.9),(15.8,35.2)],[(28,35.2),(43.4,35.2),(35.7,7.9)],[(47.9,7.9),(63.3,7.9),(55.6,35.2)],
        [(67.7,35.2),(83.1,35.2),(75.4,7.9)],[(87.6,7.9),(103,7.9),(95.3,35.2)],[(107.5,35.2),(122.9,35.2),(115.2,7.9)]]
for t in tris: s = s.cut(cq.Workplane("XY").workplane(offset=-1).polyline(t).close().extrude(7.8).val())
result = s
