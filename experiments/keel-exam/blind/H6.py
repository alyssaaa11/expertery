import keel
p = keel.part("BRK-4612")
p.stock(90,70,8)
p.wall("west",45,t=4)
p.boss(at=(35,20),dia=14,h=10)
p.pattern(2,2,30,30)
p.hole("KF-M4",at=(35,20))
p.pattern(2,2,30,30)
solid = p.finish()
