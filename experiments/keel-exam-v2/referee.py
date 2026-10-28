"""The Keel v2 exam referee = the first-test referee (experiments/first-test/checks.py, unchanged) with overlap
tolerance 1e-6 (0.0001 % of the reference volume).
Why (verifier audit 2026-10-28, ~/agents/verifier/reports/forge-keel-exam-2026-10-28.md): correct answers written in
another order and a STEP round trip match to ~2e-14, while 0.01 % let a missing standard fillet PASS on large parts
(0.006-0.009 %). 1e-6 sits far above the noise floor and far below the smallest real error.
Import THIS module before scoring: it sets checks.TOL_DIFF for the whole process."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "first-test"))
import checks

checks.TOL_DIFF = 1e-6
measure, score, mismatch = checks.measure, checks.score, checks.mismatch
