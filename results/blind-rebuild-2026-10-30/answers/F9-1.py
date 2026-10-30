import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(57.6,(0,0,0),(0,0,1),44.6)
s = s.cut(cyl(13.8,(0,0,16.6),(1,0,0),29.8)).cut(cyl(29.2,(0,0,29.5),(0,0,1),16.1))
result = s
