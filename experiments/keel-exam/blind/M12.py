import keel
p = keel.part("STD-3307")
p.stock(30,30,3)
p.boss(at=(15,15),dia=16,h=15)
p.hole("KF-M5-CB",at=(15,15))
solid = p.finish()
