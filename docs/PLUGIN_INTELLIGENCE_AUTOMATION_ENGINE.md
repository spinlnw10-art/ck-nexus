# CK-NEXUS Plugin Intelligence & Automation Engine

Status: IMPLEMENTATION IN PROGRESS — initial inventory/UI slice only; not production-ready.

## Chosen architecture

Use a hybrid design. CK-NEXUS Core owns intent interpretation, authority, policy, approvals, credentials, evidence and final decisions. A model-facing router may propose tools from a bounded, discovered tool catalog; deterministic workflow orchestration validates dependencies, policy decisions, retry/idempotency and evidence before any execution.

Existing R28 Universal Auto Connector Fabric is the connector substrate. Do not create a second MCP registry or bypass its schema verification, endpoint security, Credential Broker, risk classification or Evidence Ledger.

## Lifecycle

`DISCOVER_INSTALLED -> REGISTER -> DISCOVER_TOOLS -> VERIFY_SCHEMA -> PLAN -> POLICY_AUTHORIZE -> EXECUTE -> VERIFY_RESULT -> EVIDENCE`

- Only adapters installed in the current application build and explicitly registered connectors appear in the user-facing inventory.
- Installed, configured, authorized and connected are distinct states.
- Tool discovery is not execution authorization.
- Read-only tools may be proposed for routing only after schema verification and read-only activation.
- Write, destructive and unknown-risk tools remain unavailable unless CK Policy Authority supplies a trusted, scoped approval.
- External plugins never receive CK-NEXUS Core authority.
- Credentials are resolved only through Credential Broker; inventory responses must not expose tokens, credential references, private endpoint URLs or OAuth secrets.
- Every execution decision and result must be linked to Evidence Graph / connector evidence.

## Existing CK-NEXUS components to reuse

- `creator_app/connector_fabric`: canonical MCP/OpenAPI registry, schema discovery, risk classification, Credential Broker resolution and hash-chained connector evidence.
- `creator_app/global_knowledge/tool_discovery.py`: bounded discovery queries and candidate ranking only; observed candidates are not installed or trusted.
- `creator_app/control_plane/orchestrator.py`: deterministic bounded agent task graphs; it is not a connector authorization service.
- `creator_app/control_plane/task_store.py` and `worker.py`: durable task queue, leases, checkpoints and bounded retries; connector jobs must add policy checks and evidence correlation before reuse.
- `creator_app/capability_fabric`: descriptive capability inventory; catalog presence does not grant runtime execution rights.

## Hybrid orchestration

1. Intent parser produces a structured task plan and required capabilities.
2. Plugin Discovery searches only the installed catalog and verified connector snapshots.
3. AI Router ranks candidate tools using descriptions, schemas and task context; the model may propose but cannot authorize.
4. Workflow Engine validates prerequisites, ordering, bounded retries, idempotency and data handoffs.
5. CK Policy Authority independently evaluates each tool call and side effect.
6. Execution Gateway invokes only authorized adapters and records request/result metadata without secrets.
7. Result verifier checks output contracts and emits evidence; failed or incomplete work is not reported as done.

## Automation policy

- Read-only: may run automatically only when the user request, connector state and Core policy permit it.
- External communication, account changes, data mutation, writes and destructive operations: require scoped approval according to Core policy.
- Merge, release, deployment, credential changes and policy changes: remain separately gated and require explicit authorization.
- Scheduled/event-triggered workflows use durable job state, idempotency keys, bounded retries, dead-letter handling and auditable cancellation.

## Implementation phases

1. **Inventory and UI (implemented slice):** protected `/api/plugins` catalog, installed-only presentation, distinct auth states, connector metadata redaction and explicit user-initiated OAuth/discovery actions.
2. **Function search (initial implementation):** protected `/api/tools/search?q=...` and the Functions workspace search UI query only persisted schema-verified connector snapshots, rank namespaced functions, mark write/destructive risk and never return endpoint URLs, credentials, raw schemas or execution permission. The separate authenticated /api/tools/discovery/mcp-registry?q=... endpoint searches the official MCP Registry (latest active versions only), supports opaque cursor pagination and labels every result OBSERVED; no installation or execution action is exposed.
3. **Discovery and model binding:** refresh verified MCP/OpenAPI tool snapshots, normalize tool schemas and expose namespaced logical tools to the AI router without enabling execution.
4. **Policy-backed routing:** bind ToolAuthorizer to CK Capability Policy Authority signed grants; test deny-by-default, scopes, expiry, replay protection and approval references.
5. **Workflow orchestration:** DAG/state-machine execution, idempotency, durable resume, bounded retry, cancellation and evidence correlation.
6. **Automation triggers:** schedule/webhook/event sources with authentication, deduplication, rate limits and per-trigger policy.
7. **Independent validation:** security review, compatibility, regression, connector contract tests, staging and rollback evidence before any merge/deploy proposal.

## Current implementation boundary

The inventory and initial function-search slices add a redacted installed-adapter catalog, a Connections view and search over persisted schema-verified connector snapshots. They do not add general-purpose model tool execution, automatic background jobs, arbitrary OAuth discovery, OpenAPI execution or new authority paths. R28 currently uses fail-closed execution authorization and intentionally exposes no public connector execute endpoint; that remains unchanged.

## Responsive workspace requirements

- Desktop: persistent left navigation, fluid content gutter and two-column plugin cards where space allows.
- Tablet: compact navigation and content widths; plugin and function grids adapt without horizontal page scrolling.
- Phone: safe-area-aware bottom navigation with all primary destinations retained, stacked cards, sticky composer and a bounded audio dock.
- Small phones: fluid typography and spacing, reduced neural-stage dimensions and no fixed-width controls that force horizontal overflow.
- Landscape / short-height devices: compressed navigation and topology spacing.
- Use `100svh` with `100vh` fallback, `viewport-fit=cover`, safe-area insets, touch-friendly targets, focus-visible outlines and reduced-motion support.
- Verify layouts at 320, 360, 390, 768, 1024 and 1440 CSS-pixel widths, portrait and landscape where applicable.

## Acceptance criteria

- Uninstalled plugins and unregistered connectors are absent from the UI.
- Installed-but-unconfigured adapters are visible as setup-required, not connected.
- OAuth connect actions are disabled until prerequisites and encrypted token persistence are ready.
- Connector URLs and credential references are not exposed in the catalog API.
- Connector discovery never implies execution authorization.
- Tool execution remains denied without a trusted CK Policy Authority decision.
- All user-visible connection and execution statuses reflect API evidence, not optimistic UI assumptions.

### Official MCP Registry detail inspection

- Authenticated read-only search: `GET /api/tools/discovery/mcp-registry?q=...` with opaque cursor pagination.
- Authenticated read-only detail: `GET /api/tools/discovery/mcp-registry/details?name=namespace%2Fserver&version=latest`.
- Detail responses expose only bounded metadata: repository source/allowlisted HTTPS repository URL, package registry/identifier/version, transport/runtime hints, configuration variable names with required/secret flags, and remote hostnames.
- Secret values, package runtime arguments, full remote URLs and arbitrary website URLs are not returned. Non-allowlisted repository URLs are withheld.
- Both discovery endpoints return OBSERVED candidates only. They do not register connectors, resolve credentials, install packages, launch processes or authorize execution.
- Registry records remain untrusted until source/license/SBOM/provenance/security review, Connector Fabric schema validation, evidence correlation and CK-NEXUS Core approval.
