import FreeCAD as App, Part
V = App.Vector
base = Part.makeBox(40, 20, 3, V(-20, -10, 0))
wall = Part.makeBox(40, 3, 20, V(-20, 7, 0))
holes = Part.makeCylinder(2.5, 3, V(-15, -1.5, 0)).fuse(Part.makeCylinder(2.5, 3, V(15, -1.5, 0)))
result = base.fuse(wall).cut(holes).removeSplitter()
