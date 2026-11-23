# OpenTelemetry telemetry policy — shadow prototype

**Status:** offline prototype; not an installed OpenTelemetry SDK, Collector, exporter,
production telemetry pipeline, or CK-NEXUS release gate.

## Purpose

Provide a fail-closed data-minimization boundary before any OpenTelemetry SDK or Collector
is connected. The validator accepts only synthetic JSON events with a small fixed attribute
allowlist. It has no network client, does not import the OpenTelemetry SDK, and never exports
telemetry.

## Allowed event attributes

Required:

- `service.name`: fixed value `ck-nexus`
- `ck_nexus.component`: `core`, `creator`, `agnes`, `executor`, or `verifier`
- `ck_nexus.operation`: `request`, `tool_call`, `policy_check`, `approval_check`, or `evidence_write`
- `ck_nexus.outcome`: `success`, `denied`, or `error`
- `ck_nexus.duration_ms`: finite number from 0 to 600000

Optional:

- `service.version`: bounded version-like string
- `deployment.environment.name`: `development`, `test`, or `staging`

All other attributes are rejected, including user/tenant identifiers, prompts, model inputs or
outputs, tool arguments, credential references, exception messages, URLs, IP addresses, and
request headers. The validator does not attempt to redact arbitrary strings; it rejects
unknown attributes and accepts only enumerated values for operational dimensions.

## Run locally with synthetic data

```json
[
  {
    "service.name": "ck-nexus",
    "service.version": "0.2.0",
    "deployment.environment.name": "test",
    "ck_nexus.component": "core",
    "ck_nexus.operation": "policy_check",
    "ck_nexus.outcome": "success",
    "ck_nexus.duration_ms": 12.5
  }
]
```

```bash
python scripts/assurance/otel_telemetry_policy.py synthetic-events.json
python -m unittest tests.assurance.test_otel_telemetry_policy -v
```

The command emits normalized allowlisted events or a rejection reason without echoing input
values. Input is limited to 1 MiB and 1000 events. It rejects symlinks and duplicate JSON keys.

## Integration sequence (not yet authorized or implemented)

1. Review this attribute contract against CK-NEXUS data classification and threat model.
2. Pin and verify an OpenTelemetry Collector distribution/image by digest and provenance.
3. Add a local-only synthetic Collector test with no production endpoint or secrets.
4. Verify trace propagation and metric semantics while proving prompt, payload, identity,
   credential, and tenant data are absent from telemetry.
5. Add an independently reviewed redaction/retention policy and access-control boundary.
6. Only then propose a read-only shadow integration; Core remains the sole policy and gate
   authority.

## Safety boundary

- No SDK/Collector install, container startup, network call, endpoint, secret, or real user data.
- No trace/span export, persistent telemetry store, or production environment support.
- No gate decision, approval, identity change, credential access, or execution capability.
- Passing this validator means only that the supplied synthetic JSON conforms to this local
  allowlist. It does not prove end-to-end telemetry privacy or operational readiness.

## References

- OpenTelemetry Collector documentation: https://opentelemetry.io/docs/collector/
- OpenTelemetry semantic conventions: https://opentelemetry.io/docs/specs/semconv/
- OpenTelemetry security guidance: https://opentelemetry.io/docs/security/
