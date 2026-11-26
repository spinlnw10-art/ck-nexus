"""Composition layer for CK-NEXUS planning, knowledge and bounded learning."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from creator_app.agnes_approval import CoreApprovalVerifier
from creator_app.agnes_experiential_memory import ExperientialMemory
from creator_app.agnes_ledger import AppendOnlyLedger
from creator_app.agnes_skill_foundry import SkillFoundry
from creator_app.capability_fabric.catalog import CapabilityCatalog
from creator_app.control_plane.orchestrator import ControlPlaneOrchestrator
from creator_app.dev_assistants.orchestrator import DevAssistantFabric
from creator_app.expert_fabric import ExpertRouter
from creator_app.n8n_intelligence.learning import AgentLearningMemory

from . import journal as brain_journal
from .journal import BrainJournal

BRAIN_ROOT = Path(__file__).resolve().parents[2]
STATE_DIRECTORY = ".state"
TASK_DATABASE_PATH = BRAIN_ROOT / STATE_DIRECTORY / "control-plane.sqlite3"
KNOWLEDGE_DATABASE_PATH = Path("/var/lib/cknexus-knowledge/ebooks.sqlite3")
EVIDENCE_DIRECTORY = BRAIN_ROOT / "evidence" / "auto_dev"
FABRIC_LEDGER_PATH = BRAIN_ROOT / STATE_DIRECTORY / "agnes-fabric-ledger.jsonl"


class BrainRuntime:
    """Single facade over existing capabilities; no independent authority plane."""

    def __init__(
        self,
        *,
        orchestrator=None,
        expert_router=None,
        dev_assistant_fabric=None,
        approval_verifier: CoreApprovalVerifier | None = None,
    ):
        self.root = BRAIN_ROOT
        self.catalog_path = self.root / "config" / "capability_catalog.json"
        self.journal_path = brain_journal.BRAIN_JOURNAL_PATH
        self.task_db_path = TASK_DATABASE_PATH
        self.knowledge_db_path = KNOWLEDGE_DATABASE_PATH
        self.evidence_dir = EVIDENCE_DIRECTORY
        self.orchestrator = orchestrator or ControlPlaneOrchestrator()
        self.expert_router = expert_router or ExpertRouter()
        self.dev_assistant_fabric = dev_assistant_fabric or DevAssistantFabric()
        self.fabric_ledger_path = FABRIC_LEDGER_PATH
        self.fabric_ledger = AppendOnlyLedger(self.fabric_ledger_path)
        self.experiential_memory = ExperientialMemory(
            self.fabric_ledger, approval_verifier=approval_verifier
        )
        self.skill_foundry = SkillFoundry(self.fabric_ledger, approval_verifier=approval_verifier)

    def _catalog(self):
        return CapabilityCatalog.load(self.catalog_path)

    def _open_task_count(self):
        if not self.task_db_path.is_file():
            return None
        uri = f"file:{self.task_db_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=2) as db:
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='control_plane_tasks'"
            ).fetchone()
            if exists is None:
                return 0
            row = db.execute(
                "SELECT COUNT(*) FROM control_plane_tasks WHERE state IN ('queued','running')"
            ).fetchone()
        return int(row[0])

    def status(self):
        try:
            catalog = self._catalog()
            artifacts = catalog.list()
            catalog_state = "available"
            classes = {}
            statuses = {}
            for item in artifacts:
                classes[item.artifact_class.value] = classes.get(item.artifact_class.value, 0) + 1
                statuses[item.status.value] = statuses.get(item.status.value, 0) + 1
        except (OSError, ValueError, KeyError) as exc:
            catalog_state = f"degraded:{type(exc).__name__}"
            artifacts = ()
            classes = {}
            statuses = {}
        tasks = {"database_present": self.task_db_path.is_file(), "open_tasks": None}
        if self.task_db_path.is_file():
            try:
                tasks["open_tasks"] = self._open_task_count()
            except (OSError, sqlite3.Error):
                tasks["status"] = "unavailable"
        knowledge = {"database_present": self.knowledge_db_path.is_file(), "source_count": None}
        if self.knowledge_db_path.is_file():
            try:
                from creator_app.global_knowledge.ebook_store import EbookKnowledgeStore

                documents = EbookKnowledgeStore(self.knowledge_db_path).list_documents_readonly()
                knowledge["source_count"] = len(documents)
                knowledge["active_source_count"] = sum(
                    not bool(item.get("revoked", False)) for item in documents
                )
                knowledge["revoked_source_count"] = sum(
                    bool(item.get("revoked", False)) for item in documents
                )
            except (ImportError, OSError, ValueError):
                knowledge["status"] = "unavailable"
        journal = {"database_present": self.journal_path.is_file()}
        if self.journal_path.is_file():
            try:
                journal.update(BrainJournal().summary(limit=3))
            except (OSError, ValueError):
                journal["status"] = "unavailable"
        else:
            journal.update({"observation_count": 0, "pending_improvement_candidates": 0})
        assistants = self.dev_assistant_fabric.discover()
        specialist_profiles = self.expert_router.registry.all()
        try:
            knowledge_fabric = {
                "status": "available",
                "experiential_memory": self.experiential_memory.summary(),
                "skill_foundry": self.skill_foundry.summary(),
                "approval_verifier_configured": self.experiential_memory.approval_verifier
                is not None,
                "ledger_locking_mode": self.fabric_ledger.locking_mode,
                "auto_install": False,
                "auto_activate": False,
                "authority_scope": "NONE",
            }
        except (OSError, RuntimeError, ValueError) as exc:
            knowledge_fabric = {
                "status": "integrity_failure",
                "error_type": type(exc).__name__,
                "auto_install": False,
                "auto_activate": False,
                "authority_scope": "NONE",
            }
        return {
            "brain_status": "ready_for_planning" if catalog_state == "available" else "degraded",
            "architecture": "CK-NEXUS_BRAIN_FABRIC_V1",
            "catalog": {
                "status": catalog_state,
                "artifact_count": len(artifacts),
                "class_counts": classes,
                "status_counts": statuses,
            },
            "planner": {
                "status": "available",
                "implementation": "ControlPlaneOrchestrator",
                "execution_performed": False,
            },
            "task_queue": tasks,
            "knowledge": {**knowledge, "retrieval_mode": "lexical", "rights_gated_ingestion": True},
            "learning_journal": journal,
            "learning": {
                "status": "evidence_derived",
                "raw_prompts_stored": False,
                "self_reported_outcomes_promoted": False,
            },
            "knowledge_fabric": knowledge_fabric,
            "specialist_fabric": {
                "status": "planning_only",
                "internal_expert_count": len(specialist_profiles),
                "internal_experts": [profile.expert_id for profile in specialist_profiles],
                "external_assistant_count": len(assistants),
                "external_binary_count": sum(bool(item["available"]) for item in assistants),
                "external_runtime_verified_count": sum(
                    bool(item["runtime_verified"]) for item in assistants
                ),
                "external_assistants": assistants,
                "execution_performed": False,
                "authority_scope": "NONE",
            },
            "authority": {
                "core": "CK-NEXUS Core L3 only",
                "external_tools": "NONE",
                "external_mutation_authorized": False,
            },
            "production_status": "NO-GO",
            "q10_status": "NOT_VERIFIED",
            "release_evidence": False,
        }

    def plan(self, request: str, *, priority=2, context=""):
        if not isinstance(request, str) or not request.strip() or len(request) > 20000:
            raise ValueError("request must be non-empty and at most 20000 characters")
        if priority not in {1, 2, 3}:
            raise ValueError("priority must be 1, 2 or 3")
        expert_route = self.expert_router.route(request)
        task_type = expert_route.domains[0] if expert_route.domains else "general"
        relevant_experiences = self.experiential_memory.retrieve_relevant(task_type, limit=3)
        memory_context = [
            f"Validated prior experience ({entry.experience_id}): {entry.lesson}; "
            f"strategy={entry.action_strategy}; evidence={','.join(entry.evidence_links)}"
            for entry in relevant_experiences
        ]
        combined_context = "\n".join(part for part in (context, *memory_context) if part)
        graph = self.orchestrator.plan(request, priority=priority, context=combined_context)
        workstreams = {}
        for expert_id in (expert_route.primary_expert, *expert_route.supporting_experts):
            profile = self.expert_router.registry.get(expert_id)
            workstreams[f"{expert_id}:{profile.agent_id}"] = profile.capabilities
        assistant_plan = self.dev_assistant_fabric.build_parallel_plan(request, workstreams)
        return {
            "plan": graph.as_dict(),
            "queue_payloads": self.orchestrator.queue_payloads(graph),
            "specialist_route": expert_route.as_dict(),
            "external_assistant_plan": assistant_plan,
            "relevant_experiences": [entry.as_dict() for entry in relevant_experiences],
            "execution_state": "PLANNED_NOT_EXECUTED",
            "external_mutation_authorized": False,
            "production_status": "NO-GO",
            "release_evidence": False,
        }

    def learning_context(self, task):
        return AgentLearningMemory(self.evidence_dir, max_records=20).context_for(task)

    def record_observation(self, **kwargs):
        return BrainJournal().record_observation(**kwargs)

    def propose_improvement(self, **kwargs):
        return BrainJournal().propose_improvement(**kwargs)

    def journal_summary(self):
        if not self.journal_path.is_file():
            return {
                "observation_count": 0,
                "pending_improvement_candidates": 0,
                "raw_prompts_or_outputs_stored": False,
            }
        return BrainJournal().summary()

    def record_experience(self, **kwargs):
        return self.experiential_memory.record_experience(**kwargs).as_dict()

    def validate_experience(self, experience_id, **kwargs):
        return self.experiential_memory.validate_provenance(experience_id, **kwargs).as_dict()

    def retrieve_experiences(self, task_type, *, limit=10):
        return [
            entry.as_dict()
            for entry in self.experiential_memory.retrieve_relevant(task_type, limit=limit)
        ]

    def experiential_provenance_graph(self):
        return self.experiential_memory.build_provenance_graph()

    def discover_skill_candidate(self, **kwargs):
        return self.skill_foundry.discover(**kwargs).as_dict()

    def skill_candidates(self):
        return [candidate.as_dict() for candidate in self.skill_foundry.list_candidates()]

    def release_skill_quarantine(self, candidate_id, **kwargs):
        return self.skill_foundry.clear_quarantine(candidate_id, **kwargs).as_dict()

    def record_skill_security_scan(self, candidate_id, **kwargs):
        return self.skill_foundry.record_security_scan(candidate_id, **kwargs).as_dict()

    def record_skill_sandbox_test(self, candidate_id, **kwargs):
        return self.skill_foundry.record_sandbox_test(candidate_id, **kwargs).as_dict()

    def record_skill_benchmark(self, candidate_id, **kwargs):
        return self.skill_foundry.record_benchmark(candidate_id, **kwargs).as_dict()

    def record_skill_compatibility(self, candidate_id, **kwargs):
        return self.skill_foundry.record_compatibility(candidate_id, **kwargs).as_dict()

    def approve_skill_candidate(self, candidate_id, **kwargs):
        return self.skill_foundry.approve(candidate_id, **kwargs).as_dict()

    def knowledge_search(self, query, *, limit=8):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        if not self.knowledge_db_path.is_file():
            return []
        from creator_app.global_knowledge.ebook_store import EbookKnowledgeStore

        hits = EbookKnowledgeStore(self.knowledge_db_path).search_readonly(query, limit=limit)
        return [
            {
                "chunk_id": h.chunk_id,
                "source_sha256": h.source_sha256,
                "title": h.title,
                "chapter_id": h.chapter_id,
                "chunk_order": h.chunk_order,
                "text": h.text,
            }
            for h in hits
        ]
