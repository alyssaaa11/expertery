import keel
p = keel.part("PLT-2304")
p.stock(90,50,3)
p.hole("KF-M3",at=(15,12))
p.pattern(3,2,30,26)
p.fillet()
solid = p.finish()
