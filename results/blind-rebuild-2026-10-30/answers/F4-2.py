import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = cyl(61.2,(0,0,0),(0,0,1),8.4).cut(cyl(12.6,(16.3,0,-1),(0,0,1),10.4))
(x0,y0),(x1,y1) = (3.6,9.3),(11.5,29.4)
L = math.hypot(x1-x0,y1-y0); ang = math.degrees(math.atan2(y1-y0,x1-x0))
slot = cq.Workplane("XY").workplane(offset=-1).center((x0+x1)/2,(y0+y1)/2).transformed(rotate=(0,0,ang)).rect(L,5.5).extrude(10.4).val()
result = s.cut(slot)
