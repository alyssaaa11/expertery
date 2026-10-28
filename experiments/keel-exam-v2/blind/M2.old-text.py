import keel
p = keel.part("PLT-2412", material="AL6061")
p.stock(80, 60, 4)
p.mount("PETREL-MOUNT-A", origin=(20, 15), finish="CS")
p.fillet()
solid = p.finish()
