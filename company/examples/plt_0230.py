"""PLT-0230 mounting plate with a KF-M3 hole pattern."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("PLT-0230", material="AL6061")
p.stock(80, 60, 3)
p.hole("KF-M3", at=(10, 10))
p.pattern(4, 3, 20, 20)
p.fillet()
solid = p.finish()
