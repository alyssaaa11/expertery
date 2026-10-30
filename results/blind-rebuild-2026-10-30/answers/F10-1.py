import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

r0, r1, h = 17.1, 27.2, 34.3
k = (r1-r0)/h
outer = Solid.makeCone(r0, r1, h, Vector(0,0,0), Vector(0,0,1))
# inner recess: same wall slope as the outer cone (bottom diameter not given)
ri_top = 47.8/2; ri_bot = ri_top - k*(35.3-7)
inner = Solid.makeCone(ri_bot, ri_top, 35.3-7, Vector(0,0,7), Vector(0,0,1))
rim = cyl(54.4,(0,0,h),(0,0,1),4.4).cut(cyl(54.4-2*4.9,(0,0,h-1),(0,0,1),6.4))
s = outer.fuse(cyl(17.4,(0,0,-14.9),(0,0,1),18.9)).cut(inner).fuse(rim)
s = s.cut(cyl(10.6,(0,0,-15.9),(0,0,1),23.9))
result = s.clean()
