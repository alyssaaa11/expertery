#!/bin/zsh
# FreeCAD gap-test session: the money cap and the app stop are the same as
# for every other paid run. Uses experiments/common/run_session.sh
# unchanged, through its RUN_SESSION_RUNNER_CMD hook, to call runner_fc.py
# (arms G,S by default, k = 1, 8 workers, Baseten's own cap $3.00 and
# Wonder's own cap $3.00; the Modal+Baseten session cap, default $3.50, is
# set by the session cap argument and reaches the runner as --budget with
# --gpu-start through the hook, so the whole-session cap applies).
# Usage: run_fc_session.sh <absolute-out-dir> [cap-$] [--pilot <spec>] [--run <spec> ...]
# Each spec is "<jobs>:<subdir>:<arms>:<k>" (e.g. "main:main-GS:G,S:1").
set -u
FORGE=~/projects/forge
# Keys loaded without printing them (never echo a key); refuse when empty.
# envsave takes the OPAQUE id, not the name.
export BASETEN_KEY=$(envsave get es_LMDrY_C1YRDJYOAGLb2hB1y5WpczSEujtnquV4V5DTzZSMhp)
[ -z "$BASETEN_KEY" ] && { echo "Baseten key is empty (envsave); refusing to run"; exit 1; }
HERDSHOT_ID=$(grep -o -m1 'es_[A-Za-z0-9_]*' "$HOME/.local/bin/muse-wonder" 2>/dev/null)
export META_HERDSHOT_API_KEY=$(envsave get "$HERDSHOT_ID")
[ -z "$META_HERDSHOT_API_KEY" ] && { echo "HerdShot key is empty (envsave); refusing to run"; exit 1; }
export RUN_SESSION_RUNNER_CMD="$FORGE/.venv/bin/python -I $FORGE/experiments/freecad/runner_fc.py --workers 8 --budget-c 3.00 --budget-w 3.00"
OUT=$1; shift
CAP=3.50
case "${1:-}" in
  [0-9]* ) CAP=$1; shift;;
esac
exec "$FORGE/experiments/common/run_session.sh" "$OUT" "$CAP" "$@"
