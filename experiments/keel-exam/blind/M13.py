import keel
p = keel.part("CLP-3402")
p.stock(45,25,5)
p.slot(at=(8,8),to=(8,17),width=4)
p.pattern(2,1,29,0)
solid = p.finish()
