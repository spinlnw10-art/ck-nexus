from __future__ import annotations

import pytest

from creator_app.agnes.gitlab_duo_bootstrap import (
    build_core_governed_gitlab_duo_dispatcher,
)
from creator_app.council_authority.authority import BrokerScopeAdapter, CapabilityAuthority
from creator_app.council_authority.identity import IdentityVerifier
from creator_app.council_authority.storage import AuthorityStore
from creator_app.credential_broker import CredentialBroker

CAPABILITY = "integration.gitlab_duo.dispatch"


def make_core(tmp_path, *, agent_id="CK-NEXUS-DISPATCHER", evidence=True):
    broker = CredentialBroker()
    verifier = IdentityVerifier(b"identity-test-secret-material-32bytes")
    token = verifier.issue(service_id="cknexus-core", agent_id=agent_id)
    contract = {
        "version": "test-policy",
        "capabilities": {
            CAPABILITY: {
                "costClass": "high",
                "requiresCredential": False,
                "requiresSourceEvidence": evidence,
                "evidenceKinds": ["git_commit"],
            }
        },
        "agents": {
            "CK-NEXUS-DISPATCHER": {"permissions": [CAPABILITY]},
            "UNAUTHORIZED": {"permissions": []},
        },
    }
    authority = CapabilityAuthority(
        contract,
        store=AuthorityStore(str(tmp_path / "authority.sqlite3")),
        broker_adapter=BrokerScopeAdapter(broker),
        grant_secret=b"grant-test-secret-material-32bytes",
    )
    return authority, verifier, token, broker


def build(tmp_path, **overrides):
    authority, verifier, token, broker = make_core(tmp_path)
    values = {
        "authority": authority,
        "identity_verifier": verifier,
        "identity_token": token,
        "broker": broker,
        "approval_verifier": lambda _ref, _request, _project: True,
        "project_id": "12345",
        "ledger_path": tmp_path / "dispatch.sqlite3",
        "allowed_workflow_definitions": ("developer/v1",),
        "allowed_agent_privileges": (1, 2),
        "branch_protection_verifier": lambda _project, _branch: True,
    }
    values.update(overrides)
    return build_core_governed_gitlab_duo_dispatcher(**values)


def test_core_bootstrap_composes_fail_closed_dispatcher(tmp_path):
    client = build(tmp_path)
    status = client.readiness()
    assert status["ready"] is False
    assert status["checks"]["core_authority_connected"] is True
    assert status["checks"]["durable_ledger_connected"] is True
    assert status["checks"]["workflow_allowlist_configured"] is True
    assert status["checks"]["privilege_allowlist_configured"] is True
    assert status["checks"]["protected_branch_verifier_connected"] is True
    assert status["checks"]["credential_configured"] is False
    assert (tmp_path / "dispatch.sqlite3").exists()


def test_bootstrap_rejects_unverified_identity(tmp_path):
    authority, verifier, token, broker = make_core(tmp_path)
    with pytest.raises(PermissionError, match="could not be verified"):
        build_core_governed_gitlab_duo_dispatcher(
            authority=authority,
            identity_verifier=verifier,
            identity_token=token + "tampered",
            broker=broker,
            approval_verifier=lambda *_args: True,
            project_id="12345",
            ledger_path=tmp_path / "dispatch.sqlite3",
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1,),
            branch_protection_verifier=lambda *_args: True,
        )


def test_bootstrap_rejects_identity_without_capability_permission(tmp_path):
    authority, verifier, _token, broker = make_core(tmp_path, agent_id="UNAUTHORIZED")
    token = verifier.issue(service_id="cknexus-core", agent_id="UNAUTHORIZED")
    with pytest.raises(PermissionError, match="not permitted"):
        build_core_governed_gitlab_duo_dispatcher(
            authority=authority,
            identity_verifier=verifier,
            identity_token=token,
            broker=broker,
            approval_verifier=lambda *_args: True,
            project_id="12345",
            ledger_path=tmp_path / "dispatch.sqlite3",
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1,),
            branch_protection_verifier=lambda *_args: True,
        )


def test_bootstrap_rejects_policy_without_task_bound_evidence(tmp_path):
    authority, verifier, token, broker = make_core(tmp_path, evidence=False)
    with pytest.raises(PermissionError, match="task-bound source evidence"):
        build_core_governed_gitlab_duo_dispatcher(
            authority=authority,
            identity_verifier=verifier,
            identity_token=token,
            broker=broker,
            approval_verifier=lambda *_args: True,
            project_id="12345",
            ledger_path=tmp_path / "dispatch.sqlite3",
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1,),
            branch_protection_verifier=lambda *_args: True,
        )


def test_bootstrap_requires_core_approval_verifier(tmp_path):
    with pytest.raises(TypeError, match="approval_verifier"):
        build(tmp_path, approval_verifier=None)


def test_bootstrap_requires_absolute_ledger_path(tmp_path):
    with pytest.raises(ValueError, match="absolute"):
        build(tmp_path, ledger_path="relative/dispatch.sqlite3")
