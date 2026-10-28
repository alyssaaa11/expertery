import keel
p = keel.part("FRM-3509")
p.stock(70,70,6)
p.pocket(at=(10,10),L=50,W=50,depth=3)
p.fillet()
solid = p.finish()
