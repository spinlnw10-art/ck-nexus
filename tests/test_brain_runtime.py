from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from creator_app.agnes_approval import CoreApprovalDecision
from creator_app.brain import BrainJournal, BrainRuntime
from creator_app.dev_assistants.orchestrator import DevAssistantFabric


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    payload = {
        "schema_version": "1.0.0",
        "artifacts": [
            {
                "id": "core",
                "name": "CK-NEXUS Core",
                "class": "core",
                "status": "present",
                "integration_point": "internal",
                "authority_scope": "L3",
            },
            {
                "id": "provider",
                "name": "Provider",
                "class": "ai_provider",
                "status": "partial",
                "integration_point": "gateway",
                "authority_scope": "NONE",
            },
        ],
    }
    (root / "config" / "capability_catalog.json").write_text(json.dumps(payload), encoding="utf-8")
    return root


def test_brain_status_composes_components_and_fails_closed(tmp_path):
    brain = BrainRuntime(
        root=_root(tmp_path),
        journal_path=tmp_path / "brain.sqlite3",
        task_db_path=tmp_path / "tasks.sqlite3",
        knowledge_db_path=tmp_path / "missing.sqlite3",
        evidence_dir=tmp_path / "missing",
    )
    status = brain.status()
    assert (
        status["brain_status"] == "ready_for_planning" and status["catalog"]["artifact_count"] == 2
    )
    assert (
        status["planner"]["execution_performed"] is False
        and status["authority"]["external_mutation_authorized"] is False
    )
    assert status["production_status"] == "NO-GO" and status["q10_status"] == "NOT_VERIFIED"
    assert status["specialist_fabric"]["internal_expert_count"] == 8
    assert status["specialist_fabric"]["execution_performed"] is False
    assert status["specialist_fabric"]["external_runtime_verified_count"] == 0


def test_brain_plan_never_executes_or_grants_authority(tmp_path):
    brain = BrainRuntime(
        root=_root(tmp_path),
        journal_path=tmp_path / "brain.sqlite3",
        task_db_path=tmp_path / "tasks.sqlite3",
        knowledge_db_path=tmp_path / "missing.sqlite3",
        evidence_dir=tmp_path / "missing",
    )
    result = brain.plan("Improve model fallback and verify tests", priority=2)
    assert result["execution_state"] == "PLANNED_NOT_EXECUTED" and len(result["plan"]["nodes"]) == 4
    assert result["external_mutation_authorized"] is False
    assert all(x["external_mutation_authorized"] is False for x in result["queue_payloads"])


def test_journal_stores_fingerprint_not_raw_task_and_never_claims_verification(tmp_path):
    db = tmp_path / "brain.sqlite3"
    journal = BrainJournal(db)
    task = "private prompt marker DO_NOT_PERSIST"
    result = journal.record_observation(
        task=task,
        outcome="reported_success",
        reason_code="tests_passed_reported",
        evidence_refs=["sha256:abc123"],
        metrics={"duration_ms": 120, "arbitrary_prompt": 999, "input_tokens": 20},
    )
    assert result["raw_task_stored"] is False and result["verification_claimed"] is False
    assert task.encode() not in db.read_bytes() and b"arbitrary_prompt" not in db.read_bytes()
    summary = journal.summary()
    assert summary["observation_count"] == 1 and summary["outcomes"]["reported_success"] == 1
    assert summary["self_reported_outcomes_are_verified"] is False


def test_improvement_proposals_remain_candidates_until_owner_review(tmp_path):
    journal = BrainJournal(tmp_path / "brain.sqlite3")
    item = journal.propose_improvement(
        candidate_type="retrieval_quality",
        title="Add multilingual semantic retrieval",
        rationale=(
            "Benchmark semantic retrieval against lexical baseline using a rights-cleared corpus."
        ),
        evidence_refs=["evidence:retrieval-benchmark-001"],
    )
    assert (
        item["state"] == "candidate"
        and item["owner_approval_required"] is True
        and item["auto_promotion"] is False
    )
    assert journal.summary()["pending_improvement_candidates"] == 1


def test_journal_rejects_untrusted_outcomes_and_secret_shaped_refs(tmp_path):
    journal = BrainJournal(tmp_path / "brain.sqlite3")
    with pytest.raises(ValueError):
        journal.record_observation(task="task", outcome="verified")
    with pytest.raises(ValueError):
        journal.record_observation(
            task="task", outcome="reported_success", evidence_refs=["ghp_" + "a" * 30]
        )


def test_brain_plan_composes_internal_experts_and_external_assistant_candidates(tmp_path):
    brain = BrainRuntime(
        root=_root(tmp_path),
        journal_path=tmp_path / "brain.sqlite3",
        task_db_path=tmp_path / "tasks.sqlite3",
        knowledge_db_path=tmp_path / "missing.sqlite3",
        evidence_dir=tmp_path / "missing",
        dev_assistant_fabric=DevAssistantFabric(path_lookup=lambda _command: None),
    )
    result = brain.plan("Audit security vulnerability in authentication")
    route = result["specialist_route"]
    assert route["primary_expert"] == "guardian"
    assert "independent_verifier" in route["supporting_experts"]
    assert route["approval_required"] is True
    assert route["execution_performed"] is False
    assert route["authority_scope"] == "NONE"
    assistant_plan = result["external_assistant_plan"]
    assert assistant_plan["execution_state"] == "PLANNED_NOT_EXECUTED"
    assert assistant_plan["runtime_verified"] is False
    assert assistant_plan["cost_authorization_required"] is True
    assert assistant_plan["external_mutation_authorized"] is False


