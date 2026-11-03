"""expertery command-line interface.

Subcommands (also importable for tests; every handler takes `run` and
`print_fn` so tests can mock the subprocess boundary):

- init
- exam build | review | lock
- test --exam ... --model trained|base ...
- serve --name ...
- train --data ... --out ... --cap-dollars ...
- status

Every command that can spend money takes --cap-dollars (required,
> 0) and --dry-run (prints the plan and the estimated spend, spends
nothing). No handler prints secret values (keys stay in env, never in
argv or stdout).

This module imports only the stdlib at import time; expertery.cloud
and expertery.exam_agent are imported inside handlers.
"""

import argparse
import json
import os
import re
import subprocess
import sys

from . import config as _config

COMMANDS_EPILOG = """commands:
  init                          check Modal + reader key, deploy box+grader
  exam build|review|lock        turn past work into a locked exam
  test --exam ...               run the exam on trained|base
  serve --name ...              deploy the trained model
  train --data ... --out ...    train on practice records (full-r5)
  status                        config, Modal apps, latest exam dirs
"""


def _cap(value):
    """--cap-dollars: required float > 0 (argparse errors exit 2)."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("--cap-dollars must be > 0")
    if not amount > 0:
        raise argparse.ArgumentTypeError("--cap-dollars must be > 0")
    return amount


def build_parser():
    """The full argparse parser (used by main and the --help test)."""
    parser = argparse.ArgumentParser(
        prog="expertery",
        description="Expertery v0: private factory with an exam agent.",
        epilog=COMMANDS_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="check Modal + key, deploy, write "
                                       "~/.expertery/config.json")
    init.add_argument("--dry-run", action="store_true",
                      help="print the plan, change nothing")

    exam = sub.add_parser("exam", help="build | review | lock an exam")
    exam_sub = exam.add_subparsers(dest="exam_cmd", required=True)

    build = exam_sub.add_parser("build", help="build candidates from "
                                              "past work")
    build.add_argument("past_work_dir")
    build.add_argument("--out", required=True, help="exam dir to create")
    build.add_argument("--cap-dollars", type=_cap, required=True)
    build.add_argument("--readers", type=int, default=2)
    build.add_argument("--workers", type=int, default=4)
    build.add_argument("--dry-run", action="store_true")

    review = exam_sub.add_parser("review", help="decide FLAGGED jobs")
    review.add_argument("exam_dir")
    group = review.add_mutually_exclusive_group()
    group.add_argument("--accept-all", action="store_true")
    group.add_argument("--keep-all", action="store_true")

    lock = exam_sub.add_parser("lock", help="write exam.jsonl + FREEZE.txt")
    lock.add_argument("exam_dir")

    test = sub.add_parser("test", help="run the exam on a model")
    test.add_argument("--exam", required=True)
    test.add_argument("--model", required=True, choices=("trained", "base"))
    test.add_argument("--name", required=True)
    test.add_argument("--out", required=True)
    test.add_argument("--cap-dollars", type=_cap, required=True)
    test.add_argument("--loop", action="store_true")
    test.add_argument("--k", type=int, default=3)
    test.add_argument("--dry-run", action="store_true")

    serve = sub.add_parser("serve", help="deploy the trained model")
    serve.add_argument("--name", required=True)
    serve.add_argument("--dry-run", action="store_true")

    train = sub.add_parser("train", help="train on practice records")
    train.add_argument("--data", required=True)
    train.add_argument("--out", required=True)
    train.add_argument("--cap-dollars", type=_cap, required=True)
    train.add_argument("--dry-run", action="store_true")

    sub.add_parser("status", help="config, Modal apps, latest exam dirs")
    return parser


def spawn_env(overrides, remove=()):
    """Full child env: os.environ plus overrides minus removals."""
    env = dict(os.environ)
    for key in remove:
        env.pop(key, None)
    env.update(overrides)
    return env


def _fail(message, print_fn):
    print_fn("expertery: error: %s" % message, file=sys.stderr)
    return 2


def cmd_init(args, run=subprocess.run, print_fn=print):
    """Check Modal + reader key, deploy box + grader, write config."""
    from . import cloud as _cloud
    if args.dry_run:
        print_fn("dry-run: would run `modal profile current`")
        print_fn("dry-run: reader key %s (or %s): %s"
                 % (_config.READER_KEY_ENV, _config.READER_KEY_FALLBACK_ENV,
                    "present" if _cloud.reader_key() else "missing"))
        print_fn("dry-run: would run `modal deploy %s`"
                 % _cloud.cloud_cq_path())
        print_fn("dry-run: would write %s" % _config.CONFIG_PATH)
        return 0
    profile = run(["modal", "profile", "current"],
                  capture_output=True, text=True)
    if profile.returncode != 0:
        return _fail("Modal token does not work "
                     "(`modal profile current` failed); run `modal setup`",
                     print_fn)
    print_fn("Modal profile: OK")
    key_present = bool(_cloud.reader_key())
    print_fn("reader key %s (fallback %s): %s"
             % (_config.READER_KEY_ENV, _config.READER_KEY_FALLBACK_ENV,
                "present" if key_present else "missing"))
    deploy = run(["modal", "deploy", _cloud.cloud_cq_path()],
                 capture_output=True, text=True)
    if deploy.returncode != 0:
        return _fail("deploy failed: %s" % (deploy.stderr or "")[-2000:],
                     print_fn)
    out_lines = (deploy.stdout or "").strip().splitlines()
    print_fn(out_lines[-1] if out_lines else "deployed")
    url, model, _ = _cloud.reader_config()
    os.makedirs(_config.CONFIG_DIR, exist_ok=True)
    with open(_config.CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"tool": _config.TOOL, "reader_url": url,
                   "reader_model": model}, f, indent=1)
        f.write("\n")
    print_fn("wrote %s" % _config.CONFIG_PATH)
    print_fn("next step: expertery exam build <past-work-dir> "
             "--out <exam-dir> --cap-dollars X")
    return 0


def cmd_exam_build(args, print_fn=print):
    """Build exam candidates from a past-work dir."""
    from . import exam_agent as _agent
    if args.readers < 1:
        return _fail("--readers must be >= 1", print_fn)
    try:
        result = _agent.build_exam(
            args.past_work_dir, args.out, args.cap_dollars,
            readers=args.readers, workers=args.workers,
            dry_run=args.dry_run, print_fn=print_fn)
    except _agent.ExamError as e:
        return _fail(str(e), print_fn)
    if not args.dry_run:
        counts = {}
        for cand in result["candidates"]:
            counts[cand["status"]] = counts.get(cand["status"], 0) + 1
        print_fn("built %d jobs (%s) in %s"
                 % (len(result["candidates"]),
                    ", ".join("%d %s" % (counts[k], k)
                              for k in sorted(counts)),
                    args.out))
        print_fn("spent_estimate: $%.4f" % result["spent_estimate"])
    return 0


def cmd_exam_review(args, print_fn=print, input_fn=None):
    """Review FLAGGED jobs in an exam dir."""
    from . import exam_agent as _agent
    try:
        _agent.review_exam(args.exam_dir, accept_all=args.accept_all,
                           keep_all=args.keep_all, input_fn=input_fn,
                           print_fn=print_fn)
    except _agent.ExamError as e:
        return _fail(str(e), print_fn)
    print_fn("review recorded in %s" % args.exam_dir)
    return 0


def cmd_exam_lock(args, print_fn=print):
    """Lock an exam dir: write exam.jsonl + FREEZE.txt."""
    from . import exam_agent as _agent
    try:
        rows = _agent.lock_exam(args.exam_dir)
    except _agent.ExamError as e:
        return _fail(str(e), print_fn)
    print_fn("locked %d jobs in %s" % (len(rows), args.exam_dir))
    return 0


def test_plan(exam, model, name, out, cap_dollars, loop, k):
    """(argv, env_overrides, env_removals, subdir) for `expertery test`.

    trained -> run_final_session.sh with FORGE_MODEL_NAME=<name>,
    --pilot "" and --run "${EXAM}:<sub>:FT:<k>"; base ->
    run_base_session.sh with --run "${EXAM}:<sub>:A:<k>". --loop sets
    RUNNER_EXTRA="--bx-loop" (base + loop also needs FORGE_RULE_CARD;
    trained + loop must run without it).
    """
    from . import cloud as _cloud
    exam_abs = os.path.abspath(exam)
    out_abs = os.path.abspath(out)
    stem = os.path.splitext(os.path.basename(exam_abs))[0]
    if model == "trained":
        script = _cloud.final_session_script()
        sub = "%s-FT" % stem
        argv = [script, out_abs, str(cap_dollars), "--pilot", "",
                "--run", "%s:%s:FT:%d" % (exam_abs, sub, k)]
        overrides = {"FORGE_MODEL_NAME": name}
        removals = ()
        if loop:
            overrides["RUNNER_EXTRA"] = "--bx-loop"
            removals = ("FORGE_RULE_CARD",)
    else:
        script = _cloud.base_session_script()
        sub = "%s-A" % stem
        argv = [script, out_abs, str(cap_dollars), "--pilot", "",
                "--run", "%s:%s:A:%d" % (exam_abs, sub, k)]
        overrides = {}
        removals = ()
        if loop:
            overrides = {"RUNNER_EXTRA": "--bx-loop",
                         "FORGE_RULE_CARD": _cloud.rule_card_path()}
    return argv, overrides, removals, sub


def print_summary(out, sub, print_fn=print):
    """Print the pass rate from the session's summary.json."""
    path = os.path.join(os.path.abspath(out), sub, "summary.json")
    try:
        with open(path, encoding="utf-8") as f:
            summary = json.load(f)
    except (OSError, ValueError):
        print_fn("no summary.json at %s" % path)
        return
    print_fn("pass rate: %s (%s/%s PASS)" % (
        summary.get("pass_rate"), summary.get("PASS"),
        (summary.get("PASS") or 0) + (summary.get("FAIL") or 0)))


