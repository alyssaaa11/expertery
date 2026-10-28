import keel
p = keel.part("FRM-2603", material="AL6061")
p.stock(100, 60, 6)
p.hole("KF-M5", at=(8, 8))
p.hole("KF-M5", at=(92, 8))
p.hole("KF-M5", at=(8, 52))
p.hole("KF-M5", at=(92, 52))
p.pocket(at=(20, 15), L=60, W=30, depth=3)
solid = p.finish()
