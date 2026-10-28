import keel
p = keel.part("PLT-5208")
p.stock(120,80,4)
p.hole("KF-M2",at=(10,10))
p.pattern(6,4,20,20)
p.wall("west",10)
p.fillet()
solid = p.finish()
