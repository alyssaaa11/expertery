import keel
p = keel.part("STD-4409", material="TI6AL4V", cls="FLIGHT")
p.stock(40, 40, 6)
p.boss(at=(20, 20), dia=20, h=30)
p.hole("KF-M6-CS", at=(20, 20))
p.mount("STAR-TRACKER-3", origin=(20, 20), finish="CB")
solid = p.finish()
