import keel
p = keel.part("PLT-3608", material="AL6061")
p.stock(100, 40, 3)
p.mount("HARNESS-P2", origin=(10, 20), finish="plain")
p.pattern(3, 1, 30, 0)
p.fillet(edges="vertical", r=2)
solid = p.finish()