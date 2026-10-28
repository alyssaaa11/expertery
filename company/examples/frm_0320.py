"""FRM-0320 rail frame with a central slot and end walls."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("FRM-0320", material="AL6061")
p.stock(120, 40, 5)
p.slot(at=(15, 20), to=(105, 20), width=6)
p.wall("east", 15)
p.wall("west", 15)
p.hole("KF-M4", at=(6, 6))
p.pattern(2, 2, 108, 28)
solid = p.finish()
