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
    / "q16_evidence_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("q16_evidence_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Q16EvidenceManifestTests(unittest.TestCase):
    def _workspace(self, root: Path) -> Path:
        workspace = root / MODULE.WORKSPACE
        workspace.mkdir(parents=True)
        for filename in MODULE.INPUTS.values():
            (workspace / filename).write_text('{"synthetic":true}', encoding="utf-8")
        return workspace

    def test_digest_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text('{"synthetic":true}', encoding="utf-8")
            self.assertEqual(
                MODULE.digest(path),
                "a8198524f58e72b56283ab71ebddada22840f108b46ef7165bb3fca9919c5558",
            )

    def test_manifest_binds_candidate_and_fixed_report_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = self._workspace(root)
            manifest = MODULE.build_manifest("a" * 40, workspace)
            self.assertEqual(manifest["candidate_commit_sha"], "a" * 40)
            self.assertEqual(
                manifest["artifacts"]["scancode_full_repo"]["sha256"],
                hashlib.sha256(
                    (workspace / MODULE.INPUTS["scancode_full_repo"]).read_bytes()
                ).hexdigest(),
            )
            self.assertFalse(manifest["authority"]["gate_decision_made"])
            self.assertFalse(manifest["authority"]["legal_conclusion_made"])

    def test_rejects_invalid_candidate_sha(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "candidate SHA"):
                MODULE.build_manifest("not-a-sha", self._workspace(Path(directory)))

    def test_rejects_symlink_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = self._workspace(root)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            report = workspace / MODULE.INPUTS["scancode_full_repo"]
            report.unlink()
            report.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "missing or unsafe"):
                MODULE.build_manifest("b" * 40, workspace)


if __name__ == "__main__":
    unittest.main()
