# CK-NEXUS Governed Autonomous Engineering Integration Plan

Status: **proposal / documentation baseline only**  
Target: canonical CK-NEXUS runtime  
Implementation policy: preserve existing authority boundaries; no production mutation.

## 1. Decision

Integrate capabilities into the existing CK-NEXUS platform. Do not create a competing orchestrator or a second canonical runtime.

- AGNES remains the central orchestration and execution layer.
- Creator Workspace remains the user-facing project/task interface.
- Development Council remains advisory; it does not gain mutation authority.
- CK-NEXUS Core / L3 Authority remains the owner of identity, state, permissions, policy, approvals, credentials, execution decisions and evidence.
- Codex/engineering workers remain bounded execution adapters operating in isolated worktrees.
- Q10 backups, sessions and audit evidence are linked by stable project, task and run identifiers.

## 2. Current repository evidence

The current source already documents or implements:
- canonical runtime `creator_app.unified`;
- AGNES runtime, skill registry, dispatcher, policy and append-only ledger;
- provider routing and credential broker;
- Creator Runtime and session persistence;
- Development Council with five advisory roles;
- isolated engineering workflow and deterministic verification;
- Q10-Q16 fail-closed production closure contract.

Relevant source:
- `creator_app/agnes_runtime.py`
- `creator_app/runtime.py`
- `creator_app/provider_router.py`
- `creator_app/credential_broker.py`
- `docs/CK_NEXUS_UNIFIED_ARCHITECTURE.md`
- `docs/ARCHITECTURE.md`
- `docs/DEVELOPMENT_COUNCIL.md`
- `docs/Q10_Q16_CLOSURE_CONTRACT.md`
- `RELEASE_STATUS.md`

## 3. Target capability map

| Capability | Canonical owner | Integration direction | Initial safety boundary |
|---|---|---|---|
| Intent intake and task planning | AGNES | reuse existing orchestration contracts | planning is not approval |
| Specialist consultation | Development Council / skill registry | reuse existing agents and role contracts | advisory only |
| Model selection | Provider Router | extend capability/cost/health metadata only after tests | credentials remain brokered |
| Creator workspace | Creator application | add project/task/session/evidence views | no direct privileged writes |
| Codex sessions | engineering worker adapter | persist session-to-task and worktree references | isolated worktree; no implicit merge |
| Backup/checkpoint | backup adapter | bind snapshot IDs and hashes to task/run | preserve originals; verify restore separately |
| Audit/evidence | append-only ledger + evidence bundle | correlate events with project/task/run/commit | append-only; redact secrets |
| Verification | independent test/security workers | publish machine-readable results | executor cannot self-certify |
| Release | release gate | consume exact-subject evidence | Q10-Q16 remains fail-closed |

## 4. Correlation contract

Every engineering operation should carry:
- `project_id`
- `task_id`
- `run_id`
- `agent_identity`
- `capability_lease_id`
- `approval_id` when applicable
- `codex_session_id` when applicable
- `worktree_ref` and `git_branch`
- `backup_id` and source/tree digests when applicable
- `audit_event_ids`
- `verification_bundle_id`
- `pull_request_url` when applicable

Do not store provider secrets, raw API keys, or sensitive credential values in session metadata, audit events, or evidence bundles.

## 5. Proposed workflow

1. Creator receives a request and creates a project/task record.
2. AGNES classifies risk and prepares a bounded plan.
3. Advisory agents may research, design, build-plan and review.
4. CK-NEXUS policy evaluates capability, lease, budget, reversibility and approval requirements.
5. For approved code changes, create a verified backup/checkpoint and isolated worktree.
6. Start or resume a Codex engineering session bound to the task and worktree.
7. Execute bounded changes; capture tool events and outputs in the ledger.
8. Run deterministic tests and independent security/QA verification.
9. Assemble an evidence bundle tied to exact commit/tree/runtime subjects.
10. Open a Pull Request. Human review remains mandatory for merge and release.
11. Keep production promotion blocked until the exact candidate passes every applicable Q10-Q16 gate.

## 6. Delivery phases

### Phase A — inventory and contracts
- inventory canonical and related repositories;
- identify duplicate/legacy implementations and ownership;
- map existing schemas, session stores, backup formats and audit event contracts;
- reconcile external design references and the user's spreadsheet when accessible.

### Phase B — correlation and observability
- define stable IDs and event schemas;
- link Creator runs, AGNES execution, Codex sessions, worktrees, backups and evidence;
- add redaction and retention rules.

### Phase C — Creator engineering workspace
- project/task/session timeline;
- agent activity and approval status;
- evidence and PR links;
- resume/retry from verified checkpoints.

### Phase D — Codex worker adapter
- explicit session lifecycle;
- isolated worktree lifecycle;
- bounded tool permissions and budgets;
- deterministic verification;
- PR-only delivery by default.

### Phase E — backup and recovery
- snapshot manifest and integrity verification;
- isolated restore rehearsal;
- recovery-point and recovery-time objectives;
- no destructive restore against seller/current working databases.

### Phase F — controlled self-improvement
- collect evaluation results and failure patterns;
- propose changes, never self-authorize them;
- implement in a branch/worktree;
- require independent review and evidence before merge.

## 7. Non-goals for this integration baseline

- no new competing runtime;
- no automatic production deployment;
- no automatic merge;
- no deletion or overwrite of original branches, backups or data;
- no agent-controlled changes to policy, permissions or its own approval;
- no claim of Production readiness based on documentation or partial CI.

## 8. Acceptance criteria

- all new workflows use the canonical runtime and existing authority chain;
- each task can be traced across Creator, AGNES, Codex, backup, audit and PR;
- every consequential mutation is permission-checked and approval-gated;
- code execution is isolated and idempotent;
- verification is independent of the executor;
- evidence is bound to the exact source and runtime subject;
- recovery is demonstrated on an isolated target;
- Q10-Q16 remains NO-GO until all required exact-subject gates pass.

## 9. Open evidence dependencies

The Pinterest short URL and Google Sheets document were supplied by the user, but their underlying content has not yet been retrieved in this execution context. No feature or requirement is attributed to either source until the pin destination/media and spreadsheet contents are inspected. The user should provide the pin image/expanded URL and an exported XLSX/CSV (or enable an authorized Sheets connector) to complete source-to-system traceability.

## 10. Change scope of this PR

Documentation-only integration baseline. No runtime code, database, backup, secrets, branch history, deployment or production configuration is changed.
