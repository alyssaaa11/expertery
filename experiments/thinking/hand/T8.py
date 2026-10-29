import FreeCAD as App, Part
V = App.Vector
s = Part.makeBox(85, 55, 32.5, V(-42.5, -27.5, 0)).cut(Part.makeBox(80, 50, 30, V(-40, -25, 2.5)))
for x in (-36.25, 36.25):
    for y in (-21.25, 21.25):
        s = s.fuse(Part.makeCylinder(3.75, 30, V(x, y, 2.5))).cut(Part.makeCylinder(1.2, 30, V(x, y, 2.5)))
result = s.removeSplitter()
