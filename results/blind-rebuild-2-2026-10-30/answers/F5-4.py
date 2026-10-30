import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(26.4,(0,0,0),(1,0,0),98.4).fuse(cyl(24.2,(48.4,-1,0),(0,1,0),48.6), cyl(38.6,(-6,0,0),(1,0,0),6))
s = s.cut(cyl(19.6,(-7,0,0),(1,0,0),106.4)).cut(cyl(17.2,(48.4,-1,0),(0,1,0),49.6))
result = s
