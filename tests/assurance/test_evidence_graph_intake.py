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
    def _manifest(self, root: Path, profile: str = "q16") -> dict:
        artifacts = {}
        for name, relative_path in MODULE.ARTIFACT_PATHS[profile].items():
            artifact = root / relative_path
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text('{"synthetic":true}', encoding="utf-8")
            artifacts[name] = {
                "size_bytes": artifact.stat().st_size,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        return {
            "candidate_commit_sha": "a" * 40,
            "evidence_type": (
                "CK-NEXUS-Q16-LICENSE-SCAN"
                if profile == "q16"
                else "CK-NEXUS-OTEL-SHADOW"
            ),
            "artifacts": artifacts,
        }

    def test_builds_candidate_bound_q16_graph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = MODULE.build_graph_document(self._manifest(root), root, "q16")
            self.assertEqual(result["candidate_commit_sha"], "a" * 40)
            self.assertEqual(result["graph_report"]["node_count"], 5)
            self.assertEqual(result["graph_report"]["edge_count"], 4)
            self.assertFalse(result["authority"]["gate_decision_made"])
            self.assertFalse(result["authority"]["independent_validation_claimed"])
            self.assertTrue(
                all(not edge["independent_validation"] for edge in result["edges"])
            )

    def test_builds_candidate_bound_otel_graph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = MODULE.build_graph_document(
                self._manifest(root, "otel"), root, "otel"
            )
            self.assertEqual(result["evidence_type"], "CK-NEXUS-OTEL-SHADOW")
            self.assertEqual(result["graph_report"]["node_count"], 6)
            self.assertEqual(result["graph_report"]["edge_count"], 5)

    def test_rejects_tampered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            (root / "scancode-full-repo.json").write_text(
                '{"tampered":true}', encoding="utf-8"
            )
            with self.assertRaisesRegex(MODULE.EvidenceIntakeError, "does not match"):
                MODULE.build_graph_document(manifest, root, "q16")

    def test_rejects_artifact_path_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            manifest["artifacts"]["scancode_full_repo"]["path"] = "../../outside"
            with self.assertRaisesRegex(MODULE.EvidenceIntakeError, "must not contain file paths"):
                MODULE.build_graph_document(manifest, root, "q16")

    def test_rejects_empty_artifact_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(
            MODULE.EvidenceIntakeError, "fixed profile"
        ):
            MODULE.build_graph_document(
                {
                    "candidate_commit_sha": "c" * 40,
                    "evidence_type": "CK-NEXUS-Q16-LICENSE-SCAN",
                    "artifacts": {},
                },
                Path(directory),
                "q16",
            )


if __name__ == "__main__":
    unittest.main()
