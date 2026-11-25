import pytest

from creator_app.agnes_approval import CoreApprovalDecision
from creator_app.agnes_ledger import AppendOnlyLedger
from creator_app.agnes_skill_foundry import FoundryState, SkillFoundry


class FakeVerifier:
    def __init__(self, actor_id="core_owner", approved=True):
        self.actor_id = actor_id
        self.approved = approved

    def verify(self, approval_ref, *, subject_id, action, request_digest):
        if not self.approved:
            return None
        return CoreApprovalDecision(
            approval_ref, subject_id, action, request_digest, self.actor_id, True
        )


def _candidate(foundry, **overrides):
    values = {
        "skill_id": "safe-reader",
        "version": "1.0.0",
        "source_url": "https://agentskills.io/safe-reader",
        "checksum_sha256": "a" * 64,
        "license_id": "MIT",
        "has_executable_scripts": False,
        "requests_credentials": False,
        "requests_network": False,
    }
    values.update(overrides)
    return foundry.discover(**values)


def _complete_review(foundry, candidate_id):
    foundry.record_security_scan(candidate_id, evidence_ref="scan:sha256:111", passed=True)
    foundry.record_sandbox_test(candidate_id, evidence_ref="sandbox:run:222", passed=True)
    foundry.record_benchmark(candidate_id, evidence_ref="benchmark:run:333", passed=True)
    return foundry.record_compatibility(
        candidate_id,
        evidence_ref="compatibility:run:444",
        independent_verification_ref="review:independent:555",
        passed=True,
    )


def test_candidate_requires_checksum_license_and_trusted_source(tmp_path):
    foundry = SkillFoundry(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    candidate = _candidate(
        foundry,
        source_url="https://untrusted.example/skill",
        checksum_sha256="missing",
        license_id="",
    )
    assert candidate.state is FoundryState.QUARANTINED
    assert candidate.activation_allowed is False
    assert any("checksum" in reason.lower() for reason in candidate.reasons)
    assert any("license" in reason.lower() for reason in candidate.reasons)
    assert any("trusted" in reason.lower() for reason in candidate.reasons)


def test_executable_skill_starts_quarantined_and_requires_core_release(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    foundry = SkillFoundry(ledger)
    candidate = _candidate(foundry, has_executable_scripts=True)
    assert candidate.state is FoundryState.QUARANTINED
    assert any("executable" in reason for reason in candidate.reasons)
    with pytest.raises(ValueError, match="invalid skill candidate transition"):
        foundry.record_security_scan(
            candidate.candidate_id, evidence_ref="scan:run:blocked", passed=True
        )
    with pytest.raises(PermissionError, match="not configured"):
        foundry.clear_quarantine(
            candidate.candidate_id,
            approval_ref="core-release-1",
            evidence_ref="review:quarantine:1",
            resolved_reasons=candidate.reasons,
            resolution_summary="Reviewed every quarantine reason.",
        )
    reviewed = SkillFoundry(ledger, approval_verifier=FakeVerifier()).clear_quarantine(
        candidate.candidate_id,
        approval_ref="core-release-1",
        evidence_ref="review:quarantine:1",
        resolved_reasons=candidate.reasons,
        resolution_summary="Reviewed every quarantine reason.",
    )
    assert reviewed.state is FoundryState.DISCOVERED
    assert reviewed.reasons == ()
    assert reviewed.quarantine_released_by == "core_owner"


def test_source_url_rejects_embedded_credentials_query_and_nonstandard_port(tmp_path):
    foundry = SkillFoundry(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    with pytest.raises(ValueError, match="HTTPS URL"):
        _candidate(foundry, source_url="http://agentskills.io/skill")
    with pytest.raises(ValueError, match="query/fragment"):
        _candidate(foundry, source_url="https://agentskills.io/skill?token=abc")
    with pytest.raises(ValueError, match="standard HTTPS port"):
        _candidate(foundry, source_url="https://agentskills.io:444/skill")


def test_failed_scan_rejects_candidate_and_stops_pipeline(tmp_path):
    foundry = SkillFoundry(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    candidate = _candidate(foundry)
    rejected = foundry.record_security_scan(
        candidate.candidate_id,
        evidence_ref="scan:run:failed",
        passed=False,
        reason="critical finding",
    )
    assert rejected.state is FoundryState.REJECTED
    with pytest.raises(ValueError, match="invalid skill candidate transition"):
        foundry.record_sandbox_test(
            candidate.candidate_id, evidence_ref="sandbox:run:never", passed=True
        )


def test_full_admission_requires_core_approval_and_never_installs(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    foundry = SkillFoundry(ledger)
    candidate = _candidate(foundry)
    awaiting = _complete_review(foundry, candidate.candidate_id)
    assert awaiting.state is FoundryState.AWAITING_APPROVAL
    with pytest.raises(PermissionError, match="not configured"):
        foundry.approve(
            candidate.candidate_id,
            approval_ref="core-approval-1",
            evidence_ref="approval:evidence:1",
        )

    approved = SkillFoundry(ledger, approval_verifier=FakeVerifier()).approve(
        candidate.candidate_id,
        approval_ref="core-approval-1",
        evidence_ref="approval:evidence:1",
    )
    assert approved.state is FoundryState.REGISTERABLE
    assert approved.approved_by == "core_owner"
    assert approved.activation_allowed is False
    assert approved.approval_ref_sha256
    assert foundry.summary()["auto_install"] is False
    assert foundry.summary()["auto_activate"] is False


def test_self_approval_is_rejected(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    foundry = SkillFoundry(ledger, approval_verifier=FakeVerifier(actor_id="agnes"))
    candidate = _candidate(foundry)
    _complete_review(foundry, candidate.candidate_id)
    with pytest.raises(PermissionError, match="cannot approve its own"):
        foundry.approve(
            candidate.candidate_id,
            approval_ref="self-approval",
            evidence_ref="approval:evidence:2",
        )


def test_evidence_reference_rejects_query_tokens(tmp_path):
    foundry = SkillFoundry(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    candidate = _candidate(foundry)
    with pytest.raises(ValueError, match="opaque reference"):
        foundry.record_security_scan(
            candidate.candidate_id,
            evidence_ref="https://example.test/scan?token=secret",
            passed=True,
        )


def test_ledger_tampering_blocks_candidate_reads(tmp_path):
    path = tmp_path / "ledger.jsonl"
    foundry = SkillFoundry(AppendOnlyLedger(path))
    _candidate(foundry)
    path.write_text(path.read_text() + '{"tampered":true}\n')
    with pytest.raises(RuntimeError, match="integrity check failed"):
        foundry.list_candidates()


def test_compatibility_requires_distinct_independent_verification_evidence(tmp_path):
    foundry = SkillFoundry(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    candidate = _candidate(foundry)
    foundry.record_security_scan(candidate.candidate_id, evidence_ref="scan:1", passed=True)
    foundry.record_sandbox_test(candidate.candidate_id, evidence_ref="sandbox:1", passed=True)
    foundry.record_benchmark(candidate.candidate_id, evidence_ref="benchmark:1", passed=True)
    with pytest.raises(ValueError, match="independent verification evidence"):
        foundry.record_compatibility(
            candidate.candidate_id, evidence_ref="compatibility:1", passed=True
        )
    with pytest.raises(ValueError, match="distinct evidence"):
        foundry.record_compatibility(
            candidate.candidate_id,
            evidence_ref="compatibility:1",
            independent_verification_ref="compatibility:1",
            passed=True,
        )
