# CK-NEXUS Migration Matrix — Initial Evidence-Based Disposition

Status: preliminary; no migration or deletion executed.

| Source repository / artifact | Candidate capability or data | Proposed action | Destination | Preconditions | Risk / rollback |
|---|---|---|---|---|---|
| ck-nexus main | AGNES, Creator, control plane, provider router, audit/evidence | KEEP as canonical | same repository | preserve authority boundaries | Critical; no replacement |
| CK-NEXUS-Ai main + branches | orchestration/governance concept | REFERENCE; inspect branch diffs | contracts only if unique | inspect all 4 branch trees and tests | Low current evidence; preserve repo |
| ck-nexus-pro-evolution main + phase1 branch | organic/self-learning architecture concept | REFERENCE; inspect phase1 | selected design docs only | inspect branch tree, provenance, tests | Self-modification risk; no policy authority |
| ck-nexus-runtime-backup main | historical API hub/MCP/state/billing/scripts | PRESERVE; selective ADAPT only | canonical adapters after review | provenance, security scan, tests, contract mapping | High; never overwrite canonical modules |
| ck-nexus-emergency-backup main | ZIP/TAR archives, signed attestations, Caddy snapshots | PRESERVE as recovery artifact | isolated recovery vault | checksum/signature validation and restore rehearsal | Critical; never unpack into live runtime |
| agnes-brain master | research, provider routing, health, watchdog, PubNub MCP, skills | ADAPT selected skills | AGNES skill/adapter interfaces | license/dependency review, least privilege, sanitization, tests | High; retain original and feature-flag adapter |
| nexus-check main | React/Convex UI, auth, dashboard | SEPARATE PRODUCT REVIEW; no merge yet | Creator only if product owner confirms | resolve .env.keys flag; inspect auth/data ownership and routes | High; preserve auth files and separate deployment |
| OpenClaw repository | external agent framework / skills | REFERENCE ONLY | isolated adapters if needed | pin version/license/security review | High supply-chain risk; no bulk copy |

## Candidate-level decisions

| Candidate | Evidence | Decision |
|---|---|---|
| Current canonical FastMCP server | `creator_app/agnes/mcp_server.py`, loopback and canonical contracts | KEEP |
| Dated backup stdlib MCP API-hub server | different protocol subset and historical API-hub upstream | DO NOT REPLACE canonical MCP; consider only as historical adapter reference |
| Dated backup billing gateway | separate SQLite billing service; suspicious error-path expression; no current tests verified | DO NOT MIGRATE until repaired and independently tested |
| AGNES research/provider/health patterns | documented in agnes-brain capability audit; source exists | ADAPT individually behind CK-NEXUS policy and evidence |
| PubNub MCP | existing adapter with approval/security contracts | EVALUATE as transport adapter; CK-NEXUS remains authority |
| nexus-check auth and dashboard | independent Convex Auth stack; README forbids modifying auth configuration | KEEP SEPARATE pending product/tenant/data ownership decision |
| emergency archive payloads | compressed files plus signature/attestation docs | PRESERVE; no payload migration until isolated verification |
| tracked `.env.keys` | tree entry exists; content intentionally not retrieved | SECURITY HOLD; secure inspection/rotation/history plan before use |

## Mandatory per-file migration record

For every proposed file move/copy, record:
- source repository, branch, commit SHA, path, blob SHA and license;
- destination path and owning subsystem/contract;
- exact vs normalized similarity result;
- dependency and secret scan results;
- tests and runtime compatibility evidence;
- backup/checkpoint ID and rollback steps;
- approval ID and reviewer;
- post-migration verification and evidence bundle.

No file should be classified as deletable solely because it is old, duplicated by filename, or absent from the canonical default branch.
