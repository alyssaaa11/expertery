import keel
p = keel.part("CLP-3405", material="AL6061")
p.stock(60, 30, 5)
p.hole("KF-M3", at=(8, 8))
p.mirror("ew")
p.mirror("ns")
p.slot(at=(20, 15), to=(40, 15), width=6, depth=2)
solid = p.finish()
