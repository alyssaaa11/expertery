import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

outer = Solid.makeCone(34.2/2, 54.4/2, 34.3, Vector(0,0,0), Vector(0,0,1))
inner = Solid.makeCone(24.4/2, 47.8/2, 35.3-7, Vector(0,0,7), Vector(0,0,1))
rim = cyl(64.2,(0,0,34.3),(0,0,1),4.4).cut(cyl(47.8,(0,0,33.3),(0,0,1),6.4))
s = outer.fuse(cyl(17.4,(0,0,-14.9),(0,0,1),18.9)).cut(inner).fuse(rim)
s = s.cut(cyl(10.6,(0,0,-15.9),(0,0,1),23.9))
result = s.clean()
