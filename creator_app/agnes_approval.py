from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Protocol

_SELF_ACTORS = frozenset({"agnes", "assistant", "model", "self", "self_verifier"})
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class CoreApprovalDecision:
    """Verified approval result returned by CK-NEXUS Core, never caller assertions."""

    approval_ref: str
    subject_id: str
    action: str
    request_digest: str
    actor_id: str
    approved: bool


class CoreApprovalVerifier(Protocol):
    """Adapter contract for the authoritative CK-NEXUS Core approval service."""

    def verify(
        self,
        approval_ref: str,
        *,
        subject_id: str,
        action: str,
        request_digest: str,
    ) -> CoreApprovalDecision | None: ...


def approval_request_digest(action: str, subject_id: str, payload: dict[str, object]) -> str:
    """Bind approval to the exact evidence, candidate version and requested transition."""
    if not action or not subject_id or not isinstance(payload, dict):
        raise ValueError("approval request requires an action, subject and object payload")
    canonical = json.dumps(
        {"action": action, "subject_id": subject_id, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def require_core_approval(
    verifier: CoreApprovalVerifier | None,
    approval_ref: str,
    *,
    subject_id: str,
    action: str,
    request_digest: str,
) -> CoreApprovalDecision:
    reference = approval_ref.strip()
    if not reference or len(reference) > 512:
        raise ValueError("approval_ref must be a non-empty opaque reference")
    if not _SHA256_RE.fullmatch(request_digest):
        raise ValueError("request_digest must be a SHA-256 digest")
    if verifier is None:
        raise PermissionError("CK-NEXUS Core approval verifier is not configured")
    decision = verifier.verify(
        reference,
        subject_id=subject_id,
        action=action,
        request_digest=request_digest,
    )
    if decision is None or not decision.approved:
        raise PermissionError("CK-NEXUS Core approval was not verified")
    if (
        decision.approval_ref != reference
        or decision.subject_id != subject_id
        or decision.action != action
        or decision.request_digest != request_digest
    ):
        raise PermissionError(
            "CK-NEXUS Core approval does not match the requested action and evidence"
        )
    actor = decision.actor_id.strip()
    if not actor or actor.casefold() in _SELF_ACTORS:
        raise PermissionError("AGNES or a model cannot approve its own action")
    return decision


def approval_reference_digest(approval_ref: str) -> str:
    """Persist only a digest of the opaque approval reference in evidence."""
    return hashlib.sha256(approval_ref.encode("utf-8")).hexdigest()
