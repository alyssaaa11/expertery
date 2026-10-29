"""Whole-session money-left helper for Glimmer evaluation sessions.

Budget LEFT = cap - GPU time since deploy x rate/h. Refuses (returns None)
when $0.05 or less is left. Used by experiments/common/run_session.sh and
unit-tested offline with fixed numbers.
"""

import sys
import time

MIN_LEFT = 0.05  # refuse to start a runner call at or below this, in $
RESERVE = 0.30  # default holdback: the runner's guard stops only NEW calls


def budget_left(cap, gpu_start, now=None, rate_per_hour=2.50, reserve=RESERVE):
    """Money left minus the reserve, in $ (rounded to cents).

    Returns None when too little is left to start a runner call. The
    reserve is held back because the runner's guard stops only NEW calls
    and in-flight answers still cost money.
    """
    now = time.time() if now is None else now
    left = float(cap) - max(0.0, now - float(gpu_start)) * float(rate_per_hour) / 3600.0
    left = round(left - float(reserve or 0.0), 2)
    if left <= MIN_LEFT:
        return None
    return left


def main(argv):
    """CLI: budget_left.py <cap> <gpu-start-unix> [rate] [--reserve X].

    Prints $ left after the reserve. Exits 2 (printing CAP REACHED) when
    nothing may start.
    """
    args = list(argv[1:])
    reserve = RESERVE
    if "--reserve" in args:
        i = args.index("--reserve")
        try:
            reserve = float(args[i + 1])
        except (IndexError, ValueError):
            print("usage: budget_left.py <cap-dollars> <gpu-start-unix> "
                  "[rate-per-hour] [--reserve dollars]")
            return 2
        del args[i:i + 2]
    if len(args) not in (2, 3):
        print("usage: budget_left.py <cap-dollars> <gpu-start-unix> "
              "[rate-per-hour] [--reserve dollars]")
        return 2
    rate = float(args[2]) if len(args) == 3 else 2.50
    left = budget_left(args[0], args[1], rate_per_hour=rate, reserve=reserve)
    if left is None:
        print("CAP REACHED, not starting runner")
        return 2
    print("%.2f" % left)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
