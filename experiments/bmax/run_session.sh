#!/bin/zsh
# Step-2 baseline in ONE Glimmer session (one cold start): pilot on dry jobs D1-D3 (BR, BX, k=1), then wait for
# Claude's pilot check (touch <out>/GO within 20 min, or <out>/STOP), then BR (k=1) and B2+BX (k=3) on the 30 exam jobs,
# each arm alone on the GPU. Always stops the app. Based on experiments/first-test/run_live.sh (same key/deploy steps).
# Usage: run_session.sh <out-dir>
set -u
OUT=$1; mkdir -p "$OUT"
cd ~/projects/forge
K=$(python3 -I -c "import secrets;print(secrets.token_urlsafe(32))")
envsave set FORGE_GLIMMER_VLLM_API_KEY "$K" >/dev/null 2>&1 && echo "key saved"
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
run() { GLIMMER_URL="$URL" GLIMMER_KEY="$K" $PY -I runner.py --budget 3.0 --gpu-start "$GPU_START" --sandbox "$SBX" --workers 8 "$@"; echo "runner exit $? $(date +%T)"; }
date +"pilot start %T"
run --jobs dry --out "$OUT/pilot" --arms BR,BX --k 1
echo "PILOT DONE: waiting for $OUT/GO or $OUT/STOP (20 min max)"
for i in {1..120}; do
  [ -e "$OUT/GO" ] && break
  [ -e "$OUT/STOP" ] && { echo "STOP requested"; exit 0; }
  sleep 10
done
[ ! -e "$OUT/GO" ] && { echo "no GO within 20 min, stopping"; exit 0; }
date +"main start %T"
run --jobs main --out "$OUT/main-BR" --arms BR --k 1
run --jobs main --out "$OUT/main-B2BX" --arms B2,BX --k 3
date +"done %T"
