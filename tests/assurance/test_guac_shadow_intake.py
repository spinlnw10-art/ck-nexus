from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.assurance.guac_shadow_intake import IntakeError, build_manifest


CANDIDATE = "a" * 40


class GuacShadowIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, name: str, payload: object) -> str:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_cyclonedx_sbom_is_admitted_with_digest(self) -> None:
        sbom = self.write_json(
            "sbom.json",
            {"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []},
        )
        manifest = build_manifest(CANDIDATE, [sbom])
        self.assertEqual(manifest["status"], "READY_FOR_GUAC_INGESTION")
        self.assertEqual(manifest["documents"][0]["document_type"], "cyclonedx")
        self.assertEqual(len(manifest["documents"][0]["sha256"]), 64)
        self.assertFalse(manifest["gate_decision_made"])

    def test_spdx_sbom_is_admitted(self) -> None:
        sbom = self.write_json("sbom.spdx.json", {"spdxVersion": "SPDX-2.3", "packages": []})
        manifest = build_manifest(CANDIDATE, [sbom])
        self.assertIn("spdx", manifest["document_types"])

    def test_in_toto_statement_is_admitted_alongside_sbom(self) -> None:
        sbom = self.write_json("sbom.json", {"bomFormat": "CycloneDX", "specVersion": "1.6"})
        attestation = self.write_json(
            "attestation.json",
            {"_type": "https://in-toto.io/Statement/v1", "subject": []},
        )
        manifest = build_manifest(CANDIDATE, [sbom, attestation])
        self.assertEqual(set(manifest["document_types"]), {"cyclonedx", "in-toto"})

    def test_rejects_candidate_sha_with_wrong_shape(self) -> None:
        sbom = self.write_json("sbom.json", {"bomFormat": "CycloneDX", "specVersion": "1.6"})
        with self.assertRaisesRegex(IntakeError, "candidate SHA"):
            build_manifest("not-a-commit", [sbom])

    def test_rejects_attestation_without_sbom(self) -> None:
        attestation = self.write_json(
            "attestation.json",
            {"_type": "https://in-toto.io/Statement/v1", "subject": []},
        )
        with self.assertRaisesRegex(IntakeError, "at least one SBOM"):
            build_manifest(CANDIDATE, [attestation])

    def test_rejects_unknown_document(self) -> None:
        unknown = self.write_json("unknown.json", {"hello": "world"})
        with self.assertRaisesRegex(IntakeError, "unsupported document"):
            build_manifest(CANDIDATE, [unknown])

    def test_rejects_non_object_json(self) -> None:
        path = self.root / "array.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(IntakeError, "root must be a JSON object"):
            build_manifest(CANDIDATE, [str(path)])

    def test_rejects_symlink(self) -> None:
        target = self.root / "target.json"
        target.write_text('{"bomFormat":"CycloneDX","specVersion":"1.6"}', encoding="utf-8")
        link = self.root / "link.json"
        link.symlink_to(target)
        with self.assertRaisesRegex(IntakeError, "non-symlink"):
            build_manifest(CANDIDATE, [str(link)])


if __name__ == "__main__":
    unittest.main()
