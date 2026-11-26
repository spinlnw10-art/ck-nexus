from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

from creator_app.agnes.gitlab_duo_dispatcher import (
    DISPATCH_CAPABILITY_ID,
    BrokerGitLabTokenProvider,
    CapabilityAuthorityDispatchAuthorizer,
    DuoDispatchLedger,
    DuoDispatchRequest,
    GitLabDuoDispatchError,
    GitLabDuoFlowsClient,
    GitLabProtectedBranchVerifier,
    _RejectRedirectHandler,
    _open_without_redirect,
)
from creator_app.council_authority.authority import CapabilityAuthority
from creator_app.council_authority.identity import CallerIdentity
from creator_app.council_authority.storage import AuthorityStore
from creator_app.credential_broker import CredentialBroker, CredentialId


class Broker:
    def check_scope(self, consumer, credential_ref):
        return True


class AllowAuthorizer:
    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def authorize(self, request, project_id):
        self.calls += 1
        if self.error:
            raise self.error
        return "core-grant-ref"


class GitLabDuoFlowsClientTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def client(self, *, authorizer=None, token_provider=None):
        return GitLabDuoFlowsClient(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=token_provider or (lambda: "test-token-not-real"),
            dispatch_authorizer=authorizer or AllowAuthorizer(),
            dispatch_ledger=DuoDispatchLedger(f"{self.tempdir.name}/dispatch.sqlite3"),
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1, 2),
            branch_protection_verifier=lambda _project, _branch: True,
        )

    def request(self, **overrides):
        values = {
            "task_id": "CKN-123",
            "goal": "Implement a small adapter and tests.",
            "workflow_definition": "developer/v1",
            "source_branch": "agents/cknexus/CKN-123",
            "agent_privileges": (1, 2),
            "confirmation_binding": "bound-confirmation",
            "evidence_refs": ("git:commit:123",),
        }
        values.update(overrides)
        return DuoDispatchRequest(**values)

    def test_goal_contains_non_bypassable_scope_constraints(self):
        goal = GitLabDuoFlowsClient.governed_goal("Do the task", task_id="CKN-123")
        self.assertIn("Do not read, modify, stage, or transmit data/", goal)
        self.assertIn("Do not merge, release, deploy", goal)
        self.assertIn("CKN-123", goal)
        self.assertIn(chr(10) * 2 + "CK-NEXUS GOVERNANCE", goal)

    def test_goal_rejects_token_shaped_content(self):
        with self.assertRaisesRegex(ValueError, "credential material"):
            GitLabDuoFlowsClient.governed_goal("token=glpat-" + "x" * 30, task_id="x")

    def test_dispatch_requires_core_authorizer(self):
        client = GitLabDuoFlowsClient(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=lambda: "test-token",
            dispatch_ledger=DuoDispatchLedger(f"{self.tempdir.name}/dispatch.sqlite3"),
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1, 2),
            branch_protection_verifier=lambda _project, _branch: True,
        )
        with self.assertRaisesRegex(GitLabDuoDispatchError, "Core dispatch authorizer"):
            client.start_flow(self.request())

    def test_denied_core_authorization_stops_before_token_acquisition_or_network(self):
        authorizer = AllowAuthorizer(GitLabDuoDispatchError("CK-NEXUS Core denied dispatch"))
        acquired = []
        client = self.client(
            authorizer=authorizer,
            token_provider=lambda: acquired.append(True) or "test-token",
        )
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "Core denied"):
                client.start_flow(self.request())
            request.assert_not_called()
        self.assertEqual(acquired, [])

    def test_dispatch_rejects_branch_outside_agent_namespace(self):
        client = self.client()
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "agents/ or feat/duo/"):
                client.start_flow(self.request(source_branch="main"))
            request.assert_not_called()

    def test_dispatch_rejects_project_override(self):
        client = self.client()
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "does not match"):
                client.start_flow(self.request(project_id="other/project"))
            request.assert_not_called()

    def test_dispatch_requires_explicit_privilege_allowlist(self):
        client = self.client()
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "privileges exceed"):
                client.start_flow(self.request(agent_privileges=()))
            request.assert_not_called()

    def test_dispatch_sends_governed_payload_and_returns_minimal_result(self):
        client = self.client()
        response = {
            "id": 71,
            "status": "running",
            "web_url": "https://gitlab.com/group/project/-/automate/agent-sessions/71",
            "summary": "Started",
            "service_account_id": 99,
        }
        with patch.object(client, "_request", return_value=response) as request:
            result = client.start_flow(self.request())
        args, kwargs = request.call_args
        self.assertEqual(args, ("POST", "ai/duo_workflows/workflows"))
        body = kwargs["payload"]
        self.assertEqual(body["agent_privileges"], [1, 2])
        self.assertEqual(body["pre_approved_agent_privileges"], [])
        self.assertTrue(body["allow_agent_to_request_user"])
        self.assertIn("Do not merge", body["goal"])
        self.assertEqual(result.workflow_id, 71)
        self.assertNotIn("service_account_id", result.as_dict())

    def test_duplicate_task_id_is_rejected_before_second_network_call(self):
        client = self.client()
        response = {
            "id": 72,
            "status": "running",
            "web_url": "https://gitlab.com/group/project/-/automate/agent-sessions/72",
        }
        with patch.object(client, "_request", return_value=response) as request:
            client.start_flow(self.request())
            with self.assertRaisesRegex(GitLabDuoDispatchError, "already has a dispatch record"):
                client.start_flow(self.request())
        self.assertEqual(request.call_count, 1)
        ledger_item = client._dispatch_ledger.get("CKN-123")
        self.assertEqual(ledger_item["state"], "submitted")
        self.assertEqual(ledger_item["workflow_id"], 72)

    def test_missing_durable_ledger_blocks_dispatch(self):
        client = GitLabDuoFlowsClient(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=lambda: "test-token",
            dispatch_authorizer=AllowAuthorizer(),
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1, 2),
            branch_protection_verifier=lambda _project, _branch: True,
        )
        with self.assertRaisesRegex(GitLabDuoDispatchError, "Durable dispatch ledger"):
            client.start_flow(self.request())

    def test_dispatch_rejects_workflow_outside_configured_allowlist(self):
        client = self.client()
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "Workflow definition"):
                client.start_flow(self.request(workflow_definition="unknown/v9"))
            request.assert_not_called()

    def test_dispatch_rejects_privilege_outside_configured_allowlist(self):
        client = self.client()
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "exceed the Core-configured"):
                client.start_flow(self.request(agent_privileges=(1, 99)))
            request.assert_not_called()

    def test_dispatch_fails_closed_when_gitlab_reports_protected_branch(self):
        client = GitLabDuoFlowsClient(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=lambda: "test-token",
            dispatch_authorizer=AllowAuthorizer(),
            dispatch_ledger=DuoDispatchLedger(f"{self.tempdir.name}/protected.sqlite3"),
            allowed_workflow_definitions=("developer/v1",),
            allowed_agent_privileges=(1, 2),
            branch_protection_verifier=lambda _project, _branch: False,
        )
        with patch.object(client, "_request") as request:
            with self.assertRaisesRegex(GitLabDuoDispatchError, "unprotected"):
                client.start_flow(self.request())
            request.assert_not_called()

    def test_get_flow_status_uses_gitlab_workflow_id_scalar(self):
        from unittest.mock import MagicMock

        client = self.client()
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = (
            b'{"data":{"duoWorkflowWorkflows":{"nodes":'
            b'[{"status":"running","webUrl":"https://gitlab.com/group/project/-/duo_workflows/123"}]}}}'
        )
        with (
            patch.object(client, "_acquire_token", return_value="test-token"),
            patch(
                "creator_app.agnes.gitlab_duo_dispatcher._open_without_redirect",
                return_value=response,
            ) as open_request,
        ):
            result = client.get_flow_status(123)
        request = open_request.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertIn(
            "$workflowId: AiDuoWorkflowsWorkflowID!",
            body["query"],
        )
        self.assertEqual(
            body["variables"]["workflowId"],
            "gid://gitlab/Ai::DuoWorkflows::Workflow/123",
        )
        self.assertEqual(result["status"], "running")

    def test_secret_assignment_pattern_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "credential material"):
            GitLabDuoFlowsClient.governed_goal("password = not-a-real-secret", task_id="CKN-123")

    def test_constructor_rejects_insecure_base_url(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            GitLabDuoFlowsClient(
                base_url="http://gitlab.com",
                project_id="p",
                credential_provider=lambda: "x",
                dispatch_authorizer=AllowAuthorizer(),
                dispatch_ledger=DuoDispatchLedger(f"{self.tempdir.name}/dispatch.sqlite3"),
                allowed_workflow_definitions=("developer/v1",),
                allowed_agent_privileges=(1, 2),
                branch_protection_verifier=lambda _project, _branch: True,
            )

    def test_gitlab_token_is_acquired_only_through_credential_broker(self):
        broker = CredentialBroker(
            environment={CredentialId.GITLAB_DUO_TOKEN: "broker-managed-test-token"}
        )
        provider = BrokerGitLabTokenProvider(broker)
        self.assertEqual(provider(), "broker-managed-test-token")
        self.assertTrue(
            broker.is_allowed(
                CredentialId.GITLAB_DUO_TOKEN,
                consumer="gitlab.duo.dispatcher",
            )
        )


class GitLabProtectedBranchVerifierTests(unittest.TestCase):
    def test_lists_rules_and_requires_existing_unprotected_branch(self):
        from unittest.mock import MagicMock

        verifier = GitLabProtectedBranchVerifier(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=lambda: "test-token",
        )
        rules_response = MagicMock()
        rules_response.__enter__.return_value = rules_response
        rules_response.read.return_value = b'[{"name":"main"}]'
        rules_response.headers.get.return_value = ""
        branch_response = MagicMock()
        branch_response.__enter__.return_value = branch_response
        branch_response.read.return_value = b'{"name":"agents/CKN-1","protected":false}'
        with patch(
            "creator_app.agnes.gitlab_duo_dispatcher._open_without_redirect",
            side_effect=[rules_response, branch_response],
        ):
            self.assertTrue(verifier("group/project", "agents/CKN-1"))

        rules_response.read.return_value = b'[{"name":"main"},{"name":"agents/*"}]'
        with patch("creator_app.agnes.gitlab_duo_dispatcher._open_without_redirect", return_value=rules_response):
            self.assertFalse(verifier("group/project", "agents/CKN-1"))
        self.assertFalse(verifier("other/project", "agents/CKN-1"))

    def test_branch_response_must_explicitly_report_unprotected(self):
        from unittest.mock import MagicMock

        verifier = GitLabProtectedBranchVerifier(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=lambda: "test-token",
        )
        for payload in (
            b'{"name":"agents/CKN-1","protected":true}',
            b'{"name":"agents/CKN-1"}',
            b'{"name":"agents/CKN-1","protected":"false"}',
        ):
            rules_response = MagicMock()
            rules_response.__enter__.return_value = rules_response
            rules_response.read.return_value = b"[]"
            rules_response.headers.get.return_value = ""
            branch_response = MagicMock()
            branch_response.__enter__.return_value = branch_response
            branch_response.read.return_value = payload
            with patch(
                "creator_app.agnes.gitlab_duo_dispatcher._open_without_redirect",
                side_effect=[rules_response, branch_response],
            ):
                self.assertFalse(verifier("group/project", "agents/CKN-1"))

    def test_transport_rejects_redirects_instead_of_forwarding_private_token(self):
        from urllib.request import Request

        handler = _RejectRedirectHandler()
        request = Request("https://gitlab.com/api/v4/projects")
        self.assertIsNone(
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://attacker.example/collect",
            )
        )
        opener = unittest.mock.MagicMock()
        response = unittest.mock.MagicMock()
        opener.open.return_value = response
        with patch("urllib.request.build_opener", return_value=opener) as build_opener:
            self.assertIs(_open_without_redirect(request, timeout=5), response)
        self.assertIs(build_opener.call_args.args[0], _RejectRedirectHandler)
        opener.open.assert_called_once_with(request, timeout=5)

    def test_branch_verifier_fails_closed_on_api_errors_or_missing_branch(self):
        import urllib.error
        from unittest.mock import MagicMock

        verifier = GitLabProtectedBranchVerifier(
            base_url="https://gitlab.com",
            project_id="group/project",
            credential_provider=lambda: "test-token",
        )
        with patch(
            "creator_app.agnes.gitlab_duo_dispatcher._open_without_redirect",
            side_effect=urllib.error.HTTPError("https://gitlab.com", 403, "Forbidden", {}, None),
        ):
            self.assertFalse(verifier("group/project", "agents/CKN-1"))

        rules_response = MagicMock()
        rules_response.__enter__.return_value = rules_response
        rules_response.read.return_value = b"[]"
        rules_response.headers.get.return_value = ""
        with patch(
            "creator_app.agnes.gitlab_duo_dispatcher._open_without_redirect",
            side_effect=[
                rules_response,
                urllib.error.HTTPError("https://gitlab.com", 404, "Not Found", {}, None),
            ],
        ):
            self.assertFalse(verifier("group/project", "agents/missing"))


