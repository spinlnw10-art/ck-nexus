from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "assurance"
    / "q16_evidence_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("q16_evidence_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Q16EvidenceManifestTests(unittest.TestCase):
    def test_digest_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text('{"synthetic":true}', encoding="utf-8")
            self.assertEqual(
                MODULE.digest(path),
                "a8198524f58e72b56283ab71ebddada22840f108b46ef7165bb3fca9919c5558",
            )

    def test_manifest_binds_candidate_and_artifact_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text('{"synthetic":true}', encoding="utf-8")
            manifest = MODULE.build_manifest(
                "a" * 40,
                {"synthetic": path},
            )
            self.assertEqual(manifest["candidate_commit_sha"], "a" * 40)
            self.assertEqual(
                manifest["artifacts"]["synthetic"]["sha256"],
                MODULE.digest(path),
            )
            self.assertFalse(manifest["authority"]["gate_decision_made"])
            self.assertFalse(manifest["authority"]["legal_conclusion_made"])

    def test_rejects_invalid_candidate_sha(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate SHA"):
            MODULE.build_manifest("not-a-sha", {})

    def test_rejects_symlink_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                MODULE.build_manifest("b" * 40, {"linked": link})


if __name__ == "__main__":
    unittest.main()
