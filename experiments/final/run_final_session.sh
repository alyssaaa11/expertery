#!/bin/zsh
# Final-exam session for the trained model: deploy deploy/modal_forge.py
# (app forge-trained), wait for ready, run runner_final.py calls one after
# another, each with --budget = the whole cap (the runner's own guard stops
# new calls at the $0.30 reserve; budget_left.py below is only the
# refuse-to-start check, so time and reserve are not subtracted twice),
# optional pilot + GO/STOP file pause, always stops the app and prints
# whether it stopped. Same behaviour as experiments/freecad/run_fc_session.sh,
# for runner_final.py with app forge-trained.
# Usage: run_final_session.sh <absolute-out-dir> [cap-$] [--pilot <spec>] [--run <spec> ...]
# Each spec is "<jobs>:<subdir>:<arms>:<k>" (e.g. "main:main-FT:FT:3").
# jobs "dev" means the factory dev file (experiments/factory/jobs_dev.jsonl);
# anything else means --jobs <jobs> on the exam. Default pilot is the dev
# check (PLAN step 5 gate) and the default run is the final exam (step 6).
#
# Each runner call starts in the background (cmd & RPID=$!; wait $RPID) so
# the EXIT/INT/TERM/HUP trap can always run. The trap kills the runner and
# its children (kill -TERM $RPID; pkill -TERM -P $RPID; macOS has no setsid),
# then always runs `modal app stop forge-trained -y` and prints whether it
# stopped.
#
# Offline-test seams (env, all optional; production defaults unchanged):
#   RUN_SESSION_SKIP_DEPLOY=1  skip secret/deploy/ready, pretend URL=skip
#   MODAL_BIN               modal binary (default "modal"; stub it in tests)
#   CURL_BIN                curl binary (default "curl"; stub it in tests)
set -u
FORGE=~/projects/forge
OUT=$1; shift
CAP=3.0
case "${1:-}" in
  [0-9]* ) CAP=$1; shift;;
esac
PILOT="dev:dev-FT:FT:3"
RUNS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --pilot) PILOT=$2; shift 2;;
    --run) RUNS+=("$2"); shift 2;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done
[ ${#RUNS[@]} -eq 0 ] && RUNS=("main:main-FT:FT:3")
mkdir -p "$OUT"
cd ~/projects/forge
COMMON=~/projects/forge/experiments/common
MODAL_BIN=${MODAL_BIN:-modal}
CURL_BIN=${CURL_BIN:-curl}
K=$(python3 -I -c "import secrets;print(secrets.token_urlsafe(32))")
echo "key generated (never printed)"
RPID=""
CLEANED=""
cleanup() {  # runs once: kill the runner + children, then stop the app
  [ -n "$CLEANED" ] && return 0
  CLEANED=1
  if [ -n "$RPID" ]; then
    kill -TERM "$RPID" 2>/dev/null || true
    pkill -TERM -P "$RPID" 2>/dev/null || true
  fi
  if "$MODAL_BIN" app stop forge-trained -y >/dev/null 2>&1; then
    echo "app stopped $(date +%T)"
  else
    echo "APP STOP FAILED"
  fi
}
trap 'cleanup' EXIT
trap 'cleanup; exit 143' INT TERM HUP
if [ "${RUN_SESSION_SKIP_DEPLOY:-}" = "1" ]; then
  date +"deploy start %T (skipped)"
  GPU_START=$(date +%s)
  URL="skip"
else
  "$MODAL_BIN" secret create forge-glimmer VLLM_API_KEY="$K" --force >/dev/null 2>&1 && echo "secret updated"
  date +"deploy start %T"
  GPU_START=$(date +%s)
  DEP=$("$MODAL_BIN" deploy deploy/modal_forge.py 2>&1); echo "$DEP" | tail -3
  URL=$(echo "$DEP" | grep -oE 'https://[a-zA-Z0-9.-]+\.modal\.run' | head -1)
  [ -z "$URL" ] && { echo "no URL, abort"; exit 1; }
  for i in {1..90}; do
    code=$("$CURL_BIN" -s -o /dev/null -w "%{http_code}" -m 60 -H "Authorization: Bearer $K" "$URL/v1/models")
    [ "$code" = "200" ] && { date +"ready %T (try $i)"; break; }
    sleep 20
  done
  [ "$code" != "200" ] && { echo "Forge not ready after 30 min, abort"; exit 1; }
  # Verifier D1: refuse the pilot unless the server serves the model this
  # session deployed (FORGE_MODEL_NAME, default final). The trap stops
  # the app on this exit 1.
  MODELS_JSON=$("$CURL_BIN" -s -m 60 -H "Authorization: Bearer $K" "$URL/v1/models")
  SERVED_ROOT=$(printf '%s' "$MODELS_JSON" | python3 -I -c "import sys,json; d=json.load(sys.stdin); items=d.get('data',[]); print(items[0].get('root','') if items else '')" 2>/dev/null || true)
  echo "served model root: $SERVED_ROOT"
  EXPECTED_ROOT="/vol/${FORGE_MODEL_NAME:-final}/merged"
  if [ "$SERVED_ROOT" != "$EXPECTED_ROOT" ]; then
    echo "MODEL MISMATCH: served $SERVED_ROOT, expected $EXPECTED_ROOT"
    exit 1
  fi
fi
PY=~/projects/forge/.venv/bin/python
DEV_JOBS=~/projects/forge/experiments/factory/jobs_dev.jsonl
run() {
  # Refuse-to-start check only (verifier D1): the runner gets the whole
  # cap and enforces the reserve itself, so time and reserve are no
  # longer subtracted twice.
  "$PY" -I "$COMMON/budget_left.py" "$CAP" "$GPU_START" >/dev/null 2>&1 || { echo "budget left for this runner call: CAP REACHED"; echo "CAP REACHED, not starting runner"; return 1; }
  FORGE_URL="$URL" FORGE_KEY="$K" $PY -I ~/projects/forge/experiments/final/runner_final.py --workers 8 --budget "$CAP" --gpu-start "$GPU_START" "$@" & RPID=$!
  wait $RPID
  rc=$?
  RPID=""
  echo "runner exit $rc $(date +%T)"
  return $rc
}
runspec() {  # "<jobs>:<subdir>:<arms>:<k>" -> runner args
  local spec=$1
  local jobs=${spec%%:*}; local rest=${spec#*:}
  local sub=${rest%%:*}; rest=${rest#*:}
  local arms=${rest%%:*}; local k=${rest##*:}
  if [ "$jobs" = "dev" ]; then
    run --jobs-file "$DEV_JOBS" --out "$OUT/$sub" --arms "$arms" --k "$k"
  else
    run --jobs "$jobs" --out "$OUT/$sub" --arms "$arms" --k "$k"
  fi
}
if [ -n "$PILOT" ]; then
  date +"pilot start %T"
  runspec "$PILOT"
  echo "PILOT DONE: waiting for $OUT/GO or $OUT/STOP (20 min max)"
  for i in {1..120}; do
    [ -e "$OUT/GO" ] && break
    [ -e "$OUT/STOP" ] && { echo "STOP requested"; exit 0; }
    sleep 10
  done
  [ ! -e "$OUT/GO" ] && { echo "no GO within 20 min, stopping"; exit 0; }
  date +"main start %T"
fi
for spec in "${RUNS[@]}"; do
  runspec "$spec" || exit $?
done
date +"done %T"
