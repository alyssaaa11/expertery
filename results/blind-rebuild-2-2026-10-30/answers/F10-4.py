import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

outer = Solid.makeCone(30.4/2, 67.4/2, 43.8, Vector(0,0,0), Vector(0,0,1))
inner = Solid.makeCone(20.2/2, 60.6/2, 44.8-8.2, Vector(0,0,8.2), Vector(0,0,1))
rim = cyl(75.4,(0,0,43.8),(0,0,1),3).cut(cyl(60.6,(0,0,42.8),(0,0,1),5))
s = outer.fuse(cyl(14,(0,0,-19.9),(0,0,1),23.9)).cut(inner).fuse(rim)
s = s.cut(cyl(6.4,(0,0,-20.9),(0,0,1),30.1))
result = s.clean()
