#!/usr/bin/env python3
"""Create a non-authoritative Q16 evidence manifest from fixed CI workspace paths."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_manifest(candidate_sha: str, workspace: Path) -> dict:
    if not SHA_RE.fullmatch(candidate_sha):
        raise ValueError("candidate SHA must be a 40-character lowercase Git commit SHA")
    root = workspace.resolve(strict=True)
    inputs = {
        "scancode_full_repo": root / "scancode-full-repo.json",
        "scancode_install_report": root / "scancode-install-report.json",
        "ort_analyzer": root / "q16" / "analyzer-result.json",
        "ort_scanner": root / "q16" / "scan-result.yml",
    }
    artifacts = {}
    for name, path in inputs.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"required {name} report is missing or unsafe")
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        artifacts[name] = {
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
            "ort_pipeline": "synthetic fixture only; no project dependency resolution requested",
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
    root = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    candidate_sha = os.environ["GITHUB_SHA"]
    output = root / "q16" / "q16-evidence.json"
    evidence = build_manifest(candidate_sha, root)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "EVIDENCE_MANIFEST_CREATED", "artifacts": 4}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
