from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "assurance"
    / "evidence_graph_intake.py"
)
SPEC = importlib.util.spec_from_file_location("evidence_graph_intake", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EvidenceGraphIntakeTests(unittest.TestCase):
    def _manifest(self, root: Path) -> dict:
        artifact = root / "scan-report.json"
        artifact.write_text('{"synthetic":true}', encoding="utf-8")
        return {
            "candidate_commit_sha": "a" * 40,
            "evidence_type": "CK-NEXUS-Q16-LICENSE-SCAN",
            "artifacts": {
                "scancode": {
                    "path": str(artifact),
                    "size_bytes": artifact.stat().st_size,
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }
            },
        }

    def test_builds_candidate_bound_graph_with_non_authoritative_edges(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = MODULE.build_graph_document(self._manifest(root), root)
            self.assertEqual(result["candidate_commit_sha"], "a" * 40)
            self.assertEqual(result["graph_report"]["node_count"], 2)
            self.assertEqual(result["graph_report"]["edge_count"], 1)
            self.assertFalse(result["authority"]["gate_decision_made"])
            self.assertFalse(result["authority"]["independent_validation_claimed"])
            self.assertFalse(result["edges"][0]["independent_validation"])

    def test_rejects_tampered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            (root / "scan-report.json").write_text('{"tampered":true}', encoding="utf-8")
            with self.assertRaisesRegex(MODULE.EvidenceIntakeError, "does not match"):
                MODULE.build_graph_document(manifest, root)

    def test_rejects_artifact_outside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            root.mkdir()
            outside = base / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            manifest = {
                "candidate_commit_sha": "b" * 40,
                "evidence_type": "CK-NEXUS-OTEL-SHADOW",
                "artifacts": {
                    "external": {
                        "path": str(outside),
                        "size_bytes": outside.stat().st_size,
                        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                    }
                },
            }
            with self.assertRaisesRegex(MODULE.EvidenceIntakeError, "within allowed root"):
                MODULE.build_graph_document(manifest, root)

    def test_rejects_empty_artifact_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(MODULE.EvidenceIntakeError, "1 to 50"):
                MODULE.build_graph_document(
                    {
                        "candidate_commit_sha": "c" * 40,
                        "evidence_type": "CK-NEXUS-OTEL-SHADOW",
                        "artifacts": {},
                    },
                    Path(directory),
                )


if __name__ == "__main__":
    unittest.main()
