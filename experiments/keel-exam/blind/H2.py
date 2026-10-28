import keel
p = keel.part("PLT-4210")
p.stock(150,100,5)
p.pocket(at=(60,40),L=30,W=20,depth=3)
p.hole("KF-M4-CB",at=(15,15))
p.pattern(4,3,40,35)
p.fillet()
solid = p.finish()
