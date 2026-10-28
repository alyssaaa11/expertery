import keel
p = keel.part("PLT-4703")
p.stock(100,60,3)
p.hole("KF-M3",at=(10,6))
p.pattern(5,2,20,48)
p.slot(at=(30,30),to=(70,30),width=12)
p.fillet()
solid = p.finish()
