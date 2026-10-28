import keel
p = keel.part("STD-5410")
p.stock(60,30,5)
p.boss(at=(15,15),dia=14,h=18)
p.pattern(2,1,30,0)
p.hole("KF-M4-CB",at=(15,15))
p.pattern(2,1,30,0)
p.slot(at=(25,15),to=(35,15),width=5)
solid = p.finish()
