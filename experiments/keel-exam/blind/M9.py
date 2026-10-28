import keel
p = keel.part("FRM-3001")
p.stock(100,40,5)
p.slot(at=(20,20),to=(80,20),width=8)
p.hole("KF-M4",at=(8,8))
p.pattern(2,2,84,24)
solid = p.finish()
