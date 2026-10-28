import keel
p = keel.part("PLT-4503", material="SS316", cls="FLIGHT")
p.stock(120, 80, 5)
p.mount("PETREL-MOUNT-A", origin=(10, 10), finish="CS")
p.mount("PETREL-MOUNT-A", origin=(70, 10), finish="CS")
p.slot(at=(30, 65), to=(90, 65), width=8)
solid = p.finish()