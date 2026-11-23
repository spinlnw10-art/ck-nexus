# Q14 Observability Integration Assessment — 2026-11-23

Status: READ-ONLY ARCHITECTURE ASSESSMENT — NO RUNTIME CHANGES
Base commit: `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`
Scope: canonical CK-NEXUS main only; no live-host access or production telemetry inspection.

## Executive finding

CK-NEXUS already has a useful observability foundation. Do not replace it with a second metrics stack.

Existing capabilities observed in source:
- `creator_app/observability.py` provides a correlation ID helper, key-name-based structured-log redaction, an HTTP request counter, aggregate latency sums, 5xx counters and process uptime.
- `creator_app/api.py` adds HTTP middleware, returns `X-Correlation-ID`, records method/route/status/duration, exposes authenticated `/metrics`, and exposes `/health`, `/health/live` and `/health/ready`.
- `observability/alert_rules.yaml` defines high-5xx, stale-email-lease and outbox-backlog alerts.
- `scripts/gate_observability.py` requires an operator receipt file and invokes `scripts/p0_observability_check.py`.
- Existing tests cover basic metric output, correlation ID handling and structured log redaction.

Important limitations:
1. The API's current request middleware records metrics and structured logs, but this source path does not create an OpenTelemetry server span or show W3C trace-context extraction/injection.
2. `pyproject.toml` declares `opentelemetry-api` only in the optional billing extra. The inspected core dependencies do not include the SDK, FastAPI instrumentation, OTLP exporter or Collector.
3. Current custom Prometheus metrics include a request latency sum but no matching observation count/histogram in the inspected registry. This prevents reliable percentile/SLO analysis from that metric family alone.
4. Route labels are normally taken from the framework route template, which is good for bounded cardinality; the fallback uses the raw request path and must be normalized before metric labels are expanded.
5. Structured redaction is based on sensitive key names. It does not prove that arbitrary values, exception messages, prompts, headers or nested third-party logs cannot contain secrets or personal data.
6. The current `/metrics` endpoint is protected by the application access token. Scrape authentication and network isolation need an explicit deployment contract; do not make it public merely to ease collection.
7. Q14 historical evidence `evidence/Q14_OBSERVABILITY_ALERT.json` is bound to source SHA `4cf17cd3befaafeaf64cd4c149739133aa220f73`, tree `dfe3888bb6adc9aebbb0351efe4a06006f4e0a48`, and manifest `96dcd0f0f93b1aaa69e88da30fedcce1b786b51b83f36b72baf7ac910d02b04f`. It is historical only and cannot satisfy Q14 for the current candidate.
8. `RELEASE_STATUS.md` explicitly marks Q14 as NOT_VERIFIED / STALE SUBJECT for the current release line. Old sign-off shell scripts that print VERIFIED/PASS are not authoritative evidence for the current candidate.

## Recommended toolchain

| Layer | Recommended component | Integration decision |
|---|---|---|
| Instrumentation API/SDK | OpenTelemetry Python API + SDK | Add behind an explicit optional runtime extra after version and compatibility review |
| ASGI instrumentation | OpenTelemetry FastAPI/ASGI instrumentation | Prefer maintained official instrumentation over hand-written trace middleware |
| Export protocol | OTLP | Use OTLP with explicit endpoint, TLS/auth and bounded timeouts |
| Collection | OpenTelemetry Collector | Deploy as a separate staging service/sidecar; receiver/exporter allowlist and memory limits required |
| Metrics backend | Existing Prometheus | Keep existing Prometheus and custom metrics; add histograms and scrape config only after cardinality review |
| Alert routing | Existing Alertmanager | Keep existing routing; test deduplication, grouping, inhibition and receiver delivery |
| Logs | Existing structured logger initially | Preserve current format; add trace/span correlation only after secret/PII redaction review |

Do not introduce Jaeger, Grafana, Loki, Tempo or a second metrics database in this phase. Those are optional backend choices, not prerequisites for fixing the current instrumentation gaps.

## Target flow

`Agent/Creator request -> CK-NEXUS middleware -> request/agent/executor spans -> OTLP -> OpenTelemetry Collector -> approved backends`

In parallel:
- Existing `/metrics` remains the Prometheus scrape surface.
- Prometheus evaluates the existing alert rules plus reviewed SLO/latency rules.
- Alertmanager groups/routes notifications to the configured staging receiver.
- Logs carry correlation ID and, when available, trace ID/span ID; sensitive payloads remain excluded.
- Evidence recorder captures source SHA/tree, configuration digest, collector image digest, Prometheus/Alertmanager image digests, test-run ID, alert receipt digest and independent verifier.

