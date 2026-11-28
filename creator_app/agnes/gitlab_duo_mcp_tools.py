"""Fail-closed MCP tool handlers for the governed GitLab Duo adapter.

The handlers are separated from the FastMCP server module so they can be
unit-tested without importing the full application server or starting a host.
"""

from __future__ import annotations

from typing import Any

from creator_app.agnes.gitlab_duo_bootstrap import (
    build_core_governed_gitlab_duo_dispatcher,
)
from creator_app.agnes.gitlab_duo_dispatcher import (
    DuoDispatchRequest,
    GitLabDuoDispatchError,
    GitLabDuoFlowsClient,
)

_CLIENT: GitLabDuoFlowsClient | None = None


def configure_gitlab_duo_dispatcher(client: GitLabDuoFlowsClient | None) -> None:
    """Inject a fully governed GitLab Duo client from the trusted Core bootstrap."""
    global _CLIENT
    if client is not None and not isinstance(client, GitLabDuoFlowsClient):
        raise TypeError("client must be a GitLabDuoFlowsClient or None")
    _CLIENT = client


def configure_gitlab_duo_dispatcher_from_core(**core_bindings: Any) -> dict[str, Any]:
    """Build and inject the dispatcher from explicit trusted Core-owned bindings."""
    client = build_core_governed_gitlab_duo_dispatcher(**core_bindings)
    configure_gitlab_duo_dispatcher(client)
    return client.readiness()


def gitlab_duo_status() -> dict[str, Any]:
    """Return redacted local readiness without exposing credentials."""
    client = _CLIENT
    if client is None:
        return {
            "ok": True,
            "ready": False,
            "configured": False,
            "reason": "Trusted CK-NEXUS Core bootstrap has not injected the dispatcher.",
            "live_dispatch_attempted": False,
        }
    return client.readiness()


def gitlab_duo_start_flow(
    *,
    task_id: str,
    goal: str,
    workflow_definition: str,
    source_branch: str,
    agent_privileges: list[int],
    confirmation_binding: str,
    evidence_refs: list[str],
    approval_ref: str,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Start one governed GitLab Duo flow; CK-NEXUS Core authorization is mandatory."""
    client = _CLIENT
    if client is None:
        return {
            "ok": False,
            "error_code": "DISPATCHER_NOT_CONFIGURED",
            "message": "Trusted CK-NEXUS Core bootstrap has not injected the dispatcher.",
            "live_dispatch_attempted": False,
        }
    try:
        request = DuoDispatchRequest(
            task_id=task_id,
            goal=goal,
            workflow_definition=workflow_definition,
            source_branch=source_branch,
            agent_privileges=tuple(agent_privileges),
            confirmation_binding=confirmation_binding,
            evidence_refs=tuple(evidence_refs),
            project_id=project_id,
            approval_ref=approval_ref,
        )
        result = client.start_flow(request)
        return {"ok": True, **result.as_dict()}
    except GitLabDuoDispatchError as exc:
        return {
            "ok": False,
            "error_code": "GITLAB_DUO_DISPATCH_DENIED",
            "message": str(exc),
            "dispatch_outcome": "not_confirmed",
            "reconciliation_required": True,
        }
    except (TypeError, ValueError) as exc:
        return {
            "ok": False,
            "error_code": "INVALID_DISPATCH_REQUEST",
            "message": str(exc),
            "live_dispatch_attempted": False,
        }


def gitlab_duo_flow_status(workflow_id: int) -> dict[str, Any]:
    """Poll a GitLab Duo flow through the configured Credential Broker."""
    client = _CLIENT
    if client is None:
        return {
            "ok": False,
            "error_code": "DISPATCHER_NOT_CONFIGURED",
            "message": "Trusted CK-NEXUS Core bootstrap has not injected the dispatcher.",
        }
    try:
        return {"ok": True, **client.get_flow_status(workflow_id)}
    except GitLabDuoDispatchError as exc:
        return {
            "ok": False,
            "error_code": "GITLAB_DUO_STATUS_UNAVAILABLE",
            "message": str(exc),
        }
    except ValueError as exc:
        return {
            "ok": False,
            "error_code": "INVALID_WORKFLOW_ID",
            "message": str(exc),
        }
