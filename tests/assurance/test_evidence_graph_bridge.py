from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "assurance"
    / "evidence_graph_bridge.py"
)
SPEC = importlib.util.spec_from_file_location("evidence_graph_bridge", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CANDIDATE = "a" * 40
DIGEST = "b" * 64
OTEL = {
    "evidence_type": "CK-NEXUS-Q14-OTEL-SHADOW",
    "candidate_commit_sha": CANDIDATE,
    "collector_version": "0.165.0",
    "upstream_asset_sha256": DIGEST,
    "sigstore_bundle_sha256": DIGEST,
    "local_image_id": f"sha256:{DIGEST}",
    "image_archive_sha256": DIGEST,
    "trace_validation": "PASS",
    "metrics_validation": "PASS",
    "secret_redaction_validation": "PASS",
    "no_external_exporter_configured": True,
    "authority": {"gate_decision_made": False},
}
Q16 = {
    "evidence_type": "CK-NEXUS-Q16-LICENSE-SCAN",
    "candidate_commit_sha": CANDIDATE,
    "artifacts": {
        "scancode_full_repo": {"sha256": DIGEST, "size_bytes": 10},
        "ort_analyzer": {"sha256": "c" * 64, "size_bytes": 20},
        "ort_scanner": {"sha256": "d" * 64, "size_bytes": 30},
    },
    "authority": {"gate_decision_made": False, "legal_conclusion_made": False},
}


class EvidenceGraphBridgeTests(unittest.TestCase):
    def test_read_json_rejects_path_outside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / (root.name + "-outside.json")
            outside.write_text(json.dumps({"safe": True}), encoding="utf-8")
            self.addCleanup(outside.unlink)
            with self.assertRaisesRegex(
                MODULE.EvidenceGraphError, "inside the allowed root"
            ):
                MODULE.read_json(outside, allowed_root=root)

    def test_builds_graph_with_candidate_tool_and_artifact_edges(self) -> None:
        graph = MODULE.build_graph(CANDIDATE, OTEL, DIGEST, Q16, "e" * 64)
        self.assertEqual(graph["candidate_commit_sha"], CANDIDATE)
        self.assertTrue(any(edge["type"] == "PRODUCED_BY" for edge in graph["edges"]))
        self.assertTrue(any(edge["type"] == "EMITS" for edge in graph["edges"]))
        self.assertTrue(any(edge["type"] == "SUBJECT_OF" for edge in graph["edges"]))
        self.assertFalse(graph["authority"]["gate_decision_made"])
        statement = MODULE.make_statement(graph)
        self.assertEqual(
            statement["predicateType"],
            "https://ck-nexus.dev/attestations/evidence-graph/v1",
        )

    def test_rejects_candidate_mismatch(self) -> None:
        with self.assertRaisesRegex(MODULE.EvidenceGraphError, "different candidate"):
            MODULE.build_graph("f" * 40, OTEL, DIGEST, Q16, "e" * 64)

    def test_rejects_failed_or_unverified_otel_evidence(self) -> None:
        altered = {**OTEL, "secret_redaction_validation": "FAIL"}
        with self.assertRaisesRegex(MODULE.EvidenceGraphError, "redaction"):
            MODULE.build_graph(CANDIDATE, altered, DIGEST, Q16, "e" * 64)

    def test_rejects_q16_legal_conclusion_or_gate_authority(self) -> None:
        altered = {
            **Q16,
            "authority": {"gate_decision_made": True, "legal_conclusion_made": False},
        }
        with self.assertRaisesRegex(MODULE.EvidenceGraphError, "non-authoritative"):
            MODULE.build_graph(CANDIDATE, OTEL, DIGEST, altered, "e" * 64)

    def test_rejects_malformed_artifact_digest(self) -> None:
        altered = {
            **Q16,
            "artifacts": {"bad": {"sha256": "not-a-digest", "size_bytes": 1}},
        }
        with self.assertRaisesRegex(MODULE.EvidenceGraphError, "SHA-256"):
            MODULE.build_graph(CANDIDATE, OTEL, DIGEST, altered, "e" * 64)


if __name__ == "__main__":
    unittest.main()
