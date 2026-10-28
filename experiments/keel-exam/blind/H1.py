import keel
p = keel.part("BRK-4105")
p.stock(120,60,6)
p.wall("north",40)
p.wall("south",40)
p.hole("KF-M5",at=(20,18))
p.pattern(3,2,40,24)
p.fillet(r=4)
solid = p.finish()
