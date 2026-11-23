# CK-NEXUS Assurance Standard Toolchain Selection
**Date:** 2026-11-23  
**Status:** Proposal for review; staging shadow mode only  
**Repository baseline:** main at `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`

## Decision summary

Adopt external tools as replaceable evidence producers behind CK-NEXUS adapters. Do not replace existing Q10-Q16 controls wholesale. Do not grant an external tool authority to approve, promote, merge, deploy, or mutate CK-NEXUS gate state.

| Gate | Preferred candidate | Secondary / conditional | Existing control to preserve | Initial decision |
|---|---|---|---|---|
| Q10 | Anchore Syft + Grype | OWASP Dependency-Track as centralized SBOM/vulnerability inventory | pip-audit, Bandit, repository secret scan, attack regression | Add SBOM and image/SBOM scan in shadow mode; retain existing scanners |
| Q11 | Promptfoo | Microsoft PyRIT for multi-turn campaigns; NVIDIA Garak for specialized probes | CK-NEXUS live provider smoke and existing security regression | Start Promptfoo on synthetic/local test target; no live credentials in first stage |
| Q12 | gVisor runsc | Kata Containers only if VM/hardware virtualization and runtime topology justify it | Existing cgroup v2 enforcement, non-root runner, resource limits | Compatibility spike only; no host runtime change |
| Q13 | pgBackRest | Barman if multi-server backup orchestration is a better topology fit | Existing isolated PostgreSQL restore gate | Evaluate against real topology/RPO/RTO; test only in disposable isolated DB |
| Q14 | OpenTelemetry Collector | Prometheus exporters/remote-write-compatible backends | Existing Prometheus, Alertmanager and rules | Add Collector as a telemetry gateway in staging; preserve current alert path |
| Q15 | GitHub-hosted ephemeral runners | Self-hosted ephemeral runner; ARC only with an existing Kubernetes platform | Existing GitHub-hosted VM portability test | Prefer hosted ephemeral runner; prove workspace/credential cleanup |
| Q16 | ORT + ScanCode | Syft-generated SBOM reused from Q10; Cosign/in-toto attestations | Existing runtime image license inventory and release evidence workflow | Add source/dependency license analysis and artifact provenance in shadow mode |

## Why these choices

### Q10 — software supply chain
Syft catalogs packages from source directories, filesystems, archives and container images and emits native JSON, SPDX and CycloneDX. Grype scans images, filesystems and SBOM inputs, including Syft, SPDX and CycloneDX formats. This provides a direct producer-consumer chain without replacing pip-audit or Bandit. Dependency-Track is useful as a persistent portfolio service, but introduces a database, service operations, authentication, retention and API lifecycle; defer it until CK-NEXUS needs cross-build inventory and continuous monitoring rather than a one-off CI report.

### Q11 — AI/LLM security
Promptfoo is the first integration because it supports HTTP/API targets, adversarial red-team tests and CI workflows. PyRIT adds extensible multi-turn attack strategies and human-led campaigns; Garak adds specialized probes. These tools overlap in places, so do not run every probe suite on every commit. Use a tiered test profile: deterministic smoke tests on PRs, bounded adversarial suite on scheduled/staging runs, and approved human-led campaigns for release assurance. Every test must target a dedicated non-production CK-NEXUS endpoint and synthetic data.

### Q12 — execution isolation
gVisor is the first candidate because its OCI runtime `runsc` integrates with Docker/container tooling and does not require introducing Kubernetes. Its documented Linux kernel and architecture requirements must be verified on the actual host. Kata uses VM-backed isolation and requires supported hardware virtualization; it is a conditional alternative, not an automatic upgrade. Neither replaces cgroup limits, non-root execution, capability dropping, seccomp/AppArmor policy or network controls.

### Q13 — PostgreSQL disaster recovery
pgBackRest is the preferred first candidate for a single/few PostgreSQL topology where repository-based full/differential/incremental backup, WAL archiving and PITR are required. Barman remains a valid alternative when centralized management of multiple PostgreSQL servers and its operational model fit better. Do not choose before documenting topology, PostgreSQL version, storage/object-store target, encryption/key ownership, RPO, RTO, retention and restore ownership. A backup success is not restore proof.

### Q14 — telemetry
OpenTelemetry Collector is a vendor-neutral receive/process/export layer. Add it in front of existing monitoring rather than replacing Prometheus/Alertmanager. Use explicit pipelines, bounded queues, TLS/authentication where crossing trust boundaries, redaction/filtering before export, and a self-observability endpoint. Do not export prompts, tokens, email contents, personal data or raw secrets as telemetry attributes.

### Q15 — reproducible infrastructure
GitHub-hosted runners are already ephemeral by service design and are the lowest-complexity default for ordinary CI. For workloads requiring private network or controlled hardware, use one-job ephemeral self-hosted runners with external log forwarding and verified teardown. ARC is appropriate only if Kubernetes is already operated and secured. Packer/Terraform/Ansible are not a bundle to install by default: add each only when immutable image creation, infrastructure lifecycle or configuration convergence is an identified requirement.

### Q16 — license and provenance
ORT provides dependency analysis, policy evaluation, license/copyright scanning integration and CycloneDX/SPDX outputs. ScanCode is a mature license/copyright scanner and can produce JSON and SPDX formats. Cosign can sign and verify artifacts and in-toto attestations; use GitHub OIDC/keyless identity with tightly scoped verification policy where supported. A successful metadata scan is not legal approval, and a signature is not proof that the build process was trustworthy unless provenance claims are also verified.

## Non-goals

- No production installation, host package installation, runtime switch, database restore, secret creation, or cloud resource provisioning in this proposal.
- No replacement of Q10-Q16 gate definitions or PASS criteria.
- No automatic merge/deploy or external tool gate authority.
- No broad adoption of Kubernetes, a second orchestrator, a second database, or a second telemetry backend without a documented need.
- No unpinned `latest` tool downloads in release workflows.

## Version and supply-chain policy

For each selected tool, pin a reviewed release version and immutable container image digest or verified release checksum; record upstream source, license, supported platforms, SBOM, vulnerability findings and update owner. Prefer official release artifacts and official documentation. Re-evaluate pinned versions on a scheduled cadence. Do not commit floating image tags or shell-pipe installers into production workflows.

## Official references

- Syft SBOM generation: https://oss.anchore.com/docs/guides/sbom/
- Syft output formats: https://oss.anchore.com/docs/guides/sbom/formats/
- Grype scan targets: https://oss.anchore.com/docs/guides/vulnerability/scan-targets/
- Dependency-Track: https://docs.dependencytrack.org/
- Promptfoo red-team quickstart: https://www.promptfoo.dev/docs/red-team/quickstart/
- PyRIT: https://microsoft.github.io/PyRIT/
- Garak: https://garak.ai/
- gVisor: https://gvisor.dev/docs/
- Kata installation: https://github.com/kata-containers/kata-containers/blob/main/docs/installation.md
- pgBackRest: https://pgbackrest.org/user-guide.html
- Barman: https://docs.pgbarman.org/
- OpenTelemetry Collector architecture: https://opentelemetry.io/docs/collector/architecture/
- GitHub ephemeral runners: https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- ARC: https://docs.github.com/en/actions/concepts/runners/actions-runner-controller
- ORT: https://oss-review-toolkit.org/ort/docs/intro
- ScanCode: https://scancode-toolkit.readthedocs.io/
- Sigstore Cosign: https://docs.sigstore.dev/quickstart/quickstart-cosign/
