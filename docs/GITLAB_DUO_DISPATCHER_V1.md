# CK-NEXUS GitLab Duo Dispatcher — V1 Adapter

## Implementation status

The adapter, Credential Broker binding, Core CapabilityAuthority adapter,
SQLite dispatch ledger, and three registered MCP tools (redacted status, flow
start, and flow status) are implemented with local unit tests. The MCP tools
fail closed until a trusted Core bootstrap injects a fully governed client.
The adapter is not running and has not made an authenticated request to GitLab.

## Integration contract

- Flow creation: POST /api/v4/ai/duo_workflows/workflows.
- Status polling: GraphQL duoWorkflowWorkflows using the workflow global ID.
- GitLab token is acquired only through CredentialBroker using credential ID
  gitlab.duo_token and consumer gitlab.duo.dispatcher. No direct environment
  token reads occur in the dispatcher.
- GitLab project and base URL are runtime configuration, not secrets:
  GITLAB_DUO_PROJECT_ID and GITLAB_DUO_BASE_URL.
- Dispatch authorization uses the existing CapabilityAuthority and a verified
  CallerIdentity. A separate Core-owned task approval verifier must validate an
  opaque approval reference against the exact request, task, and project before
  the authority grant is consumed. A deterministic confirmation hash alone is
  not treated as proof of user approval.
- The checked-in capability-policy example does not contain
  integration.gitlab_duo.dispatch. The production policy/runtime was not
  inspected or modified. Live dispatch must remain disabled unless the actual
  runtime CapabilityAuthority policy explicitly grants this capability to a
  dedicated dispatcher identity.
- The proposed policy entry (not applied) should require:
  - capability ID integration.gitlab_duo.dispatch
  - costClass high (bound confirmation required)
  - requiresSourceEvidence true, with task-bound git_commit/artifact evidence
  - requiresCredential true, credentialRef gitlab.duo_token,
    credentialConsumer gitlab.duo.dispatcher
  - adminOnly true and a dedicated service identity with only this capability
  - a Core-owned task approval verifier that checks an opaque approval reference
    against the exact request/task before the capability grant is consumed
- A durable SQLite ledger records one task ID per attempted dispatch. A task
  with an ambiguous or failed submission cannot be retried under the same ID;
  reconcile it first and create a new task/approval only when appropriate.
- Flow requests require both a configured workflow-definition allowlist and
  a configured numeric agent_privileges allowlist. Privilege IDs must be
  discovered from the target GitLab project; they are not guessed or defaulted
  to all privileges.
- Before dispatch, a read-only GitLab API check enumerates all protected
  branch rules (including wildcard patterns) and confirms the exact source
  branch exists and is not protected. Pagination, permission, network, or
  parsing errors fail closed.
- pre_approved_agent_privileges is always empty.
- source branch must be under agents/ or feat/duo/, and the project override
  must match the Core-configured project. The Developer Flow is a CI-backed
  flow, so GitLab documents source_branch for this execution mode. The flow may
  also create its own duo-developer-backup/ branch while updating work; existing
  protected-branch rules and push rules must remain authoritative. The
  dispatcher does not change those rules and does not claim it can constrain
  every internal branch created by GitLab's managed flow.
- Every goal receives fixed restrictions: never access data/, secrets, or
  .env; never weaken security gates; never push protected branches; never
  merge, release, deploy, or change repository permissions.
- allow_agent_to_request_user is true so a flow can pause for user input.
- API errors are reduced to safe status messages; token values and response
  bodies are not included in exceptions or result objects.

## Required activation work

1. Have the CK-NEXUS Core policy owner review and add the capability entry and
   dedicated service identity permission. Do not modify the active policy
   automatically.
2. Confirm the GitLab group plan, Duo Agent Platform entitlement, project
   availability, flow definition, service-account identity requirements, and
   privilege IDs with an authorized GitLab administrator.
