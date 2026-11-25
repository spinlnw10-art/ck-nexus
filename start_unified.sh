#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

if [ -x .venv-termux-runtime/bin/python ]; then
  VENV_DIR=.venv-termux-runtime
else
  VENV_DIR=.venv
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  python -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install -e ".[dev]"
fi

if [ -n "${TERMUX_VERSION:-}" ] && [ -n "${PREFIX:-}" ]; then
  PYTHON_VERSION=$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  PYTHON_SHARED_LIBRARY="$PREFIX/lib/libpython${PYTHON_VERSION}.so"
  if [ -f "$PYTHON_SHARED_LIBRARY" ]; then
    case ":${LD_PRELOAD:-}:" in
      *":$PYTHON_SHARED_LIBRARY:"*) ;;
      *) LD_PRELOAD="$PYTHON_SHARED_LIBRARY${LD_PRELOAD:+:$LD_PRELOAD}"; export LD_PRELOAD ;;
    esac
  fi
fi

if [ ! -f .env.local ]; then
  cp .env.example .env.local
fi

exec "$VENV_DIR/bin/python" -m creator_app.unified
