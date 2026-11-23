#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

. "$SCRIPT_DIR/scripts/cknexus-brand.sh"
cknexus_banner

if [ ! -d .venv ]; then
  if ! cknexus_run_quiet "สร้าง virtual environment" python -m venv .venv; then
    exit 1
  fi
  if ! cknexus_run_quiet "ติดตั้ง CK-NEXUS และเครื่องมือ" .venv/bin/python -m pip install -e ".[dev]"; then
    exit 1
  fi
fi

if [ ! -f .env.local ]; then
  cp .env.example .env.local
  printf '\033[38;5;220m✓ เตรียมไฟล์ตั้งค่า .env.local แล้ว\033[0m\n'
fi

printf '\033[38;5;220m👨‍🚀 >> เริ่ม CK-NEXUS\033[0m\n'
exec .venv/bin/python -m creator_app.unified
