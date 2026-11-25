import pytest

from creator_app.agnes_approval import (
    CoreApprovalDecision,
    approval_reference_digest,
    approval_request_digest,
    require_core_approval,
)


class FakeVerifier:
    def __init__(self, actor_id="core_owner", approved=True):
        self.actor_id = actor_id
        self.approved = approved

    def verify(self, approval_ref, *, subject_id, action, request_digest):
        if not self.approved:
            return None
        return CoreApprovalDecision(
            approval_ref=approval_ref,
            subject_id=subject_id,
            action=action,
            request_digest=request_digest,
            actor_id=self.actor_id,
            approved=True,
        )


def test_core_approval_requires_configured_verifier():
    with pytest.raises(PermissionError, match="not configured"):
        require_core_approval(
            None,
            "approval-1",
            subject_id="candidate-1",
            action="skill.register",
            request_digest="a" * 64,
        )


def test_core_approval_rejects_self_approval():
    with pytest.raises(PermissionError, match="cannot approve its own"):
        require_core_approval(
            FakeVerifier(actor_id="AGNES"),
            "approval-1",
            subject_id="candidate-1",
            action="skill.register",
            request_digest="a" * 64,
        )


def test_core_approval_binds_subject_and_action():
    class WrongSubjectVerifier:
        def verify(self, approval_ref, *, subject_id, action, request_digest):
            return CoreApprovalDecision(
                approval_ref=approval_ref,
                subject_id="other-subject",
                action=action,
                request_digest=request_digest,
                actor_id="core_owner",
                approved=True,
            )

    with pytest.raises(PermissionError, match="does not match"):
        require_core_approval(
            WrongSubjectVerifier(),
            "approval-1",
            subject_id="candidate-1",
            action="skill.register",
            request_digest="a" * 64,
        )


def test_approval_reference_is_stored_as_digest():
    assert approval_reference_digest("opaque-ref") != "opaque-ref"
    assert len(approval_reference_digest("opaque-ref")) == 64


def test_approval_request_digest_binds_exact_payload():
    first = approval_request_digest(
        "skill.register", "candidate-1", {"checksum": "a" * 64, "evidence": "review:1"}
    )
    changed = approval_request_digest(
        "skill.register", "candidate-1", {"checksum": "a" * 64, "evidence": "review:2"}
    )
    assert first != changed
    assert len(first) == 64


def test_core_approval_rejects_evidence_digest_mismatch():
    class WrongDigestVerifier:
        def verify(self, approval_ref, *, subject_id, action, request_digest):
            return CoreApprovalDecision(
                approval_ref=approval_ref,
                subject_id=subject_id,
                action=action,
                request_digest="b" * 64,
                actor_id="core_owner",
                approved=True,
            )

    with pytest.raises(PermissionError, match="action and evidence"):
        require_core_approval(
            WrongDigestVerifier(),
            "approval-1",
            subject_id="candidate-1",
            action="skill.register",
            request_digest="a" * 64,
        )
