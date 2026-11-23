# Q10 Bandit finding review — exact code candidate efbb2ee

> Historical review only: this report is bound to source efbb2ee157fcfdedfde054508fafaf21cbaf88fa. Subsequent security fixes changed application/source files and introduced a canonical Q10–Q16 manifest. Do not use this report as current-candidate sign-off; generate and review the new Q10 artifact for the new source SHA.

**Review type:** AI-assisted source-context triage; not an independent third-party audit.
**Decision:** Owner sign-off still required. Q10 remains REVIEW_REQUIRED / NOT_VERIFIED.

## Evidence identity

| Field | Value |
|---|---|
| Source commit | efbb2ee157fcfdedfde054508fafaf21cbaf88fa |
| Source tree | 2da60b807af2c389f1a798a1443fa475f91a94ed |
| Runtime subject manifest | be62b62b04827ee7c90a090e59da8adf55212ed477671b99cb0dd885fa5a3d4b |
| Q10 workflow run | 45088376317 |
| Q10 report SHA-256 | 71dab5d573b4f2bf1bf0e31cf794c13b0be17c08e8f317b580b9f8bb4626b192 |
| Bandit JSON SHA-256 | 5d180508658f4bae93f170b69b2975d8e397e19a171a48292793f04b077d2547 |

## Scan totals

- 541 findings, all LOW; HIGH 0; MEDIUM 0.
- Dependency vulnerabilities: 0.
- Secret scan: PASS over 872 tracked files.
- Attack regression: 22/22 passed.
- 434 findings are under test paths; 107 are outside test paths.
- Bandit process exit was non-zero because LOW findings remain; the workflow threshold recorded zero HIGH/MEDIUM and aggregate open-source scan PASS.

## Non-test findings and dispositions

| Rule | Count | Source-level disposition |
|---|---:|---|
| B404 | 23 | Import-only warning. Importing subprocess is not execution; call sites are reviewed under B603/B607. |
| B105 | 23 | False-positive constants: boolean/status labels, credential reference names, OAuth URL, and policy labels; no credential values or API secrets identified. |
| B603 | 38 | Subprocess calls use argv lists, no shell=True; arguments are fixed or validated/bounded and execution is constrained. |
| B607 | 20 | Executable names resolve through the process PATH; call sites use fixed/validated arguments. PATH integrity remains an operator environment assumption. |
| B101 | 1 | One guarded internal invariant (cgroups is not None) inside the phase3_enabled branch; not the sole external authorization check. |
| B112 | 1 | Verification retries are bounded; exceptions do not produce VERIFIED and exhaustion returns FAILED. |
| B110 | 1 | Cleanup-only exception suppression while deleting a temporary Redis key; residual is possible cleanup leakage, not code execution or privilege escalation. |

### Reviewed subprocess call sites

- creator_app/agnes/execution/phase3/sandbox.py: compiler path from shutil.which; fixed compiler flags and paths under the sandbox policy directory.
- creator_app/agnes/execution/phase3/workspace.py and creator_app/agnes/execution/sandbox/workspace.py: Git operations use argument arrays; workspace paths are derived from managed workspaces; baseline commit must be a full hexadecimal SHA.
- creator_app/agnes/mcp_server.py: browser invocation uses a fixed sudo -n wrapper; exposed browser actions are fixed tool functions; open URLs pass HTTPS host allowlisting.
- creator_app/dynamic_verifier/verifier.py and creator_app/patch_verifier/verifier.py: exact SHA/digest checks, allowlisted engine/profile, digest-pinned trusted image, no shell, no network, disposable worktree/container.
- creator_app/sandbox_executor/executor.py: allowlisted engine, digest-pinned image, exact source SHA, bounded task/limits, no credentials, network denied, non-root container, patch-only result.
- creator_app/global_knowledge/ebook_ingest.py: pdftotext resolved from PATH; source file size and extraction size are bounded; argv list and timeout used.
- scripts/agnes_cgroup_v2_staging_gate.py: fixed sys.executable and constant child program; no user-provided command string.

### Full non-test finding index

