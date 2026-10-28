"""PLT-0277 cover plate with counterbored holes and a shallow pocket."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("PLT-0277", material="AL6061")
p.stock(70, 50, 4)
p.hole("KF-M4-CB", at=(8, 8))
p.pattern(2, 2, 54, 34)
p.pocket(at=(20, 15), L=30, W=20, depth=2)
p.fillet()
solid = p.finish()
