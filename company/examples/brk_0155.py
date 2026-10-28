"""BRK-0155 corner bracket with two walls."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("BRK-0155", material="AL6061")
p.stock(50, 50, 5)
p.wall("north", 20)
p.wall("east", 20)
p.hole("KF-M5", at=(8, 8))
p.pattern(2, 1, 34, 0)
p.fillet()
solid = p.finish()
