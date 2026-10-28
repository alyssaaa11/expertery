import keel
p = keel.part("PLT-3603")
p.stock(80,30,4)
p.hole("KF-M4",at=(15,15))
p.pattern(3,1,25,0)
p.wall("south",10)
solid = p.finish()
