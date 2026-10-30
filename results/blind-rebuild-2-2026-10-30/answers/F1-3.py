import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(46.4,(0,0,0),(0,0,1),3.5).fuse(cyl(19,(0,0,3.5),(0,0,1),18), cyl(46.4,(0,0,21.5),(0,0,1),3.5))
s = s.cut(cyl(9.6,(0,0,-1),(0,0,1),27)).cut(box(-24.2,24.2,-2.1,2.1,0,3.5))
result = s
