import math
import cadquery as cq
from cadquery import Solid, Vector
def box(x0,x1,y0,y1,z0,z1): return Solid.makeBox(x1-x0,y1-y0,z1-z0,Vector(x0,y0,z0))
def cyl(d,p,dirv,L): return Solid.makeCylinder(d/2,L,Vector(*p),Vector(*dirv))

s = box(0,76.8,0,55.6,0,27.3)
yc, zt, zb, wt, wb = 27.8, 27.3, 16.4, 15.7, 25.5
prof = cq.Workplane("YZ").polyline([(yc-wt/2,zt),(yc+wt/2,zt),(yc+wb/2,zb),(yc-wb/2,zb)]).close().extrude(78.8).translate((-1,0,0)).val()
s = s.cut(prof)
for x in (19.2,57.6): s = s.cut(cyl(7.5,(x,27.8,-1),(0,0,1),29.3))
result = s
