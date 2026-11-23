from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum
from urllib.parse import urlparse
from uuid import uuid4

from creator_app.agnes_approval import (
    CoreApprovalVerifier,
    approval_reference_digest,
    approval_request_digest,
    require_core_approval,
)
from creator_app.agnes_discovery import SkillDiscoveryPolicy
from creator_app.agnes_ledger import AppendOnlyLedger


class FoundryState(StrEnum):
    DISCOVERED = "DISCOVERED"
    QUARANTINED = "QUARANTINED"
    SCANNED = "SCANNED"
    SANDBOX_TESTED = "SANDBOX_TESTED"
    BENCHMARKED = "BENCHMARKED"
    COMPATIBLE = "COMPATIBLE"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    REGISTERABLE = "REGISTERABLE"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class SkillCandidate:
    candidate_id: str
    skill_id: str
    version: str
    source_url: str
    checksum_sha256: str
    license_id: str
    has_executable_scripts: bool
    requests_credentials: bool
    requests_network: bool
    readiness_score: float
    state: FoundryState
    reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    approved_by: str | None = None
    approval_ref_sha256: str | None = None
    independent_verification_ref: str | None = None
    quarantine_released_by: str | None = None
    quarantine_approval_ref_sha256: str | None = None

    @property
    def activation_allowed(self) -> bool:
        return False

    @property
    def auto_install(self) -> bool:
        return False

    @property
    def auto_activate(self) -> bool:
        return False

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "skill_id": self.skill_id,
            "version": self.version,
            "source_url": self.source_url,
            "checksum_sha256": self.checksum_sha256,
            "license_id": self.license_id,
            "has_executable_scripts": self.has_executable_scripts,
            "requests_credentials": self.requests_credentials,
            "requests_network": self.requests_network,
            "readiness_score": self.readiness_score,
            "state": self.state.value,
            "reasons": list(self.reasons),
            "evidence_refs": list(self.evidence_refs),
            "approved_by": self.approved_by,
            "approval_ref_sha256": self.approval_ref_sha256,
            "independent_verification_ref": self.independent_verification_ref,
            "quarantine_released_by": self.quarantine_released_by,
            "quarantine_approval_ref_sha256": self.quarantine_approval_ref_sha256,
            "activation_allowed": False,
            "auto_install": False,
            "auto_activate": False,
            "authority_scope": "NONE",
        }


_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SECRET_RE = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"(?:api[_-]?key|password|client[_-]?secret|access[_-]?token)\s*[:=]\s*\S+)"
)


