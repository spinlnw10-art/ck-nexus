from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).resolve().parents[1] / "capabilities" / "system-skills.catalog.json"
VALID_DECISIONS = {"REUSE", "EXTEND", "NEW_SKILL", "EVALUATE", "BLOCKED_BY_EVIDENCE", "REJECT"}
VALID_RISKS = {
    "read_only",
    "local_reversible",
    "guarded",
    "credentialed",
    "external_side_effect",
    "paid",
    "production",
    "unknown",
}
AUTO_SAFE_RISKS = {"read_only", "local_reversible"}
_SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    skill_id: str
    decision: str
    risk: str
    auto_safe: bool
    next_action: str
    reason: str
    requires_core_approval: bool
    requires_cost_approval: bool
    auto_install: bool = False
    auto_activate: bool = False
    authority_scope: str = "NONE"


def _validate_policy(policy: Any) -> None:
    if not isinstance(policy, dict):
        raise ValueError("catalog adoption policy must be an object")
    for field in ("auto_install", "auto_activate", "auto_merge", "auto_deploy"):
        if policy.get(field) is not False:
            raise ValueError(f"adoption policy must keep {field}=false")
    if policy.get("authority_scope") != "NONE":
        raise ValueError("external capability catalog cannot carry authority")


def _validate_skill(item: Any) -> str:
    if not isinstance(item, dict):
        raise ValueError("each skill entry must be an object")
    skill_id = str(item.get("id", ""))
    if not _SKILL_ID.fullmatch(skill_id):
        raise ValueError("catalog requires valid non-empty skill ids")
    if item.get("decision") not in VALID_DECISIONS:
        raise ValueError(f"invalid decision for {skill_id}")
    if item.get("risk") not in VALID_RISKS:
        raise ValueError(f"invalid risk for {skill_id}")
    evidence = item.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError(f"missing evidence for {skill_id}")
    return skill_id


def _validate_skills(skills: Any) -> None:
    if not isinstance(skills, list) or not skills:
        raise ValueError("catalog requires a non-empty skills list")
    ids = [_validate_skill(item) for item in skills]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate skill ids")


def load_catalog() -> dict[str, Any]:
    try:
        raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("system skills catalog cannot be read or parsed") from exc
    if not isinstance(raw, dict):
        raise ValueError("system skills catalog root must be an object")
    if raw.get("schema") != "cknexus.system-skills.catalog.v1":
        raise ValueError("unsupported system skills catalog schema")
    _validate_policy(raw.get("adoption_policy", {}))
    _validate_skills(raw.get("skills", []))
    return raw


def decide(skill: dict[str, Any]) -> AdmissionDecision:
    decision = str(skill["decision"])
    risk = str(skill["risk"])
    skill_id = str(skill["id"])
    auto_safe = risk in AUTO_SAFE_RISKS and decision not in {"BLOCKED_BY_EVIDENCE", "REJECT"}
    requires_cost = risk == "paid"
    requires_core = (not auto_safe) or decision in {"EXTEND", "NEW_SKILL", "EVALUATE"}
    if decision in {"BLOCKED_BY_EVIDENCE", "REJECT"}:
        next_action = "STOP"
        reason = "evidence or policy blocks adoption"
    elif not auto_safe:
        next_action = "REVIEW_WITH_CORE_APPROVAL"
        reason = str(skill.get("notes") or "guarded capability requires explicit Core review")
    elif decision == "REUSE":
        next_action = "REUSE_CANONICAL"
        reason = str(skill.get("notes") or "canonical capability already exists")
    elif decision == "EXTEND":
        next_action = "EXTEND_IN_DEV"
        reason = str(skill.get("notes") or "extend existing capability without replacement")
    else:
        next_action = "EVALUATE_IN_DEV"
        reason = str(skill.get("notes") or "prove measurable delta before canonical adoption")
    return AdmissionDecision(
        skill_id=skill_id,
        decision=decision,
        risk=risk,
        auto_safe=auto_safe,
        next_action=next_action,
        reason=reason,
        requires_core_approval=requires_core,
        requires_cost_approval=requires_cost,
    )


def plan() -> list[AdmissionDecision]:
    catalog = load_catalog()
    return [decide(item) for item in catalog["skills"]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only CK-NEXUS capability admission planner")
    parser.add_argument("--skill")
    parser.add_argument("--auto-safe", action="store_true")
    args = parser.parse_args()
    decisions = plan()
    if args.skill:
        decisions = [item for item in decisions if item.skill_id == args.skill]
        if not decisions:
            raise SystemExit(f"unknown skill: {args.skill}")
    if args.auto_safe:
        decisions = [item for item in decisions if item.auto_safe and item.next_action != "STOP"]
    print(json.dumps([asdict(item) for item in decisions], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
