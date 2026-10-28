import keel
p = keel.part("STD-3004", material="AL6061")
p.stock(40, 40, 5)
p.mount("STAR-TRACKER-3", origin=(20, 20))
p.fillet()
solid = p.finish()