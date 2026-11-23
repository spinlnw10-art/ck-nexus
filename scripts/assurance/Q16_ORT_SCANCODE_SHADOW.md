# Q16 ORT + ScanCode Shadow Intake

## Status

This is an offline evidence-integrity prototype. It does **not** install ORT or
ScanCode, execute either scanner, interpret license findings, provide legal
approval, or make a release-gate decision.

## Intended coverage

- ORT: dependency, package, and declared-license analysis across supported
  ecosystems, using a pinned configuration and documented package managers.
- ScanCode Toolkit: package, file, license, copyright, and notice detection.
- SPDX and CycloneDX: preserve machine-readable inventory and component
  relationships for downstream review.
- REUSE: optional source-tree license-declaration consistency checks.

The actual tool invocation adapters must be implemented only after exact
versions, distribution checksums/signatures, supported output schemas, and
network/cache behavior are reviewed. Do not assume Python-only coverage is
sufficient: include frontend, native, OS package, and container layers where
present in the release candidate.

## Intake contract

`q16_license_evidence_intake.py` accepts a JSON evidence file, tool identity
(`ort` or `scancode`), version, and exact 40-character candidate commit SHA.
It rejects symlinks, non-regular files, duplicate JSON keys, invalid JSON,
non-object roots, empty/oversized files, and invalid candidate identifiers.
It emits the raw evidence SHA-256 and explicit non-authority flags.

The prototype deliberately treats tool output as opaque bytes. A hash proves
which bytes were received, not that a scanner ran correctly, that its findings
are complete, or that a license is legally compatible.

## Required next stage

1. Pin ORT and ScanCode releases and verify signed release artifacts/checksums.
2. Run only in an isolated disposable runner with synthetic fixtures first.
3. Capture tool version, command/config hash, source tree SHA, candidate SHA,
   output SHA-256, runner identity, and timestamps.
4. Validate actual ORT and ScanCode output schemas with versioned fixtures.
5. Reconcile SPDX/CycloneDX components, package URLs, file paths, and license
   expressions; retain disagreements as unresolved evidence.
6. Route ambiguous or policy-sensitive findings to human legal/security review.
7. Attach evidence to the CK-NEXUS Evidence Graph under the exact same release
   candidate as Q10-Q15. CK-NEXUS Core alone verifies completeness and decides
   gates.

## Safety boundary

No production source/data, secrets, credentials, deployment endpoints, or
external network access are used by this prototype. Scanner findings are
advisory evidence only. No external tool can approve, deny, bypass, or modify
CK-NEXUS policy, approval records, credentials, execution, or release gates.
