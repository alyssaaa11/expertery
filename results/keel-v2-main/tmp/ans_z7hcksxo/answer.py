import keel
p = keel.part("FRM-4308", material="AL6061")
p.stock(140, 100, 10)
p.hole("KF-M6", at=(8, 8))
p.pattern(2, 2, 124, 84)
p.pocket(at=(10, 20), L=20, W=60, depth=6)
p.pocket(at=(110, 20), L=20, W=60, depth=6)
p.mount("PETREL-MOUNT-B", origin=(40, 30), finish="CB")
solid = p.finish()