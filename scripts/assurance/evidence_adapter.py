#!/usr/bin/env python3
"""Read-only evidence envelope prototype.

This adapter validates metadata binding for a report. It never executes tools,
reads credentials, changes gate state, or converts a tool result into gate PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = (
    "gate_id",
    "gate_policy_version",
    "repository",
    "source_sha",
    "source_tree",
    "runtime_subject_sha256",
    "artifact_digest",
    "tool_name",
    "tool_version",
    "adapter_version",
    "configuration_sha256",
    "workflow_run_id",
    "scope",
    "scope_complete",
    "tool_result",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(report: dict[str, Any], expected: dict[str, str], raw_digest: str) -> dict[str, Any]:
    missing = [key for key in REQUIRED if key not in report]
    mismatches: list[str] = []

    for key in ("source_sha", "source_tree"):
        value = report.get(key)
        if not isinstance(value, str) or not GIT_SHA_RE.fullmatch(value):
            mismatches.append(f"invalid_{key}")
        elif expected.get(key) and value != expected[key]:
            mismatches.append(f"{key}_mismatch")

    for key in ("runtime_subject_sha256", "artifact_digest"):
        value = report.get(key)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            mismatches.append(f"invalid_{key}")
        elif expected.get(key) and value != expected[key]:
            mismatches.append(f"{key}_mismatch")
    workflow_run_id = report.get("workflow_run_id")
    if (
        not isinstance(workflow_run_id, (str, int))
        or str(workflow_run_id).strip() == ""
    ):
        mismatches.append("invalid_workflow_run_id")
    if report.get("scope_complete") is not True:
        mismatches.append("scope_not_complete")
    if not isinstance(report.get("scope"), str) or not report.get("scope", "").strip():
        mismatches.append("scope_missing")
    if not isinstance(report.get("tool_result"), str) or not report.get("tool_result", "").strip():
        mismatches.append("tool_result_missing")

    status = "INCOMPLETE" if missing or mismatches else "EVIDENCE_READY_FOR_GATE_EVALUATION"
    return {
        "schema_version": 1,
        "adapter": "cknexus-readonly-evidence-envelope",
        "adapter_version": "0.1.0",
        "status": status,
        "gate_state_changed": False,
        "gate_pass_claimed": False,
        "missing_fields": missing,
        "binding_or_scope_errors": sorted(set(mismatches)),
        "raw_report_sha256": raw_digest,
        "evidence": {key: report.get(key) for key in REQUIRED if key in report},
        "decision_authority": "CK-NEXUS gate evaluator only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-source-sha", required=True)
    parser.add_argument("--expected-source-tree", required=True)
    parser.add_argument("--expected-runtime-subject-sha256", required=True)
    parser.add_argument("--expected-artifact-digest", required=True)
    args = parser.parse_args()

    try:
        report = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise ValueError("input report must be a JSON object")
        expected = {
            "source_sha": args.expected_source_sha,
            "source_tree": args.expected_source_tree,
            "runtime_subject_sha256": args.expected_runtime_subject_sha256,
            "artifact_digest": args.expected_artifact_digest,
        }
        for key, value in expected.items():
            if key == "source_sha":
                if not GIT_SHA_RE.fullmatch(value):
                    raise ValueError("expected source SHA must be 40 lowercase hex characters")
            elif not SHA256_RE.fullmatch(value):
                raise ValueError(f"expected {key} must be 64 lowercase hex characters")
        result = validate(report, expected, sha256_file(args.input))
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary_keys = (
            "status",
            "gate_state_changed",
            "gate_pass_claimed",
            "missing_fields",
            "binding_or_scope_errors",
            "raw_report_sha256",
        )
        print(json.dumps({key: result[key] for key in summary_keys}, sort_keys=True))
        return 0 if result["status"] == "EVIDENCE_READY_FOR_GATE_EVALUATION" else 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"adapter input error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
