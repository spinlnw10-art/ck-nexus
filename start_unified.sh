#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

log() {
  printf '[CK-NEXUS] %s\n' "$*"
}

PYTHON_BIN="${CKNEXUS_PYTHON:-python3}"
UV_BIN=$(command -v uv || true)

if [ ! -x .venv/bin/python ]; then
  if [ -n "$UV_BIN" ]; then
    log "Creating project virtual environment with uv"
    "$UV_BIN" venv .venv
  else
    log "Creating project virtual environment with Python"
    "$PYTHON_BIN" -m venv .venv
  fi
fi

if [ -n "$UV_BIN" ]; then
  PLATFORM=$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_platform().lower())')
  case "$PLATFORM" in
    *android*)
      log "Android detected; syncing base runtime dependencies and preserving installed extras"
      "$UV_BIN" sync --inexact --frozen
      ;;
    *)
      log "Reconciling all locked project extras and development dependencies with uv"
      "$UV_BIN" sync --all-extras --dev --frozen
      ;;
  esac
elif .venv/bin/python -m pip --version >/dev/null 2>&1; then
  log "uv not found; installing the editable project and dev extra with pip"
  .venv/bin/python -m pip install -e ".[dev]"
else
  log "ERROR: uv is unavailable and this virtual environment has no pip module." >&2
  log "Install uv, then run ./start_unified.sh again." >&2
  exit 1
fi

if [ ! -f .env.local ]; then
  log "Creating .env.local from .env.example"
  cp .env.example .env.local
fi

HOST="${CKNEXUS_HOST:-127.0.0.1}"
PORT_VALUE="${PORT:-8000}"
STARTUP_TIMEOUT="${CKNEXUS_STARTUP_TIMEOUT_SECONDS:-90}"

case "$PORT_VALUE" in
  ''|*[!0-9]*)
    log "ERROR: PORT must be an integer between 1 and 65535 (received: $PORT_VALUE)" >&2
    exit 2
    ;;
esac
if [ "$PORT_VALUE" -lt 1 ] || [ "$PORT_VALUE" -gt 65535 ]; then
  log "ERROR: PORT must be between 1 and 65535 (received: $PORT_VALUE)" >&2
  exit 2
fi
case "$STARTUP_TIMEOUT" in
  ''|*[!0-9]*|0)
    log "ERROR: CKNEXUS_STARTUP_TIMEOUT_SECONDS must be a positive integer" >&2
    exit 2
    ;;
esac

log "Starting unified runtime (host=$HOST port=$PORT_VALUE)"
.venv/bin/python -m creator_app.unified &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

if ! .venv/bin/python scripts/wait_for_health.py \
  --host "$HOST" \
  --port "$PORT_VALUE" \
  --timeout "$STARTUP_TIMEOUT"
then
  log "ERROR: startup failed; inspect the runtime log above and the health endpoint." >&2
  exit 1
fi

log "CK-NEXUS startup checks passed; keeping the unified runtime in the foreground"
wait "$SERVER_PID"
