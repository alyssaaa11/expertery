import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,108,0,81.8,0,5.7)
for b in [(-13.1,3,29.6,52.1),(105,121.1,29.6,52.1),(42.8,65.2,-13.1,3),(42.8,65.2,78.8,94.9)]: s = s.fuse(box(b[0],b[1],b[2],b[3],0,5.7))
win = cq.Workplane("XY").workplane(offset=-1).center(54,40.9).rect(80.2,54).extrude(7.7).edges("|Z").fillet(9.8).val()
s = s.cut(win)
for p in [(-6.5,40.9),(114.5,40.9),(54,-6.5),(54,88.3)]: s = s.cut(cyl(7.2,(p[0],p[1],-1),(0,0,1),7.7))
result = s.clean()
