import keel
p = keel.part("FRM-3507", material="TI6AL4V")
p.stock(120, 60, 8)
p.pocket(at=(10, 10), L=100, W=40, depth=5)
p.wall("north", 15)
p.wall("south", 15)
solid = p.finish()