def cmd_test(args, run=subprocess.run, print_fn=print):
    """Run the exam on the trained or the base model."""
    from . import cloud as _cloud
    argv, overrides, removals, sub = test_plan(
        args.exam, args.model, args.name, args.out, args.cap_dollars,
        args.loop, args.k)
    if args.dry_run:
        print_fn("dry-run: would run: %s" % " ".join(argv))
        print_fn("dry-run: env overrides: %s"
                 % " ".join(sorted(overrides)))
        if removals:
            print_fn("dry-run: env removed: %s" % " ".join(removals))
        print_fn("dry-run: GPU spend accrues in your Modal account "
                 "within $%.2f" % args.cap_dollars)
        return 0
    proc = run(argv, env=spawn_env(overrides, removals))
    if proc.returncode != 0:
        return _fail("session script failed (exit %d)"
                     % proc.returncode, print_fn)
    if args.model == "trained":
        redeploy = run(["modal", "deploy", _cloud.modal_forge_path()],
                       env=spawn_env({"FORGE_MODEL_NAME": args.name}),
                       capture_output=True, text=True)
        if redeploy.returncode != 0:
            return _fail("redeploy failed (the session script stops "
                         "the app; a live product may depend on it)",
                         print_fn)
        print_fn("redeployed forge-trained (%s)" % args.name)
    print_summary(args.out, sub, print_fn=print_fn)
    return 0


