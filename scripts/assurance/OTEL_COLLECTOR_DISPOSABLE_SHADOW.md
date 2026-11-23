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
No mutable base image is pulled. CI records the image config digest and the SHA-256 of the
saved image archive, then creates a GitHub build-provenance attestation for that archive.
The locally built image is not pushed to a registry.

## Experiment

- Internal-only Docker network (`--internal`); only loopback port 4318 is published.
- Read-only root filesystem, no capabilities, no-new-privileges, PID/memory/CPU limits.
- Synthetic OTLP trace with a parent and child span sharing one trace ID.
- Synthetic OTLP metric `ck_nexus_shadow_requests`.
- Resource and span/datapoint attribute processors delete user, tenant, prompt, tool argument,
  authorization, API-key, credential-reference, URL and database-statement attributes.
- CI asserts the trace and parent/child span IDs plus metric name appear in Collector debug
  output, and that synthetic secret markers do not appear.
- A cleanup step stops the container and removes the internal Docker network.

## Limits

This is a disposable integration test, not production telemetry, not an installed service,
and not proof of privacy for every possible telemetry schema. The allowlist validator in
`otel_telemetry_policy.py` remains a separate upstream policy boundary. No Collector output
can approve, deny, authorize, merge, deploy, access credentials, or decide CK-NEXUS gates.

## References

- https://opentelemetry.io/docs/collector/install/docker/
- https://github.com/open-telemetry/opentelemetry-collector-releases/releases/tag/v0.165.0
- https://github.com/sigstore/cosign
- https://github.com/actions/attest-build-provenance
