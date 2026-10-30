import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(29.8,(0,0,0),(1,0,0),86.8).fuse(cyl(26.2,(46.2,-1,0),(0,1,0),37.5), cyl(43,(-6,0,0),(1,0,0),6))
s = s.cut(cyl(23,(-7,0,0),(1,0,0),94.8)).cut(cyl(18.8,(46.2,-2,0),(0,1,0),39.5))
result = s
