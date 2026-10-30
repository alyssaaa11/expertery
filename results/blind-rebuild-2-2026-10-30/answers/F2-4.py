import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,89.6,0,71.7,0,60)
for y in (22.9,47.3): s = s.cut(cyl(10.2,(-1,y,18),(1,0,0),91.6))
for x in (30.5,59.1): s = s.cut(cyl(8.2,(x,-1,42),(0,1,0),73.7))
s = s.cut(cyl(11,(75.6,57.7,49.1),(0,0,1),11.9))
result = s
