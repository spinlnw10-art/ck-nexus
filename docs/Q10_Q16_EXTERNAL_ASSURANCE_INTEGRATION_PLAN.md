# CK-NEXUS Q10–Q16 External Assurance Integration Plan
Date: 2026-11-23
Status: Evaluation proposal only — not installed, not enabled, and not evidence of any gate passing.

## 1. Decision

Retain the existing CK-NEXUS Q10–Q16 release gates and their fail-closed semantics. Do not replace the gates with a single scanner, vendor platform, framework, or aggregate score.

Keep `creator_app.unified` as the primary runtime. External tools are bounded evidence producers behind CK-NEXUS-owned adapters/workflows. CK-NEXUS Core remains authoritative for identity, capability leases, policy, approvals, credential references, execution envelopes, independent effect verification and evidence records.

No tool receives authority to approve its own execution, alter gate policy, merge, deploy, or mark a release GO.

## 2. Gate-to-tool evaluation matrix

| Gate | Candidate standards / tools | Intended role | What the tool cannot prove |
|---|---|---|---|
| Q10 — Security and dependency assurance | CycloneDX or SPDX SBOM; Trivy or Grype for image/filesystem vulnerability scanning; OWASP Dependency-Check for supported ecosystems; Dependency-Track for continuous SBOM portfolio/policy tracking; optional Snyk only after commercial/privacy review | Generate SBOM, scan direct/transitive dependencies and images, normalize findings and policy violations | Absence of unknown vulnerabilities, runtime exploitability, complete provenance, or authorization to release |
| Q11 — Live AI provider validation | OWASP AI Testing Guide v1; OWASP GenAI Security Project guidance / red-team test cases; CK-NEXUS provider contract tests and runtime telemetry | Test provider identity, model/version, timeout/retry/fallback, structured output, prompt-injection handling, data-boundary enforcement, refusal and audit behavior against a controlled staging tenant | General safety of all model outputs, future provider behavior, or permission to access production credentials |
| Q12 — Linux cgroup v2 sandbox enforcement | OCI runtime behavior and Linux cgroup v2 controls; containerd/runc or Docker runtime inspection; optional gVisor or Kata Containers as stronger-isolation candidates; AppArmor/SELinux and seccomp | Verify actual CPU/memory/pids/IO limits, namespace/capability/device/mount/network restrictions and denied escape probes on the target host/runtime | Kernel immunity, universal containment, or security based solely on a Compose file / declared configuration |
| Q13 — PostgreSQL disaster recovery | Native WAL archiving and PITR; pgBackRest or Barman (select one primary path after compatibility review); PostgreSQL-native restore verification | Produce backup/WAL evidence and perform isolated restore/PITR drills with RPO/RTO measurements | Recoverability from a backup-success log alone; production failover safety without a tested runbook |
| Q14 — Observability and alert delivery | OpenTelemetry SDK/Collector; Prometheus; Grafana; Alertmanager; optional PagerDuty/Opsgenie after operational and licensing review | Correlate traces, metrics and logs; verify alert rules, routing, delivery, deduplication and incident acknowledgement | Complete observability without instrumentation coverage, or successful alert delivery based only on configuration |
| Q15 — Clean-machine deployment | Ephemeral GitHub Actions runner or equivalent isolated CI worker; pinned OCI base images; Packer/Ansible/Terraform only where infrastructure provisioning requires them | Build and deploy from a fresh environment, prove no inherited workspace/credentials/state, record image and configuration digests | Cleanliness merely because a pipeline says “fresh”; isolation must be tested and independently attested |
| Q16 — Release packaging and licensing | SPDX or CycloneDX SBOM; REUSE for repository license metadata; OSS Review Toolkit (ORT) for dependency/license policy; FOSSology/ClearlyDefined as supplemental review inputs | Inventory shipped components, license declarations and notices; detect unknown/prohibited license conditions; bind package manifest to exact release artifact | Legal interpretation of ambiguous/custom licenses or completeness where dependencies are omitted from packaging |

## 3. Recommended minimal first evaluation stack

Do not install all candidates at once. Evaluate a small, replaceable stack first:

1. Q10: CycloneDX SBOM generation plus one scanner (Trivy is a reasonable first candidate); add Dependency-Track only if continuous portfolio tracking is needed.
2. Q11: OWASP AI Testing Guide v1 test methodology plus CK-NEXUS-owned provider contract and adversarial test harness. No external agent gets provider credentials by default.
3. Q12: test the existing Linux host/runtime configuration first; do not add Kubernetes, gVisor or Kata unless the threat model and current runtime justify their operational cost.
4. Q13: evaluate pgBackRest versus Barman against the actual PostgreSQL topology, storage, WAL policy and restore objectives; choose one primary implementation.
5. Q14: OpenTelemetry as the instrumentation contract; use Prometheus/Alertmanager/Grafana only if the current stack does not already provide equivalent capabilities.
6. Q15: use an ephemeral CI runner and pinned build inputs before introducing a separate infrastructure-as-code platform.
7. Q16: choose one SBOM format (SPDX or CycloneDX) as the release contract; evaluate REUSE and ORT for source/dependency license checks.

