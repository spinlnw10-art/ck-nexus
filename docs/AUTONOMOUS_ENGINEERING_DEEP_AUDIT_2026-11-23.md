# CK-NEXUS Deep Repository Audit — 2026-11-23

Status: **Phase 1 structural audit complete; full branch/content audit remains open**  
Scope: seven CK-NEXUS-related repositories under `spinlnw10-art`. Read-only inspection only, except this audit documentation on the already-authorized integration branch.

## Executive findings

1. The canonical source remains `spinlnw10-art/ck-nexus` (`main`). Its tree contains 870 tracked files and is the only public repository in this seven-repository set.
2. The other six repositories are private. Their purposes differ: architecture stubs, dated runtime backup, emergency archive, AGNES skills/operations, and a separate React/Convex application.
3. The default-branch structural snapshots contain 1,192 tracked files in total. A cross-repository Git blob SHA comparison found **zero exact duplicate file contents** across these seven default-branch snapshots.
4. Ten basename overlaps were found. These are candidates for semantic comparison, not proof of duplication. In particular, the canonical MCP server and the 2026-09-15 backup MCP server have different sizes, blob hashes, protocols and responsibilities.
5. The canonical repository has **403 branches**. All branch names were enumerated successfully. The other six repositories have 18 branches combined. This audit did not fetch and compare every non-default branch tree; branch-level divergence remains open.
6. A tracked `nexus-check/.env.keys` file exists (416 bytes; blob SHA `fe72a7b3f6cdc78cc87d0754bf1cfe4b6d06c7f6`). Its content was deliberately not opened or copied. The current `.gitignore` only ignores `.env.local`, not `.env.keys`. Treat this as a **potential secret exposure requiring owner-led secure inspection and rotation if credentials are present**.
7. The emergency backup contains compressed archives and signed-attestation material. Archive payloads were not unpacked or verified in this GitHub-only pass. Preserve it as a recovery artifact.
8. No runtime code, secrets, data, backup, original branch or deployment was changed by this audit.

## Repository snapshot

Counts are from each default branch recursive Git tree. The `size` value reported by GitHub repository metadata is approximate repository size in KiB, not a file count.

| Repository | Default branch | Visibility | Tracked files | GitHub size (KiB) | Branches | Disposition |
|---|---|---:|---:|---:|---:|---|
| `ck-nexus` | main | public | 870 | 7,874 | 403 | Canonical source; KEEP |
| `CK-NEXUS-Ai` | main | private | 1 | 54 | 4 | Reference stub; preserve |
| `ck-nexus-pro-evolution` | main | private | 1 | 10 | 2 | Concept reference; preserve |
| `ck-nexus-runtime-backup` | main | private | 47 | 186 | 2 | Historical runtime backup; preserve |
| `ck-nexus-emergency-backup` | main | private | 21 | 124 | 1 | Emergency recovery archive; preserve |
| `agnes-brain` | master | private | 150 | 817 | 7 | Selective capability source; preserve |
| `nexus-check` | main | private | 102 | 202 | 2 | Separate UI/application; preserve |
| **Total** | | | **1,192** | | **421** | |

## Exact duplicate and overlap evidence

### Exact content duplicates

Method: compare Git blob SHA values for every blob in each default-branch recursive tree. Result: **0 blob SHA values shared between different repositories** in this seven-repository snapshot.

This establishes no exact byte-for-byte duplicates in the inspected default-branch trees. It does not rule out:
- near-duplicates with different formatting or edits;
- copies inside ZIP/TAR/GZIP archives;
- duplicates on non-default branches;
- generated or vendored code with different content;
- semantic duplication across differently named modules.

### Shared basenames (10)

| Basename | Repositories | Audit interpretation |
|---|---|---|
| `.env.example` | ck-nexus, agnes-brain, nexus-check | Configuration examples; compare variable contracts, never copy secrets |
| `README.md` | all except runtime-backup | Common filename only |
| `.gitignore` | ck-nexus, emergency-backup, agnes-brain, nexus-check | Compare ignore rules; nexus-check gap noted below |
| `mcp_server.py` | ck-nexus, runtime-backup | Different MCP server generations/purposes; not drop-in duplicates |
| `index.html` | ck-nexus, nexus-check | Different frontend entry points; ownership must be established |
| `app.py` | ck-nexus, runtime-backup | Different applications (gateway vs historical billing gateway) |
| `package.json` | ck-nexus, nexus-check | Compare dependencies/scripts before any frontend reuse |
| `index.ts` | ck-nexus, nexus-check | Filename overlap only |
| `tsconfig.json` | ck-nexus, nexus-check | Configuration overlap only |
| `STATUS.md` | runtime-backup, agnes-brain | Historical status documents; freshness differs |

## Targeted code/document inspection

### Canonical `ck-nexus`
The canonical architecture documents one runtime, with AGNES as orchestration/execution, Creator as workspace, and CK-NEXUS Core/L3 as the authority for identity, policy, approval, credentials, execution and evidence. Preserve this ownership model.

The current `creator_app/agnes/mcp_server.py` is a 41,529-byte FastMCP-based development MCP server, documented to bind to loopback and use a separately authenticated HTTPS boundary for remote access. It integrates the canonical Creator/AGNES/control-plane components.

### `ck-nexus-runtime-backup`
The 2026-09-15 snapshot contains 47 tracked files, including historical API hub, MCP server, state API, key-management and billing components. Its backup status document reports earlier security remediation and explicitly keeps production NO-GO pending human verification.

The backup `scripts/mcp_server.py` is a 4,999-byte stdlib JSON-RPC subset proxying a historical API hub on loopback port 8905. It is not the same component as the canonical FastMCP development server. Do not overwrite the canonical server with it.

