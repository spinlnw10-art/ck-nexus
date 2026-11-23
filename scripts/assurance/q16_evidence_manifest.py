#!/usr/bin/env python3
"""Create a non-authoritative, hash-bound manifest for Q16 scan outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--scancode-report", type=Path, required=True)
    parser.add_argument("--ort-analyzer-result", type=Path, required=True)
    parser.add_argument("--ort-scan-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not SHA_RE.fullmatch(args.candidate_sha):
        parser.error("candidate SHA must be a 40-character lowercase Git commit SHA")

    inputs = {
        "scancode_full_repo": args.scancode_report,
        "ort_analyzer": args.ort_analyzer_result,
        "ort_scanner": args.ort_scan_result,
    }
    for name, path in inputs.items():
        if path.is_symlink() or not path.is_file():
            parser.error(f"{name} must be a regular non-symlink file")

    evidence = {
        "schema_version": 1,
        "evidence_type": "CK-NEXUS-Q16-LICENSE-SCAN",
        "candidate_commit_sha": args.candidate_sha,
        "scope": {
            "repository_source_scan": "full checked-out source tree; generated and VCS directories excluded",
            "ort_pipeline": "synthetic fixture only; no dependency download requested",
        },
        "artifacts": {
            name: {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
            }
            for name, path in inputs.items()
        },
        "authority": {
            "gate_decision_made": False,
            "license_approval_made": False,
            "legal_conclusion_made": False,
            "external_tool_authority": "advisory evidence only",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "EVIDENCE_MANIFEST_CREATED", "artifacts": len(inputs)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
