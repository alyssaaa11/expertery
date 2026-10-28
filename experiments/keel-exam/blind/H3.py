import keel
p = keel.part("STD-4302")
p.stock(50,50,6)
p.boss(at=(25,25),dia=20,h=25)
p.hole("KF-M6-CB",at=(25,25))
p.hole("KF-M4",at=(6,6))
p.pattern(2,2,38,38)
p.fillet()
solid = p.finish()
