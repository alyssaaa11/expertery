"""FRM-1031 frame dimensioned from the centre, west pair mirrored. Run with the project venv from company/ (or repo root)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

# Request gives holes at (+-45, +-35) from the frame centre; Keel uses the
# corner datum, so x = 100/2 + xr, y = 80/2 + yr. West pair mirrored about x = 50.
p = keel.part("FRM-1031", material="AL6061")
p.stock(100, 80, 6)
p.wall("north", 12)
p.wall("south", 12)
p.hole("KF-M5", at=(5, 5))
p.hole("KF-M5", at=(5, 75))
p.mirror("ew")
p.pocket(at=(10, 10), L=80, W=60, depth=4)
solid = p.finish()
