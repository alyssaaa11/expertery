"""Whole-session money-left helper for Glimmer evaluation sessions.

Budget LEFT = cap - GPU time since deploy x rate/h. Refuses (returns None)
when $0.05 or less is left. Used by experiments/common/run_session.sh and
unit-tested offline with fixed numbers.
"""

import sys
import time

MIN_LEFT = 0.05  # refuse to start a runner call at or below this, in $


def budget_left(cap, gpu_start, now=None, rate_per_hour=2.50):
    """Money left in $ (rounded to cents), or None when too little is left."""
    now = time.time() if now is None else now
    left = float(cap) - max(0.0, now - float(gpu_start)) * float(rate_per_hour) / 3600.0
    left = round(left, 2)
    if left <= MIN_LEFT:
        return None
    return left


def main(argv):
    """CLI: budget_left.py <cap> <gpu-start-unix> [rate] -> prints $ left.

    Exits 2 (printing CAP REACHED) when nothing may start.
    """
    if len(argv) not in (3, 4):
        print("usage: budget_left.py <cap-dollars> <gpu-start-unix> [rate-per-hour]")
        return 2
    rate = float(argv[3]) if len(argv) == 4 else 2.50
    left = budget_left(argv[1], argv[2], rate_per_hour=rate)
    if left is None:
        print("CAP REACHED, not starting runner")
        return 2
    print("%.2f" % left)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
