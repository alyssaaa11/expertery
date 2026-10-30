import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,88.6,0,83.9,0,5.4)
for b in [(-10.8,3,31.8,52.2),(85.6,99.4,31.8,52.2),(34.1,54.5,-10.8,3),(34.1,54.5,80.9,94.7)]: s = s.fuse(box(b[0],b[1],b[2],b[3],0,5.4))
win = cq.Workplane("XY").workplane(offset=-1).center(44.3,42).rect(59.4,54.7).extrude(7.4).edges("|Z").fillet(6.2).val()
s = s.cut(win)
for p in [(-5.4,42),(94,42),(44.3,-5.4),(44.3,89.3)]: s = s.cut(cyl(6.2,(p[0],p[1],-1),(0,0,1),7.4))
result = s.clean()
