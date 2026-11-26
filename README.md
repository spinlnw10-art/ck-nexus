# CK-NEXUS

**Governed Autonomous AI Operating System** — a self-hosted platform for AI orchestration, governed tool execution, persistent knowledge, and evidence-based operations.

CK-NEXUS is one platform with one canonical application runtime. **Agnes** is its AI orchestration and execution layer; the Creator Workspace is a user-facing workspace; and **/development** is an internal evidence dashboard. These are parts and interfaces of CK-NEXUS, not separate products or competing system identities.

> **Release decision: NO-GO for Production.** Do not treat a passing test subset, CI run, implemented feature, or running service as Production approval. The current release decision and gate evidence are maintained in [Release Status](RELEASE_STATUS.md) and the [Q10–Q16 Closure Contract](docs/Q10_Q16_CLOSURE_CONTRACT.md).

## Latest engineering status — 2026-11-26

This is a dated engineering snapshot, not a live Production-health claim.

| Area | Verified status |
|---|---|
| Governed GitLab Duo dispatcher | [PR #421](https://github.com/spinlnw10-art/ck-nexus/pull/421) is open; all 7 GitHub Actions workflows passed on head `86cd16b3c910dc71d19bbdcc954a4cbeae2a619b`; all 3 CodeRabbit review threads are resolved; Copilot review remains outstanding. |
| Homepage / status documentation | [PR #422](https://github.com/spinlnw10-art/ck-nexus/pull/422) updates the homepage, README, and release status; all 3 GitHub Actions workflows passed on head `1d2048ba2073a4e9d61e875bbff9d08a3dfb437b`; PR remains open for review. |
| CK-NEXUS Core bootstrap | [PR #420](https://github.com/spinlnw10-art/ck-nexus/pull/420) is open and stacked on PR #421; it is not merged. |
| Automated tests | Targeted suite: 45 passed on Termux and 45 passed on independent Ubuntu. Full Ubuntu suite: 1,026 passed, 2 skipped, 15 warnings. |
| Quality / security checks | Ruff checks, changed-file format check, `git diff --check`, and the documented Bandit reviewed-finding gate passed for the recorded scope. |
| MCP smoke test | Local Streamable HTTP initialize and tools/list returned HTTP 200; 35 tools were listed, including 3 GitLab Duo tools. Duo readiness correctly remained `ready=false` / `configured=false`; the smoke-test server was stopped. |
| Live integration | No live GitLab Duo dispatch was attempted. The target GitLab project remains empty; trusted Core bindings, broker credential, workflow definitions, and approved privilege IDs are still prerequisites. |
| Production release | **NO-GO.** No gate bypass, merge, credential provisioning, or deployment was performed. Q10–Q16 release evidence remains mandatory. |

Use the [CK-NEXUS web workspace](creator_app/web/index.html), [PR #421](https://github.com/spinlnw10-art/ck-nexus/pull/421), [PR #420](https://github.com/spinlnw10-art/ck-nexus/pull/420), and [Release Status](RELEASE_STATUS.md) for the supporting evidence. The dated test results above do not certify a newer commit or a live runtime.

## Start here

| Need | Open |
|---|---|
| Understand the system | [Unified Architecture](docs/CK_NEXUS_UNIFIED_ARCHITECTURE.md) · [Architecture](docs/ARCHITECTURE.md) |
| Run the application | [Quick start](#quick-start) · [Canonical Runtime Contract](docs/CK_NEXUS_UNIFIED_OPERATIONS_CONTRACT_V1.md) |
| See live development evidence | Start the Creator App and open **/development**; API: **/api/dev-status** |
| Understand Agnes and agent governance | [Agnes Master Upgrade](docs/CK-NEXUS-AGNES-MASTER-UPGRADE.md) · [Development Council](docs/DEVELOPMENT_COUNCIL.md) |
| Configure integrations | [Integration Hub](docs/INTEGRATION_HUB.md) |
| Review security and tests | [Security Audit](docs/SECURITY_AUDIT.md) · [Test Report](docs/TEST_REPORT.md) |
| Prepare a release | [Release Status](RELEASE_STATUS.md) · [Release Checklist](docs/RELEASE_CHECKLIST.md) · [Q10–Q16 Contract](docs/Q10_Q16_CLOSURE_CONTRACT.md) |
| Prepare customer delivery | [Seller Checklist](docs/SELLER_CHECKLIST.md) |

## What CK-NEXUS provides

- **Agnes orchestration** — interprets requests, plans bounded work, coordinates specialist roles, and reports outcomes.
- **Governed execution** — permission checks, approval gates, isolated workspaces, bounded workers, idempotency, verification, and a kill switch.
- **Brain, memory, and knowledge** — session/context handling, knowledge retrieval, observations, and evidence-linked learning workflows.
- **Skills and capabilities** — discoverable capability contracts and adapters for approved tools.
- **Integration layer** — server-side connectors such as GitHub and model providers, mediated by the Credential Broker and CK-NEXUS policy.
- **Operations and evidence** — status APIs, audit records, test results, release subjects, and deployment evidence.
- **User workspace** — a web interface for interacting with CK-NEXUS capabilities.

These are capability areas of the same platform. A capability is not considered Production-ready merely because its code or documentation exists; its required runtime and release evidence must also pass.

## System architecture

~~~text
Users / API / Web Workspace
            |
       Agnes Orchestrator
            |
  Skills · Agents · Knowledge · Memory
            |
 CK-NEXUS Core / L3 Authority
 State · Permissions · Policy · Approvals
            |
 Governed Execution Kernel
 Queue · Sandbox · Idempotency · Verify
            |
 Approved Tool and Provider Adapters
 GitHub · Model Providers · MCP · Other Integrations
            |
 Evidence · Audit · Release Gates
~~~

**Authority boundary:** CK-NEXUS Core / L3 Authority owns state, memory, permissions, policy, execution decisions, and evidence. External tools and workflow services are adapters only; they do not become policy or release authorities. All consequential mutations must pass the applicable CK-NEXUS permission, approval, idempotency, and verification controls.

## Quick start

Requirements: Python 3.11 or later.

Linux / macOS:

~~~bash
cp .env.example .env.local
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m creator_app.unified
~~~

Windows PowerShell:

~~~powershell
Copy-Item .env.example .env.local
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m creator_app.unified
~~~

Open http://127.0.0.1:8000. The canonical application entry point is:

~~~bash
python3 -m creator_app.unified
~~~

Legacy launchers may remain for compatibility, but new setup instructions and deployment definitions must use the canonical entry point and the [Canonical Runtime Contract](docs/CK_NEXUS_UNIFIED_OPERATIONS_CONTRACT_V1.md).

## Runtime and developer interfaces

| Interface | Purpose |
|---|---|
| GET /health | Application health/readiness endpoint |
| GET /api/status | Redacted application and configuration status |
| GET /docs | OpenAPI reference for the running build |
| /development | Internal development and evidence dashboard |
| GET /api/dev-status | Authenticated development-status snapshot |

The running build's OpenAPI document is authoritative for the complete API surface. Do not assume an endpoint or integration is available from a roadmap or historical report alone.

## Security and operating rules

- Keep production_status = NO-GO until every mandatory release gate is verified against the exact release subject and independently reviewed where required.
- Keep the MCP service bound to loopback (127.0.0.1:8765) under the current deployment contract; do not expose it directly to the public Internet.
- Keep credentials server-side in the approved credential mechanism. Never put keys, tokens, private keys, or secret values in source, README files, screenshots, or logs.
- Treat repository state, deployed runtime state, test results, and release evidence as separate facts; reconcile them before deployment.
- Do not reset, clean, overwrite, merge, or deploy over existing work without reviewing the exact diff and preserving required evidence.
- External tools have no CK-NEXUS policy authority. No evidence means no completion.

## Release readiness

Production promotion is fail-closed. The [Q10–Q16 Closure Contract](docs/Q10_Q16_CLOSURE_CONTRACT.md) defines the mandatory security, live-provider, sandbox, recovery, observability, clean-machine deployment, and final-release evidence.

A release claim must identify the exact source commit, source tree, runtime/deployment subject, test and security reports, and required independent review. Evidence from a different commit or runtime is historical evidence, not proof for the candidate being released.

Run the repository's release check from the intended, clean release environment:

~~~bash
python3 scripts/release_check.py
~~~

Then follow the complete [Release Checklist](docs/RELEASE_CHECKLIST.md). A successful command is one piece of evidence, not a substitute for the full release decision.

## Engineering records

Implementation phases and historical milestones (including R-series and Agnes Execution Kernel phases) are documented as engineering records under [docs/](docs/). They describe the evolution and validation of individual capabilities; they are not separate products, runtime entry points, or independent Production certifications.

Useful references:

- [Agnes Execution Kernel Phase 3](docs/AGNES_EXECUTION_KERNEL_PHASE3_HARDENED_PIPELINE.md)
- [Credential Broker and Provider Router](docs/R7_CREDENTIAL_BROKER_PROVIDER_CUTOVER.md)
- [Canonical R9–R11 Implementation](docs/R9_R11_CANONICAL_IMPLEMENTATION.md)
- [Plans and reports](docs/plans/)
- [Repository Issues](https://github.com/spinlnw10-art/ck-nexus/issues)
- [Repository Actions](https://github.com/spinlnw10-art/ck-nexus/actions)

---

**Product identity:** CK-NEXUS.
**AI orchestration and execution layer:** Agnes.
**Canonical application runtime:** creator_app.unified.
**Current release decision:** NO-GO until the exact candidate passes all mandatory gates.
