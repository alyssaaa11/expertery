"""FRM-0310 panel frame with a central pocket and side walls."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("FRM-0310", material="AL6061")
p.stock(100, 80, 6)
p.pocket(at=(10, 10), L=80, W=60, depth=4)
p.wall("north", 12)
p.wall("south", 12)
p.hole("KF-M5", at=(5, 5))
p.pattern(2, 2, 90, 70)
solid = p.finish()
