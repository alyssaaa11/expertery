import keel
p = keel.part("FRM-4810")
p.stock(120,120,12)
p.pocket(at=(15,15),L=90,W=90,depth=8)
p.hole("KF-M6-CB",at=(9,9))
p.pattern(2,2,102,102)
p.wall("north",30)
solid = p.finish()
