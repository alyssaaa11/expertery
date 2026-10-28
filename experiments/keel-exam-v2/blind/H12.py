import keel
p = keel.part("PLT-5307", material="TI6AL4V", cls="FLIGHT")
p.stock(140, 90, 5)
p.mount("PETREL-MOUNT-A", origin=(10, 10), finish="CS")
p.mirror("ew")
p.pocket(at=(50, 60), L=40, W=20, depth=3)
p.hole("KF-M6-CB", at=(70, 25))
solid = p.finish()
