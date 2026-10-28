import keel
p = keel.part("STD-2507", material="TI6AL4V", cls="FLIGHT")
p.stock(30, 30, 4)
p.boss(at=(15, 15), dia=12, h=14)
p.hole("KF-M4-CS", at=(15, 15))
solid = p.finish()