def cmd_serve(args, run=subprocess.run, print_fn=print):
    """Deploy the trained model; print the URL."""
    from . import cloud as _cloud
    argv = ["modal", "deploy", _cloud.modal_forge_path()]
    if args.dry_run:
        print_fn("dry-run: would run: %s with FORGE_MODEL_NAME=%s"
                 % (" ".join(argv), args.name))
        return 0
    proc = run(argv, env=spawn_env({"FORGE_MODEL_NAME": args.name}),
               capture_output=True, text=True)
    if proc.returncode != 0:
        return _fail("deploy failed: %s" % (proc.stderr or "")[-2000:],
                     print_fn)
    match = re.search(r"https://[A-Za-z0-9.-]+\.modal\.run",
                      proc.stdout or "")
    print_fn(match.group(0) if match else (proc.stdout or "").strip())
    return 0


def cmd_train(args, run=subprocess.run, print_fn=print):
    """Train: the guarded forge_train.py entrypoint (never ::train)."""
    from . import cloud as _cloud
    argv = [sys.executable, _cloud.forge_train_path(), "full-r5",
            "--data", os.path.abspath(args.data),
            "--out", args.out,
            "--cap-dollars", str(args.cap_dollars)]
    if args.dry_run:
        print_fn("dry-run: would run: %s" % " ".join(argv))
        print_fn("dry-run: practice data in v0 comes from the factory "
                 "scripts (experiments/factory, experiments/r5)")
        return 0
    proc = run(argv)
    if proc.returncode != 0:
        return _fail("train failed (exit %d)" % proc.returncode, print_fn)
    return 0


def cmd_status(args, run=subprocess.run, print_fn=print):
    """Config (no secrets), Modal apps, latest exam dirs nearby."""
    url, model = None, None
    try:
        with open(_config.CONFIG_PATH, encoding="utf-8") as f:
            saved = json.load(f)
        url, model = saved.get("reader_url"), saved.get("reader_model")
    except (OSError, ValueError):
        print_fn("no config; run `expertery init`")
    else:
        print_fn("tool: %s" % saved.get("tool"))
        print_fn("reader_url: %s" % url)
        print_fn("reader_model: %s" % model)
    from . import cloud as _cloud
    key_present = bool(_cloud.reader_key())
    print_fn("reader key: %s" % ("present" if key_present else "missing"))
    apps = run(["modal", "app", "list"], capture_output=True, text=True)
    if apps.returncode == 0:
        print_fn((apps.stdout or "").strip())
    else:
        print_fn("`modal app list` failed")
    found = []
    for name in os.listdir("."):
        if os.path.isfile(os.path.join(name, "candidates.jsonl")):
            found.append((os.path.getmtime(name), name))
    for _, name in sorted(found, reverse=True)[:5]:
        print_fn("exam dir: %s" % name)
    if not found:
        print_fn("no exam dirs under %s" % os.path.abspath("."))
    return 0


def main(argv=None, run=subprocess.run, print_fn=print):
    """Entry point: `expertery = expertery.cli:main`."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "init":
        return cmd_init(args, run=run, print_fn=print_fn)
    if args.cmd == "exam":
        if args.exam_cmd == "build":
            return cmd_exam_build(args, print_fn=print_fn)
        if args.exam_cmd == "review":
            return cmd_exam_review(args, print_fn=print_fn)
        return cmd_exam_lock(args, print_fn=print_fn)
    if args.cmd == "test":
        return cmd_test(args, run=run, print_fn=print_fn)
    if args.cmd == "serve":
        return cmd_serve(args, run=run, print_fn=print_fn)
    if args.cmd == "train":
        return cmd_train(args, run=run, print_fn=print_fn)
    return cmd_status(args, run=run, print_fn=print_fn)


if __name__ == "__main__":
    sys.exit(main())
