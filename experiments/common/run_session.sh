#!/bin/zsh
# Glimmer evaluation session with a whole-session cap (generalised run_session_v2.sh).
# One deploy of deploy/modal_glimmer.py, wait for ready, run the given runner
# commands one after another, each with --budget = money LEFT =
# cap - GPU time since deploy x $2.50/h minus the $0.30 reserve (refuse to
# start when <= $0.05), optional pilot + GO/STOP file pause, always stops the
# app and prints whether it stopped.
# Arms/jobs/k are parameters (not hard-coded): each RUN spec is
#   "<jobs>:<out-subdir>:<arms>:<k>"   (e.g. "main:main-BR:BR:1").
# Usage: run_session.sh <absolute-out-dir> [cap-$] [--pilot <jobs>:<subdir>:<arms>:<k>] [--run <jobs>:<subdir>:<arms>:<k> ...]
# Default runs mirror the step-2 baseline: pilot dry/BR,BX/k=1, then main BR/k=1 and main B2,BX/k=3.
#
# Each runner call starts in the background (cmd & RPID=$!; wait $RPID) so
# the EXIT/INT/TERM/HUP trap can always run. The trap kills the runner and
# its children (kill -TERM $RPID; pkill -TERM -P $RPID; macOS has no setsid),
# then always runs `modal app stop forge-glimmer -y` and prints whether it
# stopped.
#
# Offline-test seams (env, all optional; production defaults unchanged):
#   RUN_SESSION_RUNNER_CMD  full runner command prefix instead of runner.py
#                           (e.g. "sleep 300" for the TERM test)
#   RUN_SESSION_SKIP_DEPLOY=1  skip secret/deploy/ready, pretend URL=skip
#   MODAL_BIN               modal binary (default "modal"; stub it in tests)
set -u
OUT=$1; shift
CAP=3.0
case "${1:-}" in
  [0-9]* ) CAP=$1; shift;;
esac
PILOT="dry:pilot:BR,BX:1"
RUNS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --pilot) PILOT=$2; shift 2;;
    --run) RUNS+=("$2"); shift 2;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done
[ ${#RUNS[@]} -eq 0 ] && RUNS=("main:main-BR:BR:1" "main:main-B2BX:B2,BX:3")
mkdir -p "$OUT"
cd ~/projects/forge
COMMON=~/projects/forge/experiments/common
MODAL_BIN=${MODAL_BIN:-modal}
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
  if "$MODAL_BIN" app stop forge-glimmer -y >/dev/null 2>&1; then
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
  DEP=$("$MODAL_BIN" deploy deploy/modal_glimmer.py 2>&1); echo "$DEP" | tail -3
  URL=$(echo "$DEP" | grep -oE 'https://[a-zA-Z0-9.-]+\.modal\.run' | head -1)
  [ -z "$URL" ] && { echo "no URL, abort"; exit 1; }
  for i in {1..90}; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -m 60 -H "Authorization: Bearer $K" "$URL/v1/models")
    [ "$code" = "200" ] && { date +"ready %T (try $i)"; break; }
    sleep 20
  done
  [ "$code" != "200" ] && { echo "Glimmer not ready after 30 min, abort"; exit 1; }
fi
SBX=~/projects/forge/experiments/b2-hint/sandbox_cq.sb
PY=~/projects/forge/.venv/bin/python
cd experiments/first-test
run() {
  B=$($PY -I "$COMMON/budget_left.py" "$CAP" "$GPU_START" 2>&1) || { echo "budget left for this runner call: CAP REACHED"; echo "CAP REACHED, not starting runner"; return 1; }
  echo "budget left for this runner call: \$$B"
  if [ -n "${RUN_SESSION_RUNNER_CMD:-}" ]; then
    ${=RUN_SESSION_RUNNER_CMD} "$@" & RPID=$!
  else
    GLIMMER_URL="$URL" GLIMMER_KEY="$K" $PY -I runner.py --budget "$B" --gpu-start "$GPU_START" --sandbox "$SBX" --workers 8 "$@" & RPID=$!
  fi
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
  run --jobs "$jobs" --out "$OUT/$sub" --arms "$arms" --k "$k"
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
