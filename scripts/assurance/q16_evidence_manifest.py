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


def build_manifest(
    candidate_sha: str,
    inputs: dict[str, Path],
    allowed_root: Path | None = None,
) -> dict:
    if not SHA_RE.fullmatch(candidate_sha):
        raise ValueError("candidate SHA must be a 40-character lowercase Git commit SHA")
    if not inputs:
        raise ValueError("at least one evidence artifact is required")

    root = (allowed_root or Path.cwd()).resolve(strict=True)
    artifacts = {}
    for name, path in sorted(inputs.items()):
        if path.is_symlink():
            raise ValueError(f"{name} must not be a symlink")
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise ValueError(f"{name} must resolve within the allowed directory") from exc
        if not resolved.is_file():
            raise ValueError(f"{name} must be a regular file")
        artifacts[name] = {
            "path": str(resolved),
            "size_bytes": resolved.stat().st_size,
            "sha256": digest(resolved),
        }

    return {
        "schema_version": 1,
        "evidence_type": "CK-NEXUS-Q16-LICENSE-SCAN",
        "candidate_commit_sha": candidate_sha,
        "scope": {
            "repository_source_scan": (
                "full checked-out source tree; generated and VCS directories excluded"
            ),
            "ort_pipeline": "synthetic fixture only; no dependency download requested",
        },
        "artifacts": artifacts,
        "authority": {
            "gate_decision_made": False,
            "license_approval_made": False,
            "legal_conclusion_made": False,
            "external_tool_authority": "advisory evidence only",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--allowed-root", type=Path, required=True)
    parser.add_argument("--scancode-report", type=Path, required=True)
    parser.add_argument("--scancode-install-report", type=Path, required=True)
    parser.add_argument("--ort-analyzer-result", type=Path, required=True)
    parser.add_argument("--ort-scan-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        root = args.allowed_root.resolve(strict=True)
        evidence = build_manifest(
            args.candidate_sha,
            {
                "scancode_full_repo": args.scancode_report,
                "scancode_install_report": args.scancode_install_report,
                "ort_analyzer": args.ort_analyzer_result,
                "ort_scanner": args.ort_scan_result,
            },
            root,
        )
        parent = args.output.parent.resolve(strict=True)
        parent.relative_to(root)
        output_path = parent / args.output.name
        with output_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": "EVIDENCE_MANIFEST_CREATED", "artifacts": 4}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
