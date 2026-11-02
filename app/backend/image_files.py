"""Explicit web-image file list (verifier S2).

ONLY these repo-relative files go into the homegrown-web Modal image:
app/web/*, app/backend/*, the two loop helpers (runner_final.py with its
cloud box runner) and the minimum they import (runner.py, its checks.py,
and budget_left.py which runner_final.py imports with a fallback).

NEVER the exam answers or training data: no expected.json, no jobs.py, no
results/ file, no other exam file. Only ``cloud_cq.run_answer_in_box`` is
used; the grader app is not deployed.
"""

WEB_FILES = [
    "app/web/index.html",
    "app/web/styles.css",
    "app/web/app.js",
    "app/web/object.jpeg",
    "app/web/recorded_run.json",
    "app/web/dev_server.py",
]

BACKEND_FILES = [
    "app/backend/__init__.py",
    "app/backend/config.py",
    "app/backend/selfcheck.py",
    "app/backend/loop.py",
    "app/backend/limits.py",
    "app/backend/budget.py",
    "app/backend/stream.py",
    "app/backend/image_files.py",
]

# experiments/final/runner_final.py imports runner (frozen, same way) and
# cloud_cq (lazy Modal inside); runner.py imports checks.py; runner_final.py
# imports budget_left with a RESERVE fallback.
EXPERIMENT_FILES = [
    "experiments/final/runner_final.py",
    "experiments/final/cloud_cq.py",
    "experiments/final/run_cq_box.py",
    "experiments/first-test/runner.py",
    "experiments/first-test/checks.py",
    "experiments/common/budget_left.py",
]

WEB_IMAGE_FILES = WEB_FILES + BACKEND_FILES + EXPERIMENT_FILES

# Files that must never enter the image (exam answers, jobs, results).
FORBIDDEN_BASENAMES = ("expected.json", "jobs.py", "jobs.jsonl")
FORBIDDEN_DIRS = ("results/", "data/")


def check_file_list(files=None):
    """(problems) — every forbidden entry found in the image file list."""
    problems = []
    for path in files if files is not None else WEB_IMAGE_FILES:
        base = path.rsplit("/", 1)[-1]
        if base in FORBIDDEN_BASENAMES:
            problems.append(path)
        if any(seg in ("results", "data", "__pycache__")
               for seg in path.split("/")):
            problems.append(path)
    return problems
