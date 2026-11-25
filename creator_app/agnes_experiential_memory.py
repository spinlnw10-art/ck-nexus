from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from creator_app.agnes_approval import (
    CoreApprovalVerifier,
    approval_reference_digest,
    approval_request_digest,
    require_core_approval,
)
from creator_app.agnes_ledger import AppendOnlyLedger


class ExperienceResult(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"
    BLOCKED = "BLOCKED"


class ValidityStatus(StrEnum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VALID = "VALID"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True, slots=True)
class ExperienceEntry:
    experience_id: str
    task_type: str
    context_digest: str
    action_strategy: str
    result: ExperienceResult
    failure_reason: str | None
    lesson: str
    confidence: float
    source_run: str
    evidence_links: tuple[str, ...]
    created_at: str
    validity_status: ValidityStatus
    supersedes: str | None = None
    verified_by: str | None = None
    approval_ref_sha256: str | None = None
    independent_verification_ref: str | None = None
    invalidation_reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "experience_id": self.experience_id,
            "task_type": self.task_type,
            "context_digest": self.context_digest,
            "action_strategy": self.action_strategy,
            "result": self.result.value,
            "failure_reason": self.failure_reason,
            "lesson": self.lesson,
            "confidence": self.confidence,
            "source_run": self.source_run,
            "evidence_links": list(self.evidence_links),
            "created_at": self.created_at,
            "validity_status": self.validity_status.value,
            "supersedes": self.supersedes,
            "verified_by": self.verified_by,
            "approval_ref_sha256": self.approval_ref_sha256,
            "independent_verification_ref": self.independent_verification_ref,
            "invalidation_reason": self.invalidation_reason,
            "execution_grant": False,
            "authority_scope": "NONE",
        }


_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_REF_RE = re.compile(r"[A-Za-z0-9._:/-]{1,256}")
_SECRET_RE = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"(?:api[_-]?key|password|client[_-]?secret|access[_-]?token)\s*[:=]\s*\S+)"
)


