"""Trusted Core composition for the governed GitLab Duo dispatcher.

This module deliberately does not create policy, identities, approvals, or
credentials. Those objects must be supplied by the already-authenticated
CK-NEXUS Core runtime.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from creator_app.agnes.gitlab_duo_dispatcher import (
    DISPATCH_CAPABILITY_ID,
    GITLAB_CREDENTIAL_CONSUMER,
    BrokerGitLabTokenProvider,
    CapabilityAuthorityDispatchAuthorizer,
    DuoDispatchLedger,
    DuoDispatchRequest,
    GitLabDuoFlowsClient,
    GitLabProtectedBranchVerifier,
)
from creator_app.council_authority.authority import CapabilityAuthority
from creator_app.council_authority.identity import IdentityError, IdentityVerifier
from creator_app.credential_broker import CredentialBroker, CredentialId

ApprovalVerifier = Callable[[str, DuoDispatchRequest, str], bool]


def build_core_governed_gitlab_duo_dispatcher(
    *,
    authority: CapabilityAuthority,
    identity_verifier: IdentityVerifier,
    identity_token: str,
    broker: CredentialBroker,
    approval_verifier: ApprovalVerifier,
    project_id: str,
    ledger_path: str | Path,
    allowed_workflow_definitions: tuple[str, ...],
    allowed_agent_privileges: tuple[int, ...],
    base_url: str = "https://gitlab.com",
    timeout_seconds: int = 20,
    branch_protection_verifier: Callable[[str, str], bool] | None = None,
) -> GitLabDuoFlowsClient:
    """Compose a dispatcher only from explicit, already-governed Core bindings.

    No policy or identity is synthesized here. Missing capability permission,
    task-approval verification, broker scope, project configuration, or
    allowlists causes construction to fail closed. Credential presence is
    checked by the client's redacted readiness probe without revealing it.
    """
    if not isinstance(authority, CapabilityAuthority):
        raise TypeError("authority must be the live CK-NEXUS CapabilityAuthority")
    if not isinstance(identity_verifier, IdentityVerifier):
        raise TypeError("identity_verifier must be the live CK-NEXUS IdentityVerifier")
    if not isinstance(identity_token, str) or not identity_token.strip():
        raise ValueError("a signed CK-NEXUS service identity token is required")
    try:
        identity = identity_verifier.verify(identity_token)
    except (IdentityError, ValueError, TypeError):
        raise PermissionError("CK-NEXUS service identity token could not be verified") from None
    if not isinstance(broker, CredentialBroker):
        raise TypeError("broker must be the live CK-NEXUS CredentialBroker")
    if not callable(approval_verifier):
        raise TypeError("approval_verifier must be supplied by CK-NEXUS Core")
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("an explicitly configured GitLab project ID is required")
    if not isinstance(ledger_path, (str, Path)) or not str(ledger_path).strip():
        raise ValueError("an explicit durable dispatch ledger path is required")
    if not Path(ledger_path).expanduser().is_absolute():
        raise ValueError("dispatch ledger path must be absolute")
    if not allowed_workflow_definitions or any(
        not isinstance(item, str) or not item.strip() for item in allowed_workflow_definitions
    ):
        raise ValueError("Core-approved workflow definitions are required")
    if not allowed_agent_privileges or any(
        type(item) is not int or item < 1 for item in allowed_agent_privileges
    ):
        raise ValueError("Core-approved positive agent privilege IDs are required")
    if not broker.is_allowed(CredentialId.GITLAB_DUO_TOKEN, consumer=GITLAB_CREDENTIAL_CONSUMER):
        raise PermissionError("Credential Broker policy denies the GitLab Duo consumer")

    capability = authority.contract.get("capabilities", {}).get(DISPATCH_CAPABILITY_ID)
    if not isinstance(capability, dict):
        raise PermissionError("Core policy does not register the GitLab Duo dispatch capability")
    if capability.get("costClass") not in {"medium", "high"}:
        raise PermissionError(
            "GitLab Duo dispatch must require bound medium/high-cost confirmation"
        )
    if capability.get("requiresSourceEvidence") is not True:
        raise PermissionError("Core policy must require task-bound source evidence")
    if not capability.get("evidenceKinds"):
        raise PermissionError("Core policy must define accepted source-evidence kinds")

    agent_policy = authority.contract.get("agents", {}).get(identity.agent_id, {})
    permissions = agent_policy.get("permissions", [])
    if not any(
        permission == DISPATCH_CAPABILITY_ID
        or (
            isinstance(permission, str)
            and permission.endswith("*")
            and DISPATCH_CAPABILITY_ID.startswith(permission[:-1])
        )
        for permission in permissions
    ):
        raise PermissionError("verified Core identity is not permitted to dispatch GitLab Duo")

    token_provider = BrokerGitLabTokenProvider(broker)
    branch_verifier = branch_protection_verifier or GitLabProtectedBranchVerifier(
        base_url=base_url,
        project_id=project_id,
        credential_provider=token_provider,
        timeout_seconds=timeout_seconds,
    )
    authorizer = CapabilityAuthorityDispatchAuthorizer(
        authority,
        identity,
        approval_verifier=approval_verifier,
    )
    ledger = DuoDispatchLedger(Path(ledger_path).expanduser())
    return GitLabDuoFlowsClient(
        base_url=base_url,
        project_id=project_id,
        credential_provider=token_provider,
        dispatch_authorizer=authorizer,
        dispatch_ledger=ledger,
        allowed_workflow_definitions=tuple(allowed_workflow_definitions),
        allowed_agent_privileges=tuple(allowed_agent_privileges),
        branch_protection_verifier=branch_verifier,
        timeout_seconds=timeout_seconds,
    )
