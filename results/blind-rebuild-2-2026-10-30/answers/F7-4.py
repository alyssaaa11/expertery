import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,80.8,0,43.4,0,31.5)
yc=21.7
s = s.cut(box(-1,81.8,yc-11.7/2,yc+11.7/2,26.1,32.5)).cut(box(-1,81.8,yc-21.1/2,yc+21.1/2,19.4,26.1))
for x in (10.7,68.5): s = s.cut(cyl(6.2,(x,yc,-1),(0,0,1),33.5))
result = s
