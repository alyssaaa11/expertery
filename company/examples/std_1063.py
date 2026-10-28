"""STD-1063 stainless tracker plate with STAR-TRACKER-3. Run with the project venv from company/ (or repo root)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("STD-1063", material="SS316")
p.stock(60, 60, 5)
p.mount("STAR-TRACKER-3", origin=(30, 30))
p.fillet()
solid = p.finish()
