import keel
p = keel.part("BRK-2911", material="AL6061")
p.stock(60, 30, 5)
p.wall("north", 30)
p.wall_hole("north", "KF-M5", at=(15, 18))
p.hole("KF-M4", at=(10, 10))
p.hole("KF-M4", at=(50, 10))
solid = p.finish()