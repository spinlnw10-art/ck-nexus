# Q14 OpenTelemetry Collector Cosign + SLSA provenance shadow

## Status

This is a CI-only verification path. It does not install a Collector, pull image layers,
start a container, configure an exporter, or connect to production telemetry.

## Selected upstream artifact

- Official release repository: https://github.com/open-telemetry/opentelemetry-collector-releases
- Distribution: `otelcol-contrib`
- Registry: `ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-contrib`
- Initial release tag: `v0.165.0` (workflow_dispatch accepts another stable `vX.Y.Z`)
- Image tag is derived from the validated release tag (for example `v0.165.0` -> `0.165.0`).

The official release repository warns that Git tags may change and should not be relied upon as
immutable identifiers. Cosign verification therefore records the immutable image digest.

## Observed verification — 2026-11-23

GitHub Actions run: https://github.com/spinlnw10-art/ck-nexus/actions/runs/45174328029

- Cosign installer succeeded using pinned installer commit
  `faadad0cce49287aee09b3a48701e75088a2c6ad` and Cosign `v3.0.2`.
- Official release metadata check passed for `v0.165.0`.
- Image signature verification passed with the exact release workflow identity and GitHub OIDC issuer.
- Verified image digest:
  `sha256:e40d61f10c9a617cca1ffd1be4d7e2b3a4b0f0001798ff07e58cabe82e618cea`.
- SLSA provenance verification did not pass. Cosign found only
  `https://sigstore.dev/cosign/sign/v1` attestations and no `slsaprovenance` predicate.
- This is recorded as missing upstream image provenance, not as a successful provenance check.

The upstream release configuration at
https://github.com/open-telemetry/opentelemetry-collector-releases/blob/main/distributions/otelcol-contrib/.goreleaser.yaml
declares `docker_signs` for container images and signed release artifacts, and generates SBOMs
for archives/packages. That configuration and the observed Cosign result do not establish a
SLSA provenance attestation for the image digest. A signed SBOM for a platform archive is not
interchangeable with image-level SLSA provenance.

## Verification sequence

1. Run synthetic evidence-guard unit tests.
2. Validate the stable release tag and official GitHub release metadata.
3. Install Cosign using pinned `sigstore/cosign-installer` commit
   `faadad0cce49287aee09b3a48701e75088a2c6ad` and Cosign `v3.0.2`.
4. Verify the image signature using the exact OpenTelemetry release identity:
   `https://github.com/open-telemetry/opentelemetry-collector-releases/.github/workflows/base-release.yaml@refs/tags/<RELEASE_TAG>`
   and OIDC issuer `https://token.actions.githubusercontent.com`.
5. Extract the digest from Cosign's verified signature payload.
6. Check SLSA provenance for the same `image@sha256:...` and same certificate identity.
7. Bind signature/provenance status and raw evidence hashes to the exact CK-NEXUS candidate SHA.
8. Upload a short-lived evidence artifact even when provenance is absent, then fail the
   provenance requirement explicitly (NO-GO).

The workflow has `contents: read` only; no `id-token: write`, package write, repository write,
deployment, or environment permissions.

## Safety and interpretation

- Registry metadata and Sigstore services are contacted; `network_accessed=true` in the report.
- The workflow does not pull image layers and does not start a container.
- It does not use production endpoints, secrets, real user data, or telemetry payloads.
- It does not run the Collector on Android/Termux.
- Missing signature, identity mismatch, missing SLSA attestation, invalid payload, or digest
  mismatch fails closed; no fallback to unsigned images or unverified provenance.
- A valid image signature proves the expected release identity signed the digest; it does not
  independently prove the build process or source-to-image provenance.
- Evidence is advisory only. It cannot approve, deny, bypass, or modify CK-NEXUS gates.
- CK-NEXUS Core alone owns candidate identity, evidence completeness, approvals, policy, and
  release decisions.

## Limitations / next stage

- This shadow targets the official contrib multi-architecture image only. Production should use
  a custom distribution containing only required components after separate compatibility and
  attack-surface review.
- A successful signature does not prove the Collector configuration is safe, telemetry is
  redacted end-to-end, or runtime isolation is effective.
- Do not run a disposable Collector experiment until image-level provenance is supplied or an
  independently reviewed alternative provenance chain is accepted by CK-NEXUS Core.
- The current Q14 PR #407 remains separate; its SonarCloud failure must be resolved independently.

## References

- OpenTelemetry release repository: https://github.com/open-telemetry/opentelemetry-collector-releases
- Official contrib GoReleaser config: https://github.com/open-telemetry/opentelemetry-collector-releases/blob/main/distributions/otelcol-contrib/.goreleaser.yaml
- Sigstore CI quickstart: https://docs.sigstore.dev/quickstart/quickstart-ci/
- Cosign verification: https://github.com/sigstore/cosign/blob/main/doc/cosign_verify.md
- Cosign attestation verification: https://github.com/sigstore/cosign/blob/main/doc/cosign_verify-attestation.md
- SLSA provenance: https://slsa.dev/spec/v1.1/provenance