def _clean_text(value: str, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    clean = value.strip()
    if not clean or len(clean) > maximum or _SECRET_RE.search(clean):
        raise ValueError(f"{field} is empty, too long, or contains secret-shaped data")
    return clean


def _clean_ref(value: str, field: str = "reference") -> str:
    clean = _clean_text(value, field, 256)
    if not _REF_RE.fullmatch(clean):
        raise ValueError(f"{field} must be an opaque reference")
    return clean


class ExperientialMemory:
    """Append-only lessons; only Core-verified experiences are retrievable as trusted memory."""

    def __init__(
        self,
        ledger: AppendOnlyLedger,
        *,
        approval_verifier: CoreApprovalVerifier | None = None,
    ) -> None:
        self.ledger = ledger
        self.approval_verifier = approval_verifier

    def _events(self) -> list[dict[str, object]]:
        return [
            row
            for row in self.ledger.read_all()
            if str(row.get("event_type", "")).startswith("experience_")
        ]

    def _state(self) -> dict[str, ExperienceEntry]:
        state: dict[str, ExperienceEntry] = {}
        for event in self._events():
            event_type = str(event["event_type"])
            payload = event["payload"]
            experience_id = str(payload["experience_id"])
            if event_type == "experience_recorded":
                state[experience_id] = ExperienceEntry(
                    experience_id=experience_id,
                    task_type=str(payload["task_type"]),
                    context_digest=str(payload["context_digest"]),
                    action_strategy=str(payload["action_strategy"]),
                    result=ExperienceResult(str(payload["result"])),
                    failure_reason=payload.get("failure_reason"),
                    lesson=str(payload["lesson"]),
                    confidence=float(payload["confidence"]),
                    source_run=str(payload["source_run"]),
                    evidence_links=tuple(str(item) for item in payload.get("evidence_links", [])),
                    created_at=str(event["at"]),
                    validity_status=ValidityStatus.PENDING_VERIFICATION,
                    supersedes=payload.get("supersedes"),
                )
                continue
            current = state.get(experience_id)
            if current is None:
                raise RuntimeError("experiential memory ledger references an unknown entry")
            if event_type == "experience_validated":
                state[experience_id] = ExperienceEntry(
                    **{
                        **{
                            field: getattr(current, field) for field in current.__dataclass_fields__
                        },
                        "validity_status": ValidityStatus.VALID,
                        "verified_by": str(payload["verified_by"]),
                        "approval_ref_sha256": str(payload["approval_ref_sha256"]),
                        "independent_verification_ref": str(
                            payload["independent_verification_ref"]
                        ),
                        "evidence_links": tuple(
                            dict.fromkeys(
                                (*current.evidence_links, *payload.get("evidence_links", []))
                            )
                        ),
                    }
                )
            elif event_type == "experience_superseded":
                state[experience_id] = ExperienceEntry(
                    **{
                        **{
                            field: getattr(current, field) for field in current.__dataclass_fields__
                        },
                        "validity_status": ValidityStatus.SUPERSEDED,
                    }
                )
            elif event_type == "experience_invalidated":
                state[experience_id] = ExperienceEntry(
                    **{
                        **{
                            field: getattr(current, field) for field in current.__dataclass_fields__
                        },
                        "validity_status": ValidityStatus.INVALIDATED,
                        "invalidation_reason": str(payload["reason"]),
                    }
                )
        return state

    def get(self, experience_id: str) -> ExperienceEntry:
        try:
            return self._state()[experience_id]
        except KeyError as exc:
            raise KeyError("unknown experience") from exc

    def list_entries(self) -> list[ExperienceEntry]:
        return sorted(self._state().values(), key=lambda item: item.created_at)

    def record_experience(
        self,
        *,
        task_type: str,
        context_digest: str,
        action_strategy: str,
        result: ExperienceResult | str,
        lesson: str,
        confidence: float,
        source_run: str,
        evidence_links: tuple[str, ...] | list[str],
        failure_reason: str | None = None,
        supersedes: str | None = None,
    ) -> ExperienceEntry:
        clean_task = _clean_text(task_type, "task_type", 80)
        digest = context_digest.strip().lower() if isinstance(context_digest, str) else ""
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError("context_digest must be a SHA-256 digest; raw context is not stored")
        clean_strategy = _clean_text(action_strategy, "action_strategy", 1200)
        clean_lesson = _clean_text(lesson, "lesson", 2000)
        clean_source = _clean_ref(source_run, "source_run")
        try:
            clean_result = ExperienceResult(str(result))
        except ValueError as exc:
            raise ValueError("result must be SUCCESS, PARTIAL, FAILURE, or BLOCKED") from exc
        score = float(confidence)
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        clean_failure = (
            _clean_text(failure_reason, "failure_reason", 1000) if failure_reason else None
        )
        clean_links = tuple(
            dict.fromkeys(_clean_ref(item, "evidence_link") for item in evidence_links)
        )
        if not clean_links:
            raise ValueError("at least one evidence link is required")
        clean_supersedes = _clean_ref(supersedes, "supersedes") if supersedes else None
        experience_id = f"experience_{uuid4().hex}"
        self.ledger.append(
            "experience_recorded",
            {
                "experience_id": experience_id,
                "task_type": clean_task,
                "context_digest": digest,
                "action_strategy": clean_strategy,
                "result": clean_result.value,
                "failure_reason": clean_failure,
                "lesson": clean_lesson,
                "confidence": score,
                "source_run": clean_source,
                "evidence_links": list(clean_links),
                "supersedes": clean_supersedes,
                "validity_status": ValidityStatus.PENDING_VERIFICATION.value,
                "raw_context_stored": False,
                "execution_grant": False,
                "authority_scope": "NONE",
            },
        )
        return self.get(experience_id)

    def validate_provenance(
        self,
        experience_id: str,
        *,
        approval_ref: str,
        evidence_links: tuple[str, ...] | list[str],
        independent_verification_ref: str,
    ) -> ExperienceEntry:
        current = self.get(experience_id)
        if current.validity_status is not ValidityStatus.PENDING_VERIFICATION:
            raise ValueError("only pending experiences can be validated")
        clean_links = tuple(
            dict.fromkeys(_clean_ref(item, "evidence_link") for item in evidence_links)
        )
        if not clean_links:
            raise ValueError("provenance validation requires evidence links")
        independent_ref = _clean_ref(independent_verification_ref, "independent_verification_ref")
        if independent_ref == current.source_run or independent_ref in current.evidence_links:
            raise ValueError("independent verification must be a distinct evidence reference")
        action = "memory.validate_experience"
        request_payload = {
            "experience_id": experience_id,
            "context_digest": current.context_digest,
            "evidence_links": list(clean_links),
            "independent_verification_ref": independent_ref,
        }
        request_digest = approval_request_digest(action, experience_id, request_payload)
        decision = require_core_approval(
            self.approval_verifier,
            approval_ref,
            subject_id=experience_id,
            action=action,
            request_digest=request_digest,
        )
        self.ledger.append(
            "experience_validated",
            {
                "experience_id": experience_id,
                "verified_by": decision.actor_id,
                "approval_ref_sha256": approval_reference_digest(approval_ref),
                "approval_request_digest": request_digest,
                "evidence_links": list(clean_links),
                "independent_verification_ref": independent_ref,
                "validity_status": ValidityStatus.VALID.value,
                "execution_grant": False,
                "authority_scope": "NONE",
            },
        )
        return self.get(experience_id)

    def retrieve_relevant(self, task_type: str, *, limit: int = 10) -> list[ExperienceEntry]:
        clean_task = _clean_text(task_type, "task_type", 80)
        bounded = max(1, min(int(limit), 50))
        matches = [
            entry
            for entry in self.list_entries()
            if entry.task_type == clean_task and entry.validity_status is ValidityStatus.VALID
        ]
        return sorted(matches, key=lambda item: (item.confidence, item.created_at), reverse=True)[
            :bounded
        ]

    def supersede_experience(
        self,
        old_id: str,
        new_id: str,
        *,
        approval_ref: str,
        evidence_ref: str,
    ) -> ExperienceEntry:
        old = self.get(old_id)
        new = self.get(new_id)
        if old.validity_status is not ValidityStatus.VALID:
            raise ValueError("only valid experiences can be superseded")
        if new.validity_status is not ValidityStatus.VALID or new.supersedes != old_id:
            raise ValueError(
                "replacement must be independently validated and reference the old entry"
            )
        clean_evidence = _clean_ref(evidence_ref, "evidence_ref")
        subject = f"{old_id}->{new_id}"
        action = "memory.supersede_experience"
        request_payload = {
            "old_id": old_id,
            "new_id": new_id,
            "old_context_digest": old.context_digest,
            "new_context_digest": new.context_digest,
            "evidence_ref": clean_evidence,
        }
        request_digest = approval_request_digest(action, subject, request_payload)
        decision = require_core_approval(
            self.approval_verifier,
            approval_ref,
            subject_id=subject,
            action=action,
            request_digest=request_digest,
        )
        self.ledger.append(
            "experience_superseded",
            {
                "experience_id": old_id,
                "replacement_id": new_id,
                "evidence_ref": clean_evidence,
                "verified_by": decision.actor_id,
                "approval_ref_sha256": approval_reference_digest(approval_ref),
                "approval_request_digest": request_digest,
                "validity_status": ValidityStatus.SUPERSEDED.value,
                "authority_scope": "NONE",
            },
        )
        return self.get(old_id)

    def invalidate_experience(
        self,
        experience_id: str,
        *,
        reason: str,
        approval_ref: str,
        evidence_ref: str,
    ) -> ExperienceEntry:
        current = self.get(experience_id)
        if current.validity_status is not ValidityStatus.VALID:
            raise ValueError("only valid experiences can be invalidated")
        clean_reason = _clean_text(reason, "reason", 1000)
        clean_evidence = _clean_ref(evidence_ref, "evidence_ref")
        action = "memory.invalidate_experience"
        request_payload = {
            "experience_id": experience_id,
            "context_digest": current.context_digest,
            "reason": clean_reason,
            "evidence_ref": clean_evidence,
        }
        request_digest = approval_request_digest(action, experience_id, request_payload)
        decision = require_core_approval(
            self.approval_verifier,
            approval_ref,
            subject_id=experience_id,
            action=action,
            request_digest=request_digest,
        )
        self.ledger.append(
            "experience_invalidated",
            {
                "experience_id": experience_id,
                "reason": clean_reason,
                "evidence_ref": clean_evidence,
                "verified_by": decision.actor_id,
                "approval_ref_sha256": approval_reference_digest(approval_ref),
                "approval_request_digest": request_digest,
                "validity_status": ValidityStatus.INVALIDATED.value,
                "authority_scope": "NONE",
            },
        )
        return self.get(experience_id)

    def build_provenance_graph(self) -> dict[str, object]:
        entries = self.list_entries()
        nodes = [
            {
                "id": entry.experience_id,
                "task_type": entry.task_type,
                "result": entry.result.value,
                "validity_status": entry.validity_status.value,
                "context_digest": entry.context_digest,
                "lesson_digest": hashlib.sha256(entry.lesson.encode("utf-8")).hexdigest(),
                "source_run": entry.source_run,
                "evidence_links": list(entry.evidence_links),
                "independent_verification_ref": entry.independent_verification_ref,
            }
            for entry in entries
        ]
        edges = []
        for entry in entries:
            if entry.supersedes:
                edges.append(
                    {
                        "source": entry.experience_id,
                        "target": entry.supersedes,
                        "kind": "supersedes",
                    }
                )
            for ref in entry.evidence_links:
                edges.append({"source": entry.experience_id, "target": ref, "kind": "supported_by"})
        return {
            "nodes": nodes,
            "edges": edges,
            "ledger": self.ledger.verify().as_dict(),
            "authority_scope": "NONE",
        }

    def summary(self) -> dict[str, object]:
        entries = self.list_entries()
        counts = {status.value: 0 for status in ValidityStatus}
        for entry in entries:
            counts[entry.validity_status.value] += 1
        return {
            "experience_count": len(entries),
            "state_counts": counts,
            "ledger": self.ledger.verify().as_dict(),
            "approval_verifier_configured": self.approval_verifier is not None,
            "raw_context_stored": False,
            "execution_grant": False,
            "authority_scope": "NONE",
        }
