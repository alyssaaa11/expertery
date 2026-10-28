import keel
p = keel.part("STD-2411")
p.stock(24,24,5)
p.boss(at=(12,12),dia=10,h=12)
p.hole("KF-M3",at=(12,12))
solid = p.finish()
