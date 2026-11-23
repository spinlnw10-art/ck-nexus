# CK-NEXUS Unified Assurance Integration Architecture

**Status:** Design proposal; no runtime wiring authorized  
**Authority:** CK-NEXUS Core remains the sole policy, approval and gate-decision authority.

## 1. Integration boundary

External assurance tools are untrusted evidence producers. They may:
- receive a narrowly scoped source tree, immutable build artifact, SBOM or staging endpoint;
- execute only the test profile assigned to their capability lease;
- emit raw reports and tool metadata;
- return an exit status and artifact references.

They may not:
- approve their own findings or waive policy;
- change Q10-Q16 state, release status, deployment state or approval registry;
- access production credentials or unrestricted CK-NEXUS data;
- invoke arbitrary tools, shell commands or network destinations outside an allowlist;
- write directly to the authoritative Evidence Registry.

## 2. Logical flow

`Human Principal -> Agent Identity -> Capability Lease -> Policy/Reversibility -> Approval Registry -> Credential Reference Broker -> Deny-by-default Sandbox -> Execution Envelope/Journal -> Tool Adapter -> Independent Evidence Verification -> Evidence Registry/Evidence Graph -> CK-NEXUS Gate Evaluator`

The adapter is the only permitted integration surface. Raw tool reports are retained as immutable artifacts; normalized envelopes reference them by digest. The gate evaluator independently verifies subject binding, scope, provenance, signature (where applicable), tool/version policy and freshness before applying existing gate rules.

## 3. Canonical evidence envelope

The current read-only prototype is a starting point, not a production schema. The target schema should include:

- schema identifier and version;
- gate identifier and policy version;
- repository identity, source commit SHA and Git tree SHA;
- release subject manifest digest and built artifact/image digest;
- tool name, version, distribution digest and configuration digest;
- workflow/run identity, runner identity/class and timestamps;
- exact target, scan scope, exclusions and completeness statement;
- raw report URI/reference, media type, byte length and SHA-256;
- tool result and normalized findings (with severity and stable identifiers);
- signature/attestation references and verifier outcome;
- adapter version, execution journal reference and independent verifier identity;
- status such as `INCOMPLETE`, `EVIDENCE_READY_FOR_GATE_EVALUATION`, `REJECTED`; never a tool-authored `PASS`.

A report-supplied digest is not proof of the artifact's digest. The adapter must hash the actual immutable artifact or obtain a verified digest from the build system and compare it with the expected subject. A raw report hash only binds the report bytes, not the scanned target.

## 4. Trust and isolation controls

- Use read-only checkout and immutable artifact references.
- Give each tool a separate least-privilege capability and egress allowlist.
- Keep secrets in the existing credential broker; never pass secret values in command-line arguments or reports.
- Redact before telemetry export; do not place prompts, tokens or user data in evidence metadata.
- Store raw reports and normalized envelopes in append-only or versioned storage.
- Verify cryptographic signatures and OIDC identity against explicit issuer, repository, workflow and ref constraints.
- Fail closed on missing scope, partial scans, stale subject, digest mismatch, unknown tool version, invalid signature or unverifiable provenance.
- Do not treat scanner exit code alone as a gate decision.

## 5. Adapter interfaces

Each adapter should expose a narrow contract:
1. `preflight()`: validate runtime, version, config, target and permissions without scanning.
2. `execute()`: run only a fixed allowlisted command/profile.
3. `collect()`: capture exit status, stdout/stderr policy, report files and artifact digests.
4. `normalize()`: convert report to the canonical envelope without changing findings.
5. `verify()`: independently validate report schema, target binding, scope, tool identity and signatures.
6. `publish()`: submit evidence references to CK-NEXUS evidence ingestion; no gate mutation.

The adapter must be deterministic where practical and idempotent for the same run identity and report digest.

## 6. Gate-specific adapter mapping

| Gate | Adapter responsibility | Evidence output |
|---|---|---|
| Q10 | Syft SBOM + Grype scan + optional Dependency-Track upload | SBOM, scan report, vulnerability DB metadata, subject digest |
| Q11 | Promptfoo/PyRIT/Garak profile execution against staging endpoint | Test plan, target identity, prompt corpus version, findings and redacted transcript |
| Q12 | gVisor/Kata runtime preflight and sandbox conformance test | Host/kernel/runtime versions, isolation profile, negative tests and resource enforcement |
| Q13 | pgBackRest/Barman backup and isolated restore verification | Backup manifest, WAL range, restore target identity, PITR timestamp and data-integrity checks |
| Q14 | OTel Collector config validation and telemetry pipeline smoke | Collector build/config digest, receiver/exporter health, redaction and alert receipt |
| Q15 | Ephemeral runner lifecycle and workspace/credential cleanup | Runner identity, one-job lifecycle, image/toolchain digest, teardown attestation |
| Q16 | ORT/ScanCode analysis and Cosign/in-toto verification | License findings, SBOM references, artifact signature and provenance verification |

## 7. Rollback

All initial integrations are opt-in and shadow-only. Rollback consists of disabling the new adapter/workflow and retaining the generated evidence for audit. It must not remove or rewrite prior evidence, existing Q-gate controls, source branches, or runtime services.
