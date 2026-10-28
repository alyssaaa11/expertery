import keel
p = keel.part("CLP-2704", material="AL6061")
p.stock(50, 25, 4)
p.wall("east", 10)
p.mount("HARNESS-P2", origin=(10, 8), finish="plain")
p.mount("HARNESS-P2", origin=(10, 17), finish="plain")
solid = p.finish()