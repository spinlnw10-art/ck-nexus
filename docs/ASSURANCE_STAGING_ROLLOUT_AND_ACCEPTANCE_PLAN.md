# CK-NEXUS Assurance Staging Rollout and Acceptance Plan

**Status:** Proposed; staging shadow mode only  
**No production installation, gate-policy change, merge or deployment is authorized by this document.**

## Phase 0 — Repair and baseline
1. Repair PR #396 Ruff failures (4 E501 findings) and inspect the separate AI Factory deterministic-check failure.
2. Rerun exact-head CI; require all relevant checks to conclude successfully before reusing the prototype.
3. Review the evidence envelope schema. The current prototype validates declared digests but does not itself hash the built artifact; production integration must close that gap.
4. Record baseline Q10-Q16 results and exact source/tree/release-subject identifiers before adding any new producer.

Acceptance: clean CI on exact head, reviewed schema, explicit known limitations, no gate state mutation.

## Phase 1 — Q10 synthetic supply-chain
1. Pin Syft and Grype releases and verify release checksums/signatures.
2. Generate Syft native JSON and CycloneDX/SPDX from a small synthetic fixture and the exact staging image.
3. Scan the same image/SBOM with Grype using a controlled vulnerability database snapshot or record its database metadata.
4. Validate malformed SBOM, stale subject, truncated report, empty scope, missing tool version and digest tampering.
5. Preserve existing pip-audit, Bandit and secret scan results unchanged.
6. Defer Dependency-Track until its persistent service, DB, authentication, TLS, retention, backup and API lifecycle are approved.

Acceptance: reports are reproducible and bound to the same exact subject; no scanner result can set Q10 PASS.

## Phase 2 — Q11 safe AI red-team
1. Start with Promptfoo against a local mock endpoint and synthetic fixtures; pin Node and tool versions.
2. Validate test plan version, target identity, prompt corpus version, run ID, bounded concurrency and redacted output.
3. Add PyRIT only for a defined multi-turn scenario that Promptfoo does not cover.
4. Add Garak only for a documented probe gap.
5. Block production/customer targets and unapproved provider calls at policy layer.

Acceptance: all probes run only against an allowlisted staging target; transcripts contain no secrets or personal data; failed/partial campaigns are INCOMPLETE.

## Phase 3 — Q12 sandbox compatibility
1. Collect host facts without changing configuration.
2. Verify Linux kernel >= 5.6 and x86_64/ARM64 before a gVisor trial.
3. Test `runsc` in an isolated runner/VM or disposable host; do not change the global Docker runtime.
4. Compare baseline and sandboxed workloads for filesystem, network, mounts, process limits, CPU/memory/pids, shutdown and cleanup.
5. Evaluate Kata only if hardware virtualization and threat model justify it.

Acceptance: sandbox negative tests prove denied host access and bounded resources; no production runtime change.

## Phase 4 — Q13 isolated DR
1. Document PostgreSQL topology and approved RPO/RTO.
2. Compare pgBackRest and Barman against topology, operator model, repository backend, encryption, WAL archiving, retention and restore complexity.
3. Build an isolated test cluster and backup repository using synthetic data.
4. Execute backup, verify, restore and PITR into a disposable target.
5. Validate row counts/checksums and record actual recovery time and recovery point.
6. Test missing WAL, corrupted backup, unavailable repository and wrong target safeguards.

Acceptance: successful restore/PITR on an isolated target; no production database or working volume is touched.

## Phase 5 — Q14 telemetry shadow
1. Add a pinned OpenTelemetry Collector distribution/config in staging.
2. Begin with non-sensitive service health and synthetic spans/metrics.
3. Validate receiver/exporter health, backpressure, queue behavior, TLS/auth and redaction.
4. Confirm current Prometheus/Alertmanager alert delivery remains unchanged.
5. Compare signal completeness and duplicate alert behavior.

Acceptance: no secrets or user payloads exported; no loss of existing alert coverage; rollback by disabling only the Collector service.

## Phase 6 — Q15 runner lifecycle
1. Prefer current GitHub-hosted runners for standard jobs.
2. If private infrastructure is required, build one-job ephemeral runner images with pinned toolchains.
3. Verify unique runner identity, one job only, workspace destruction, credential revocation, log forwarding and no cross-job cache leakage.
4. Consider ARC only if Kubernetes is already operated and the scale requirement is measured.

Acceptance: evidence proves runner de-registration and resource teardown after one job; no credential or workspace persists.

## Phase 7 — Q16 license and provenance
1. Run ORT and ScanCode on a synthetic source/dependency fixture.
2. Compare findings with existing Q16 runtime distribution inventory.
3. Normalize SPDX/CycloneDX references and resolve package identity without overwriting source reports.
4. Test Cosign signature and in-toto attestation verification in shadow mode using non-production artifacts.
5. Require exact issuer, repository, workflow, ref and subject constraints; reject broad identity regex policies.
6. Route license ambiguities to human review; scanners do not grant legal clearance.

Acceptance: source and runtime license scopes are both explicit; signatures and provenance bind to the exact artifact digest; unresolved findings remain review-required.

## Global negative tests

Every phase must reject:
- wrong source commit/tree or runtime artifact digest;
- stale or replayed workflow run;
- missing/partial scope or hidden exclusions;
- unknown/unpinned tool version;
- tampered report bytes;
- missing/invalid signature where required;
- target outside allowlist;
- secret-bearing report or telemetry;
- attempt by tool/adapter to mutate approval, gate, release or deployment state.

## Exit criteria

A phase is eligible for review only when:
- all synthetic tests pass on the exact branch head;
- reports are stored with immutable digests and complete provenance;
- the adapter cannot change gate state;
- rollback is demonstrated;
- no current gate control has been weakened or removed;
- reviewer signs off on the phase's evidence and operational cost.

Q10-Q16 production release remains NO-GO until the existing final production workflow accepts complete, current, exact-subject evidence for every required gate.
