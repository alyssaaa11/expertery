import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,75.6,0,55.5,0,30.1)
yc, zt, zb, wt, wb = 27.8, 30.1, 19.9, 15.4, 21.2
prof = cq.Workplane("YZ").polyline([(yc-wt/2,zt),(yc+wt/2,zt),(yc+wb/2,zb),(yc-wb/2,zb)]).close().extrude(77.6).translate((-1,0,0)).val()
s = s.cut(prof)
for x in (18.9,56.7): s = s.cut(cyl(6.7,(x,27.8,-1),(0,0,1),32.1))
result = s