The backup `billing-gateway/app.py` is a distinct historical SQLite billing service, not the current `gateway/app.py`. Static inspection found a suspicious unresolved expression `lim[daily_limit]` in its rate-limit error path. Treat this as legacy code requiring tests and security review, not a migration candidate.

The backup `tests/test_security_contract.py` asserts that provider keys are not embedded in selected scripts, database passwords are environment-provided, and internal MCP/state listeners bind to loopback. These are useful historical contract ideas; the test suite must be run against the exact backup snapshot before relying on it.

### `agnes-brain`
The repository describes an established skill/operations ecosystem: multi-provider routing, research, health/supervisor/watchdog, self-heal, model registry and PubNub MCP. Its own capability audit labels itself a source-based proposal, not proof of live VPS state.

Reuse candidates should be selectively adapted behind CK-NEXUS contracts:
- research and evidence capture;
- provider routing metadata, quotas and backoff;
- health/readiness contracts and bounded restart logic;
- PubNub/MCP event transport with explicit authentication and approval gates;
- sanitized operational lessons and regression tests.

Do not import a second AGNES runtime or transfer credentials, personal data, raw logs or broad self-healing privileges. The repository's historical STATUS material includes sensitive operational/account details; it should not be copied into public evidence or the canonical repository.

### `nexus-check`
This is a separate Vite/React/Convex application with its own authentication and backend. Its README explicitly says authentication configuration files must not be modified. It is not yet proven to be the canonical Creator UI or a safe replacement for it.

**Security flag:** `.env.keys` is tracked in the default-branch tree. The content was intentionally not retrieved. `.gitignore` currently lists `.env.local`, but not `.env.keys`. Owner should inspect the file in a secure local environment, determine whether it contains credentials, revoke/rotate any real credentials, then remove secret material from tracked history using a separately reviewed procedure. Do not paste the file contents into chat or PR comments.

### `ck-nexus-emergency-backup`
The repository contains a manifest, signed-attestation coverage documents and compressed archives. The attestation manifest identifies the pack-003 copy as canonical for that particular signed artifact and marks pack-001/pack-002 copies historical. Preserve the archive and its signature context together. This GitHub-only audit did not unpack archives, verify signatures cryptographically, or validate the ZIP/TAR payload contents.

### `CK-NEXUS-Ai` and `ck-nexus-pro-evolution`
Their default branches contain only a README each. Their branch names indicate additional experiments, but no runtime implementation was established from the default-branch content. Preserve as reference repositories; inspect branch heads before deciding whether any work is worth porting.

## Security and evidence flags

| ID | Severity | Finding | Required handling |
|---|---|---|---|
| SEC-01 | High / unconfirmed | Tracked `nexus-check/.env.keys`; not ignored by current `.gitignore` | Secure local inspection; rotate if secret; separately plan history cleanup |
| SEC-02 | Medium | Historical backup contains key-management and bulk key-import utilities | Review permissions, audit logs, input handling and secret redaction before reuse |
| SEC-03 | Medium | Legacy billing gateway contains a suspicious error-path expression and lacks current compatibility evidence | Do not port; reproduce with tests or retire from candidate set |
| SEC-04 | Medium | Emergency archive payloads were not unpacked or cryptographically verified in this pass | Preserve; verify checksums/signatures and restore only in isolated environment |
| SEC-05 | Medium | Historical AGNES operational status contains sensitive account/operational details | Restrict access; redact before copying or publishing |
| EVD-01 | Open | No full recursive tree comparison for 403 canonical non-default branches | Continue branch-head and tree inventory in batches |
| EVD-02 | Open | No full-content similarity scan / AST-level comparison | Run normalized hashes and language-aware comparison on candidate files |
| EVD-03 | Open | No live VPS, database, runtime or backup-restore access in this audit | Do not claim runtime health or recoverability |

## Recommended migration decisions

- **KEEP:** canonical `ck-nexus` runtime and authority contracts.
- **ADAPT:** selected AGNES skills (research, provider routing patterns, health contracts, PubNub/MCP transport) after interface, license, dependency and security review.
- **REFERENCE ONLY:** CK-NEXUS-Ai and Pro Evolution until their non-default branches are inspected.
- **PRESERVE / NO BULK IMPORT:** dated runtime backup and emergency backup. Use only as historical source material with provenance and per-file review.
- **SEPARATE PRODUCT REVIEW:** nexus-check. Determine whether it is an independent portal, a prototype, or intended Creator UI before any consolidation.
- **DO NOT DELETE:** any repository, branch, archive, file or historical record as part of this audit.

## Next audit batch

1. Capture exact commit SHA and recursive tree SHA for every branch in all seven repositories, starting with the 403 CK-NEXUS branches in paginated batches.
2. Prioritize branches named `audit/*`, `backup/*`, `feat/agnes*`, `feat/*memory*`, `feat/*codex*`, `integration/*`, `fix/q10*` and `ops/*`.
3. Compare branch trees to canonical main and classify unique files/commits; do not cherry-pick solely by branch name.
4. Run normalized-content and AST similarity scans on candidate source files; inspect archives in an isolated, no-network workspace.
5. Securely resolve SEC-01 before using nexus-check in any integration.
6. Add migration rows with source SHA, destination contract, dependency/test plan, rollback and owner approval.
7. Only after this evidence is complete, propose narrowly scoped runtime implementation PRs. No merge, deploy, delete or credential operation is authorized by this audit.

## Audit limits

This is a structural and targeted-content audit, not a certification that all code is safe or functional. Default-branch tree enumeration is complete for the seven repositories listed; branch names are fully enumerated, but non-default branch trees and all source contents are not yet fully reviewed. No test suites were executed in a checkout. No secret values were retrieved or reproduced.