class _CoreApprovalVerifier:
    def verify(self, approval_ref, *, subject_id, action, request_digest):
        return CoreApprovalDecision(
            approval_ref=approval_ref,
            subject_id=subject_id,
            action=action,
            request_digest=request_digest,
            actor_id="core_owner",
            approved=True,
        )


def test_brain_status_exposes_fail_closed_knowledge_fabric(tmp_path):
    brain = BrainRuntime(root=_root(tmp_path), fabric_ledger_path=tmp_path / "fabric.jsonl")
    status = brain.status()
    fabric = status["knowledge_fabric"]
    assert fabric["status"] == "available"
    assert fabric["experiential_memory"]["experience_count"] == 0
    assert fabric["skill_foundry"]["candidate_count"] == 0
    assert fabric["approval_verifier_configured"] is False
    assert fabric["ledger_locking_mode"] in {"fcntl+thread", "thread_only"}
    assert fabric["auto_install"] is False
    assert fabric["auto_activate"] is False
    assert fabric["authority_scope"] == "NONE"


def test_brain_uses_only_core_validated_experiences_in_future_plans(tmp_path):
    brain = BrainRuntime(
        root=_root(tmp_path),
        fabric_ledger_path=tmp_path / "fabric.jsonl",
        approval_verifier=_CoreApprovalVerifier(),
        dev_assistant_fabric=DevAssistantFabric(path_lookup=lambda _command: None),
    )
    entry = brain.record_experience(
        task_type="security",
        context_digest=hashlib.sha256(b"synthetic context").hexdigest(),
        action_strategy="Run static checks and independent review.",
        result="SUCCESS",
        lesson="Do not accept a security fix without independent verification.",
        confidence=0.95,
        source_run="run:synthetic:security",
        evidence_links=["evidence:security:1"],
    )
    assert entry["validity_status"] == "PENDING_VERIFICATION"
    brain.validate_experience(
        entry["experience_id"],
        approval_ref="core-approval-security",
        evidence_links=["evidence:security:reviewed"],
        independent_verification_ref="review:security:independent",
    )
    plan = brain.plan("Audit security vulnerability in authentication")
    assert [item["experience_id"] for item in plan["relevant_experiences"]] == [
        entry["experience_id"]
    ]
    assert plan["execution_state"] == "PLANNED_NOT_EXECUTED"


def test_brain_skill_foundry_records_candidates_without_installing(tmp_path):
    brain = BrainRuntime(root=_root(tmp_path), fabric_ledger_path=tmp_path / "fabric.jsonl")
    candidate = brain.discover_skill_candidate(
        skill_id="safe-reader",
        version="1.0.0",
        source_url="https://agentskills.io/safe-reader",
        checksum_sha256="b" * 64,
        license_id="MIT",
    )
    assert candidate["state"] == "DISCOVERED"
    assert candidate["activation_allowed"] is False
    assert candidate["auto_install"] is False
    assert brain.skill_candidates()[0]["candidate_id"] == candidate["candidate_id"]
    assert brain.status()["knowledge_fabric"]["skill_foundry"]["candidate_count"] == 1


def test_brain_skill_foundry_requires_quarantine_release_and_independent_review(tmp_path):
    brain = BrainRuntime(
        root=_root(tmp_path),
        fabric_ledger_path=tmp_path / "fabric.jsonl",
        approval_verifier=_CoreApprovalVerifier(),
    )
    candidate = brain.discover_skill_candidate(
        skill_id="scripted-tool",
        version="2.0.0",
        source_url="https://agentskills.io/scripted-tool",
        checksum_sha256="c" * 64,
        license_id="Apache-2.0",
        has_executable_scripts=True,
    )
    assert candidate["state"] == "QUARANTINED"
    released = brain.release_skill_quarantine(
        candidate["candidate_id"],
        approval_ref="core-quarantine-release",
        evidence_ref="review:quarantine:scripted-tool",
        resolved_reasons=candidate["reasons"],
        resolution_summary=("Reviewed every quarantine reason in a disposable test workspace."),
    )
    assert released["state"] == "DISCOVERED"
    brain.record_skill_security_scan(
        candidate["candidate_id"], evidence_ref="scan:scripted-tool", passed=True
    )
    brain.record_skill_sandbox_test(
        candidate["candidate_id"], evidence_ref="sandbox:scripted-tool", passed=True
    )
    brain.record_skill_benchmark(
        candidate["candidate_id"], evidence_ref="benchmark:scripted-tool", passed=True
    )
    awaiting = brain.record_skill_compatibility(
        candidate["candidate_id"],
        evidence_ref="compatibility:scripted-tool",
        independent_verification_ref="review:independent:scripted-tool",
        passed=True,
    )
    assert awaiting["state"] == "AWAITING_APPROVAL"
    assert awaiting["independent_verification_ref"] == "review:independent:scripted-tool"
    registerable = brain.approve_skill_candidate(
        candidate["candidate_id"],
        approval_ref="core-register-scripted-tool",
        evidence_ref="approval:evidence:scripted-tool",
    )
    assert registerable["state"] == "REGISTERABLE"
    assert registerable["activation_allowed"] is False
