# Q14 OpenTelemetry Collector Cosign + SLSA provenance shadow

## Status

This change adds a CI-only verification path. It does not install a Collector, pull image
layers, start a container, configure an exporter, or connect to production telemetry.

## Selected upstream artifact

- Official release repository: https://github.com/open-telemetry/opentelemetry-collector-releases
- Distribution: `otelcol-contrib`
- Registry: `ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-contrib`
- Initial release tag: `v0.165.0` (workflow_dispatch input can select another stable `vX.Y.Z`)
- Image tag is derived from the validated release tag (for example `v0.165.0` -> `0.165.0`).
- Tag existence and non-draft/non-prerelease status are checked against the official GitHub Releases API.

The official release repository warns that Git tags may change and should not be relied upon as
immutable identifiers. The workflow therefore verifies the signature and SLSA attestation for
the registry-resolved image digest and records that digest in the evidence report.

## Verification sequence

1. Run synthetic evidence-guard unit tests.
2. Validate the requested stable release tag and official GitHub release metadata.
3. Install Cosign using the pinned `sigstore/cosign-installer` action commit and pinned Cosign
   release `v3.0.2` (the installer release's bootstrap version).
4. Verify the image signature using the exact OpenTelemetry release identity:
   `https://github.com/open-telemetry/opentelemetry-collector-releases/.github/workflows/base-release.yaml@refs/tags/<RELEASE_TAG>`
   and OIDC issuer `https://token.actions.githubusercontent.com`.
5. Extract the digest from Cosign's verified signature payload.
6. Verify SLSA provenance for the same `image@sha256:...` and the same certificate identity.
7. Validate that an in-toto SLSA provenance subject carries that exact SHA-256 digest.
8. Bind signature/provenance raw evidence hashes to the exact CK-NEXUS candidate SHA and publish
   a short-lived GitHub Actions artifact.

The workflow is read-only with `contents: read`; it has no `id-token: write`, package write,
repository write, deployment, or environment permissions.

## Safety and interpretation

- Registry metadata and Sigstore services are contacted; `network_accessed=true` in the report.
- The workflow does not pull image layers and does not start a container.
- It does not use production endpoints, secrets, real user data, or telemetry payloads.
- It does not run the Collector on Android/Termux.
- A missing signature, identity mismatch, missing SLSA attestation, invalid payload, or digest
  mismatch fails closed; no fallback to tags, unsigned images, or unverified provenance.
- Cosign verifies signatures and certificates; the helper validates evidence binding only.
- The evidence is advisory. It cannot approve, deny, bypass, or modify CK-NEXUS gates.
- CK-NEXUS Core alone owns candidate identity, evidence completeness, approvals, policy, and
  release decisions.

## Limitations / next stage

- This first shadow targets the official contrib multi-architecture image only. Production should
  use a custom distribution containing only required components after a separate compatibility
  and attack-surface review.
- A successful image signature and SLSA subject check does not prove the Collector configuration
  is safe, telemetry is redacted end-to-end, or runtime isolation is effective.
- Only after this workflow passes should a separate disposable synthetic runtime experiment be
  proposed. That experiment must independently verify trace propagation, metrics, secret
  exclusion, resource limits, and no production network route.
- The current Q14 PR #407 remains separate; its SonarCloud failure must be resolved independently.

## References

- OpenTelemetry release repository: https://github.com/open-telemetry/opentelemetry-collector-releases
- OpenTelemetry image-signature instructions: https://github.com/open-telemetry/opentelemetry-collector-releases
- Sigstore CI quickstart: https://docs.sigstore.dev/quickstart/quickstart-ci/
- Cosign verification: https://github.com/sigstore/cosign/blob/main/doc/cosign_verify.md
- Cosign attestation verification: https://github.com/sigstore/cosign/blob/main/doc/cosign_verify-attestation.md
- SLSA provenance: https://slsa.dev/spec/v1.1/provenance
