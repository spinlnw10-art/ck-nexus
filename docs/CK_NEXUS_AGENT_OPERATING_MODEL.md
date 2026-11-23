# CK-NEXUS Agent Operating Model

Status: implemented on the PR #413 feature branch; not merged or activated in production. External profile activation still depends on the target agent harness supporting repository customizations.

## Purpose

Provide reusable specialist roles and skills for GitHub Copilot-compatible agent environments. These profiles do not create new runtime processes, grant external permissions, provide API credits, or independently authorize production actions. They define role-specific instructions and tool scopes for supported agent harnesses.

## Integration with the existing CK-NEXUS runtime

The repository already contains a separate in-process team in creator_app/ai_team/
(Director, Engineer, Guardian, Analyst, Researcher, Designer, and Connector), plus a
control-plane graph with research, implementation, verification, and security roles.
Its MCP inventory surfaces include cknexus_autonomy_status, cknexus_dev_assistants,
cknexus_dev_execution_plan, and cknexus_auto_dispatch.

These are distinct layers:

- The existing CK-NEXUS runtime roles are internal application behavior.
- The .github/agents/*.agent.md files are GitHub Copilot custom-agent profiles.
- The .github/skills/*/SKILL.md files are reusable task procedures.
- A profile file does not itself start a worker, authenticate a provider, or grant tools.
- Use cknexus_autonomy_status for inventory first; it is read-only and must not be
  interpreted as proof that an inference provider is authenticated or healthy.
- cknexus_dev_execution_plan is plan-only. Do not treat a planned task as executed.
- cknexus_auto_dispatch may invoke the in-process team; use it only for bounded
  development planning/work and retain the existing approval and evidence gates.

## Integrated AGNES capability fabric

The feature branch also connects the existing `BrainRuntime` to a deterministic `ExpertRouter`, external-assistant planning, append-only experiential memory, and fail-closed skill admission. See [AGNES Capability Fabric](AGNES_CAPABILITY_FABRIC.md) and the [System Skills Catalog](../capabilities/system-skills.catalog.json) for lifecycle, evidence, cost, and authority boundaries. These components produce plans and pending evidence; they do not start external workers, install skills, or grant Core authority.

## Primary system and subordinate-assistant hierarchy

Use an evidence-first hierarchy. Do not replace a working CK-NEXUS control plane with an external agent framework merely because the external project has more features.

| Tier | System | Assigned responsibility | Promotion rule |
| --- | --- | --- | --- |
| 0 — Authority | CK-NEXUS Core/L3 | Canonical state, permissions, policy, credentials, approvals, execution authority, and evidence | Never delegated |
| 1 — Primary runtime | Existing ControlPlaneOrchestrator + TeamDirector/internal team, with AGNES execution controls, ProviderRouter, ConnectorFabric, and append-only evidence | Plan and coordinate work, route model inference, call approved tools, verify results, and record evidence | Remains the primary path; improve in place rather than adding a competing orchestrator |
| 2 — Specialist assistants | The seven .github/agents profiles in this repository | Planning, implementation, security review, test verification, evidence stewardship, recovery, and coordination | Advisory/delegated only; active only when the host supports the profile and delegation |
| 3 — External coding workers | OpenCode, Aider, OpenHands, Gemini CLI, Claude Code, Cline, Goose, mini-swe-agent through DevAssistantFabric | Optional bounded research/edit/test workers in disposable worktrees or sandboxes | Candidate until exact executable, version, license, provider, isolation, and end-to-end task evidence are verified |
| 4 — Domain tools | Syft/Grype, ORT/ScanCode, Promptfoo, OTel Collector, GUAC, and similar tools | Narrow scans, evaluations, telemetry, and machine-readable evidence | Never agents or policy authorities; outputs require source/subject binding and CK-NEXUS verification |

### Evidence-based selection criteria

