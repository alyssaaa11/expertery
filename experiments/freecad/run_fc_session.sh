#!/bin/zsh
# FreeCAD gap-test session: the money cap and the app stop are the same as
# for every other paid run. Uses experiments/common/run_session.sh
# unchanged, through its RUN_SESSION_RUNNER_CMD hook, to call runner_fc.py
# (arms G,S by default, k = 1, 8 workers, Baseten's own cap $3.00 and
# Wonder's own cap $3.00; the Modal+Baseten session cap, default $3.50, is
# set by the session cap argument and reaches the runner as --budget with
# --gpu-start through the hook, so the whole-session cap applies).
# Usage: run_fc_session.sh <absolute-out-dir> [cap-$] [--pilot <spec>] [--run <spec> ...]
# Each spec is "<exam>:<jobs>:<subdir>:<arms>:<k>" (e.g. "thinking:main:main-GS:G,S:3").
# The old 4-field form "<jobs>:<subdir>:<arms>:<k>" still means first-test.
# One exam per session: every spec must name the same exam (or omit it).
set -u
FORGE=~/projects/forge
# Keys loaded without printing them (never echo a key); refuse when empty.
# envsave takes the OPAQUE id, not the name.
export BASETEN_KEY=$(envsave get es_LMDrY_C1YRDJYOAGLb2hB1y5WpczSEujtnquV4V5DTzZSMhp)
[ -z "$BASETEN_KEY" ] && { echo "Baseten key is empty (envsave); refusing to run"; exit 1; }
HERDSHOT_ID=$(grep -o -m1 'es_[A-Za-z0-9_]*' "$HOME/.local/bin/muse-wonder" 2>/dev/null)
export META_HERDSHOT_API_KEY=$(envsave get "$HERDSHOT_ID")
[ -z "$META_HERDSHOT_API_KEY" ] && { echo "HerdShot key is empty (envsave); refusing to run"; exit 1; }
OUT=$1; shift
CAP=3.50
case "${1:-}" in
  [0-9]* ) CAP=$1; shift;;
esac
# Split an optional leading "<exam>:" off every --pilot/--run spec: the
# 5-field form names the exam, the old 4-field form means first-test.
# The exam reaches the runner as --exam (one exam per session).
FC_EXAM=""
FC_ARGS=()
EXPECT_SPEC=0
for a in "$@"; do
  if [ $EXPECT_SPEC -eq 1 ]; then
    EXPECT_SPEC=0
    if [ -z "$a" ]; then
      FC_ARGS+=("$a")  # empty pilot: no run, nothing to translate
    else
      parts=(${(s.:.)a})
      if [ ${#parts} -eq 5 ]; then
        exam=$parts[1]
        rest=${(j.:.)parts[2,5]}
      elif [ ${#parts} -eq 4 ]; then
        exam="first-test"
        rest=$a
      else
        echo "bad run spec (want <jobs>:<subdir>:<arms>:<k> or <exam>:<jobs>:<subdir>:<arms>:<k>): $a"; exit 1
      fi
      case "$exam" in
        first-test|thinking) ;;
        *) echo "unknown exam in spec: $exam (want first-test or thinking)"; exit 1;;
      esac
      if [ -z "$FC_EXAM" ]; then
        FC_EXAM=$exam
      elif [ "$FC_EXAM" != "$exam" ]; then
        echo "one exam per session (saw $FC_EXAM and $exam)"; exit 1
      fi
      FC_ARGS+=("$rest")
    fi
  elif [ "$a" = "--pilot" ] || [ "$a" = "--run" ]; then
    FC_ARGS+=("$a")
    EXPECT_SPEC=1
  else
    FC_ARGS+=("$a")
  fi
done
[ -z "$FC_EXAM" ] && FC_EXAM="first-test"
export RUN_SESSION_RUNNER_CMD="$FORGE/.venv/bin/python -I $FORGE/experiments/freecad/runner_fc.py --workers 8 --budget-c 3.00 --budget-w 3.00 --exam $FC_EXAM"
exec "$FORGE/experiments/common/run_session.sh" "$OUT" "$CAP" "${FC_ARGS[@]}"
