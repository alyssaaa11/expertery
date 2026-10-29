#!/bin/zsh
# Glimmer evaluation session with a whole-session cap (generalised run_session_v2.sh).
# One deploy of deploy/modal_glimmer.py, wait for ready, run the given runner
# commands one after another, each with --budget = money LEFT =
# cap - GPU time since deploy x $2.50/h (refuse to start when <= $0.05),
# optional pilot + GO/STOP file pause, always stops the app and prints whether it stopped.
# Arms/jobs/k are parameters (not hard-coded): each RUN spec is
#   "<jobs>:<out-subdir>:<arms>:<k>"   (e.g. "main:main-BR:BR:1").
# Usage: run_session.sh <absolute-out-dir> [cap-$] [--pilot <jobs>:<subdir>:<arms>:<k>] [--run <jobs>:<subdir>:<arms>:<k> ...]
# Default runs mirror the step-2 baseline: pilot dry/BR,BX/k=1, then main BR/k=1 and main B2,BX/k=3.
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
K=$(python3 -I -c "import secrets;print(secrets.token_urlsafe(32))")
echo "key generated (never printed)"
modal secret create forge-glimmer VLLM_API_KEY="$K" --force >/dev/null 2>&1 && echo "secret updated"
trap 'modal app stop forge-glimmer -y >/dev/null 2>&1 && echo "app stopped $(date +%T)" || echo "APP STOP FAILED"' EXIT
date +"deploy start %T"
GPU_START=$(date +%s)
DEP=$(modal deploy deploy/modal_glimmer.py 2>&1); echo "$DEP" | tail -3
URL=$(echo "$DEP" | grep -oE 'https://[a-zA-Z0-9.-]+\.modal\.run' | head -1)
[ -z "$URL" ] && { echo "no URL, abort"; exit 1; }
for i in {1..90}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 60 -H "Authorization: Bearer $K" "$URL/v1/models")
  [ "$code" = "200" ] && { date +"ready %T (try $i)"; break; }
  sleep 20
done
[ "$code" != "200" ] && { echo "Glimmer not ready after 30 min, abort"; exit 1; }
SBX=~/projects/forge/experiments/b2-hint/sandbox_cq.sb
PY=~/projects/forge/.venv/bin/python
cd experiments/first-test
run() {
  B=$($PY -I "$COMMON/budget_left.py" "$CAP" "$GPU_START" 2>&1) || { echo "budget left for this runner call: CAP REACHED"; echo "CAP REACHED, not starting runner"; return 1; }
  echo "budget left for this runner call: \$$B"
  GLIMMER_URL="$URL" GLIMMER_KEY="$K" $PY -I runner.py --budget "$B" --gpu-start "$GPU_START" --sandbox "$SBX" --workers 8 "$@"
  echo "runner exit $? $(date +%T)"
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
