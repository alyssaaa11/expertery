import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,131.2,0,51,0,4.1)
tris = [[(15.4,8),(26.3,8),(20.9,43)],[(45.2,43),(56.2,43),(50.7,8)],[(75,8),(86,8),(80.5,43)],[(104.8,43),(115.8,43),(110.3,8)]]
for t in tris: s = s.cut(cq.Workplane("XY").workplane(offset=-1).polyline(t).close().extrude(6.1).val())
result = s
