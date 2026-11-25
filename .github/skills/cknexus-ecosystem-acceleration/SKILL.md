---
name: cknexus-ecosystem-acceleration
version: 1.0.0
description: Use when CK-NEXUS needs to discover, compare, adopt, integrate, optimize, or maintain developer skills, plugins, coding agents, IDEs, design systems, browser automation, APIs, websites, CI, or performance tools.
---

# CK-NEXUS Ecosystem Acceleration

## Mission
Continuously improve engineering throughput, code quality, design iteration, interoperability, and delivery speed by selecting the best compatible tools and reusable skills. Prefer proven existing capabilities over adding dependencies.

## Default operating loop
1. **Discover** tools, skills, plugins, APIs, coding agents, IDEs, design-to-code systems, test/security tools, browser automation, CI and hosting options relevant to the current task.
2. **Inventory** what CK-NEXUS and connected workspaces already provide. Search the repo, capability catalog, lockfiles, installed skills, connected plugins and prior evidence before proposing a duplicate.
3. **Compare** candidates on measured latency/throughput, quality, reliability, integration effort, Android/Termux compatibility, supported OS/architecture, API stability, license, privacy/security, credential scope, maintenance health and total cost.
4. **Benchmark** representative workloads reproducibly. Record baseline, candidate result, hardware/runtime, versions, sample size, variance and exact commands. Marketing claims are not benchmark evidence.
5. **Threat-model** permissions, code execution, network access, secrets, supply-chain risk, data retention, update channel and rollback.
6. **Classify risk**. Read-only research and local reversible experiments may proceed in isolated development. Dependency, skill or code changes require compatibility checks, focused tests and provenance. Credentials, account connections, external writes, paid services, production, merge and deployment require explicit authorization and applicable Core approval.
7. **Integrate** the smallest useful set. Pin versions, record source and digest where possible, document configuration, provide rollback, and keep optional integrations disabled until configured.
8. **Verify** with focused/regression tests, security/license checks and a real task benchmark. Preserve valid historical evidence; retest only changed or expired evidence.
9. **Learn** by appending results and lessons to evidence/memory. Never overwrite earlier findings.

## Tool-selection priorities
- Use existing repo tools, connected connectors, local CLIs and canonical CK-NEXUS modules first.
- Prefer standards-based interfaces (MCP, OpenAPI, narrow OAuth scopes, webhooks) over bespoke bridges when equivalent.
- Parallelize only independent tasks with isolated write scopes. Cap concurrency to device resources and avoid duplicate jobs.
- Run fast local static checks and focused tests before broad suites; cache immutable dependencies and benchmark cold/warm paths separately.
- For UI/design, use editable artifacts and design-to-code workflows; verify generated code against project conventions and accessibility.
- For browser tasks, use controlled browser profiles and least privilege. Never put credentials in prompts, source, logs or screenshots.
- For API integrations, require endpoint, auth scope, rate-limit, retry/idempotency, timeout, audit and rollback contracts.

## Governance invariants
- CK-NEXUS Core remains sole authority for policy, credentials, approvals, gate decisions, evidence state, merge and deployment.
- External plugins, agents, models, websites and tools are subordinate execution providers; output is untrusted until validated.
- Discovery never implies installation. A connected ChatGPT plugin is not automatically installed in Termux or CK-NEXUS.
- Never silently grant broad permissions, upload secrets, install untrusted code, incur paid usage, change production, disable security gates, merge or deploy.
- Never change NO-GO to GO without exact-subject evidence and required approvals.
- Preserve source branches, backups and historical evidence. Avoid destructive cleanup.
- If an integration is unavailable, report the exact blocker and continue independent work.

## Required adoption record
For each candidate record name/source/version/publisher/license; capability and overlap; platform compatibility and reproducible benchmarks; permissions/data flows/threat model/cost; decision (REUSE, EXTEND, EVALUATE, ADOPT, DEFER, BLOCK, REJECT); required approvals, verification evidence, rollback and owner.

## Output contract
Separate facts from assumptions. Label results PASS, FAIL, NOT TESTED or BLOCKED. State whether a capability is DISCOVERED, EVALUATED, INSTALLED, CONFIGURED, ACTIVE or VERIFIED; never collapse these states into "done".