3. Configure the GitLab token through the Credential Broker only; do not put
   tokens in source files, chat messages, command arguments, or logs.
4. Inject the live CapabilityAuthority, verified CallerIdentity, broker token
   provider, project configuration, and persistent dispatch ledger into the
   runtime.
5. The MCP server now registers redacted status, controlled flow-start, and
   flow-status tools. The trusted bootstrap hook must inject the fully governed
   client only after the Core policy, identity, task-approval verifier,
   Credential Broker, project, and allowlists are configured.
6. Install the declared MCP SDK and remaining project dependencies in the
   Termux runtime, then start the existing loopback MCP server. Do not expose
   it remotely until an authenticated HTTPS/Secure MCP boundary is configured.
7. Run independent review on Ubuntu and complete regression tests before any
   push or external dispatch.

## Explicit non-goals

This adapter does not merge, deploy, alter protected-branch rules, modify
credential values, change security gates, or grant GitLab Duo authority over
CK-NEXUS Core. No runtime activation is implied by this document.


## Verified GitLab target metadata (read-only, 2026-11-26)

Authenticated GitLab connector reads confirmed:

- Group: `ck-nexus-group` (ID `148654539`), visibility `public`.
- Group settings: `duo_core_features_enabled=true`, `duo_features_enabled=true`,
  `duo_agent_platform_enabled=true`, `foundational_agents_default_enabled=true`,
  and `duo_remote_flows_enabled=true`.
- Group setting `duo_workflow_mcp_enabled=false`; this setting is recorded
  separately and has not been proven to block the REST/GraphQL Remote Flows API.
- Target project: `ck-nexus-group/CK-NEXUS-project` (ID `89471022`),
  visibility `private`, default branch `main`.
- Project settings: `duo_remote_flows_enabled=true` and
  `duo_foundational_flows_enabled=true`.
- The project is currently `empty_repo=true`, with zero commits, zero storage,
  and no source branches. Its workflow definitions and numeric agent privilege
  IDs therefore cannot yet be discovered or validated.
- GitLab's authenticated read-only connector identifies the account as
  `chokmantol`; no token or secret was read or exported.

Environment-only checks on both the Termux and Ubuntu shells found these
variables absent: `GITLAB_DUO_TOKEN`, `GITLAB_DUO_PROJECT_ID`,
`CKNEXUS_OMNI_IDENTITY_SECRET_HEX`, `CKNEXUS_OMNI_APPROVAL_VERIFIER`,
`CKNEXUS_CORE_IDENTITY_SECRET_HEX`, and `CKNEXUS_CORE_CONTRACT_PATH`.
These checks did not inspect `.env` files or any persistent credential store,
and do not prove that no separately configured vault exists.

## Remaining activation prerequisites

1. A Core-owned runtime must supply the real `CapabilityAuthority`,
   `IdentityVerifier`, signed dedicated dispatcher identity, and task-approval
   verifier. The current Termux and Ubuntu shells do not expose the expected
   identity/approval environment bindings.
2. Configure `GITLAB_DUO_TOKEN` through the protected CK-NEXUS Credential
   Broker for consumer `gitlab.duo.dispatcher`; never place it in source,
   chat, command arguments, or logs.
3. Populate the private GitLab project with an authorized repository source,
   then discover and explicitly allowlist the intended workflow definition and
   numeric agent privilege IDs. Do not guess these IDs or grant all privileges.
4. Confirm whether the group-level `duo_workflow_mcp_enabled=false` setting
   affects the selected integration path with a GitLab administrator.
5. Only after the above are satisfied may Core call
   `configure_gitlab_duo_dispatcher_from_core` with the real bindings and run
   a controlled non-production canary under the existing policy and review
   gates.

The group and project feature flags being enabled do not establish plan
entitlement, usable credentials, workflow availability, or permission to
dispatch. No live GitLab Duo dispatch has been attempted. The adapter remains
fail-closed and production deployment remains NO-GO.
