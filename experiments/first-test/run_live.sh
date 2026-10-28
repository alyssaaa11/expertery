#!/bin/zsh
# Live run of the first test: deploy Forge's Glimmer, wait until it is ready, run the runner, always stop the app.
# Usage: run_live.sh dry|main <out-dir>
set -u
JOBS=$1; OUT=$2; mkdir -p "$OUT"
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
date +"waiting for Glimmer %T"
for i in {1..90}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 60 -H "Authorization: Bearer $K" "$URL/v1/models")
  [ "$code" = "200" ] && { date +"ready %T (try $i)"; break; }
  sleep 20
done
[ "$code" != "200" ] && { echo "Glimmer not ready after 30 min, abort"; exit 1; }
BK=$(envsave get es_LMDrY_C1YRDJYOAGLb2hB1y5WpczSEujtnquV4V5DTzZSMhp 2>/dev/null)
cd experiments/first-test
GLIMMER_URL="$URL" GLIMMER_KEY="$K" BASETEN_KEY="$BK" ~/projects/forge/.venv/bin/python -I runner.py --jobs "$JOBS" --out "$OUT" --budget 5.0 --gpu-start "$GPU_START"
echo "runner exit $?"; date +"done %T"
