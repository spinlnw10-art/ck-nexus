from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from creator_app.agnes_ledger import AppendOnlyLedger
from creator_app.privacy_firewall.firewall import redact_value

from .manifest import ImmutableExecutionManifest
from .result import SkillExecutionResult


def redact(value: Any) -> Any:
    """Compatibility facade over the shared privacy firewall redactor."""
    return redact_value(value)


@dataclass(slots=True)
class EvidenceBuilder:
    ledger: AppendOnlyLedger

    def pre_audit(self, manifest: ImmutableExecutionManifest) -> str:
        row = self.ledger.append("execution_pre_audit", manifest.as_dict())
        return str(row["hash"])

    def finalize(
        self,
        manifest: ImmutableExecutionManifest,
        result: SkillExecutionResult,
    ) -> str:
        payload = {
            "manifest_hash": manifest.manifest_hash,
            "execution_id": manifest.execution_id,
            "skill_id": manifest.skill_id,
            "status": result.status.value,
            "output": redact(result.output),
            "artifacts": list(result.artifacts),
            "error": redact(result.error),
            "duration_ms": result.duration_ms,
        }
        row = self.ledger.append("execution_final_audit", payload)
        return str(row["hash"])
