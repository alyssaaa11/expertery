import keel
p = keel.part("FRM-2502")
p.stock(80,60,8)
p.pocket(at=(10,10),L=60,W=40,depth=5)
p.hole("KF-M4",at=(5,5))
p.pattern(2,2,70,50)
solid = p.finish()
