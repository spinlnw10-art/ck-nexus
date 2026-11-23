#!/usr/bin/env sh
# CK-NEXUS compact golden terminal identity and quiet installer.
# POSIX sh; dependency-free apart from the shell utilities already used by setup.

cknexus_banner() {
  printf '\033[38;5;220m'
  cat <<'LOGO'
   ╭────────────────────────────────────╮
   │   👨‍🚀  CK-NEXUS  ✦                 │
   │       AUTONOMOUS SYSTEM            │
   ╰────────────────────────────────────╯
LOGO
  printf '\033[0m'
}

# Run a setup command quietly, retain its full output in a local log, and
# show only a small animated status. On failure, reveal the useful log tail.
cknexus_run_quiet() {
  label=$1
  shift
  log_file=${CKNEXUS_INSTALL_LOG:-"$PWD/.cknexus-install.log"}
  "$@" >"$log_file" 2>&1 &
  command_pid=$!
  frame=0

  printf '\033[?25l'
  while kill -0 "$command_pid" 2>/dev/null; do
    case $frame in
      0) glyph='◐' ;;
      1) glyph='◓' ;;
      2) glyph='◑' ;;
      *) glyph='◒' ;;
    esac
    printf '\r\033[38;5;220m👨‍🚀 >> %s %s\033[0m' "$label" "$glyph"
    frame=$(( (frame + 1) % 4 ))
    sleep 0.15
  done

  wait "$command_pid"
  result=$?
  printf '\r\033[K'
  printf '\033[?25h'
  if [ "$result" -eq 0 ]; then
    printf '\033[38;5;220m✓ %s สำเร็จ\033[0m\n' "$label"
    return 0
  fi

  printf '\033[31m✗ %s ไม่สำเร็จ — รายละเอียด 30 บรรทัดท้ายอยู่ใน %s\033[0m\n' "$label" "$log_file"
  tail -n 30 "$log_file" 2>/dev/null || cat "$log_file"
  return "$result"
}
