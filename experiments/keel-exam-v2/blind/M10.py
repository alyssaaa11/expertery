import keel
p = keel.part("PLT-3206", material="TI6AL4V", cls="FLIGHT")
p.stock(90, 60, 4)
p.mount("PETREL-MOUNT-B", origin=(15, 10), finish="CB")
solid = p.finish()