These are candidates, not installation decisions. Avoid overlapping scanners/observability stacks until their incremental coverage is demonstrated.

## 4. Mandatory CK-NEXUS adapter and evidence contract

Every adapter must be deny-by-default, least-privileged, time-bounded and incapable of changing gate state directly.

Each evidence record must include at minimum:

- `gate_id` and `gate_policy_version`
- `repository`, full `commit_sha`, branch/ref and clean/dirty source state
- `build_id`, immutable artifact digest (OCI digest or package SHA-256), and build provenance reference
- tool name, exact version, image/package digest, adapter version and configuration digest
- execution environment identity, timestamp, test profile and scope
- raw report reference plus normalized finding summary and severity counts
- exit status, completeness indicator, suppressed/ignored findings with rationale and expiry
- evidence record ID, signer/attestation identity and retention classification

A report with missing commit/artifact binding, incomplete scan scope, unsupported tool version, expired evidence, failed signature verification or unreviewed suppression must be treated as INCOMPLETE/NO-GO, not PASS.

All tools run in isolated staging or ephemeral workers first. Secrets are passed only through CK-NEXUS credential references; never embed secrets in workflow YAML, command lines, reports, artifacts or PR comments. Redact provider payloads and sensitive logs.

## 5. Gate decision model

Use three states per check:
- PASS: required evidence is complete, current, correctly bound and satisfies the gate policy.
- FAIL: evidence demonstrates a policy violation or required test failure.
- INCOMPLETE: evidence is absent, stale, mismatched, unsigned, out of scope or cannot be independently verified.

Gate aggregation remains fail-closed: any required FAIL or INCOMPLETE prevents release progression. Advisory tools can add findings but cannot override a required check.

Q10–Q16 remain independent gates; do not average them into a score that hides a failed control.

## 6. Rollout sequence

1. Inventory existing Q10–Q16 checks, evidence schemas, CI workflows, artifact naming and current runtime controls.
2. Map each existing control to the proposed evidence contract; identify coverage gaps and duplicate checks.
3. Prototype adapters in a dedicated feature branch using synthetic data and staging credentials.
4. Test exact-subject binding, tampered report rejection, stale evidence rejection, secret redaction, timeout behavior and adapter compromise boundaries.
5. Run in shadow mode; compare tool output with current gate evidence without changing release decisions.
6. Require owner review of false positives, false negatives, license findings, operating cost and maintenance burden.
7. Enable one adapter at a time behind explicit policy versioning and rollback.
8. Re-run the complete Q10–Q16 suite against the exact release candidate before any release decision.

No production rollout, dependency installation, VPS change, merge or deployment is authorized by this evaluation document.

## 7. Compatibility, licensing and operational due diligence

Before selecting any candidate, record:
- supported OS/architecture, Python/Node/runtime and database versions
- OCI/container runtime and cgroup v2 compatibility where applicable
- license of the tool and all components shipped with it
- data residency, telemetry, source-code upload, retention and vendor access terms
- credential model, secret redaction and outbound network requirements
- CPU/memory/storage overhead, scan duration and failure behavior
- maintenance cadence, security advisories, pinned version and upgrade/rollback procedure
- whether the tool can run without privileged host access

Do not adopt two tools for the same signal unless a documented coverage gap justifies the duplication.

## 8. Reference status checked for this evaluation

- OWASP AI Testing Guide v1 was announced as published on 26 November 2025. It is a methodology for trustworthiness testing, not a turnkey runtime security monitor.
- NIST NCCoE DevSecOps Practices is a live project/document. NIST published an initial 2026 draft on 24 March 2026 and announced additional resources on 24 September 2026; treat it as evolving guidance, not a mandatory certification or final normative standard.
- NIST SP 800-218 SSDF v1.1 remains listed as final; SP 800-218 Rev. 1 v1.2 was listed as an initial public draft in December 2025. Do not label the draft as final.
- CycloneDX is an ECMA-424 standard; choose an explicit supported schema version and validate generated BOMs against that version.
- OpenTelemetry is an instrumentation/telemetry standard, not a complete monitoring or alert-delivery product.

## 9. Official references

- OWASP AI Testing Guide: https://owasp.org/projects/ai-testing-guide/
- OWASP GenAI Security Project: https://genai.owasp.org/
- NIST DevSecOps Practices: https://csrc.nist.gov/pubs/other/2026/03/24/devsecops-practices/iprd
- NIST SSDF publications: https://csrc.nist.gov/Projects/ssdf/publications
- CycloneDX specification: https://github.com/CycloneDX/specification
- OpenTelemetry: https://opentelemetry.io/docs/
- PostgreSQL continuous archiving / PITR: https://www.postgresql.org/docs/current/continuous-archiving.html
- pgBackRest: https://pgbackrest.org/
- Barman: https://docs.pgbarman.org/
- REUSE: https://reuse.software/
- OSS Review Toolkit: https://oss-review-toolkit.org/

## 10. Current decision

Evaluation only. No tool has been installed or enabled, no gate has been marked passed based on these recommendations, and no production configuration has changed. Production remains NO-GO until exact-candidate Q10–Q16 evidence passes.
