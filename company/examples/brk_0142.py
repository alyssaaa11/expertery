"""BRK-0142 flight bracket in titanium with a wall hole. Run with the project venv from company/ (or repo root)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("BRK-0142", material="TI6AL4V", cls="FLIGHT")
p.stock(60, 40, 4)
p.wall("north", 25)
p.hole("KF-M4-CB", at=(6, 6))
p.pattern(2, 2, 48, 28)
p.wall_hole("north", "KF-M3", at=(30, 12))
solid = p.finish()
