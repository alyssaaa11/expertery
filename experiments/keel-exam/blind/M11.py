import keel
p = keel.part("BRK-3204")
p.stock(55,35,4)
p.wall("west",22,t=4)
p.hole("KF-M5-CB",at=(30,17.5))
solid = p.finish()
