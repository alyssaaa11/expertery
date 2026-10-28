import keel
p = keel.part("PLT-2705")
p.stock(50,50,4)
p.hole("KF-M4-CB",at=(7,7))
p.pattern(2,2,36,36)
solid = p.finish()
