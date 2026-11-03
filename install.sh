#!/bin/sh
# Expertery v0 installer: checks for uv and modal, installs the
# expertery console script into the current environment, and prints
# the next step. It never asks for or prints secrets.
set -u
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "expertery install: 'uv' not found; install it first" >&2
  exit 1
fi
if ! command -v modal >/dev/null 2>&1; then
  echo "expertery install: 'modal' not found; install it first" >&2
  exit 1
fi
uv tool install --editable "${REPO_DIR}"
echo "next step: expertery init"
