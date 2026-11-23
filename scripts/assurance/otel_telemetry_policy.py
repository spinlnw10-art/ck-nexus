#!/usr/bin/env python3
"""Offline, fail-closed CK-NEXUS telemetry policy validator.

This module validates synthetic telemetry events only. It does not export data,
contact an OpenTelemetry Collector, or make release/security gate decisions.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 1_048_576
MAX_EVENTS = 1_000
ALLOWED_FIELDS = {
    "service.name",
    "service.version",
    "deployment.environment.name",
    "ck_nexus.component",
    "ck_nexus.operation",
    "ck_nexus.outcome",
    "ck_nexus.duration_ms",
}
REQUIRED_FIELDS = {
    "service.name",
    "ck_nexus.component",
    "ck_nexus.operation",
    "ck_nexus.outcome",
    "ck_nexus.duration_ms",
}
COMPONENTS = {"core", "creator", "agnes", "executor", "verifier"}
OPERATIONS = {"request", "tool_call", "policy_check", "approval_check", "evidence_write"}
OUTCOMES = {"success", "denied", "error"}
ENVIRONMENTS = {"development", "test", "staging"}
VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}$")


class TelemetryPolicyError(ValueError):
    """Raised when an event violates the telemetry allowlist."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TelemetryPolicyError("duplicate JSON object key")
        result[key] = value
    return result


def validate_event(event: Any) -> dict[str, Any]:
    """Return a normalized allowlisted event or reject it without echoing values."""
    if not isinstance(event, dict):
        raise TelemetryPolicyError("event must be an object")
    keys = set(event)
    unknown = keys - ALLOWED_FIELDS
    if unknown:
        raise TelemetryPolicyError("event contains non-allowlisted attributes")
    missing = REQUIRED_FIELDS - keys
    if missing:
        raise TelemetryPolicyError("event is missing required attributes")

    if event["service.name"] != "ck-nexus":
        raise TelemetryPolicyError("service.name is not the CK-NEXUS service identifier")

    component = event["ck_nexus.component"]
    operation = event["ck_nexus.operation"]
    outcome = event["ck_nexus.outcome"]
    duration = event["ck_nexus.duration_ms"]
    if component not in COMPONENTS:
        raise TelemetryPolicyError("component is not allowlisted")
    if operation not in OPERATIONS:
        raise TelemetryPolicyError("operation is not allowlisted")
    if outcome not in OUTCOMES:
        raise TelemetryPolicyError("outcome is not allowlisted")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise TelemetryPolicyError("duration_ms must be numeric")
    if not math.isfinite(duration) or not 0 <= duration <= 600_000:
        raise TelemetryPolicyError("duration_ms is outside the permitted range")

    normalized: dict[str, Any] = {
        "service.name": "ck-nexus",
        "ck_nexus.component": component,
        "ck_nexus.operation": operation,
        "ck_nexus.outcome": outcome,
        "ck_nexus.duration_ms": duration,
    }
    if "service.version" in event:
        version = event["service.version"]
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            raise TelemetryPolicyError("service.version has an invalid format")
        normalized["service.version"] = version
    if "deployment.environment.name" in event:
        environment = event["deployment.environment.name"]
        if environment not in ENVIRONMENTS:
            raise TelemetryPolicyError("environment is not allowlisted")
        normalized["deployment.environment.name"] = environment
    return normalized


def validate_document(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, list):
        raise TelemetryPolicyError("input root must be an array of events")
    if not payload or len(payload) > MAX_EVENTS:
        raise TelemetryPolicyError("event count must be between 1 and 1000")
    events = [validate_event(item) for item in payload]
    return {
        "schema_version": 1,
        "status": "POLICY_VALIDATED_SHADOW_ONLY",
        "events": events,
        "event_count": len(events),
        "network_accessed": False,
        "telemetry_exported": False,
        "gate_decision_made": False,
    }


def load_document(path: Path) -> Any:
    if path.is_symlink() or not path.is_file():
        raise TelemetryPolicyError("input must be a regular non-symlink file")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise TelemetryPolicyError("input exceeds the 1 MiB limit")
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                TelemetryPolicyError("non-finite JSON number is not permitted")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TelemetryPolicyError("input is not readable valid JSON") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON file containing synthetic events")
    args = parser.parse_args()
    try:
        result = validate_document(load_document(args.input))
    except TelemetryPolicyError as exc:
        # Deliberately report policy reason only; never echo input values.
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
