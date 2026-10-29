import FreeCAD as App, Part
V = App.Vector
s = Part.makeBox(40, 40, 10, V(-20, -20, 0))
s = s.cut(Part.makeCylinder(3.3, 10)).cut(Part.makeCylinder(5.5, 6.5, V(0, 0, 3.5)))
result = s.removeSplitter()
