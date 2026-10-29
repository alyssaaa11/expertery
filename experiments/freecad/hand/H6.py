import FreeCAD as App, Part
V = App.Vector
s = Part.makeBox(50, 40, 25, V(-25, -20, 0))
s = s.cut(Part.makeCylinder(11, 7, V(0, 0, 18))).cut(Part.makeCylinder(5, 25))
for x in (-20, 20):
    s = s.cut(Part.makeCylinder(2.5, 25, V(x, 0, 0)))
result = s.removeSplitter()
