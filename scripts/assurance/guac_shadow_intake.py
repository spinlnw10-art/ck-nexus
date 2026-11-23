#!/usr/bin/env python3
"""Validate candidate-bound SBOM/attestation files for a later GUAC ingestion run.

This tool is deliberately offline: it does not start GUAC, contact services, ingest
documents, or make CK-NEXUS gate decisions. It only hashes and validates local files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SUPPORTED = {"cyclonedx", "spdx", "in-toto"}


class IntakeError(ValueError):
    """Raised when an input cannot be safely admitted to the shadow intake manifest."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_document(document: dict[str, Any]) -> str:
    if document.get("bomFormat") == "CycloneDX":
        if not isinstance(document.get("specVersion"), str):
            raise IntakeError("CycloneDX document is missing specVersion")
        if not isinstance(document.get("components", []), list):
            raise IntakeError("CycloneDX components must be an array")
        return "cyclonedx"

    if isinstance(document.get("spdxVersion"), str) and document["spdxVersion"].startswith("SPDX-"):
        if not isinstance(document.get("packages", []), list):
            raise IntakeError("SPDX packages must be an array")
        return "spdx"

    statement_type = document.get("_type") or document.get("predicateType")
    if isinstance(statement_type, str) and "in-toto" in statement_type.lower():
        if not isinstance(document.get("subject"), list):
            raise IntakeError("in-toto statement must contain a subject array")
        return "in-toto"

    raise IntakeError("unsupported document: expected CycloneDX, SPDX, or in-toto statement")


def validate_input(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    if not path.exists() or not path.is_file() or path.is_symlink():
        raise IntakeError(f"input must be an existing regular non-symlink file: {path}")
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeError(
            f"cannot read valid UTF-8 JSON from {path}: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise IntakeError(f"document root must be a JSON object: {path}")
    kind = classify_document(document)
    return {
        "path": str(path),
        "document_type": kind,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def build_manifest(candidate_sha: str, inputs: list[str]) -> dict[str, Any]:
    if not SHA40.fullmatch(candidate_sha):
        raise IntakeError("candidate SHA must be exactly 40 lowercase hexadecimal characters")
    if not inputs:
        raise IntakeError("at least one input document is required")

    documents = [validate_input(item) for item in inputs]
    kinds = {item["document_type"] for item in documents}
    if not kinds.intersection({"cyclonedx", "spdx"}):
        raise IntakeError("at least one SBOM (CycloneDX or SPDX) is required")

    return {
        "schema_version": "ck-nexus.guac-shadow-intake.v1",
        "status": "READY_FOR_GUAC_INGESTION",
        "decision_scope": "INTAKE_ONLY_NOT_A_SECURITY_GATE",
        "candidate": {"git_commit_sha": candidate_sha},
        "documents": documents,
        "document_count": len(documents),
        "document_types": sorted(kinds),
        "network_accessed": False,
        "guac_ingestion_performed": False,
        "gate_decision_made": False,
        "limitations": [
            "This manifest validates document shape and local file digests only.",
            (
                "It does not verify signatures, provenance trust, runtime artifact identity, "
                "or GUAC graph contents."
            ),
            (
                "GUAC must independently ingest the original files; CK-NEXUS must "
                "independently bind evidence to the release candidate."
            ),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument(
        "--input", action="append", default=[],
        help="SBOM or in-toto JSON file; repeatable",
    )
    parser.add_argument("--output", required=True, help="Manifest output path")
    args = parser.parse_args(argv)

    try:
        manifest = build_manifest(args.candidate_sha, args.input)
        output = Path(args.output)
        if output.exists():
            raise IntakeError(f"refusing to overwrite existing output: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (IntakeError, OSError) as exc:
        print(f"GUAC shadow intake blocked: {exc}", file=sys.stderr)
        return 2

    print(f"GUAC shadow intake manifest created: {output}")
    print("Status: READY_FOR_GUAC_INGESTION (not a gate pass)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
