import keel
p = keel.part("PLT-2809", material="SS316")
p.stock(70, 50, 3)
p.hole("KF-M3-CS", at=(6, 6))
p.pattern(2, 2, 58, 38)
p.fillet()
solid = p.finish()
