"""Strict single-answer check: score one reply against a reference program.

Given a reply text (or a file holding it) and a reference CadQuery program
(file), extracts the code, runs it in the sandbox (runner.run_code with
experiments/b2-hint/sandbox_cq.sb), and scores it with
experiments/first-test/checks.py at TOL_DIFF = 1e-6. Prints PASS or FAIL
with reasons.

Usage: score_one.py [--reply-file PATH | <reply text>] <reference program file>
       score_one.py --reply-file reply.txt --reference ref.py [--sandbox-dir DIR]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORGE = os.path.dirname(os.path.dirname(HERE))
FT = os.path.join(FORGE, "experiments", "first-test")
if FT not in sys.path:
    sys.path.insert(0, FT)
import checks  # noqa: E402
import runner  # noqa: E402

SANDBOX_PROFILE = os.path.join(
    FORGE, "experiments", "b2-hint", "sandbox_cq.sb"
)

STRICT_TOL_DIFF = 1e-6


def read_reply(reply=None, reply_file=None):
    """Reply text, from --reply-file or from the argument (a path or text)."""
    if reply_file:
        with open(reply_file, encoding="utf-8") as f:
            return f.read()
    if reply is not None and os.path.isfile(reply):
        with open(reply, encoding="utf-8") as f:
            return f.read()
    return reply or ""


def run_reference_program(path):
    """Execute the reference program file; returns (shape, error)."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    code = runner.extract_code(src)
    if not code or not code.strip():
        code = src
    return code, src


def score_reply(reply_text, ref_path, sandbox_dir=None, timeout=None):
    """Score one reply. Returns (passed, reasons list, measurements)."""
    old_tol = checks.TOL_DIFF
    checks.TOL_DIFF = STRICT_TOL_DIFF
    try:
        code = runner.extract_code(reply_text)
        if not code or not code.strip():
            return False, ["empty reply"], None
        shape, err = runner.run_code(
            code,
            timeout=timeout or runner.RUN_TIMEOUT,
            sandbox_profile=SANDBOX_PROFILE,
            sandbox_dir=sandbox_dir,
        )
        if shape is None:
            return False, ["did not run: %s" % (err or "code error")], None
        ref_code, _ = run_reference_program(ref_path)
        ref_shape, ref_err = runner.run_code(
            ref_code,
            timeout=timeout or runner.RUN_TIMEOUT,
            sandbox_profile=SANDBOX_PROFILE,
            sandbox_dir=sandbox_dir,
        )
        if ref_shape is None:
            return False, ["reference did not run: %s" % (ref_err or "code error")], None
        expected = {k: checks.measure(ref_shape)[k]
                    for k in ("bbox", "volume", "area", "com")}
        passed, fails, m = checks.score(shape, ref_shape, expected)
        return passed, list(fails), m
    finally:
        checks.TOL_DIFF = old_tol


def main(argv=None):
    parser = argparse.ArgumentParser(description="Strict single-answer check")
    parser.add_argument("reply", nargs="?",
                        help="reply text, or a path to a file holding it")
    parser.add_argument("ref", nargs="?", help="reference CadQuery program file")
    parser.add_argument("--reply-file", default=None,
                        help="file holding the reply (overrides the reply arg)")
    parser.add_argument("--reference", default=None,
                        help="reference program file (overrides the ref arg)")
    parser.add_argument("--sandbox-dir", default=None)
    args = parser.parse_args(argv)
    reply_text = read_reply(args.reply, args.reply_file)
    reference = args.reference or args.ref
    if not reference:
        parser.error("a reference CadQuery program file is required")
    if not os.path.isfile(reference):
        parser.error("reference file not found: %s" % reference)
    passed, reasons, _ = score_reply(
        reply_text, reference, sandbox_dir=args.sandbox_dir)
    if passed:
        print("PASS")
        return 0
    print("FAIL %s" % ("; ".join(reasons) if reasons else "checks failed"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
