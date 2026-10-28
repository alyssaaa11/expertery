import keel
p = keel.part("BRK-5103")
p.stock(80,50,6)
p.wall("east",35,t=6)
p.hole("KF-M5-CB",at=(12,12))
p.pattern(2,2,40,26)
p.pocket(at=(22,10),L=20,W=30,depth=3)
solid = p.finish()
