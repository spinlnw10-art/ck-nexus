# CK-NEXUS Related Repository Inventory

Status: initial evidence snapshot; not a complete file-level duplicate audit.

## Repositories discovered

| Repository | Visibility | Default branch | Observed purpose | Initial disposition |
|---|---|---|---|---|
| `spinlnw10-art/ck-nexus` | Public | `main` | Canonical governed autonomous AI operating system | canonical source; preserve |
| `spinlnw10-art/CK-NEXUS-Ai` | Private | `main` | AI agent orchestration / governance platform | inspect for reusable contracts; do not merge wholesale |
| `spinlnw10-art/ck-nexus-pro-evolution` | Private | `main` | Organic architecture, self-learning and adaptive UI concepts | research/reference; verify code maturity before reuse |
| `spinlnw10-art/ck-nexus-runtime-backup` | Private | `main` | Runtime backup repository (repository description) | preserve as backup source; inspect tree/manifests before use |
| `spinlnw10-art/ck-nexus-emergency-backup` | Private | `main` | Emergency backup dated 2026-09-27 (repository description) | immutable reference; never treat as disposable |

## Canonical architecture evidence

The canonical README states that CK-NEXUS is one platform with one canonical application runtime; AGNES is its orchestration/execution layer; Creator Workspace is the user-facing workspace; and `/development` is an internal evidence dashboard.

The unified architecture defines this authority chain:

Human Principal -> Agent Identity -> Capability Lease -> Policy/Reversibility -> Approval Registry -> Credential Reference Broker -> Deny-by-default Sandbox -> Execution Envelope/Journal -> Executor -> Independent Effect Verification -> Evidence Record/Evidence Graph.

It also explicitly distinguishes discovered/approved, authorized/executed, executed/verified and verified/production.

## Evidence inspected

- canonical `README.md`;
- `docs/CK_NEXUS_UNIFIED_ARCHITECTURE.md`;
- `docs/ARCHITECTURE.md`;
- `docs/Q10_Q16_CLOSURE_CONTRACT.md`;
- `RELEASE_STATUS.md`;
- `docs/DEVELOPMENT_COUNCIL.md`;
- `creator_app/agnes_runtime.py`;
- `creator_app/runtime.py`;
- README files for the two private architecture/reference repositories.

## Retrieval limitations

- README retrieval for both backup repositories returned HTTP 404 through the connected GitHub file action. This is not evidence that the repositories are empty or inaccessible in GitHub; their trees and contents remain unverified.
- Private repository README summaries are minimal and insufficient to establish code overlap or safe migration.
- No branch, file, commit, backup object or history was deleted or rewritten.
- Pinterest media and Google Sheets contents were not available for inspection in this audit snapshot.

## Required next audit

1. Enumerate every branch and full recursive file tree for all five repositories.
2. Capture commit SHA, tree SHA, path, blob SHA, size and file mode.
3. Detect exact duplicates by blob SHA and near-duplicates by normalized content hash.
4. Classify each file: canonical, reusable, historical, generated, secret-bearing, orphaned, conflicting or unknown.
5. Compare runtime behavior and tests, not filenames alone.
6. Produce a migration matrix with source/destination, dependency order, rollback and evidence.
7. Require owner approval before any destructive operation or cross-repository migration.
