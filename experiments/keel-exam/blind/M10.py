import keel
p = keel.part("PLT-3110")
p.stock(64,48,2.5)
p.hole("KF-M2",at=(8,8))
p.pattern(4,2,16,32)
p.fillet(r=3)
solid = p.finish()
