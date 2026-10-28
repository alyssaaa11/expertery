import keel
p = keel.part("BRK-4904", material="SS316", cls="FLIGHT")
p.stock(60, 50, 5)
p.wall("north", 30)
p.mount("PETREL-MOUNT-A", origin=(10, 8), finish="CS")
p.wall_hole("north", "KF-M3", at=(30, 15))
solid = p.finish()