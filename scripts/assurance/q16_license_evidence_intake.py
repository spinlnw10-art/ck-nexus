#!/usr/bin/env python3
"""Offline, fail-closed intake for synthetic ORT and ScanCode evidence.

This module verifies evidence identity and integrity only. It does not interpret
license conclusions, grant legal approval, or make a CK-NEXUS release decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TOOLS = {"ort", "scancode"}
MAX_BYTES = 20 * 1024 * 1024


class IntakeError(ValueError):
    """Raised when evidence cannot be safely bound to a candidate."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntakeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def intake(path: Path, *, tool: str, version: str, candidate_sha: str) -> dict[str, Any]:
    if tool not in TOOLS:
        raise IntakeError("tool must be ort or scancode")
    if not SHA_RE.fullmatch(candidate_sha):
        raise IntakeError("candidate SHA must be 40 lowercase hexadecimal characters")
    if not version or len(version) > 80 or any(ord(c) < 32 for c in version):
        raise IntakeError("tool version is missing or invalid")

    try:
        info = path.lstat()
    except OSError as exc:
        raise IntakeError("evidence file cannot be accessed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise IntakeError("evidence must be a regular non-symlink file")
    if info.st_size == 0 or info.st_size > MAX_BYTES:
        raise IntakeError("evidence size is outside the permitted range")

    raw = path.read_bytes()
    if len(raw) != info.st_size:
        raise IntakeError("evidence changed while being read")
    try:
        document = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeError("evidence must be valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise IntakeError("evidence root must be a JSON object")

    return {
        "schema": "ck-nexus.q16-license-evidence-intake.v1",
        "candidate_sha": candidate_sha,
        "tool": tool,
        "tool_version": version,
        "evidence_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence_bytes": len(raw),
        "evidence_format": "json",
        "intake_status": "INTEGRITY_VERIFIED_ONLY",
        "license_assessment_performed": False,
        "legal_approval_granted": False,
        "gate_decision_made": False,
        "network_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--tool", required=True, choices=sorted(TOOLS))
    parser.add_argument("--version", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args()
    try:
        result = intake(
            args.input, tool=args.tool, version=args.version,
            candidate_sha=args.candidate_sha,
        )
    except IntakeError as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
