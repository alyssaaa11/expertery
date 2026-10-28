import keel
p = keel.part("STD-3703", material="AL6061", cls="FLIGHT")
p.stock(26, 26, 4)
p.boss(at=(13, 13), dia=14, h=10)
p.hole("KF-M5-CB", at=(13, 13))
solid = p.finish()
