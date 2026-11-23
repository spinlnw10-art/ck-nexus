# CK-NEXUS Q10–Q16 Standards Crosswalk

**Date:** 2026-11-23  
**Status:** Reference architecture for review; not a compliance attestation  
**Purpose:** Distinguish normative standards and frameworks from executable tools. Tools provide evidence; CK-NEXUS maps that evidence to control objectives.

## Standards and frameworks by gate

| Gate | Standards / frameworks | What they define | Evidence-producing systems |
|---|---|---|---|
| Q10 — Supply chain | NIST SP 800-218 SSDF; SLSA Build Provenance; CycloneDX ECMA-424 v1.7; SPDX ISO/IEC 5962:2021 | Secure development practices, build provenance, machine-readable component inventory and licensing metadata | Syft, Grype, optional Dependency-Track |
| Q11 — AI security | OWASP GenAI LLM Top 10 2026; NIST AI RMF + NIST AI 600-1 GenAI Profile; MITRE ATLAS; OWASP Agentic App Security guidance | Threat taxonomy, risk management, adversarial techniques and agent-specific control objectives | Promptfoo, PyRIT, Garak plus CK-NEXUS policy tests |
| Q12 — Runtime isolation | NIST SP 800-190; OCI Runtime Specification; CIS Docker Benchmark 1.9.0; Linux namespaces/cgroups/seccomp/AppArmor | Container threat model, runtime lifecycle contract and secure host/container configuration | gVisor runsc or conditional Kata; native cgroup and OS controls |
| Q13 — Disaster recovery | PostgreSQL continuous archiving and PITR documentation; explicit business RPO/RTO objectives; backup retention and restore testing | WAL continuity, recovery targets, timeline semantics and measurable recovery objectives | pgBackRest or Barman |
| Q14 — Observability | OpenTelemetry protocol/semantic conventions and Collector pipeline model; Prometheus alerting rules; Alertmanager routing/grouping/inhibition | Telemetry data model, collection/processing/export and actionable alert lifecycle | OpenTelemetry Collector, existing Prometheus and Alertmanager |
| Q15 — Reproducible infrastructure | SLSA Build Provenance; immutable/pinned toolchain and image policy; GitHub ephemeral runner lifecycle guidance; infrastructure-as-code review | Traceable build inputs/outputs, isolated execution and repeatable infrastructure | GitHub-hosted ephemeral runners; conditional Packer/Terraform/Ansible/ARC |
| Q16 — License and provenance | SPDX ISO/IEC 5962:2021; CycloneDX ECMA-424 v1.7; REUSE Specification 3.3; SLSA provenance; in-toto attestations; Sigstore verification | License/copyright metadata, component inventories, artifact identity and verifiable build claims | ORT, ScanCode, Syft, Cosign and in-toto |

## Gate-specific interpretation

### Q10 — Supply-chain assurance
- NIST SSDF is a secure-development practice framework, not a vulnerability scanner.
- SLSA provenance describes how a particular artifact was built and binds the provenance subject to artifact identity. It is not a substitute for scanning.
- CycloneDX and SPDX are interchange formats, not scanners or vulnerability databases.
- Use CycloneDX for Dependency-Track upload; preserve native Syft JSON as a source report.
- Grype scans the image or SBOM; pip-audit and Bandit continue to cover distinct Python/static-analysis paths.

### Q11 — AI and agent security
- OWASP GenAI LLM Top 10 2026 is the current risk taxonomy to map test cases against.
- NIST AI RMF and its GenAI Profile provide governance/risk-management outcomes; they do not provide a complete automated test suite.
- MITRE ATLAS provides adversary tactics and techniques for AI systems. Map selected techniques to bounded Promptfoo/PyRIT/Garak campaigns.
- CK-NEXUS-specific controls must additionally test identity, capability leases, least privilege, approval separation, tool allowlists, tenant boundaries, and effect verification. Generic LLM jailbreak tests alone are insufficient.

### Q12 — Runtime isolation
- NIST SP 800-190 and CIS Docker Benchmark guide configuration and operational hardening.
- OCI runtime specification defines the runtime lifecycle interface; conformance to OCI alone is not proof of isolation.
- gVisor/Kata provide alternative sandbox boundaries; they do not remove the need for cgroups, non-root users, filesystem restrictions, network egress policy and independent negative tests.
- Apply Kubernetes Pod Security Standards only if Kubernetes is actually part of the deployment topology.

### Q13 — Disaster recovery
- PostgreSQL PITR depends on a valid base backup and an uninterrupted required WAL history.
- Select pgBackRest or Barman only after topology and RPO/RTO are known.
- Report actual restore time and recovery point from a disposable target; backup job success alone is not DR readiness.

### Q14 — Observability
- OpenTelemetry Collector is a telemetry pipeline, not an alerting backend.
- Keep existing Prometheus rules and Alertmanager routing as the operational baseline.
- Define semantic attributes and redaction before export. Do not record credentials, raw prompts, user content, or personal data by default.

### Q15 — Reproducible infrastructure
- GitHub recommends ephemeral self-hosted runners for autoscaling rather than persistent runners; a runner should process one job and be destroyed.
- SLSA provenance should be generated by the trusted build platform and verified downstream against expected builder/workflow identity and artifact digest.
- Packer, Terraform and Ansible solve different problems; introduce only where the infrastructure design requires them.

### Q16 — License and provenance
- ISO/IEC 5962:2021 is the published SPDX edition identified in this review. The later SPDX 3.0 ISO revision was still in the approval process at the time of this review; do not claim it is already a published ISO edition.
- CycloneDX is standardized as ECMA-424, second edition, v1.7.
- REUSE provides per-file copyright/license declaration practices; ORT and ScanCode automate analysis but cannot make legal decisions.
- Cosign verifies cryptographic signatures and attestations; downstream policy must constrain issuer, identity, repository, workflow, ref and subject digest.

## Control coverage caveat

This crosswalk is a mapping aid, not a claim of certification or compliance. For each control, CK-NEXUS must record:
1. control objective and owner;
2. exact standard/framework version and applicable clauses;
3. test procedure and declared scope;
4. source commit/tree and immutable artifact digest;
5. tool version, configuration digest and raw report digest;
6. independent verification and unresolved exceptions;
7. reviewer and approval record.

## Official references

- NIST SP 800-218 SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA Build Track: https://slsa.dev/spec/v1.2/levels
- SLSA Build Provenance: https://slsa.dev/spec/v1.2/build-provenance
- CycloneDX ECMA-424: https://tc54.org/ecma424/
- SPDX ISO/IEC 5962:2021: https://www.iso.org/standard/81870.html
- OWASP GenAI LLM Top 10 2026: https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI 600-1 GenAI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- MITRE ATLAS: https://atlas.mitre.org/
- NIST SP 800-190: https://csrc.nist.gov/pubs/sp/800/190/final
- OCI Runtime Specification: https://github.com/opencontainers/runtime-spec
- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
- PostgreSQL PITR: https://www.postgresql.org/docs/current/continuous-archiving.html
- OpenTelemetry Collector: https://opentelemetry.io/docs/collector/architecture/
- Prometheus alerting rules: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
- Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/
- GitHub ephemeral runners: https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- REUSE Specification: https://reuse.software/spec/
- ORT: https://oss-review-toolkit.org/ort/docs/intro
- ScanCode: https://scancode-toolkit.readthedocs.io/
- Sigstore Cosign: https://docs.sigstore.dev/quickstart/quickstart-cosign/
