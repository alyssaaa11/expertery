"""PLT-1042 plate with a countersunk PETREL-MOUNT-A. Run with the project venv from company/ (or repo root)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import keel

p = keel.part("PLT-1042", material="AL6061")
p.stock(80, 60, 4)
p.mount("PETREL-MOUNT-A", origin=(10, 10), finish="CS")
p.fillet()
solid = p.finish()
