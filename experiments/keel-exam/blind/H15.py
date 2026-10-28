import keel
p = keel.part("BRK-5502")
p.stock(100,100,6)
p.wall("west",50)
p.wall("south",50)
p.hole("KF-M5",at=(25,25))
p.pattern(3,3,25,25)
p.fillet(r=5)
solid = p.finish()
