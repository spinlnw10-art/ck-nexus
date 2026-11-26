# AGNES Capability Fabric

Status: implemented on the PR #413 feature branch; not merged or activated in production.

## Purpose

Combine internal specialist routing, external assistant planning, provenance-backed learning, and controlled skill admission without creating a second authority plane. The fabric is an extension of the existing `BrainRuntime`, `ControlPlaneOrchestrator`, and CK-NEXUS Core/L3 controls.

## Components

| Component | Responsibility | Execution boundary |
|---|---|---|
| `creator_app/expert_fabric/` | Deterministically classify task domains and recommend internal specialists | Planning only; no agent is launched |
| `creator_app/dev_assistants/` | Discover assistant binaries and create bounded workstream plans | Binary presence is not runtime verification; no assistant is invoked by planning |
| `creator_app/agnes_experiential_memory.py` | Store lessons, evidence references, context digests, and supersession history in an append-only ledger | Only Core-validated experiences are returned as trusted memory; no execution grant |
| `creator_app/agnes_skill_foundry.py` | Quarantine, scan, sandbox-test, benchmark, and assess candidate skills | `REGISTERABLE` is not installation or activation |
| `creator_app/agnes_approval.py` | Contract for verifying an approval reference against a subject and action | No configured Core verifier means approval and validation fail closed |
| `capabilities/system-skills.catalog.json` | Deduplicate canonical capabilities and track historical candidates | Read-only catalog; no installation, activation, merge, or deployment |
| `scripts/system_skill_admission.py` | Produce a deterministic adoption decision from the catalog | Prints a plan only; never mutates files or invokes tools |

## Planning flow

1. `BrainRuntime.plan()` sends the request to `ExpertRouter`.
2. The router returns a primary specialist, supporting specialists, required capabilities, risk class, and whether approval/independent verification is required.
3. The same route is translated into workstreams for `DevAssistantFabric`.
4. The external assistant plan includes candidate capabilities, binary-presence evidence, runtime verification state, and cost gates.
5. The control-plane graph is still the primary plan. All assistant work remains `PLANNED_NOT_EXECUTED` until a separately authorized executor is connected.

The router is deterministic metadata, not an LLM decision and not an authority grant. High-risk and production-classified work requires CK-NEXUS Core approval and an independent verifier.

## Experiential memory

`record_experience()` stores a SHA-256 digest of context rather than raw context, bounded lesson/strategy text, result, source-run reference, and evidence links. New entries start as `PENDING_VERIFICATION` and are not returned by `retrieve_relevant()`.

`validate_provenance()` requires a distinct independent-verification reference plus a `CoreApprovalVerifier` result bound to the exact experience ID and action `memory.validate_experience`. The actor identity is taken from the verified Core decision, not a caller-provided `verified_by` string. Each approval is bound to a SHA-256 request digest covering the exact evidence references, context/candidate checksum, and requested transition. Approval references are stored only as SHA-256 digests. The verifier is an integration contract; no production Core adapter is wired in this branch, so the default remains fail-closed.

Only `VALID` entries are available to future planning. Supersession and invalidation also require Core approval and supporting evidence. The ledger is hash-chain verified before reads and serializes appends with a per-path thread lock plus an OS file lock where available.

## Skill admission

The skill lifecycle is:

`DISCOVERED → SCANNED → SANDBOX_TESTED → BENCHMARKED → COMPATIBLE + INDEPENDENT_VERIFICATION → AWAITING_APPROVAL → REGISTERABLE`

`QUARANTINED → CORE-APPROVED QUARANTINE RELEASE → DISCOVERED`

Any failed assessment transitions to `REJECTED`. A skill can begin quarantined because its source, checksum, license, scripts, credentials, or network requirements need review. A quarantined candidate cannot enter scanning until every quarantine reason is explicitly resolved with evidence and a Core approval bound to `skill.quarantine.release`. Compatibility also requires a distinct independent-verification reference. Every transition requires an evidence reference.

`approve()` requires a Core approval decision bound to the candidate ID, `skill.register`, candidate checksum/license, compatibility evidence, and independent-verification reference. The result is only `REGISTERABLE`; this package does not download, install, register, or activate candidate code. Readiness scores are heuristic workflow indicators, not security attestations.

## Capability catalog

Run:

```bash
python scripts/system_skill_admission.py
python scripts/system_skill_admission.py --skill cloud_worker_bridge
python scripts/system_skill_admission.py --auto-safe
```

`auto_safe` means only that a read-only or local-reversible candidate may be evaluated in a development environment. It does not authorize execution, installation, activation, external writes, paid compute, merge, or deployment. Guarded, credentialed, paid, production, and unknown-risk entries require Core review. Entries marked `BLOCKED_BY_EVIDENCE` stop until evidence is rebuilt and verified.

## Platform and runtime limits

- An executable found on `PATH` is not proof that its runtime is healthy. `runtime_verified` remains false until a real health check and bounded end-to-end task are recorded.
- A bare `unshare -Urmpn /bin/true` canary passes on the current Termux device, but the full namespace/mount/chroot runner fails because `/bin/bash` is unavailable in the current PRoot rootfs. The sandbox remains BLOCKED and must not be represented as an active isolation boundary until the full health probe passes.
- OpenCode, Aider, OpenHands, Codex CLI, provider adapters, and the GitHub Actions cloud worker remain candidates until their exact runtime, permissions, cost, and end-to-end evidence are verified.
- No paid model/API or cloud worker is invoked by these components. No production credential is read or granted.

## Non-negotiable authority

CK-NEXUS Core/L3 remains the sole authority for identity, policy, permissions, approvals, credentials, execution, evidence, and release gates. Every external agent, provider, skill, plugin, and worker has `authority_scope=NONE`. Production remains **NO-GO** until the exact release candidate passes its mandatory gates.
