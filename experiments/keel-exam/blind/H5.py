import keel
p = keel.part("CLP-4504")
p.stock(80,30,6)
p.slot(at=(15,15),to=(65,15),width=10,depth=3)
p.hole("KF-M3",at=(15,15))
p.pattern(2,1,50,0)
p.wall("west",12)
p.wall("east",12)
solid = p.finish()
