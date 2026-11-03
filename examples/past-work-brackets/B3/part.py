import cadquery as cq
from cadquery import Solid, Vector

def _box(x0, x1, y0, y1, z0, z1):
    return Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))

def _zcyl(r, x, y, z0, z1):
    return Solid.makeCylinder(r, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))

def _xcyl(r, y, z, x0, x1):
    return Solid.makeCylinder(r, x1 - x0, Vector(x0, y, z), Vector(1, 0, 0))

def _ycyl(r, x, z, y0, y1):
    return Solid.makeCylinder(r, y1 - y0, Vector(x, y0, z), Vector(0, 1, 0))

def _prism_xz(points, y0, y1):
    w = cq.Workplane("XY").polyline(points).close().extrude(y1 - y0).val()
    m = cq.Matrix([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]])
    return w.transformGeometry(m)

def _prism_xy(points, z0, z1):
    return cq.Workplane("XY").polyline(points).close().extrude(z1 - z0).translate((0, 0, z0)).val()

def _zcone(r0, r1, x, y, z0, z1):
    return Solid.makeCone(r0, r1, z1 - z0, Vector(x, y, z0), Vector(0, 0, 1))

def _rounded_plate(lx, ly, t, r):
    return cq.Workplane("XY").box(lx, ly, t, centered=(True, True, False)).edges("|Z").fillet(r).val()

s = _box(0, 25, 0, 30, 0, 3)
s = s.fuse(_box(22, 25, 0, 30, 0, 30))
s = s.fuse(_box(22, 47, 0, 30, 27, 30))
s = s.cut(_zcyl(3.25, 11, 15, -1, 4))
s = s.cut(_zcyl(3.25, 36, 15, 26, 31))
s = s.clean()
result = s
