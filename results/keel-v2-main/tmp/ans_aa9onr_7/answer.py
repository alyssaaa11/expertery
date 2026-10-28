import keel
p = keel.part("FRM-4710", material="TI6AL4V", cls="FLIGHT")
p.stock(100, 100, 8)
p.wall("east", 20)
p.wall("west", 20)
p.hole("KF-M4-CB", at=(10, 10))
p.pattern(2, 2, 80, 80)
p.pocket(at=(20, 20), L=60, W=60, depth=5)
solid = p.finish()