import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(48.2,(0,0,0),(0,0,1),38.8)
s = s.cut(cyl(13.2,(0,0,14.7),(1,0,0),25.1)).cut(cyl(29.2,(0,0,27.3),(0,0,1),12.5))
result = s
