# Disposable OpenTelemetry Collector shadow

**Scope:** GitHub-hosted ephemeral runner, synthetic telemetry only, internal Docker network,
local-only OTLP/HTTP receiver, debug exporter, no external exporter or persistent store.

## Upstream artifact verification

The workflow uses the official OpenTelemetry Collector core release `v0.165.0` from
`open-telemetry/opentelemetry-collector-releases`.

- Linux amd64 archive SHA-256:
  `78570dd4bd6570bc41eb327869ef913bbf91b87dd8170ebebbf43bec71f6370d`
- Sigstore bundle SHA-256:
  `57b0d726808d75cfc35e3f4c3e9cf7f836157e5b0375086dde33cbd05959c8b6`
- The GitHub release tag object is reported as signature-verified by GitHub.
- CI independently checks both asset hashes and runs `cosign verify-blob` against the
  Sigstore bundle, GitHub Actions OIDC issuer, repository/workflow identity and exact release tag.

The Collector image is built locally from the verified official binary using `FROM scratch`.
No mutable base image is pulled. CI records the immutable image config digest and SHA-256
of the saved image archive in a candidate-bound local provenance evidence document.
The upstream binary has a verified Sigstore blob signature; the local image record is
unsigned evidence (not a signed SLSA attestation). The PR workflow deliberately has no
`id-token: write` or `attestations: write` permission, so untrusted pull-request code cannot
mint OIDC-backed attestations. The locally built image is not pushed to a registry.

## Experiment

- Internal-only Docker bridge (`--internal`) with a fixed private address; no host port publishing and no external egress.
- Read-only root filesystem, no capabilities, no-new-privileges, PID/memory/CPU limits.
- Synthetic OTLP trace with a parent and child span sharing one trace ID.
- Synthetic OTLP metric `ck_nexus_shadow_requests`.
- The OTTL Transform Processor deletes user, tenant, prompt, tool argument, authorization,
  API-key, credential-reference, URL and database-statement attributes in explicit resource,
  span and metric-datapoint contexts. This replaces deprecated resource/attributes processors.
- CI asserts the trace and parent/child span IDs plus metric name appear in Collector debug
  output, and that synthetic secret markers do not appear.
- A candidate-bound manifest hashes the image provenance, immutable image ID/archive digest, Collector log and synthetic test result. The existing CK-NEXUS `EvidenceGraph` intake validates each path/size/hash and emits `CLAIM` / `SOURCE` nodes with `DERIVED_FROM` edges; no edge claims independent validation.
- The graph and supporting synthetic evidence are retained as a 30-day CI artifact. A cleanup step stops the container and removes the internal Docker network.

## Limits

This is a disposable integration test, not production telemetry, not an installed service,
and not proof of privacy for every possible telemetry schema. The allowlist validator in
`otel_telemetry_policy.py` remains a separate upstream policy boundary. No Collector output
can approve, deny, authorize, merge, deploy, access credentials, or decide CK-NEXUS gates.

## References

- https://opentelemetry.io/docs/collector/install/docker/
- https://opentelemetry.io/docs/collector/transforming-telemetry/
- https://github.com/open-telemetry/opentelemetry-collector-releases/releases/tag/v0.165.0
- https://github.com/sigstore/cosign
- https://github.com/actions/attest-build-provenance
