#!/usr/bin/env python3
"""Validate fixed-path candidate evidence and project it into CK-NEXUS EvidenceGraph."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from creator_app.global_knowledge import (
    EvidenceEdgeKind,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    EvidenceNodeKind,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_ARTIFACTS = 50
ARTIFACT_PATHS = {
    "q16": {
        "scancode_full_repo": "scancode-full-repo.json",
        "scancode_install_report": "scancode-install-report.json",
        "ort_analyzer": "q16/analyzer-result.json",
        "ort_scanner": "q16/scan-result.yml",
    },
    "otel": {
        "collector_image_provenance": "collector-image-provenance.json",
        "collector_image_id": "collector-image-id.txt",
        "collector_image_archive_digest": "collector-image-archive.sha256",
        "collector_shadow_log": "collector-shadow.log",
        "synthetic_telemetry_test": "otel-shadow-test-result.json",
    },
}


class EvidenceIntakeError(ValueError):
    """Raised when candidate evidence cannot be safely admitted to the graph."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceIntakeError("duplicate JSON object key")
        result[key] = value
    return result


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _fixed_artifact(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    if path.is_symlink():
        raise EvidenceIntakeError("evidence paths must not be symlinks")
    resolved = path.resolve(strict=True)
    resolved.relative_to(root)
    if not resolved.is_file():
        raise EvidenceIntakeError("evidence artifact must be a regular file")
    return resolved


def build_graph_document(
    manifest: dict[str, Any],
    allowed_root: Path,
    profile: str,
) -> dict[str, Any]:
    if profile not in ARTIFACT_PATHS:
        raise EvidenceIntakeError("unsupported evidence profile")
    if not isinstance(manifest, dict):
        raise EvidenceIntakeError("manifest root must be an object")
    candidate_sha = manifest.get("candidate_commit_sha")
    evidence_type = manifest.get("evidence_type")
    artifacts = manifest.get("artifacts")
    if not isinstance(candidate_sha, str) or not SHA_RE.fullmatch(candidate_sha):
        raise EvidenceIntakeError("candidate commit SHA is invalid")
    if not isinstance(evidence_type, str) or not NAME_RE.fullmatch(evidence_type):
        raise EvidenceIntakeError("evidence type is invalid")
    expected = ARTIFACT_PATHS[profile]
    if not isinstance(artifacts, dict) or set(artifacts) != set(expected):
        raise EvidenceIntakeError("manifest artifact set does not match its fixed profile")

    root = allowed_root.resolve(strict=True)
    observed_at = manifest.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at:
        observed_at = datetime.now(UTC).isoformat()

    nodes: list[EvidenceGraphNode] = []
    edges: list[EvidenceGraphEdge] = []
    artifact_records: list[dict[str, Any]] = []
    claim_id = f"{evidence_type}:{candidate_sha}"
    claim_node_id = f"claim:{candidate_sha}:{evidence_type}"
    nodes.append(
        EvidenceGraphNode(
            node_id=claim_node_id,
            kind=EvidenceNodeKind.CLAIM,
            claim_id=claim_id,
            observed_at=observed_at,
        )
    )

    for name, relative_path in expected.items():
        descriptor = artifacts.get(name)
        if not isinstance(descriptor, dict) or "path" in descriptor:
            raise EvidenceIntakeError("artifact descriptors must not contain file paths")
        declared_sha = descriptor.get("sha256")
        declared_size = descriptor.get("size_bytes")
        if not isinstance(declared_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", declared_sha):
            raise EvidenceIntakeError("artifact SHA-256 is invalid")
        if (
            isinstance(declared_size, bool)
            or not isinstance(declared_size, int)
            or declared_size < 0
        ):
            raise EvidenceIntakeError("artifact size is invalid")

        resolved = _fixed_artifact(root, relative_path)
        if resolved.stat().st_size != declared_size or _sha256(resolved) != declared_sha:
            raise EvidenceIntakeError("artifact size or SHA-256 does not match manifest")

        node_id = f"source:{candidate_sha}:{name}"
        source_id = f"sha256:{declared_sha}"
        nodes.append(
            EvidenceGraphNode(
                node_id=node_id,
                kind=EvidenceNodeKind.SOURCE,
                source_id=source_id,
                observed_at=observed_at,
            )
        )
        edge_id = hashlib.sha256(f"{claim_node_id}->{node_id}".encode()).hexdigest()
        edges.append(
            EvidenceGraphEdge(
                edge_id=f"edge:{edge_id}",
                from_node_id=claim_node_id,
                to_node_id=node_id,
                kind=EvidenceEdgeKind.DERIVED_FROM,
                independent_validation=False,
            )
        )
        artifact_records.append(
            {
                "name": name,
                "node_id": node_id,
                "source_id": source_id,
                "size_bytes": declared_size,
                "sha256": declared_sha,
            }
        )

    graph = EvidenceGraph(tuple(nodes), tuple(edges))
    lineage = graph.trace_lineage(claim_node_id)
    report = graph.report()
    return {
        "schema_version": 1,
        "graph_type": "CK-NEXUS-EVIDENCE-GRAPH-INTAKE",
        "candidate_commit_sha": candidate_sha,
        "evidence_type": evidence_type,
        "nodes": [
            {
                "node_id": node.node_id,
                "kind": node.kind.value,
                "source_id": node.source_id,
                "claim_id": node.claim_id,
                "observed_at": node.observed_at,
            }
            for node in graph.nodes
        ],
        "edges": [
            {
                "edge_id": edge.edge_id,
                "from_node_id": edge.from_node_id,
                "to_node_id": edge.to_node_id,
                "kind": edge.kind.value,
                "independent_validation": edge.independent_validation,
            }
            for edge in graph.edges
        ],
        "artifacts": artifact_records,
        "graph_report": {
            "node_count": report.node_count,
            "edge_count": report.edge_count,
            "citation_cycles": list(report.citation_cycles),
            "lineage_paths": [
                {
                    "root_node_id": item.root_node_id,
                    "node_ids": list(item.node_ids),
                    "depth": item.depth,
                    "independent_validation_edges": item.independent_validation_edges,
                    "cycle_detected": item.cycle_detected,
                }
                for item in lineage
            ],
        },
        "authority": {
            "gate_decision_made": False,
            "license_approval_made": False,
            "production_promotion_made": False,
            "independent_validation_claimed": False,
            "external_tools_are_advisory_only": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(ARTIFACT_PATHS), required=True)
    args = parser.parse_args()

    if args.profile == "q16":
        root = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
        manifest_path = root / "q16" / "q16-evidence.json"
        output_path = root / "q16" / "q16-evidence-graph.json"
    else:
        root = Path.cwd().resolve(strict=True)
        manifest_path = root / "otel-shadow-evidence-manifest.json"
        output_path = root / "otel-shadow-evidence-graph.json"

    try:
        manifest_file = _fixed_artifact(root, str(manifest_path.relative_to(root)))
        if manifest_file.stat().st_size > MAX_MANIFEST_BYTES:
            raise EvidenceIntakeError("manifest exceeds 2 MiB")
        manifest = json.loads(
            manifest_file.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
        document = build_graph_document(manifest, root, args.profile)
        with output_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "status": "EVIDENCE_GRAPH_INTAKE_VALIDATED",
                "node_count": len(document["nodes"]),
                "edge_count": len(document["edges"]),
                "gate_decision_made": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
