import keel
p = keel.part("STD-5208", material="AL6061", cls="FLIGHT")
p.stock(60, 30, 5)
p.boss(at=(15, 15), dia=14, h=20)
p.boss(at=(45, 15), dia=14, h=20)
p.hole("KF-M4-CS", at=(15, 15))
p.hole("KF-M4-CS", at=(45, 15))
p.mount("HARNESS-P2", origin=(22.5, 5), finish="CB")
solid = p.finish()