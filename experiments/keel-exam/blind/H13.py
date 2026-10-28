import keel
p = keel.part("FRM-5306")
p.stock(100,50,8)
p.wall("north",16)
p.wall("south",16)
p.slot(at=(15,25),to=(85,25),width=8,depth=4)
p.hole("KF-M4-CB",at=(10,10))
p.pattern(2,2,80,30)
solid = p.finish()
