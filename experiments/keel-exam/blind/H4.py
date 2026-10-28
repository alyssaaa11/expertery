import keel
p = keel.part("FRM-4407")
p.stock(140,90,10)
p.pocket(at=(10,10),L=55,W=70,depth=6)
p.pattern(2,1,65,0)
p.hole("KF-M5",at=(6,6))
p.pattern(2,2,128,78)
solid = p.finish()
