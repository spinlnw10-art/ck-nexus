from unittest.mock import patch

from creator_app.agnes import gitlab_duo_mcp_tools as tools
from creator_app.agnes.gitlab_duo_dispatcher import DuoDispatchResult, GitLabDuoFlowsClient


def teardown_function():
    tools.configure_gitlab_duo_dispatcher(None)


def test_status_is_fail_closed_without_trusted_bootstrap():
    tools.configure_gitlab_duo_dispatcher(None)
    result = tools.gitlab_duo_status()
    assert result["ok"] is True
    assert result["ready"] is False
    assert result["configured"] is False
    assert result["live_dispatch_attempted"] is False


def test_start_flow_is_fail_closed_without_trusted_bootstrap():
    tools.configure_gitlab_duo_dispatcher(None)
    result = tools.gitlab_duo_start_flow(
        task_id="CKN-1",
        goal="Inspect a test branch",
        workflow_definition="developer/v1",
        source_branch="agents/CKN-1",
        agent_privileges=[1],
        confirmation_binding="",
        evidence_refs=[],
        approval_ref="",
    )
    assert result["ok"] is False
    assert result["error_code"] == "DISPATCHER_NOT_CONFIGURED"
    assert result["live_dispatch_attempted"] is False


def test_flow_status_is_fail_closed_without_trusted_bootstrap():
    tools.configure_gitlab_duo_dispatcher(None)
    result = tools.gitlab_duo_flow_status(1)
    assert result["ok"] is False
    assert result["error_code"] == "DISPATCHER_NOT_CONFIGURED"


def test_status_reports_redacted_readiness_without_acquiring_token():
    client = GitLabDuoFlowsClient(
        base_url="https://gitlab.com",
        project_id="148654539/ck-nexus",
        credential_provider=lambda: "never-read-in-status",
        dispatch_ledger=None,
    )
    with patch.object(client, "_acquire_token") as acquire:
        tools.configure_gitlab_duo_dispatcher(client)
        result = tools.gitlab_duo_status()
    acquire.assert_not_called()
    assert result["ok"] is True
    assert result["ready"] is False
    assert result["checks"]["project_configured"] is True
    assert result["checks"]["durable_ledger_connected"] is False
    assert "never-read-in-status" not in repr(result)


def test_start_flow_delegates_to_core_governed_client():
    client = GitLabDuoFlowsClient(
        base_url="https://gitlab.com",
        project_id="148654539/ck-nexus",
        credential_provider=lambda: "test-token",
    )
    expected = DuoDispatchResult(
        17,
        "running",
        "https://gitlab.com/ck-nexus-group/ck-nexus/-/automate/agent-sessions/17",
        "started",
    )
    with patch.object(client, "start_flow", return_value=expected) as start:
        tools.configure_gitlab_duo_dispatcher(client)
        result = tools.gitlab_duo_start_flow(
            task_id="CKN-2",
            goal="Run a bounded test",
            workflow_definition="developer/v1",
            source_branch="agents/CKN-2",
            agent_privileges=[1],
            confirmation_binding="core-bound-confirmation",
            evidence_refs=["evidence:CKN-2"],
            approval_ref="core-approval:CKN-2",
            project_id="148654539/ck-nexus",
        )
    assert result["ok"] is True
    assert result["workflow_id"] == 17
    assert result["merge_authorized"] is False
    assert result["deploy_authorized"] is False
    assert start.call_args.args[0].agent_privileges == (1,)
    assert start.call_args.args[0].evidence_refs == ("evidence:CKN-2",)
    assert start.call_args.args[0].approval_ref == "core-approval:CKN-2"


def test_flow_status_delegates_to_configured_client():
    client = GitLabDuoFlowsClient(
        base_url="https://gitlab.com",
        project_id="148654539/ck-nexus",
        credential_provider=lambda: "test-token",
    )
    with patch.object(
        client,
        "get_flow_status",
        return_value={"workflow_id": 17, "status": "running", "web_url": None},
    ) as get_status:
        tools.configure_gitlab_duo_dispatcher(client)
        result = tools.gitlab_duo_flow_status(17)
    assert result == {"ok": True, "workflow_id": 17, "status": "running", "web_url": None}
    get_status.assert_called_once_with(17)


def test_invalid_workflow_id_is_reported_without_leaking_details():
    client = GitLabDuoFlowsClient(
        base_url="https://gitlab.com",
        project_id="148654539/ck-nexus",
        credential_provider=lambda: "test-token",
    )
    tools.configure_gitlab_duo_dispatcher(client)
    result = tools.gitlab_duo_flow_status(0)
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_WORKFLOW_ID"