Rank candidate systems by, in order: (1) demonstrated end-to-end task success on the exact commit and target platform; (2) reproducible tests and CI; (3) security/isolation and least-privilege behavior; (4) provenance, license, and maintenance; (5) integration cost and resource fit; and (6) model/provider cost and offline capability. Feature count, popularity, or documentation claims alone do not qualify a system for the primary tier.

Use explicit lifecycle labels:
- VERIFIED: exact version/commit and target-platform smoke/tests passed with retained evidence.
- CANDIDATE: source and contract reviewed, but target-platform or end-to-end execution remains unverified.
- REFERENCE_ONLY: useful design/code reference, not activated for work.
- BLOCKED: a required dependency, credential, signature, platform capability, or policy check is unavailable.

Current adoption decision: keep the existing CK-NEXUS runtime as the sole primary system. The seven specialist profiles are the first subordinate layer. External CLIs remain candidates until individually installed and exercised through a real bounded task. In particular, a failed Termux package-source/signature preflight is BLOCKED, not an installation success. No external assistant receives Core/L3 authority or raw credentials.

## Specialist roles

| Role profile | Default tool scope | Responsibility |
| --- | --- | --- |
| CK-NEXUS Coordinator | Read, search, agent delegation | Decompose work, coordinate reviewers, maintain status/evidence ledger |
| CK-NEXUS Planner | Read, search | Plan changes without editing |
| CK-NEXUS Implementer | Read, search, edit, execute | Make narrow changes, add tests, commit/push to intended branch |
| CK-NEXUS Security Reviewer | Read, search | Independent read-only adversarial review |
| CK-NEXUS Test Verifier | Read, search, execute | Reproduce and verify changes |
| CK-NEXUS Evidence Steward | Read, search | Validate evidence completeness, provenance, and subject identity |
| CK-NEXUS SRE Recovery | Read, search, execute | Diagnose SSH, Termux, and service recovery paths |

The available tools vary by host. A profile's tool list cannot grant a capability that the active host or account does not provide.

## Operating loop

1. **Discover:** inspect repository state, issue/PR, available tools, and current permissions.
2. **Plan:** define task scope, acceptance criteria, rollback, and exact target commit.
3. **Implement:** isolate changes on a feature branch and add regression tests.
4. **Review:** have a separate read-only security reviewer challenge the diff.
5. **Verify:** run focused checks and CI against the exact pushed commit.
6. **Evidence:** preserve logs, hashes, scan reports, and limitations.
7. **Report:** distinguish designed, implemented, executed, verified, and production.
8. **Learn:** update the relevant skill only when a reusable lesson is supported by evidence and reviewed.

## Non-negotiable governance

- CK-NEXUS Core/L3 remains the only canonical authority for state, memory, permissions, policy, execution, and evidence.
- AI agents, external tools, CI, and plugins have authority_level=NONE.
- No evidence means no completion claim. A green test does not certify Q10 or production.
- Q10/Q11/Q12 gates must not be silently weakened, bypassed, or relabeled.
- Preserve frozen subjects and canonical evidence. Never fabricate attestations, reviewer identity, scan IDs, or PASS states.
- No secret values in logs, prompts, commits, or reports.
- No paid compute/API usage without cost confirmation.
- No automatic merge or production deployment by virtue of agent approval.
- The Owner retains final authority; the Coordinator is advisory.

## Skills

- q10-evidence-integrity: canonical evidence and gate discipline.
- github-actions-triage: exact-commit CI debugging.
- secure-change-delivery: isolated changes, tests, review, and verified push.
- termux-rescue: safe SSH reverse-tunnel diagnosis and resilience checks.
- cknexus-tool-discovery: inspect available tools and avoid false credential/capability assumptions.

## Adoption and validation

Before merging, validate frontmatter and tool scopes, review the security boundary, and ensure required checks pass. After merge, verify the profiles appear in a supported agent picker and test one read-only task per role. Repository files alone do not prove the agents are activated or that independent subagent delegation is available.
