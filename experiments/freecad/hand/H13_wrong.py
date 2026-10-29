import FreeCAD as App, Part
V = App.Vector
s = Part.makeBox(30, 4, 60, V(-15, 0, 0))
s = s.fuse(Part.makeBox(10, 30, 5, V(-5, 4, 25))).fuse(Part.makeBox(10, 5, 15, V(-5, 29, 30)))
for z in (15, 45):
    hole = Part.makeCylinder(2, 4, V(0, 0, z), V(0, 1, 0))
    csk = Part.makeCone(4.5, 2, 2.5, V(0, 4, z), V(0, -1, 0))   # 8 mm at Y=4 down to 4 mm at Y=2 (90 degrees)
    s = s.cut(hole).cut(csk)
result = s.removeSplitter()
