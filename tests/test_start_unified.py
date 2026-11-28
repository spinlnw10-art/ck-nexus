from __future__ import annotations

import json
from urllib.error import URLError

from scripts.wait_for_health import health_url, wait_for_health


class FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode()

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload

    def getcode(self) -> int:
        return self.status


def test_health_url_uses_loopback_for_wildcard_bind() -> None:
    assert health_url("0.0.0.0", 8123) == "http://127.0.0.1:8123/health/ready"
    assert health_url("::", 8123) == "http://127.0.0.1:8123/health/ready"


def test_health_url_brackets_ipv6_host() -> None:
    assert health_url("::1", 8123) == "http://[::1]:8123/health/ready"


def test_wait_retries_until_runtime_is_ready() -> None:
    calls = 0

    def opener(*_args: object, **_kwargs: object) -> FakeResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise URLError("server is still starting")
        return FakeResponse({"ready": True, "state": "ready"})

    ready, detail = wait_for_health(
        "http://127.0.0.1:8123/health/ready",
        timeout=1,
        interval=0,
        opener=opener,
        sleeper=lambda _delay: None,
        progress=lambda _message: None,
    )

    assert ready is True
    assert detail == "ready=true"
    assert calls == 2


def test_wait_does_not_accept_http_success_without_readiness() -> None:
    ready, detail = wait_for_health(
        "http://127.0.0.1:8123/health/ready",
        timeout=0.01,
        interval=0.005,
        opener=lambda *_args, **_kwargs: FakeResponse({"ready": False, "causes": ["DB_DOWN"]}),
        progress=lambda _message: None,
    )

    assert ready is False
    assert "ready=false" in detail


def test_wait_reports_timeout_when_server_never_responds() -> None:
    clock = [0.0]

    def monotonic() -> float:
        return clock[0]

    def sleeper(delay: float) -> None:
        clock[0] += delay

    ready, detail = wait_for_health(
        "http://127.0.0.1:8123/health/ready",
        timeout=0.03,
        interval=0.01,
        opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("connection refused")),
        monotonic=monotonic,
        sleeper=sleeper,
        progress=lambda _message: None,
    )

    assert ready is False
    assert "connection refused" in detail
    assert clock[0] >= 0.03


def test_wait_exits_immediately_when_server_process_has_exited() -> None:
    calls = 0

    def opener(*_args: object, **_kwargs: object) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse({"ready": False})

    ready, detail = wait_for_health(
        "http://127.0.0.1:8123/health/ready",
        timeout=90,
        process_pid=1234,
        process_alive=lambda _pid: False,
        opener=opener,
        progress=lambda _message: None,
    )

    assert ready is False
    assert detail == "server process exited (pid=1234)"
    assert calls == 0
