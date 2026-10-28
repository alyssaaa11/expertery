import keel
p = keel.part("BRK-4206", material="TI6AL4V", cls="FLIGHT")
p.stock(80, 50, 6)
p.wall("north", 35)
p.hole("KF-M5-CS", at=(8, 8))
p.pattern(2, 2, 64, 30)
p.wall_hole("north", "KF-M4", at=(20, 20))
p.wall_hole("north", "KF-M4", at=(50, 20))
solid = p.finish()