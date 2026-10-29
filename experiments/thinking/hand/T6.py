import FreeCAD as App, Part
V = App.Vector
# board 70x45 + 0.5 clearance -> inside 71x46; plastic walls 2.5; inside 25 tall
s = Part.makeBox(76, 51, 27.5, V(-38, -25.5, 0)).cut(Part.makeBox(71, 46, 25, V(-35.5, -23, 2.5)))
# board centred: holes 3.5 from board edges -> (+-31.5, +-19); M3 bosses d7.5, pilot d2.4, 6 tall
for x in (-31.5, 31.5):
    for y in (-19, 19):
        s = s.fuse(Part.makeCylinder(3.75, 6, V(x, y, 2.5))).cut(Part.makeCylinder(1.2, 6, V(x, y, 2.5)))
result = s.removeSplitter()
