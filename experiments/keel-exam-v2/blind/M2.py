import keel
p = keel.part("PLT-2412", material="SS316")
p.stock(90, 70, 5)
p.mount("PETREL-MOUNT-A", origin=(25, 20), finish="CB")
p.hole("KF-M6", at=(75, 55))
p.fillet()
solid = p.finish()
