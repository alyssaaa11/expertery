import keel
p = keel.part("FRM-3102", material="AL6061")
p.stock(80, 80, 5)
p.slot(at=(20, 40), to=(60, 40), width=6)
p.hole("KF-M4", at=(8, 8))
p.pattern(2, 2, 64, 64)
solid = p.finish()