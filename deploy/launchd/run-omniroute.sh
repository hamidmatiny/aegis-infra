#!/bin/bash
# Supervised OmniRoute for AEGIS Track B fleet (LaunchAgent KeepAlive).
set -euo pipefail
# /usr/sbin: node-machine-id needs ioreg for OmniRoute's local CLI token auth (2026-10-09)
export PATH="/Users/hamidrezamatiny/.npm-global/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PORT="${PORT:-20129}"
export OMNIROUTE_SERVER_HOST="${OMNIROUTE_SERVER_HOST:-0.0.0.0}"
# Load OmniRoute env (PORT/HOST may already be set above)
if [[ -f "$HOME/.omniroute/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$HOME/.omniroute/.env"
  set +a
fi
export PORT=20129
export OMNIROUTE_SERVER_HOST=0.0.0.0
exec omniroute serve --port 20129 --no-open --no-tray