## Required design controls

- Preserve current request authentication on `/metrics`; restrict scrape network path and use dedicated least-privilege scrape credentials if required by the deployment.
- Do not place user IDs, tenant IDs, email addresses, prompts, raw paths, tokens or arbitrary exception text in metric labels.
- Normalize unknown routes to a bounded label such as `__unmatched__`.
- Prefer histogram buckets for request/agent/executor duration; document bucket boundaries and avoid changing existing metric semantics without migration tests.
- Configure W3C Trace Context propagation. Reject malformed context safely and do not treat trace IDs as authorization or tenant identity.
- Do not export prompt bodies, model responses, tool arguments, credentials, approval payloads or raw user content by default.
- Apply allowlisted span attributes and bounded values; sanitize exception events and headers.
- Collector must have memory limiter, batch processor, bounded queues/retries, explicit receivers/exporters and no unauthenticated public listener.
- Scrape/export failures must not block or fail user requests. Telemetry is best-effort and must not gain execution authority.
- Keep alert delivery fail-closed for the Q14 gate: missing receipt, mismatched subject or missing raw artifacts => BLOCKED.
- Do not alter production alert rules or Q14 gate state in this assessment.

## Proposed staged implementation

| Stage | Deliverable | Exit criteria |
|---|---|---|
| 0 | Existing-stack inventory | Source and historical-evidence gaps documented (this PR) |
| 1 | Instrumentation adapter prototype | Unit tests for trace context, span allowlist, redaction and no-op behavior when telemetry disabled |
| 2 | Local synthetic Collector test | OTLP trace export to isolated local collector; no external endpoint or credentials |
| 3 | Prometheus metrics hardening | Histogram/count, bounded labels, exposition tests, compatibility check for existing alert rules |
| 4 | Alertmanager shadow validation | Synthetic failure injection and test receiver; prove grouping/deduplication/inhibition and receipt hashing |
| 5 | Staging end-to-end | Exact candidate SHA/tree, configuration/image digests, trace/log/metric correlation and operator receipt |
| 6 | Q14 gate evaluation | Run canonical gate on exact same candidate; independent review; no automatic promotion |

Stages 1–4 can be developed on isolated branches or local CI fixtures. Stages 2 and 4 must not contact production endpoints. Staging deployment requires a separate host-specific authorization. No production installation is authorized.

## Acceptance evidence

A future Q14 evidence bundle must include:
- exact source commit SHA and Git tree SHA;
- runtime/deployment subject and configuration digests;
- exact SDK/instrumentation/Collector/Prometheus/Alertmanager versions and image digests;
- raw OTLP test trace and collector health/export result;
- Prometheus exposition and scrape result;
- alert rule evaluation and raw Alertmanager test-receiver receipt;
- failure-injection procedure, timestamps and cleanup result;
- redaction tests with synthetic canary secrets and confirmation that canaries do not appear in exported logs/spans;
- bounded-cardinality test for unknown routes and hostile header values;
- artifact hashes and independent verifier identity.

A component test PASS is not Q14 PASS. Q14 PASS applies only to complete evidence bound to the same exact release candidate. Production remains NO-GO until all Q10–Q16 gates pass on that candidate and owner authorization is separately recorded.

## Primary references

- OpenTelemetry Python instrumentation: https://opentelemetry.io/docs/languages/python/instrumentation/
- OpenTelemetry context propagation: https://opentelemetry.io/docs/languages/python/propagation/
- OpenTelemetry Collector documentation: https://opentelemetry.io/docs/collector/
- Prometheus metric and label naming: https://prometheus.io/docs/practices/naming/
- Prometheus instrumentation practices: https://prometheus.io/docs/practices/instrumentation/
- Prometheus Python client labels: https://prometheus.github.io/client_python/instrumenting/labels/
- Alertmanager concepts: https://prometheus.io/docs/alerting/latest/alertmanager/

## Non-claims

This document does not claim an OpenTelemetry SDK or Collector is installed, that traces currently flow end-to-end, that Alertmanager is reachable, or that Q14 passes on current main. It does not modify runtime code, dependencies, workflow behavior, alert rules, gate state, secrets or production infrastructure.
