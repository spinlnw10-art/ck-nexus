# CK-NEXUS Open-Source Toolchain Integration Catalog
**Assessment date:** 2026-11-23  
**Baseline:** `main` at `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`  
**Status:** Evaluation and integration plan only — no production installation, gate-policy change, merge, or deployment.

## Executive decision

Prefer integrating mature, narrowly scoped upstream tools through CK-NEXUS-owned adapters. Do not replace CK-NEXUS Core, AGNES, Creator, its approval registry, capability leases, policy engine, execution journal, or evidence authority with an external platform. External tools produce observations and signed/structured evidence; CK-NEXUS remains the authority that binds evidence to a release candidate and decides whether a gate can be evaluated.

The initial toolchain shortlist is:

| Area | Preferred upstream project(s) | Role in CK-NEXUS | Adoption status |
|---|---|---|---|
| Q10 SBOM + vulnerability | [Syft](https://github.com/anchore/syft) + [Grype](https://github.com/anchore/grype) | Generate SBOMs and scan them; retain native reports | Already prototyped in PR #398; source-tree scope only |
| Q10 continuous inventory | [OWASP Dependency-Track](https://dependencytrack.org/) | Ingest CycloneDX and continuously monitor components | Evaluate as a separate staging service; not installed |
| Q10/Q16 supply-chain graph | [GUAC](https://github.com/guacsec/guac) | Correlate SBOM, provenance, vulnerability and attestation relationships | Strong candidate for Evidence Graph prototype; OpenSSF incubating / active development |
| Q11 LLM/agent testing | [Promptfoo](https://github.com/promptfoo/promptfoo) | CI evals, red-team probes and regression tests | Already prototyped synthetically in PR #399; real model/provider gate remains separate |
| Q11 complementary testing | [Garak](https://github.com/NVIDIA/garak), [Giskard](https://github.com/Giskard-AI/giskard-oss) | Expand probe coverage and agent/RAG evaluation where Promptfoo coverage is insufficient | Evaluate on offline fixtures first; do not run against production |
| Q12 sandbox | [gVisor](https://gvisor.dev/) | Additional isolation boundary for untrusted workloads | Compatibility spike only; no installation |
| Q13 PostgreSQL DR | [pgBackRest](https://pgbackrest.org/) or [Barman](https://pgbarman.org/) | Physical backup, WAL archiving and PITR | Select only after topology, storage, RPO and RTO are established |
| Q14 observability | [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) + [Prometheus](https://prometheus.io/) + [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) | Standard traces, metrics, logs pipeline and alert delivery | Adapter/config prototype; preserve existing metrics and alerts |
| Q15 provenance | [SLSA](https://slsa.dev/) + [in-toto](https://in-toto.io/) + [Sigstore Cosign](https://github.com/sigstore/cosign) | Build provenance, artifact identity, signatures and verification | Evidence-envelope design first; no signing keys or production trust policy changes |
| Q16 license compliance | [OSS Review Toolkit (ORT)](https://github.com/oss-review-toolkit/ort) + [ScanCode](https://github.com/aboutcode-org/scancode-toolkit) + [REUSE](https://reuse.software/) | Dependency/license analysis, source license scanning and repository metadata | Run read-only against a detached candidate checkout |
| Q16 broad artifact scan | [Trivy](https://github.com/aquasecurity/trivy) | OS/package/image vulnerabilities, secrets, misconfiguration and SBOM scan | Compare against Syft/Grype overlap before adopting; avoid duplicate gate authority |

## Selection rationale and constraints

### Q10 — SBOM and vulnerability intelligence
- Keep Syft + Grype as the first CI pair because the existing PR #398 already creates CycloneDX and SPDX SBOMs and a Grype report with pinned binary checksums.
- The current shadow scan covers the source tree, not the built runtime image. A zero-match result is not a clean bill of health for production.
- Dependency-Track adds persistent portfolio inventory, policy and continuous re-analysis after new vulnerability intelligence arrives. It needs a dedicated PostgreSQL-backed service and network access; treat it as a staging service with synthetic data until data residency, retention and authentication are reviewed.
- Trivy is a possible consolidator for image, OS, secret and misconfiguration scans, but do not add it blindly beside Grype. Run a comparison matrix on the same immutable artifacts and databases first.

### Q11 — LLM and agent assurance
- Keep Promptfoo as the primary test orchestrator. PR #399 currently validates only a deterministic synthetic provider; it does not prove model robustness, tool isolation, tenant separation or live provider behavior.
- Garak supplies a broad LLM vulnerability probe catalog. Giskard v3 supplies modular agent testing and vulnerability/quality scanning. Use them as coverage supplements, not competing gate authorities.
- All probes must run in an isolated, non-production environment with synthetic fixtures, explicit request budgets, no real secrets and no ability to invoke destructive tools. Live model tests require an independently approved staging credential and a candidate-bound evidence envelope.

### Q12 — runtime isolation
- Continue the gVisor compatibility spike already documented in PR #400. gVisor is an application-kernel isolation layer, not a replacement for CK-NEXUS authorization, capability leases or policy checks.
- Benchmark syscall compatibility, filesystem/network behavior, resource limits, startup latency and escape-resistance assumptions against the actual workload profile. Keep the current deny-by-default sandbox as the policy boundary.
- Do not select Firecracker/Kata or change the production runtime until the workload, host kernel, nested virtualization availability and operational support are known.

### Q13 — PostgreSQL disaster recovery
- pgBackRest is MIT-licensed and supports parallel backup/restore, multiple repositories and remote operation. Barman is GPL-3.0 and provides WAL archiving, PITR and multi-server management.
- Do not choose between them based on feature lists alone. First document PostgreSQL version, primary/standby topology, database size, storage target, network path, encryption/KMS, retention, required RPO/RTO and restore ownership.
- Test backup and restore only against disposable synthetic PostgreSQL instances. No production DB URL, real data, or live restore is authorized by this plan.

### Q14 — observability
- Use the OpenTelemetry Collector as the vendor-neutral ingestion/processing/export layer. Keep Prometheus for metrics/rules and Alertmanager for routing.
- Add trace context propagation and OTel instrumentation through bounded adapters. Preserve existing health endpoints, correlation IDs and alert semantics during shadow mode.
- Redact secrets and personal data before telemetry leaves the process; review cardinality and authenticated scrape/export paths. Never treat telemetry availability as proof that a security gate passed.

### Q15/Q16 — provenance and license assurance
- Bind every report to the exact Git commit, tree, build invocation, runtime artifact digest and immutable workflow artifact digest. Use SLSA/in-toto-compatible attestations and Cosign verification where supported.
- ORT provides dependency analysis, license policy evaluation and CycloneDX/SPDX reporting; ScanCode adds source-level license/copyright detection; REUSE validates repository licensing metadata.
- Trivy can complement runtime OS/package coverage. Do not assume any one Python package inventory represents the full OS image, native libraries, frontend assets or legal compliance.
- Human legal disposition remains necessary for ambiguous license findings. A tool's successful exit code is not a legal approval.

## Integration contract

1. External tools run as isolated, least-privilege workers with pinned versions and verified release checksums/signatures.
2. Workers receive an immutable candidate snapshot and explicit scope; they do not receive CK-NEXUS production credentials or direct authority to mutate gate state.
3. Each adapter emits raw report digests, tool identity/version, invocation metadata, scope completeness, source commit/tree, runtime subject digest (when applicable), and artifact provenance.
4. CK-NEXUS independently verifies artifact digests and candidate identity; adapter-declared hashes alone are insufficient.
5. Missing, stale, partial, unverifiable or scope-mismatched evidence is `INCOMPLETE` / `NOT_VERIFIED`, never PASS.
6. External dashboards and policy engines may advise; only the existing CK-NEXUS gate authority may evaluate gate state.
7. No tool may self-approve, approve a deployment, bypass human approval, acquire credentials, merge a PR, or deploy.

## Phased execution plan

- **Phase A — inventory and compatibility:** map current scripts/workflows to the shortlist, identify overlap, license obligations, data flows, deployment requirements and exact supported versions.
- **Phase B — detached/offline prototypes:** run tools against synthetic fixtures or immutable source snapshots; produce normalized evidence; no secrets, live services or production data.
- **Phase C — staging shadow integrations:** only after explicit staging approval, test service connectivity and real candidate artifacts; retain raw evidence and compare with existing checks.
- **Phase D — gate binding proposal:** demonstrate same-candidate evidence, independent artifact verification, replay protection and fail-closed behavior. This phase may propose code, but does not change gate policy.
- **Phase E — human review:** maintain Draft PRs until security findings, compatibility, license review and acceptance criteria are resolved.

## Known blockers and open decisions

- PR #398 and #399 have unresolved SonarCloud Security Rating failures; exact findings must be retrieved and fixed or formally dispositioned before either is merge-ready.
- PR #399's synthetic Promptfoo tests do not replace the live Q11 Responses API test.
- PR #400 is a design assessment, not a gVisor runtime test.
- PR #402 cannot select pgBackRest vs Barman without database topology and RPO/RTO requirements.
- PR #401 does not yet establish end-to-end OpenTelemetry trace/metric/log coverage.
- PR #404 identifies missing candidate-bound provenance fields and incomplete OS/native/frontend license coverage.
- GUAC is promising for the cross-gate evidence graph, but is an incubating project under active development; first prove import/export and query behavior using synthetic SBOM/attestation fixtures.

## Evidence references reviewed

- OWASP Dependency-Track project overview: https://owasp.org/projects/dependency-track
- Syft releases and checksums: https://github.com/anchore/syft/releases
- Promptfoo repository and releases: https://github.com/promptfoo/promptfoo and https://github.com/promptfoo/promptfoo/releases
- Garak: https://github.com/NVIDIA/garak
- Giskard OSS: https://github.com/Giskard-AI/giskard-oss
- gVisor security model and releases: https://gvisor.dev/docs/ and https://github.com/google/gvisor/releases
- pgBackRest: https://pgbackrest.org/
- Barman: https://pgbarman.org/about/
- OpenTelemetry Collector: https://opentelemetry.io/docs/collector/
- GUAC and OpenSSF: https://github.com/guacsec/guac and https://openssf.org/projects/guac/
- ORT: https://oss-review-toolkit.org/ort/docs/intro
- Cosign: https://github.com/sigstore/cosign
- Trivy SBOM scanning: https://github.com/aquasecurity/trivy/blob/main/docs/guide/target/sbom.md

## Safety statement

This catalog is a proposal for branch-based integration only. It does not authorize production installation, service exposure, credential creation, data migration, database restore, destructive testing, gate-policy changes, merge, release promotion or deployment. Preserve all original repositories, branches, backups, evidence and source data.
