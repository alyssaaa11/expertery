import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,82.9,0,42.9,0,29)
yc=21.4
s = s.cut(box(-1,83.9,yc-9.3/2,yc+9.3/2,16.9,30)).cut(box(-1,83.9,yc-20.3/2,yc+20.3/2,11.7,16.9))
for x in (13.8,72.5): s = s.cut(cyl(8,(x,yc,-1),(0,0,1),31))
result = s
