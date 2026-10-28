"""BRK-0101 L-bracket. Run with the project venv from company/ (or repo root)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("BRK-0101", material="AL6061")
p.stock(60, 40, 4)
p.wall("north", 25)
p.hole("KF-M4", at=(6, 6))
p.pattern(2, 2, 48, 28)
p.fillet()
solid = p.finish()
