from __future__ import annotations

import contextlib
import os
import select
import subprocess
import sys
from pathlib import Path

import pytest

from creator_app.agnes.execution.sandbox.runner import _GATED_LAUNCHER_SCRIPT


def _start_gated_helper(target_code: str, gate_timeout: float = 5.0):
    gate_read_fd, gate_write_fd = os.pipe()
    ready_read_fd, ready_write_fd = os.pipe()
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _GATED_LAUNCHER_SCRIPT,
                str(ready_write_fd),
                str(gate_read_fd),
                str(gate_timeout),
                sys.executable,
                "-c",
                target_code,
            ],
            pass_fds=(ready_write_fd, gate_read_fd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except BaseException:
        for fd in (gate_read_fd, gate_write_fd, ready_read_fd, ready_write_fd):
            with contextlib.suppress(OSError):
                os.close(fd)
        raise
    os.close(ready_write_fd)
    os.close(gate_read_fd)
    return process, gate_write_fd, ready_read_fd


def _read_ready_signal(fd: int, timeout: float = 5.0) -> bytes:
    readable, _, _ = select.select([fd], [], [], timeout)
    assert readable, "launcher did not signal ready before deadline"
    return os.read(fd, 1)


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
        assert _read_ready_signal(ready_read_fd) == b"1"
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
                with contextlib.suppress(OSError):
                    os.close(fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_gated_launcher_does_not_exec_when_parent_withholds_release(tmp_path: Path) -> None:
    payload = tmp_path / "payload-must-not-run"
    target_code = f"from pathlib import Path; Path({str(payload)!r}).write_text('ran')"
    process, gate_write_fd, ready_read_fd = _start_gated_helper(target_code)
    try:
        assert _read_ready_signal(ready_read_fd) == b"1"
        os.close(gate_write_fd)
        gate_write_fd = -1
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 70, stderr.decode(errors="replace")
        assert not payload.exists()
    finally:
        for fd in (gate_write_fd, ready_read_fd):
            if fd >= 0:
                with contextlib.suppress(OSError):
                    os.close(fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_gated_launcher_times_out_when_parent_keeps_gate_open(tmp_path: Path) -> None:
    payload = tmp_path / "payload-must-not-run"
    target_code = f"from pathlib import Path; Path({str(payload)!r}).write_text('ran')"
    process, gate_write_fd, ready_read_fd = _start_gated_helper(target_code, gate_timeout=0.1)
    try:
        assert _read_ready_signal(ready_read_fd) == b"1"
        _, stderr = process.communicate(timeout=3)
        assert process.returncode == 70, stderr.decode(errors="replace")
        assert not payload.exists()
    finally:
        for fd in (gate_write_fd, ready_read_fd):
            if fd >= 0:
                with contextlib.suppress(OSError):
                    os.close(fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_gated_launcher_does_not_pass_unapproved_environment(tmp_path: Path, monkeypatch) -> None:
    payload = tmp_path / "environment-value"
    monkeypatch.setenv("CKNEXUS_TEST_SECRET", "must-not-reach-payload")
    target_code = (
        "import os; from pathlib import Path; "
        f"Path({str(payload)!r}).write_text(os.environ.get('CKNEXUS_TEST_SECRET', ''))"
    )
    process, gate_write_fd, ready_read_fd = _start_gated_helper(target_code)
    try:
        assert _read_ready_signal(ready_read_fd) == b"1"
        assert os.write(gate_write_fd, b"1") == 1
        os.close(gate_write_fd)
        gate_write_fd = -1
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr.decode(errors="replace")
        assert payload.read_text(encoding="utf-8") == ""
    finally:
        for fd in (gate_write_fd, ready_read_fd):
            if fd >= 0:
                with contextlib.suppress(OSError):
                    os.close(fd)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_start_gated_helper_closes_pipe_fds_when_popen_fails(monkeypatch) -> None:
    created_fds: list[int] = []
    real_pipe = os.pipe

    def tracked_pipe():
        fds = real_pipe()
        created_fds.extend(fds)
        return fds

    def fail_popen(*args, **kwargs):
        raise OSError("simulated Popen failure")

    monkeypatch.setattr(os, "pipe", tracked_pipe)
    monkeypatch.setattr(subprocess, "Popen", fail_popen)
    with pytest.raises(OSError, match="simulated Popen failure"):
        _start_gated_helper("pass")

    assert len(created_fds) == 4
    for fd in created_fds:
        with pytest.raises(OSError):
            os.fstat(fd)


@pytest.mark.parametrize(
    "launcher_args",
    [
        ("not-an-fd", "4", "1", "/bin/true"),
        ("3", "4", "1"),
    ],
)
def test_gated_launcher_rejects_invalid_argv(launcher_args: tuple[str, ...]) -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", _GATED_LAUNCHER_SCRIPT, *launcher_args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = process.communicate(timeout=3)
    assert process.returncode == 70, stderr.decode(errors="replace")