def _safe_text(value: str, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    result = value.strip()
    if not result or len(result) > maximum or _SECRET_RE.search(result):
        raise ValueError(f"{field} is empty, too long, or contains secret-shaped data")
    return result


def _evidence_ref(value: str) -> str:
    ref = _safe_text(value, "evidence_ref", 256)
    if not re.fullmatch(r"[A-Za-z0-9._:/-]+", ref):
        raise ValueError("evidence_ref must be an opaque reference")
    return ref


def _validate_source_url(source_url: str) -> None:
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("source_url must be an HTTPS URL without embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("source_url query/fragment is not accepted for a canonical source")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("source_url port is invalid") from exc
    if port not in (None, 443):
        raise ValueError("source_url must use the standard HTTPS port")


def _normalize_checksum(value: str) -> tuple[str, bool]:
    checksum = value.strip().lower() if isinstance(value, str) else ""
    return checksum, bool(_SHA256_RE.fullmatch(checksum))


def _normalize_license(value: str) -> str:
    license_id = _safe_text(value, "license_id", 128) if value else ""
    if license_id and not re.fullmatch(r"[A-Za-z0-9.+() -]{1,128}", license_id):
        raise ValueError("license_id format is invalid")
    return license_id


def _discovery_reasons(
    review_reasons: tuple[str, ...] | list[str], checksum_valid: bool, license_id: str
) -> list[str]:
    reasons = list(review_reasons)
    if not checksum_valid:
        reasons.append("SHA-256 checksum is missing or malformed")
    if not license_id:
        reasons.append("license identifier is missing")
    return reasons


def _discovery_readiness(
    checksum_valid: bool,
    license_known: bool,
    reasons: list[str],
    has_executable_scripts: bool,
    requests_credentials: bool,
    requests_network: bool,
) -> float:
    score = 0.1
    score += 0.2 if checksum_valid else 0.0
    score += 0.15 if license_known else 0.0
    score += 0.2 if not reasons else 0.0
    score += 0.1 if not has_executable_scripts else 0.0
    score += 0.1 if not requests_credentials else 0.0
    score += 0.1 if not requests_network else 0.0
    return round(min(score, 1.0), 3)


class SkillFoundry:
    """Fail-closed skill admission; REGISTERABLE never means installed or active."""

    def __init__(
        self,
        ledger: AppendOnlyLedger,
        *,
        discovery: SkillDiscoveryPolicy | None = None,
        approval_verifier: CoreApprovalVerifier | None = None,
    ) -> None:
        self.ledger = ledger
        self.discovery = discovery or SkillDiscoveryPolicy()
        self.approval_verifier = approval_verifier

    def _events(self) -> list[dict[str, object]]:
        return [
            row
            for row in self.ledger.read_all()
            if str(row.get("event_type", "")).startswith("skill_foundry_")
        ]

    def _state(self) -> dict[str, SkillCandidate]:
        state: dict[str, SkillCandidate] = {}
        for event in self._events():
            event_type = str(event["event_type"])
            payload = event["payload"]
            candidate_id = str(payload["candidate_id"])
            if event_type == "skill_foundry_discovered":
                state[candidate_id] = SkillCandidate(
                    candidate_id=candidate_id,
                    skill_id=str(payload["skill_id"]),
                    version=str(payload["version"]),
                    source_url=str(payload["source_url"]),
                    checksum_sha256=str(payload["checksum_sha256"]),
                    license_id=str(payload["license_id"]),
                    has_executable_scripts=bool(payload["has_executable_scripts"]),
                    requests_credentials=bool(payload["requests_credentials"]),
                    requests_network=bool(payload["requests_network"]),
                    readiness_score=float(payload["readiness_score"]),
                    state=FoundryState(str(payload["state"])),
                    reasons=tuple(str(item) for item in payload.get("reasons", [])),
                    evidence_refs=(),
                )
                continue
            current = state.get(candidate_id)
            if current is None:
                raise RuntimeError("skill foundry ledger references an unknown candidate")
            evidence = tuple(
                dict.fromkeys((*current.evidence_refs, *payload.get("evidence_refs", [])))
            )
            state[candidate_id] = replace(
                current,
                state=FoundryState(str(payload.get("state", current.state.value))),
                readiness_score=float(payload.get("readiness_score", current.readiness_score)),
                reasons=tuple(str(item) for item in payload.get("reasons", current.reasons)),
                evidence_refs=evidence,
                approved_by=payload.get("approved_by", current.approved_by),
                approval_ref_sha256=payload.get("approval_ref_sha256", current.approval_ref_sha256),
                independent_verification_ref=payload.get(
                    "independent_verification_ref", current.independent_verification_ref
                ),
                quarantine_released_by=payload.get(
                    "quarantine_released_by", current.quarantine_released_by
                ),
                quarantine_approval_ref_sha256=payload.get(
                    "quarantine_approval_ref_sha256", current.quarantine_approval_ref_sha256
                ),
            )
        return state

    def get_candidate(self, candidate_id: str) -> SkillCandidate:
        try:
            return self._state()[candidate_id]
        except KeyError as exc:
            raise KeyError("unknown skill candidate") from exc

    def list_candidates(self) -> list[SkillCandidate]:
        return sorted(self._state().values(), key=lambda item: item.candidate_id)

    def clear_quarantine(
        self,
        candidate_id: str,
        *,
        approval_ref: str,
        evidence_ref: str,
        resolved_reasons: tuple[str, ...] | list[str],
        resolution_summary: str,
    ) -> SkillCandidate:
        current = self.get_candidate(candidate_id)
        if current.state is not FoundryState.QUARANTINED:
            raise ValueError("candidate is not quarantined")
        resolved = tuple(
            dict.fromkeys(_safe_text(item, "resolved_reason", 512) for item in resolved_reasons)
        )
        if set(resolved) != set(current.reasons):
            raise ValueError("all quarantine reasons must be explicitly resolved")
        evidence = _evidence_ref(evidence_ref)
        summary = _safe_text(resolution_summary, "resolution_summary", 1000)
        action = "skill.quarantine.release"
        request_payload = {
            "candidate_id": candidate_id,
            "checksum_sha256": current.checksum_sha256,
            "evidence_ref": evidence,
            "resolved_reasons": list(resolved),
            "resolution_summary": summary,
        }
        request_digest = approval_request_digest(action, candidate_id, request_payload)
        decision = require_core_approval(
            self.approval_verifier,
            approval_ref,
            subject_id=candidate_id,
            action=action,
            request_digest=request_digest,
        )
        self.ledger.append(
            "skill_foundry_quarantine_released",
            {
                "candidate_id": candidate_id,
                "state": FoundryState.DISCOVERED.value,
                "readiness_score": current.readiness_score,
                "reasons": [],
                "evidence_refs": [evidence],
                "resolution_summary": summary,
                "resolved_reasons": list(resolved),
                "quarantine_released_by": decision.actor_id,
                "quarantine_approval_ref_sha256": approval_reference_digest(approval_ref),
                "approval_request_digest": request_digest,
                "auto_install": False,
                "auto_activate": False,
                "authority_scope": "NONE",
            },
        )
        return self.get_candidate(candidate_id)

    def discover(
        self,
        *,
        skill_id: str,
        version: str,
        source_url: str,
        checksum_sha256: str,
        license_id: str,
        has_executable_scripts: bool = False,
        requests_credentials: bool = False,
        requests_network: bool = False,
    ) -> SkillCandidate:
        clean_id = _safe_text(skill_id, "skill_id", 128).lower()
        if not _SKILL_ID_RE.fullmatch(clean_id):
            raise ValueError("skill_id format is invalid")
        clean_version = _safe_text(version, "version", 64)
        clean_url = _safe_text(source_url, "source_url", 2048)
        _validate_source_url(clean_url)
        clean_checksum, checksum_valid = _normalize_checksum(checksum_sha256)
        clean_license = _normalize_license(license_id)
        review = self.discovery.review_candidate(
            source_url=clean_url,
            checksum_present=checksum_valid,
            license_known=bool(clean_license),
            has_executable_scripts=has_executable_scripts,
            requests_credentials=requests_credentials,
            requests_network=requests_network,
        )
        reasons = _discovery_reasons(review.reasons, checksum_valid, clean_license)
        candidate_id = f"skill_candidate_{uuid4().hex}"
        state = FoundryState.QUARANTINED if reasons else FoundryState.DISCOVERED
        readiness = _discovery_readiness(
            checksum_valid,
            bool(clean_license),
            reasons,
            has_executable_scripts,
            requests_credentials,
            requests_network,
        )
        payload = {
            "candidate_id": candidate_id,
            "skill_id": clean_id,
            "version": clean_version,
            "source_url": clean_url,
            "checksum_sha256": clean_checksum,
            "license_id": clean_license,
            "has_executable_scripts": bool(has_executable_scripts),
            "requests_credentials": bool(requests_credentials),
            "requests_network": bool(requests_network),
            "readiness_score": readiness,
            "state": state.value,
            "reasons": reasons,
            "auto_install": False,
            "auto_activate": False,
            "authority_scope": "NONE",
        }
        self.ledger.append("skill_foundry_discovered", payload)
        return self.get_candidate(candidate_id)

    def _transition(
        self,
        candidate_id: str,
        *,
        allowed: tuple[FoundryState, ...],
        target: FoundryState,
        evidence_ref: str,
        passed: bool,
        reason: str | None = None,
        score_delta: float = 0.0,
    ) -> SkillCandidate:
        current = self.get_candidate(candidate_id)
        if current.state not in allowed:
            raise ValueError(f"invalid skill candidate transition from {current.state.value}")
        evidence = _evidence_ref(evidence_ref)
        clean_reason = _safe_text(reason, "reason", 512) if reason else None
        next_state = target if passed else FoundryState.REJECTED
        reasons = () if passed else (clean_reason or "assessment failed",)
        readiness = min(1.0, current.readiness_score + (score_delta if passed else 0.0))
        self.ledger.append(
            "skill_foundry_assessment",
            {
                "candidate_id": candidate_id,
                "state": next_state.value,
                "readiness_score": round(readiness, 3),
                "reasons": list(reasons),
                "evidence_refs": [evidence],
                "passed": bool(passed),
                "auto_install": False,
                "auto_activate": False,
                "authority_scope": "NONE",
            },
        )
        return self.get_candidate(candidate_id)

    def record_security_scan(
        self, candidate_id: str, *, evidence_ref: str, passed: bool, reason: str | None = None
    ) -> SkillCandidate:
        return self._transition(
            candidate_id,
            allowed=(FoundryState.DISCOVERED,),
            target=FoundryState.SCANNED,
            evidence_ref=evidence_ref,
            passed=passed,
            reason=reason,
            score_delta=0.2,
        )

    def record_sandbox_test(
        self, candidate_id: str, *, evidence_ref: str, passed: bool, reason: str | None = None
    ) -> SkillCandidate:
        return self._transition(
            candidate_id,
            allowed=(FoundryState.SCANNED,),
            target=FoundryState.SANDBOX_TESTED,
            evidence_ref=evidence_ref,
            passed=passed,
            reason=reason,
            score_delta=0.2,
        )

    def record_benchmark(
        self, candidate_id: str, *, evidence_ref: str, passed: bool, reason: str | None = None
    ) -> SkillCandidate:
        return self._transition(
            candidate_id,
            allowed=(FoundryState.SANDBOX_TESTED,),
            target=FoundryState.BENCHMARKED,
            evidence_ref=evidence_ref,
            passed=passed,
            reason=reason,
            score_delta=0.15,
        )

    def record_compatibility(
        self,
        candidate_id: str,
        *,
        evidence_ref: str,
        passed: bool,
        independent_verification_ref: str | None = None,
        reason: str | None = None,
    ) -> SkillCandidate:
        independent_ref = None
        if passed:
            if not independent_verification_ref:
                raise ValueError("independent verification evidence is required")
            independent_ref = _evidence_ref(independent_verification_ref)
            if independent_ref == _evidence_ref(evidence_ref):
                raise ValueError("independent verification must use a distinct evidence reference")
        result = self._transition(
            candidate_id,
            allowed=(FoundryState.BENCHMARKED,),
            target=FoundryState.COMPATIBLE,
            evidence_ref=evidence_ref,
            passed=passed,
            reason=reason,
            score_delta=0.15,
        )
        if passed:
            self.ledger.append(
                "skill_foundry_assessment",
                {
                    "candidate_id": candidate_id,
                    "state": FoundryState.AWAITING_APPROVAL.value,
                    "readiness_score": result.readiness_score,
                    "reasons": [],
                    "evidence_refs": [independent_ref] if independent_ref else [],
                    "independent_verification_ref": independent_ref,
                    "passed": True,
                    "auto_install": False,
                    "auto_activate": False,
                    "authority_scope": "NONE",
                },
            )
            return self.get_candidate(candidate_id)
        return result

    def approve(self, candidate_id: str, *, approval_ref: str, evidence_ref: str) -> SkillCandidate:
        current = self.get_candidate(candidate_id)
        if current.state is not FoundryState.AWAITING_APPROVAL:
            raise ValueError("candidate is not awaiting Core approval")
        if not current.independent_verification_ref:
            raise ValueError("independent verification evidence is required before approval")
        evidence = _evidence_ref(evidence_ref)
        action = "skill.register"
        request_payload = {
            "candidate_id": candidate_id,
            "checksum_sha256": current.checksum_sha256,
            "license_id": current.license_id,
            "evidence_ref": evidence,
            "independent_verification_ref": current.independent_verification_ref,
        }
        request_digest = approval_request_digest(action, candidate_id, request_payload)
        decision = require_core_approval(
            self.approval_verifier,
            approval_ref,
            subject_id=candidate_id,
            action=action,
            request_digest=request_digest,
        )
        self.ledger.append(
            "skill_foundry_registered",
            {
                "candidate_id": candidate_id,
                "state": FoundryState.REGISTERABLE.value,
                "readiness_score": current.readiness_score,
                "reasons": [],
                "evidence_refs": [evidence],
                "approved_by": decision.actor_id,
                "approval_ref_sha256": approval_reference_digest(approval_ref),
                "approval_request_digest": request_digest,
                "registration_requires_explicit_action": True,
                "activation_allowed": False,
                "auto_install": False,
                "auto_activate": False,
                "authority_scope": "NONE",
            },
        )
        return self.get_candidate(candidate_id)

    def summary(self) -> dict[str, object]:
        candidates = self.list_candidates()
        counts = {state.value: 0 for state in FoundryState}
        for candidate in candidates:
            counts[candidate.state.value] += 1
        verification = self.ledger.verify()
        return {
            "candidate_count": len(candidates),
            "state_counts": counts,
            "ledger": verification.as_dict(),
            "approval_verifier_configured": self.approval_verifier is not None,
            "auto_install": False,
            "auto_activate": False,
            "authority_scope": "NONE",
        }
