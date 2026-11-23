from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts/assurance/q16_license_evidence_intake.py"
)
SPEC = importlib.util.spec_from_file_location("q16_license_evidence_intake", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CANDIDATE = "a" * 40


class Q16IntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "result.json"
        self.path.write_text(json.dumps({"synthetic": True}), encoding="utf-8")

    def test_accepts_ort_evidence_without_claiming_license_approval(self) -> None:
        result = MODULE.intake(
            self.path, tool="ort", version="synthetic-1",
            candidate_sha=CANDIDATE,
            allowed_root=Path(self.temp.name),
        )
        self.assertEqual(result["intake_status"], "INTEGRITY_VERIFIED_ONLY")
        self.assertFalse(result["license_assessment_performed"])
        self.assertFalse(result["legal_approval_granted"])
        self.assertFalse(result["gate_decision_made"])

    def test_accepts_scancode_evidence(self) -> None:
        result = MODULE.intake(
            self.path, tool="scancode", version="synthetic-1",
            candidate_sha=CANDIDATE,
            allowed_root=Path(self.temp.name),
        )
        self.assertEqual(result["tool"], "scancode")
        self.assertEqual(len(result["evidence_sha256"]), 64)

    def test_rejects_unknown_tool_and_invalid_candidate(self) -> None:
        with self.assertRaises(MODULE.IntakeError):
            MODULE.intake(self.path, tool="other", version="1", candidate_sha=CANDIDATE, allowed_root=Path(self.temp.name))
        with self.assertRaises(MODULE.IntakeError):
            MODULE.intake(self.path, tool="ort", version="1", candidate_sha="bad", allowed_root=Path(self.temp.name))

    def test_rejects_duplicate_keys_and_non_object_json(self) -> None:
        self.path.write_text('{"a":1,"a":2}', encoding="utf-8")
        with self.assertRaises(MODULE.IntakeError):
            MODULE.intake(self.path, tool="ort", version="1", candidate_sha=CANDIDATE, allowed_root=Path(self.temp.name))
        self.path.write_text("[]", encoding="utf-8")
        with self.assertRaises(MODULE.IntakeError):
            MODULE.intake(self.path, tool="ort", version="1", candidate_sha=CANDIDATE, allowed_root=Path(self.temp.name))

    def test_rejects_path_outside_allowed_root(self) -> None:
        outside = Path(self.temp.name).parent / (Path(self.temp.name).name + "-outside.json")
        outside.write_text("{}", encoding="utf-8")
        self.addCleanup(outside.unlink)
        with self.assertRaisesRegex(MODULE.IntakeError, "inside the allowed root"):
            MODULE.intake(
                outside,
                tool="ort",
                version="1",
                candidate_sha=CANDIDATE,
                allowed_root=Path(self.temp.name),
            )

    def test_rejects_symlink_and_empty_file(self) -> None:
        target = Path(self.temp.name) / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = Path(self.temp.name) / "link.json"
        link.symlink_to(target)
        with self.assertRaises(MODULE.IntakeError):
            MODULE.intake(link, tool="ort", version="1", candidate_sha=CANDIDATE, allowed_root=Path(self.temp.name))
        self.path.write_bytes(b"")
        with self.assertRaises(MODULE.IntakeError):
            MODULE.intake(self.path, tool="ort", version="1", candidate_sha=CANDIDATE, allowed_root=Path(self.temp.name))


if __name__ == "__main__":
    unittest.main()
