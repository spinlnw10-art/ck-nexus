#!/usr/bin/env python3
"""Wait for the CK-NEXUS unified runtime to report dependency readiness."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def health_url(host: str, port: int, path: str = "/health/ready") -> str:
    host = host.strip()
    if host in {"", "0.0.0.0", "::"}:
        host = "127.0.0.1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"http://{host}:{port}{path}"


def wait_for_health(
    url: str,
    *,
    timeout: float,
    interval: float = 1.0,
    opener: Callable = urlopen,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    progress: Callable[[str], None] = print,
) -> tuple[bool, str]:
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    if interval < 0:
        raise ValueError("interval must not be negative")

    started = monotonic()
    deadline = started + timeout
    next_progress = started + 5.0
    last_error = "no readiness response received"

    while True:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return False, last_error

        request = Request(url, headers={"Accept": "application/json"})
        try:
            with opener(request, timeout=min(2.0, remaining)) as response:
                status = getattr(response, "status", response.getcode())
                payload = json.loads(response.read().decode("utf-8"))
            if status == 200 and isinstance(payload, dict) and payload.get("ready") is True:
                return True, "ready=true"
            if status != 200:
                last_error = f"HTTP {status}"
            elif not isinstance(payload, dict):
                last_error = "health response is not a JSON object"
            else:
                last_error = (
                    "ready=false; causes="
                    + ",".join(str(item) for item in payload.get("causes", []))
                )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"

        now = monotonic()
        if now >= next_progress:
            elapsed = int(now - started)
            progress(f"[CK-NEXUS] Still waiting for readiness ({elapsed}s): {last_error}")
            next_progress = now + 5.0

        remaining = deadline - monotonic()
        if remaining <= 0:
            return False, last_error
        sleeper(min(interval, remaining))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/health/ready")
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    url = health_url(args.host, args.port, args.path)
    print(f"[CK-NEXUS] Waiting for readiness at {url} (timeout={args.timeout:g}s)", flush=True)
    ready, detail = wait_for_health(url, timeout=args.timeout)
    if ready:
        print(f"[CK-NEXUS] Runtime is READY: {detail}", flush=True)
        return 0

    print(f"[CK-NEXUS] Runtime did not become ready: {detail}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
