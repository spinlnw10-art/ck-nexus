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
    / "otel_telemetry_policy.py"
)
SPEC = importlib.util.spec_from_file_location("otel_telemetry_policy", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TelemetryPolicyError = MODULE.TelemetryPolicyError
validate_document = MODULE.validate_document
load_document = MODULE.load_document

BASE_EVENT = {
    "service.name": "ck-nexus",
    "ck_nexus.component": "core",
    "ck_nexus.operation": "policy_check",
    "ck_nexus.outcome": "success",
    "ck_nexus.duration_ms": 12.5,
}


class OTelTelemetryPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, name: str, payload: str) -> Path:
        path = self.root / name
        path.write_text(payload, encoding="utf-8")
        return path

    def test_accepts_minimal_allowlisted_synthetic_event(self) -> None:
        result = validate_document([BASE_EVENT])
        self.assertEqual(result["status"], "POLICY_VALIDATED_SHADOW_ONLY")
        self.assertEqual(result["event_count"], 1)
        self.assertFalse(result["network_accessed"])
        self.assertFalse(result["telemetry_exported"])
        self.assertFalse(result["gate_decision_made"])

    def test_accepts_only_nonproduction_environment(self) -> None:
        event = {**BASE_EVENT, "deployment.environment.name": "staging"}
        self.assertEqual(
            validate_document([event])["events"][0]["deployment.environment.name"],
            "staging",
        )

    def test_rejects_unknown_attributes_including_user_and_prompt_fields(self) -> None:
        for key in ("user.email", "tenant.id", "prompt", "tool.arguments", "http.url"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(TelemetryPolicyError, "non-allowlisted"):
                    validate_document([{**BASE_EVENT, key: "synthetic-value"}])

    def test_rejects_production_environment(self) -> None:
        with self.assertRaisesRegex(TelemetryPolicyError, "environment"):
            validate_document([{**BASE_EVENT, "deployment.environment.name": "production"}])

    def test_rejects_unknown_component_operation_and_outcome(self) -> None:
        for key, value in (
            ("ck_nexus.component", "billing"),
            ("ck_nexus.operation", "credential_read"),
            ("ck_nexus.outcome", "approved"),
        ):
            with self.subTest(key=key):
                with self.assertRaises(TelemetryPolicyError):
                    validate_document([{**BASE_EVENT, key: value}])

    def test_rejects_boolean_nan_and_out_of_range_duration(self) -> None:
        for duration in (True, float("nan"), float("inf"), -1, 600_001):
            with self.subTest(duration=duration):
                with self.assertRaises(TelemetryPolicyError):
                    validate_document([{**BASE_EVENT, "ck_nexus.duration_ms": duration}])

    def test_rejects_duplicate_json_keys(self) -> None:
        path = self.write_json(
            "duplicate.json",
            '[{"service.name":"ck-nexus","service.name":"other"}]',
        )
        with self.assertRaisesRegex(TelemetryPolicyError, "duplicate"):
            load_document(path)

    def test_rejects_symlink_input(self) -> None:
        target = self.write_json("target.json", json.dumps([BASE_EVENT]))
        link = self.root / "link.json"
        link.symlink_to(target)
        with self.assertRaisesRegex(TelemetryPolicyError, "non-symlink"):
            load_document(link)

    def test_rejects_empty_or_oversized_event_batches(self) -> None:
        for payload in ([], [BASE_EVENT] * 1001):
            with self.subTest(count=len(payload)):
                with self.assertRaises(TelemetryPolicyError):
                    validate_document(payload)


if __name__ == "__main__":
    unittest.main()
