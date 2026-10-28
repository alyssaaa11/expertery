import keel
p = keel.part("BRK-2310", material="TI6AL4V")
p.stock(60, 40, 5)
p.wall("west", 30)
p.hole("KF-M4", at=(25, 10))
p.pattern(2, 1, 0, 20)
solid = p.finish()