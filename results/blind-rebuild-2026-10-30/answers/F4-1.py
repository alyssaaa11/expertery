import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(67.2,(0,0,0),(0,0,1),11.5).cut(cyl(12.2,(9.8,0,-1),(0,0,1),13.5))
(x0,y0),(x1,y1) = (3.4,1.4),(32,13.1)
L = math.hypot(x1-x0,y1-y0); ang = math.degrees(math.atan2(y1-y0,x1-x0))
slot = cq.Workplane("XY").workplane(offset=-1).center((x0+x1)/2,(y0+y1)/2).slot2D(L+5.9,5.9,ang).extrude(13.5).val()
result = s.cut(slot)
