from __future__ import annotations

import base64
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts/assurance/q14_otel_provenance_guard.py"
SPEC = importlib.util.spec_from_file_location("q14_otel_provenance_guard", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DIGEST = "sha256:" + "a" * 64
CANDIDATE = "b" * 40
IMAGE = "ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-contrib:0.165.0"


def signature_document(digest: str = DIGEST) -> list[dict[str, object]]:
    return [{"critical": {"image": {"docker-manifest-digest": digest}}}]


def provenance_document(digest: str = DIGEST, predicate: str = "https://slsa.dev/provenance/v1") -> list[dict[str, str]]:
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": IMAGE, "digest": {"sha256": digest.removeprefix("sha256:")}}],
        "predicateType": predicate,
        "predicate": {"buildDefinition": {"buildType": "https://example.invalid/synthetic"}},
    }
    payload = base64.b64encode(json.dumps(statement).encode()).decode()
    return [{"payload": payload}]


class Q14ProvenanceGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.signature = self.root / "signature.json"
        self.provenance = self.root / "provenance.json"

    def write_documents(self, signature: object, provenance: object) -> None:
        self.signature.write_text(json.dumps(signature), encoding="utf-8")
        self.provenance.write_text(json.dumps(provenance), encoding="utf-8")

    def test_extracts_one_digest_from_cosign_verify_output(self) -> None:
        self.assertEqual(MODULE.extract_verified_digest(signature_document()), DIGEST)

    def test_rejects_ambiguous_or_missing_signature_digest(self) -> None:
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.extract_verified_digest([])
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.extract_verified_digest(signature_document("sha256:" + "c" * 64) + signature_document())

    def test_accepts_matching_slsa_v1_subject(self) -> None:
        result = MODULE.verify_slsa_subject(provenance_document(), DIGEST)
        self.assertEqual(result["matched_attestations"], 1)

    def test_rejects_wrong_subject_digest(self) -> None:
        with self.assertRaisesRegex(MODULE.EvidenceError, "no verified SLSA provenance subject"):
            MODULE.verify_slsa_subject(provenance_document("sha256:" + "c" * 64), DIGEST)

    def test_rejects_non_slsa_predicate(self) -> None:
        with self.assertRaisesRegex(MODULE.EvidenceError, "no verified SLSA provenance subject"):
            MODULE.verify_slsa_subject(provenance_document(predicate="https://example.invalid/provenance"), DIGEST)

    def test_binds_verified_report_to_candidate_and_raw_evidence_hashes(self) -> None:
        self.write_documents(signature_document(), provenance_document())
        report = MODULE.build_report(
            self.signature,
            self.provenance,
            image=IMAGE,
            release_tag="v0.165.0",
            candidate_sha=CANDIDATE,
            slsa_status="VERIFIED",
        )
        self.assertEqual(report["image_digest"], DIGEST)
        self.assertEqual(report["candidate_sha"], CANDIDATE)
        self.assertEqual(report["signature_verification"], "COSIGN_VERIFIED_BY_WORKFLOW")
        self.assertEqual(report["slsa_provenance_status"], "VERIFIED")
        self.assertFalse(report["production_promotion_eligible"])
        self.assertFalse(report["image_layers_pulled"])
        self.assertFalse(report["container_started"])
        self.assertFalse(report["gate_decision_made"])

    def test_records_missing_slsa_without_promoting_image(self) -> None:
        self.write_documents(signature_document(), provenance_document())
        report = MODULE.build_report(
            self.signature,
            None,
            image=IMAGE,
            release_tag="v0.165.0",
            candidate_sha=CANDIDATE,
            slsa_status="NOT_PUBLISHED",
        )
        self.assertEqual(report["slsa_provenance_status"], "NOT_PUBLISHED")
        self.assertIsNone(report["provenance_evidence_sha256"])
        self.assertFalse(report["production_promotion_eligible"])
        self.assertFalse(report["gate_decision_made"])

    def test_rejects_non_official_image_or_invalid_candidate(self) -> None:
        self.write_documents(signature_document(), provenance_document())
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.build_report(self.signature, self.provenance, image="docker.io/library/alpine:latest", release_tag="v0.165.0", candidate_sha=CANDIDATE, slsa_status="VERIFIED")
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.build_report(self.signature, self.provenance, image=IMAGE, release_tag="latest", candidate_sha=CANDIDATE, slsa_status="VERIFIED")

    def test_rejects_symlink_evidence(self) -> None:
        self.write_documents(signature_document(), provenance_document())
        link = self.root / "signature-link.json"
        link.symlink_to(self.signature)
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.load_json(link)


if __name__ == "__main__":
    unittest.main()
