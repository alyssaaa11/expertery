import keel
p = keel.part("BRK-2812")
p.stock(40,30,6)
p.wall("north",18)
p.wall("east",18)
p.hole("KF-M6",at=(15,12))
solid = p.finish()
