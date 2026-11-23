from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "scripts" / "assurance" / "evidence_adapter.py"
SPEC = importlib.util.spec_from_file_location("evidence_adapter", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class EvidenceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = {
            "source_sha": "a" * 40,
            "source_tree": "b" * 40,
            "runtime_subject_sha256": "c" * 64,
            "artifact_digest": "d" * 64,
        }
        self.report = {
            "gate_id": "Q10",
            "gate_policy_version": "test-policy-v1",
            "repository": "spinlnw10-art/ck-nexus",
            **self.expected,
            "tool_name": "synthetic-fixture",
            "tool_version": "0.0.0",
            "adapter_version": "0.1.0",
            "configuration_sha256": "e" * 64,
            "workflow_run_id": 123,
            "scope": "synthetic-only",
            "scope_complete": True,
            "tool_result": "OBSERVED",
        }

    def test_complete_matching_report_is_only_evidence_ready(self) -> None:
        result = MODULE.validate(self.report, self.expected, "f" * 64)
        self.assertEqual(result["status"], "EVIDENCE_READY_FOR_GATE_EVALUATION")
        self.assertFalse(result["gate_state_changed"])
        self.assertFalse(result["gate_pass_claimed"])

    def test_stale_subject_is_incomplete(self) -> None:
        stale = dict(self.report, source_sha="9" * 40)
        result = MODULE.validate(stale, self.expected, "f" * 64)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("source_sha_mismatch", result["binding_or_scope_errors"])

    def test_incomplete_scope_is_incomplete(self) -> None:
        partial = dict(self.report, scope_complete=False)
        result = MODULE.validate(partial, self.expected, "f" * 64)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("scope_not_complete", result["binding_or_scope_errors"])

    def test_missing_fields_are_incomplete(self) -> None:
        partial = dict(self.report)
        del partial["tool_version"]
        result = MODULE.validate(partial, self.expected, "f" * 64)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("tool_version", result["missing_fields"])

    def test_invalid_git_tree_sha_is_incomplete(self) -> None:
        invalid = dict(self.report, source_tree="c" * 64)
        result = MODULE.validate(invalid, self.expected, "f" * 64)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn("invalid_source_tree", result["binding_or_scope_errors"])

    def test_runtime_digest_mismatch_is_incomplete(self) -> None:
        invalid = dict(self.report, runtime_subject_sha256="9" * 64)
        result = MODULE.validate(invalid, self.expected, "f" * 64)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIn(
            "runtime_subject_sha256_mismatch",
            result["binding_or_scope_errors"],
        )


if __name__ == "__main__":
    unittest.main()
