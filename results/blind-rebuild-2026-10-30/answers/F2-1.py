import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,89.3,0,96.7,0,58.3)
for y in (23.6,48.5,72.7): s = s.cut(cyl(11,(-1,y,17.5),(1,0,0),91.3))
for x in (21.6,45.2,67.6): s = s.cut(cyl(8.4,(x,-1,40.8),(0,1,0),98.7))
s = s.cut(cyl(10.4,(75.3,82.7,48),(0,0,1),11.3))
result = s