| Rule | File | Line | Disposition key |
| B404 | creator_app/agnes/execution/phase3/sandbox.py | 4 | IMPORT_ONLY |
| B603 | creator_app/agnes/execution/phase3/sandbox.py | 125 | ARGV_NO_SHELL_REVIEWED |
| B404 | creator_app/agnes/execution/phase3/workspace.py | 5 | IMPORT_ONLY |
| B603 | creator_app/agnes/execution/phase3/workspace.py | 74 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/agnes/execution/phase3/workspace.py | 74 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/agnes/execution/phase3/workspace.py | 80 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/agnes/execution/phase3/workspace.py | 80 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/agnes/execution/phase3/workspace.py | 88 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/agnes/execution/phase3/workspace.py | 88 | PATH_RESOLUTION_REVIEWED |
| B404 | creator_app/agnes/execution/sandbox/workspace.py | 7 | IMPORT_ONLY |
| B603 | creator_app/agnes/execution/sandbox/workspace.py | 51 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/agnes/execution/sandbox/workspace.py | 51 | PATH_RESOLUTION_REVIEWED |
| B404 | creator_app/agnes/mcp_server.py | 22 | IMPORT_ONLY |
| B105 | creator_app/agnes/mcp_server.py | 668 | CONSTANT_NOT_SECRET |
| B105 | creator_app/agnes/mcp_server.py | 935 | CONSTANT_NOT_SECRET |
| B603 | creator_app/agnes/mcp_server.py | 993 | ARGV_NO_SHELL_REVIEWED |
| B105 | creator_app/agnes/mcp_server.py | 1006 | CONSTANT_NOT_SECRET |
| B105 | creator_app/agnes/mcp_server.py | 1014 | CONSTANT_NOT_SECRET |
| B105 | creator_app/agnes/mcp_server.py | 1030 | CONSTANT_NOT_SECRET |
| B105 | creator_app/agnes/mcp_server.py | 1051 | CONSTANT_NOT_SECRET |
| B105 | creator_app/agnes/mcp_server.py | 1076 | CONSTANT_NOT_SECRET |
| B105 | creator_app/agnes/mcp_server.py | 1101 | CONSTANT_NOT_SECRET |
| B101 | creator_app/agnes_runtime.py | 156 | GUARDED_INVARIANT |
| B105 | creator_app/ai_team/auto_reply_plugin.py | 270 | CONSTANT_NOT_SECRET |
| B105 | creator_app/ai_team/auto_reply_plugin.py | 299 | CONSTANT_NOT_SECRET |
| B105 | creator_app/ai_team/ck_coordination.py | 30 | CONSTANT_NOT_SECRET |
| B105 | creator_app/ai_team/ck_v3_executor.py | 56 | CONSTANT_NOT_SECRET |
| B112 | creator_app/control_plane/verification.py | 73 | BOUNDED_FAIL_CLOSED_RETRY |
| B105 | creator_app/credentials/credential_broker.py | 14 | CONSTANT_NOT_SECRET |
| B105 | creator_app/credentials/credential_broker.py | 15 | CONSTANT_NOT_SECRET |
| B105 | creator_app/credentials/credential_broker.py | 16 | CONSTANT_NOT_SECRET |
| B105 | creator_app/credentials/credential_broker.py | 20 | CONSTANT_NOT_SECRET |
| B105 | creator_app/credentials/gmail_oauth_connector.py | 20 | CONSTANT_NOT_SECRET |
| B404 | creator_app/device_bridge/attestation.py | 13 | IMPORT_ONLY |
| B603 | creator_app/device_bridge/attestation.py | 45 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/device_bridge/attestation.py | 45 | PATH_RESOLUTION_REVIEWED |
| B404 | creator_app/dynamic_verifier/verifier.py | 14 | IMPORT_ONLY |
| B603 | creator_app/dynamic_verifier/verifier.py | 204 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/dynamic_verifier/verifier.py | 204 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/dynamic_verifier/verifier.py | 217 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/dynamic_verifier/verifier.py | 217 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/dynamic_verifier/verifier.py | 256 | ARGV_NO_SHELL_REVIEWED |
| B603 | creator_app/dynamic_verifier/verifier.py | 269 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/dynamic_verifier/verifier.py | 269 | PATH_RESOLUTION_REVIEWED |
| B105 | creator_app/github_app.py | 60 | CONSTANT_NOT_SECRET |
| B404 | creator_app/global_knowledge/ebook_ingest.py | 13 | IMPORT_ONLY |
| B603 | creator_app/global_knowledge/ebook_ingest.py | 272 | ARGV_NO_SHELL_REVIEWED |
| B105 | creator_app/gmail_oauth.py | 20 | CONSTANT_NOT_SECRET |
| B404 | creator_app/n8n_intelligence/auto_developer.py | 8 | IMPORT_ONLY |
| B404 | creator_app/n8n_intelligence/auto_gitops.py | 8 | IMPORT_ONLY |
| B404 | creator_app/patch_verifier/verifier.py | 16 | IMPORT_ONLY |
| B603 | creator_app/patch_verifier/verifier.py | 163 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/patch_verifier/verifier.py | 163 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/patch_verifier/verifier.py | 174 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/patch_verifier/verifier.py | 174 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/patch_verifier/verifier.py | 196 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/patch_verifier/verifier.py | 196 | PATH_RESOLUTION_REVIEWED |
| B105 | creator_app/privacy_firewall/contracts.py | 14 | CONSTANT_NOT_SECRET |
| B404 | creator_app/sandbox_executor/executor.py | 16 | IMPORT_ONLY |
| B603 | creator_app/sandbox_executor/executor.py | 220 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/sandbox_executor/executor.py | 220 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/sandbox_executor/executor.py | 254 | ARGV_NO_SHELL_REVIEWED |
| B603 | creator_app/sandbox_executor/executor.py | 268 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/sandbox_executor/executor.py | 268 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/sandbox_executor/executor.py | 279 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/sandbox_executor/executor.py | 279 | PATH_RESOLUTION_REVIEWED |
| B603 | creator_app/sandbox_executor/executor.py | 308 | ARGV_NO_SHELL_REVIEWED |
| B607 | creator_app/sandbox_executor/executor.py | 308 | PATH_RESOLUTION_REVIEWED |
| B105 | creator_app/unified_control.py | 336 | CONSTANT_NOT_SECRET |
| B404 | scripts/agnes_cgroup_v2_staging_gate.py | 6 | IMPORT_ONLY |
| B603 | scripts/agnes_cgroup_v2_staging_gate.py | 41 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/ai_factory_preflight.py | 7 | IMPORT_ONLY |
| B603 | scripts/ai_factory_preflight.py | 34 | ARGV_NO_SHELL_REVIEWED |
| B603 | scripts/ai_factory_preflight.py | 72 | ARGV_NO_SHELL_REVIEWED |
| B607 | scripts/ai_factory_preflight.py | 72 | PATH_RESOLUTION_REVIEWED |
| B404 | scripts/ai_github_harvester.py | 5 | IMPORT_ONLY |
| B603 | scripts/ai_github_harvester.py | 47 | ARGV_NO_SHELL_REVIEWED |
| B105 | scripts/ai_provider_capability.py | 28 | CONSTANT_NOT_SECRET |
| B404 | scripts/ck-health.py | 13 | IMPORT_ONLY |
| B603 | scripts/ck-health.py | 37 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/collect_dev_status.py | 10 | IMPORT_ONLY |
| B603 | scripts/collect_dev_status.py | 59 | ARGV_NO_SHELL_REVIEWED |
| B603 | scripts/collect_dev_status.py | 70 | ARGV_NO_SHELL_REVIEWED |
| B607 | scripts/collect_dev_status.py | 70 | PATH_RESOLUTION_REVIEWED |
| B603 | scripts/collect_dev_status.py | 98 | ARGV_NO_SHELL_REVIEWED |
| B607 | scripts/collect_dev_status.py | 98 | PATH_RESOLUTION_REVIEWED |
| B110 | scripts/gate_distributed_idempotency.py | 59 | CLEANUP_ONLY_RESIDUAL |
| B404 | scripts/gate_observability.py | 3 | IMPORT_ONLY |
| B603 | scripts/gate_observability.py | 19 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/gate_postgres_dr.py | 7 | IMPORT_ONLY |
| B603 | scripts/gate_postgres_dr.py | 47 | ARGV_NO_SHELL_REVIEWED |
| B603 | scripts/gate_postgres_dr.py | 66 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/package_buyer_delivery.py | 8 | IMPORT_ONLY |
| B603 | scripts/package_buyer_delivery.py | 45 | ARGV_NO_SHELL_REVIEWED |
| B603 | scripts/package_buyer_delivery.py | 53 | ARGV_NO_SHELL_REVIEWED |
| B607 | scripts/package_buyer_delivery.py | 53 | PATH_RESOLUTION_REVIEWED |
| B105 | scripts/package_buyer_delivery.py | 317 | CONSTANT_NOT_SECRET |
| B404 | scripts/postgres_dr.py | 9 | IMPORT_ONLY |
| B603 | scripts/postgres_dr.py | 84 | ARGV_NO_SHELL_REVIEWED |
| B603 | scripts/postgres_dr.py | 94 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/production_readiness.py | 12 | IMPORT_ONLY |
| B603 | scripts/production_readiness.py | 42 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/release_check.py | 5 | IMPORT_ONLY |
| B603 | scripts/release_check.py | 79 | ARGV_NO_SHELL_REVIEWED |
| B404 | scripts/secret_scan.py | 4 | IMPORT_ONLY |
| B603 | scripts/secret_scan.py | 16 | ARGV_NO_SHELL_REVIEWED |
| B607 | scripts/secret_scan.py | 16 | PATH_RESOLUTION_REVIEWED |

## Final disposition

No HIGH or MEDIUM finding exists in this exact report. The 107 non-test LOW findings were reviewed by source context and classified above; no exploitable user-input-to-shell path was identified in the reviewed call sites. B110 remains a low operational cleanup residual.

This is not a human sign-off and does not change the machine report. A repository owner or independent reviewer must accept the dispositions before security_review_status can change from REQUIRED and before Q10 can be marked PASS. Do not rerun Bandit or Q10 on the unchanged application source during the existing lock window.
