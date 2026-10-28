"""The Keel-exam referee = the first-test referee (experiments/first-test/checks.py, unchanged) with a stricter
overlap tolerance. Why: every Keel answer is built by Keel itself, so a correct answer written in a different order
matches the reference exactly (measured 0.00000000% on H1 and H2, 2026-10-28), while the smallest real mistake on
this exam (a missing 1 mm standard fillet, M2) differs by 0.0193%. 0.2% would let fillet mistakes pass."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "first-test"))
import checks

checks.TOL_DIFF = 0.0001  # 0.01 % of the reference volume
measure, score, mismatch = checks.measure, checks.score, checks.mismatch
