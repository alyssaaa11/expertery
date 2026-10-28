"""CLP-0012 harness clip with a through slot."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("CLP-0012", material="AL6061")
p.stock(50, 30, 4)
p.slot(at=(10, 15), to=(40, 15), width=5)
p.wall("west", 10)
p.hole("KF-M3", at=(45, 8))
p.pattern(1, 2, 0, 14)
solid = p.finish()
