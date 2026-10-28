import keel
p = keel.part("CLP-2603")
p.stock(60,20,4)
p.slot(at=(12,10),to=(48,10),width=6,depth=2)
p.wall("south",8)
solid = p.finish()
