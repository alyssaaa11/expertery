import keel
p = keel.part("BRK-2210")
p.stock(70,45,5)
p.wall("west",30)
p.hole("KF-M5",at=(20,12))
p.pattern(1,2,0,21)
solid = p.finish()
