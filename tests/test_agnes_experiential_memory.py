import hashlib

import pytest

from creator_app.agnes_approval import CoreApprovalDecision
from creator_app.agnes_experiential_memory import (
    ExperienceResult,
    ExperientialMemory,
    ValidityStatus,
)
from creator_app.agnes_ledger import AppendOnlyLedger


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


def _record(memory, **overrides):
    values = {
        "task_type": "security",
        "context_digest": hashlib.sha256(b"synthetic task context").hexdigest(),
        "action_strategy": "Run static checks and request independent review.",
        "result": ExperienceResult.SUCCESS,
        "lesson": "Require independent verification before accepting a security fix.",
        "confidence": 0.9,
        "source_run": "run:synthetic:1",
        "evidence_links": ["evidence:test:1"],
    }
    values.update(overrides)
    return memory.record_experience(**values)


def test_new_experience_is_pending_and_raw_context_is_not_stored(tmp_path):
    path = tmp_path / "ledger.jsonl"
    memory = ExperientialMemory(AppendOnlyLedger(path))
    entry = _record(memory)
    assert entry.validity_status is ValidityStatus.PENDING_VERIFICATION
    assert memory.retrieve_relevant("security") == []
    ledger_text = path.read_text()
    assert "synthetic task context" not in ledger_text
    assert entry.context_digest in ledger_text
    assert entry.verified_by is None


def test_validation_requires_core_approval_and_independent_evidence(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    memory = ExperientialMemory(ledger)
    entry = _record(memory)
    with pytest.raises(PermissionError, match="not configured"):
        memory.validate_provenance(
            entry.experience_id,
            approval_ref="approval-1",
            evidence_links=["evidence:independent:1"],
            independent_verification_ref="review:independent:1",
        )

    verified = ExperientialMemory(ledger, approval_verifier=FakeVerifier()).validate_provenance(
        entry.experience_id,
        approval_ref="approval-1",
        evidence_links=["evidence:independent:1"],
        independent_verification_ref="review:independent:1",
    )
    assert verified.validity_status is ValidityStatus.VALID
    assert verified.verified_by == "core_owner"
    assert len(verified.approval_ref_sha256) == 64
    assert [item.experience_id for item in memory.retrieve_relevant("security")] == [
        entry.experience_id
    ]


def test_verified_memory_is_retrievable_only_after_core_validation(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    memory = ExperientialMemory(ledger, approval_verifier=FakeVerifier())
    entry = _record(memory)
    memory.validate_provenance(
        entry.experience_id,
        approval_ref="approval-2",
        evidence_links=["evidence:review:2"],
        independent_verification_ref="review:independent:2",
    )
    results = memory.retrieve_relevant("security")
    assert [item.experience_id for item in results] == [entry.experience_id]


def test_self_verification_is_rejected(tmp_path):
    memory = ExperientialMemory(
        AppendOnlyLedger(tmp_path / "ledger.jsonl"),
        approval_verifier=FakeVerifier(actor_id="self_verifier"),
    )
    entry = _record(memory)
    with pytest.raises(PermissionError, match="cannot approve its own"):
        memory.validate_provenance(
            entry.experience_id,
            approval_ref="self-approval",
            evidence_links=["evidence:review:3"],
            independent_verification_ref="review:independent:3",
        )


def test_supersession_requires_two_valid_entries_and_core_approval(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    memory = ExperientialMemory(ledger, approval_verifier=FakeVerifier())
    old = _record(memory)
    memory.validate_provenance(
        old.experience_id,
        approval_ref="approval-old",
        evidence_links=["evidence:review:old"],
        independent_verification_ref="review:independent:old",
    )
    new = _record(
        memory, supersedes=old.experience_id, lesson="Use a stricter independent review gate."
    )
    memory.validate_provenance(
        new.experience_id,
        approval_ref="approval-new",
        evidence_links=["evidence:review:new"],
        independent_verification_ref="review:independent:new",
    )
    superseded = memory.supersede_experience(
        old.experience_id,
        new.experience_id,
        approval_ref="approval-supersede",
        evidence_ref="evidence:supersession:1",
    )
    assert superseded.validity_status is ValidityStatus.SUPERSEDED
    assert [item.experience_id for item in memory.retrieve_relevant("security")] == [
        new.experience_id
    ]


def test_invalidation_requires_core_approval(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    memory = ExperientialMemory(ledger, approval_verifier=FakeVerifier())
    entry = _record(memory)
    memory.validate_provenance(
        entry.experience_id,
        approval_ref="approval-valid",
        evidence_links=["evidence:review:valid"],
        independent_verification_ref="review:independent:valid",
    )
    invalidated = memory.invalidate_experience(
        entry.experience_id,
        reason="later evidence disproved this lesson",
        approval_ref="approval-invalidate",
        evidence_ref="evidence:contradiction:1",
    )
    assert invalidated.validity_status is ValidityStatus.INVALIDATED
    assert memory.retrieve_relevant("security") == []


def test_secret_shaped_lessons_and_invalid_context_digest_are_rejected(tmp_path):
    memory = ExperientialMemory(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    secret_like = "s" + "k" + "-" + ("x" * 24)
    with pytest.raises(ValueError, match="secret-shaped"):
        _record(memory, lesson=secret_like)
    with pytest.raises(ValueError, match="SHA-256"):
        _record(memory, context_digest="not-a-digest")


def test_provenance_graph_contains_digests_not_raw_context(tmp_path):
    memory = ExperientialMemory(AppendOnlyLedger(tmp_path / "ledger.jsonl"))
    entry = _record(memory)
    graph = memory.build_provenance_graph()
    assert graph["nodes"][0]["id"] == entry.experience_id
    assert graph["nodes"][0]["lesson_digest"]
    assert graph["authority_scope"] == "NONE"
    assert graph["ledger"]["valid"] is True


def test_tampered_memory_ledger_fails_closed(tmp_path):
    path = tmp_path / "ledger.jsonl"
    memory = ExperientialMemory(AppendOnlyLedger(path))
    _record(memory)
    path.write_text(path.read_text() + '{"tampered":true}\n')
    with pytest.raises(RuntimeError, match="integrity check failed"):
        memory.list_entries()
