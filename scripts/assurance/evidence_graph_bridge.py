#!/usr/bin/env python3
"""Build a candidate-bound, non-authoritative CK-NEXUS evidence graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_INPUT_BYTES = 4 * 1024 * 1024


class EvidenceGraphError(ValueError):
    """Raised when evidence cannot be safely linked to the candidate."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    if path.is_symlink() or not path.is_file():
        raise EvidenceGraphError("evidence input must be a regular non-symlink file")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise EvidenceGraphError("evidence input exceeds the 4 MiB limit")
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                EvidenceGraphError("non-finite JSON number is not permitted")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceGraphError("evidence input is not valid JSON") from exc
    if not isinstance(value, dict):
        raise EvidenceGraphError("evidence root must be an object")
    return value, sha256_bytes(raw)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceGraphError("duplicate JSON object key")
        result[key] = value
    return result


def _require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not DIGEST_RE.fullmatch(value):
        raise EvidenceGraphError(f"{label} must be a lowercase SHA-256 digest")
    return value


def validate_otel(value: dict[str, Any], candidate_sha: str) -> dict[str, Any]:
    if value.get("evidence_type") != "CK-NEXUS-Q14-OTEL-SHADOW":
        raise EvidenceGraphError("unexpected OTel evidence type")
    if value.get("candidate_commit_sha") != candidate_sha:
        raise EvidenceGraphError("OTel evidence belongs to a different candidate")
    if value.get("collector_version") != "0.165.0":
        raise EvidenceGraphError("unreviewed Collector version")
    _require_sha(value.get("upstream_asset_sha256"), "upstream Collector asset")
    _require_sha(value.get("sigstore_bundle_sha256"), "Collector Sigstore bundle")
    image_id = value.get("local_image_id")
    if not isinstance(image_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise EvidenceGraphError("local Collector image ID is invalid")
    _require_sha(value.get("image_archive_sha256"), "local Collector image archive")
    if value.get("trace_validation") != "PASS":
        raise EvidenceGraphError("trace propagation evidence is not passing")
    if value.get("metrics_validation") != "PASS":
        raise EvidenceGraphError("metrics evidence is not passing")
    if value.get("secret_redaction_validation") != "PASS":
        raise EvidenceGraphError("secret redaction evidence is not passing")
    if value.get("no_external_exporter_configured") is not True:
        raise EvidenceGraphError("Collector must have no external exporter")
    if value.get("authority", {}).get("gate_decision_made") is not False:
        raise EvidenceGraphError("external evidence must not make a gate decision")
    return value


def validate_q16(value: dict[str, Any], candidate_sha: str) -> dict[str, Any]:
    if value.get("evidence_type") != "CK-NEXUS-Q16-LICENSE-SCAN":
        raise EvidenceGraphError("unexpected Q16 evidence type")
    if value.get("candidate_commit_sha") != candidate_sha:
        raise EvidenceGraphError("Q16 evidence belongs to a different candidate")
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise EvidenceGraphError("Q16 evidence has no artifacts")
    for name, artifact in artifacts.items():
        if not isinstance(name, str) or not isinstance(artifact, dict):
            raise EvidenceGraphError("Q16 artifact entry is malformed")
        _require_sha(artifact.get("sha256"), f"Q16 artifact {name}")
        size = artifact.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise EvidenceGraphError(f"Q16 artifact {name} has invalid size")
    authority = value.get("authority")
    if not isinstance(authority, dict) or authority.get("gate_decision_made") is not False:
        raise EvidenceGraphError("Q16 evidence must remain non-authoritative")
    if authority.get("legal_conclusion_made") is not False:
        raise EvidenceGraphError("Q16 evidence cannot make legal conclusions")
    return value


def build_graph(
    candidate_sha: str,
    otel: dict[str, Any],
    otel_sha256: str,
    q16: dict[str, Any],
    q16_sha256: str,
) -> dict[str, Any]:
    if not SHA_RE.fullmatch(candidate_sha):
        raise EvidenceGraphError("candidate SHA must be a 40-character lowercase Git SHA")
    otel = validate_otel(otel, candidate_sha)
    q16 = validate_q16(q16, candidate_sha)
    _require_sha(otel_sha256, "OTel evidence file")
    _require_sha(q16_sha256, "Q16 evidence file")

    candidate_id = f"candidate:{candidate_sha}"
    nodes = [
        {
            "id": candidate_id,
            "type": "candidate",
            "repository": "spinlnw10-art/ck-nexus",
            "git_commit_sha": candidate_sha,
        }
    ]
    edges = []
    evidence_records = [
        (
            "q14-otel",
            otel,
            otel_sha256,
            [
                ("open-telemetry/opentelemetry-collector", otel["collector_version"]),
            ],
            {
                "trace_validation": otel["trace_validation"],
                "metrics_validation": otel["metrics_validation"],
                "secret_redaction_validation": otel["secret_redaction_validation"],
                "image_id": otel["local_image_id"],
                "image_archive_sha256": otel["image_archive_sha256"],
            },
        ),
        (
            "q16-license",
            q16,
            q16_sha256,
            [
                ("oss-review-toolkit/ort", "99.1.0"),
                ("aboutcode-org/scancode-toolkit", "32.5.0"),
            ],
            {
                "artifact_count": len(q16["artifacts"]),
                "artifact_names": sorted(q16["artifacts"]),
            },
        ),
    ]

    for label, record, record_sha, tools, summary in evidence_records:
        evidence_id = f"evidence:sha256:{record_sha}"
        nodes.append(
            {
                "id": evidence_id,
                "type": "evidence",
                "evidence_type": record["evidence_type"],
                "sha256": record_sha,
                "summary": summary,
            }
        )
        edges.append({"from": evidence_id, "to": candidate_id, "type": "SUBJECT_OF"})
        for tool_name, version in tools:
            tool_id = f"tool:{tool_name}@{version}"
            nodes.append(
                {
                    "id": tool_id,
                    "type": "tool",
                    "name": tool_name,
                    "version": version,
                }
            )
            edges.append({"from": evidence_id, "to": tool_id, "type": "PRODUCED_BY"})
        if label == "q16-license":
            for name, artifact in sorted(record["artifacts"].items()):
                artifact_id = f"artifact:sha256:{artifact['sha256']}"
                nodes.append(
                    {
                        "id": artifact_id,
                        "type": "artifact",
                        "name": name,
                        "sha256": artifact["sha256"],
                        "size_bytes": artifact["size_bytes"],
                    }
                )
                edges.append({"from": evidence_id, "to": artifact_id, "type": "EMITS"})

    unique_nodes = {node["id"]: node for node in nodes}
    graph = {
        "schema_version": 1,
        "graph_type": "CK-NEXUS-EVIDENCE-GRAPH",
        "candidate_commit_sha": candidate_sha,
        "nodes": [unique_nodes[key] for key in sorted(unique_nodes)],
        "edges": sorted(edges, key=lambda edge: (edge["from"], edge["type"], edge["to"])),
        "authority": {
            "gate_decision_made": False,
            "license_approval_made": False,
            "deployment_authorized": False,
            "external_tools_are_advisory_only": True,
            "network_accessed_by_bridge": False,
            "guac_ingestion_performed": False,
        },
    }
    return graph


def make_statement(graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": "spinlnw10-art/ck-nexus",
                "digest": {"gitCommit": graph["candidate_commit_sha"]},
            }
        ],
        "predicateType": "https://ck-nexus.dev/attestations/evidence-graph/v1",
        "predicate": graph,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--otel-evidence", type=Path, required=True)
    parser.add_argument("--q16-evidence", type=Path, required=True)
    parser.add_argument("--output-graph", type=Path, required=True)
    parser.add_argument("--output-statement", type=Path, required=True)
    args = parser.parse_args()

    try:
        otel, otel_sha = read_json(args.otel_evidence)
        q16, q16_sha = read_json(args.q16_evidence)
        graph = build_graph(args.candidate_sha, otel, otel_sha, q16, q16_sha)
        statement = make_statement(graph)
        for output in (args.output_graph, args.output_statement):
            if output.is_symlink():
                raise EvidenceGraphError("output must not be a symlink")
            output.parent.mkdir(parents=True, exist_ok=True)
        args.output_graph.write_text(
            json.dumps(graph, indent=2, sort_keys=True) + "\\n", encoding="utf-8"
        )
        args.output_statement.write_text(
            json.dumps(statement, indent=2, sort_keys=True) + "\\n", encoding="utf-8"
        )
    except (OSError, EvidenceGraphError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": "EVIDENCE_GRAPH_CREATED", "nodes": len(graph["nodes"]), "edges": len(graph["edges"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