class CapabilityAuthorityDispatchAuthorizerTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tempdir = tempfile.TemporaryDirectory()
        self.store = AuthorityStore(f"{self.tempdir.name}/authority.sqlite3")
        contract = {
            "version": "test",
            "capabilities": {
                DISPATCH_CAPABILITY_ID: {
                    "costClass": "high",
                    "requiresCredential": False,
                    "requiresSourceEvidence": True,
                    "evidenceKinds": ["git_commit"],
                }
            },
            "agents": {"CK-NEXUS-DISPATCHER": {"permissions": [DISPATCH_CAPABILITY_ID]}},
        }
        self.authority = CapabilityAuthority(
            contract,
            store=self.store,
            broker_adapter=Broker(),
            grant_secret=b"g" * 32,
        )
        self.identity = CallerIdentity("cknexus-service", "CK-NEXUS-DISPATCHER", "agent")
        self.authorizer = CapabilityAuthorityDispatchAuthorizer(
            self.authority,
            self.identity,
            approval_verifier=lambda approval_ref, request, project_id: (
                approval_ref == "approval:CKN-123"
                and request.task_id == "CKN-123"
                and project_id == "group/project"
            ),
        )
        self.store.seed_evidence(
            ref="git:commit:123",
            kind="git_commit",
            digest="a" * 64,
            task_id="CKN-123",
            quality=1.0,
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def request(self):
        request = DuoDispatchRequest(
            task_id="CKN-123",
            goal="Do a bounded implementation.",
            workflow_definition="developer/v1",
            source_branch="agents/cknexus/CKN-123",
            agent_privileges=(1, 2),
            confirmation_binding="",
            evidence_refs=("git:commit:123",),
            approval_ref="approval:CKN-123",
        )
        binding = self.authorizer.confirmation_binding(request, "group/project")
        return replace(request, confirmation_binding=binding)

    def test_missing_core_approval_verifier_fails_closed(self):
        authorizer = CapabilityAuthorityDispatchAuthorizer(
            self.authority,
            self.identity,
        )
        request = self.request()
        binding = authorizer.confirmation_binding(request, "group/project")
        request = replace(request, confirmation_binding=binding)
        with self.assertRaisesRegex(GitLabDuoDispatchError, "verified CK-NEXUS Core task approval"):
            authorizer.authorize(request, "group/project")

    def test_wrong_task_approval_is_denied(self):
        request = replace(self.request(), approval_ref="approval:other-task")
        binding = self.authorizer.confirmation_binding(request, "group/project")
        request = replace(request, confirmation_binding=binding)
        with self.assertRaisesRegex(GitLabDuoDispatchError, "approval was not verified"):
            self.authorizer.authorize(request, "group/project")

    def test_real_capability_authority_issues_and_consumes_bound_grant(self):
        grant_ref = self.authorizer.authorize(self.request(), "group/project")
        self.assertTrue(grant_ref)
        with self.store._db() as db:
            row = db.execute("SELECT used FROM grants WHERE grant_id=?", (grant_ref,)).fetchone()
        self.assertEqual(row["used"], 1)

    def test_missing_task_bound_evidence_is_denied(self):
        request = replace(self.request(), evidence_refs=("missing:evidence",))
        binding = self.authorizer.confirmation_binding(request, "group/project")
        request = replace(request, confirmation_binding=binding)
        with self.assertRaisesRegex(GitLabDuoDispatchError, "EVIDENCE_INVALID"):
            self.authorizer.authorize(request, "group/project")


if __name__ == "__main__":
    unittest.main()
