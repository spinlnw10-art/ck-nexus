from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from creator_app.agnes.execution.sandbox.runner import _GATED_LAUNCHER_SCRIPT


def _start_gated_helper(target_code: str):
    gate_read_fd, gate_write_fd = os.pipe()
    ready_read_fd, ready_write_fd = os.pipe()
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _GATED_LAUNCHER_SCRIPT,
            str(ready_write_fd),
            str(gate_read_fd),
            sys.executable,
            "-c",
            target_code,
        ],
        pass_fds=(ready_write_fd, gate_read_fd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    os.close(ready_write_fd)
    os.close(gate_read_fd)
    return process, gate_write_fd, ready_read_fd


def test_gated_launcher_waits_for_parent_release(tmp_path: Path) -> None:
    attached = tmp_path / "cgroup-attached"
    payload = tmp_path / "payload-ran"
    target_code = (
        "from pathlib import Path; "
        f"assert Path({str(attached)!r}).is_file(); "
        f"Path({str(payload)!r}).write_text('ran')"
    )
    process, gate_write_fd, ready_read_fd = _start_gated_helper(target_code)
    try:
        assert os.read(ready_read_fd, 1) == b"1"
        assert not payload.exists()
        attached.write_text("attached", encoding="utf-8")
        assert os.write(gate_write_fd, b"1") == 1
        os.close(gate_write_fd)
        gate_write_fd = -1
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr.decode(errors="replace")
        assert payload.read_text(encoding="utf-8") == "ran"
    finally:
        for fd in (gate_write_fd, ready_read_fd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_gated_launcher_does_not_exec_when_parent_withholds_release(tmp_path: Path) -> None:
    payload = tmp_path / "payload-must-not-run"
    target_code = f"from pathlib import Path; Path({str(payload)!r}).write_text('ran')"
    process, gate_write_fd, ready_read_fd = _start_gated_helper(target_code)
    try:
        assert os.read(ready_read_fd, 1) == b"1"
        os.close(gate_write_fd)
        gate_write_fd = -1
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 70, stderr.decode(errors="replace")
        assert not payload.exists()
    finally:
        for fd in (gate_write_fd, ready_read_fd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
