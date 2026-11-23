# CK-NEXUS Assurance Toolchain Compatibility and Readiness Matrix

**Status:** Preliminary from repository configuration and official upstream documentation. Host/VPS facts remain unverified.

## Existing repository facts used

- Canonical repository baseline: `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`.
- `docker-compose.p0.yml` declares PostgreSQL 16 Alpine and a separate app service; no evidence in this file that pgBackRest is installed or configured.
- Q10 currently runs pip-audit, Bandit, secret scan and security attack regression. The selected Q10 workflow does not currently show Syft/Grype/Dependency-Track integration.
- Q16 currently inventories runtime Python distribution license metadata from the exact production image; it does not establish complete source-code license analysis or signed build provenance.
- Existing Prometheus/Alertmanager and Q12 cgroup v2 controls must be retained.
- The R14 integration policy explicitly removed n8n from the active runtime; do not introduce another workflow/orchestration authority.

## Matrix

| Candidate | Required environment | CK-NEXUS fit | Main risk / unknown | Readiness |
|---|---|---|---|---|
| Syft | Linux/CI runner or container access to exact source/image | Strong; output SPDX/CycloneDX and native JSON | Need exact image build subject and package catalog completeness | Ready for synthetic CI spike |
| Grype | CI runner; vulnerability DB access/cache | Strong; scans Syft SBOM or image | DB freshness, network policy, severity policy and false-positive handling | Ready for synthetic CI spike |
| Dependency-Track | Persistent service, database, TLS, auth, API token, backup/upgrade plan | Useful only if central portfolio/continuous monitoring is needed | New stateful service and operational burden; exact API contract not yet mapped | Defer; API integration design first |
| Promptfoo | Node.js runtime (official quickstart currently specifies Node >=22.22.0), isolated HTTP target | Strong for staging API tests | Test cost, model nondeterminism, data egress and target safety | Ready for local/synthetic spike |
| PyRIT | Python runtime and configured target/scorers | Strong for multi-turn campaigns | Campaign cost, sensitive transcripts, model/provider access | Staging-only after Promptfoo baseline |
| Garak | Python/runtime dependencies and supported model/endpoint connector | Complementary specialized probes | Coverage overlaps; endpoint adapter compatibility to verify | Optional later phase |
| gVisor runsc | Linux 5.6+, x86_64 or ARM64 per install guide, Docker/containerd integration | Potentially strong without Kubernetes | Host kernel, architecture, storage/network/GPU compatibility and performance | Host preflight required; no installation yet |
| Kata Containers | Supported virtualization extensions (e.g. VT-x/AMD-V or architecture equivalent), hypervisor and runtime integration; commonly Kubernetes deployment | Conditional stronger VM boundary | Hardware/firmware/nested virtualization and higher resource overhead | Not selected unless threat model demands |
| pgBackRest | PostgreSQL host/client compatibility, durable repository, WAL archiving, encryption and restore target | Strong candidate for PostgreSQL backup/PITR | Existing topology, storage, RPO/RTO, DB permissions and restore process unknown | Topology discovery required |
| Barman | PostgreSQL servers, backup server/storage, replication/WAL configuration | Alternative for centrally managed multi-server estates | More infrastructure and operator model than currently evidenced | Compare only if multi-server need |
| OpenTelemetry Collector | Container or binary, explicit config and receiver/exporter endpoints | Strong; can feed existing observability backends | Cardinality, PII/secrets, TLS/auth, component distribution and queue loss | Ready for staging config validation |
| GitHub-hosted ephemeral runner | GitHub Actions hosted runner | Already aligns with current CI | Hosted environment reproducibility and limited private network access | Preferred baseline |
| Self-hosted ephemeral runner | Controlled Linux host/VM, runner registration, teardown automation, external log forwarding | Conditional for private network or hardware needs | Runner compromise, persistence, cleanup and secret leakage | Only after lifecycle proof |
| ARC | Existing supported Kubernetes cluster and operator ownership | Not needed for current observed topology | Adds Kubernetes operational dependency | Defer |
| ORT + ScanCode | CI runtime, pinned scanner distributions, source/dependency access | Strong for source and dependency license analysis | Large scan scope, package manager support and policy review effort | Ready for synthetic repository scan |
| Cosign/in-toto | Trusted CI OIDC identity or managed signing key, registry/artifact storage | Strong provenance/signature layer | Identity policy, trust root, workflow/ref binding and key custody | Shadow verification first; no signing production artifacts |

## Compatibility decisions

### Q10
Generate SBOM from the exact built production image and source tree as distinct subjects. Keep both reports; do not assume source SBOM equals runtime image SBOM. Use Grype against the same image or its SBOM. Upload to Dependency-Track only after service operation and API permissions are designed.

### Q11
Promptfoo can be the first CI integration, but test against a dedicated staging URL or local mock target. Do not point broad red-team probes at production, external customer endpoints, or provider accounts without explicit approval. Keep transcripts redacted and retention bounded.

### Q12
Do not change Docker's default runtime globally. Create an opt-in isolated test service/profile and run a disposable workload with `runsc`; compare functionality, network, mounts, CPU/memory/pids and teardown. Confirm host kernel and architecture before proceeding. Kata requires hardware virtualization support and a more substantial runtime setup.

### Q13
The P0 compose file uses PostgreSQL 16 Alpine; this does not prove the live database topology or backup storage. Do not embed backup credentials in Compose or add backup tools to the application image by default. Use a separate backup container/host identity and an isolated restore target. Never run a destructive restore against the working database.

### Q14
Run Collector as a sidecar/service in staging first. Define explicit OTLP receivers, processors (memory limiter, batch, attributes/redaction) and exporters. Validate telemetry loss/backpressure and alert routing. Keep Prometheus/Alertmanager authoritative until an independently reviewed migration plan exists.

### Q15
Continue using GitHub-hosted runners unless private networking or controlled hardware is required. If self-hosted, one job per runner, isolated VM/container, no persistent workspace, external runner logs, no privileged Docker socket by default, short-lived credentials and verified teardown. ARC is not justified without Kubernetes.

### Q16
Run ORT/ScanCode on source and dependency graph; reuse the exact Q10 SBOM as an input where appropriate. Keep existing runtime license inventory. Add Cosign verification only after CI identity constraints are specified; signature verification must pin expected issuer and identity, not accept broad regular expressions.

## Required preflight data before any host installation

- Linux distribution/version, kernel, architecture, cgroup mode, Docker/containerd versions and runtime configuration.
- Whether Kubernetes exists and who owns it.
- PostgreSQL versions, number of clusters, topology, storage, backup location, WAL retention, RPO/RTO and restore target.
- Available CPU, memory, disk, network egress policy and service ports.
- Existing telemetry receivers/exporters and retention/access policy.
- GitHub runner type, trust boundary, private network requirement and credential cleanup model.
- Artifact registry and OIDC issuer/subject claims for provenance.

No host/VPS details are inferred from repository configuration. The above preflight is a blocker to host installation.
