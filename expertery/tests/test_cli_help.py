"""`python -m expertery.cli --help` lists all commands."""

import subprocess
import sys

from expertery import cloud


def test_help_lists_all_commands():
    proc = subprocess.run(
        [sys.executable, "-m", "expertery.cli", "--help"],
        capture_output=True, text=True, cwd=cloud.repo_root())
    assert proc.returncode == 0
    for name in ("init", "exam", "build", "review", "lock", "test",
                 "serve", "train", "status"):
        assert name in proc.stdout
