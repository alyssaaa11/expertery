#!/bin/zsh
# FreeCAD gap-test session: the money cap and the app stop are the same as
# for every other paid run. Uses experiments/common/run_session.sh
# unchanged, through its RUN_SESSION_RUNNER_CMD hook, to call runner_fc.py
# (arms G,S by default, k = 1, 8 workers, Modal+Baseten cap $3.50 and
# Wonder's own cap $3.00: worst case $6.50 per PLAN).
# Usage: run_fc_session.sh <absolute-out-dir> [cap-$] [--pilot <spec>] [--run <spec> ...]
# Each spec is "<jobs>:<subdir>:<arms>:<k>" (e.g. "main:main-GS:G,S:1").
set -u
FORGE=~/projects/forge
export RUN_SESSION_RUNNER_CMD="$FORGE/.venv/bin/python -I $FORGE/experiments/freecad/runner_fc.py --workers 8 --budget 3.50 --budget-c 3.00 --budget-w 3.00"
exec "$FORGE/experiments/common/run_session.sh" "$@"
