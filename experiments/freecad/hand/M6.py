import FreeCAD as App, Part
V = App.Vector
s = Part.makeCylinder(30, 8).fuse(Part.makeCylinder(15, 20, V(0, 0, 8)))
s = s.cut(Part.makeCylinder(10, 28))
for x, y in [(22.5, 0), (0, 22.5), (-22.5, 0), (0, -22.5)]:
    s = s.cut(Part.makeCylinder(3, 8, V(x, y, 0)))
result = s.removeSplitter()
