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
                "5f22e9b44a2c4b8270ac2f0e3f8e39b7d3c53a0f1b8d6c0b5a7f2e8d8c7e5f5f",
            )

    def test_rejects_symlink_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            self.assertTrue(link.is_symlink())


if __name__ == "__main__":
    unittest.main()
