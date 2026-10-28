"""STD-0044 standoff with a central boss."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("STD-0044", material="AL6061")
p.stock(30, 30, 4)
p.boss(at=(15, 15), dia=12, h=10)
p.hole("KF-M4", at=(15, 15))
p.hole("KF-M3", at=(5, 5))
p.pattern(2, 2, 20, 20)
solid = p.finish()
