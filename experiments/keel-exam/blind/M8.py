import keel
p = keel.part("STD-2920")
p.stock(40,20,4)
p.boss(at=(10,10),dia=8,h=6)
p.pattern(2,1,20,0)
p.hole("KF-M2",at=(10,10))
p.pattern(2,1,20,0)
solid = p.finish()
