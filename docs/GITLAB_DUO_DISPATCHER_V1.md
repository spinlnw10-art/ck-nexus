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


## Discovered GitLab namespace (public metadata only)

- Group: CK-NEXUS-group
- Group URL: https://gitlab.com/groups/ck-nexus-group
- Group ID: 148654539
- Public visibility; created 2026-11-26.
- Unauthenticated GET /api/v4/groups/148654539/projects?include_subgroups=true
  returned an empty list. The user profile chokmantol has no public projects
  in the unauthenticated projects listing. Private projects cannot be ruled
  out from anonymous access.
- An environment-only Credential Broker probe reports gitlab.duo_token is
  not configured for consumer gitlab.duo.dispatcher. This probe did not inspect
  any separate persistent credential store. No token was read or shown.
- Therefore no target project ID/path, Premium/Ultimate entitlement, Duo
  Agent Platform enablement, project flow definitions, or actual privilege
  configuration could be verified. Live dispatch remains disabled.
- The existing local MCP endpoint binds only to loopback. The MCP SDK is
  declared in pyproject.toml but is not installed in this Termux Python
  environment; an install attempt stalled while building a platform dependency
  and was stopped. The MCP server has not been started. It is not exposed to
  ChatGPT over an authenticated remote MCP transport. No public tunnel or
  unauthenticated port exposure was created.
