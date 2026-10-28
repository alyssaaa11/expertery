import keel
p = keel.part("BRK-3301", material="SS316")
p.stock(50, 40, 4)
p.wall("east", 20)
p.hole("KF-M4", at=(10, 10))
p.hole("KF-M4", at=(10, 30))
solid = p.finish()
