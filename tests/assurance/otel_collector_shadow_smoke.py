# ruff: noqa: I001
from __future__ import annotations

import http.client
import json
import time


COLLECTOR_HOST = "127.0.0.1"
COLLECTOR_PORT = 4318
ALLOWED_PATHS = frozenset({"/v1/traces", "/v1/metrics"})
TRACE_ID = "5b8aa5a2d2c872e8321cf37308d69df2"
PARENT_SPAN_ID = "051581bf3cb55c13"
CHILD_SPAN_ID = "93564f51e1abe1c2"
SECRET_MARKERS = (
    "SYNTHETIC_SECRET_DO_NOT_LOG_407",
    "synthetic-user@example.invalid",
    "SYNTHETIC_TENANT_407",
    "SYNTHETIC_TOOL_ARGUMENT_407",
)


def post(path: str, payload: dict) -> None:
    if path not in ALLOWED_PATHS:
        raise ValueError("unsupported local Collector endpoint")
    body = json.dumps(payload, separators=(",", ":")).encode()
    connection = http.client.HTTPConnection(
        host=COLLECTOR_HOST,
        port=COLLECTOR_PORT,
        timeout=10,
    )
    try:
        connection.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        if response.status not in (200, 202):
            raise AssertionError(f"{path} returned HTTP {response.status}")
        response.read()
    except OSError as exc:
        raise AssertionError(f"Collector did not accept {path}") from exc
    finally:
        connection.close()


def attr(key: str, value: str) -> dict:
    return {"key": key, "value": {"stringValue": value}}


def main() -> int:
    now = str(time.time_ns())
    resource = {
        "attributes": [
            attr("service.name", "ck-nexus"),
            attr("deployment.environment.name", "test"),
            attr("user.email", SECRET_MARKERS[1]),
            attr("tenant.id", SECRET_MARKERS[2]),
            attr("authorization", SECRET_MARKERS[0]),
        ]
    }
    traces = {
        "resourceSpans": [
            {
                "resource": resource,
                "scopeSpans": [
                    {
                        "scope": {"name": "ck-nexus.synthetic-shadow", "version": "1"},
                        "spans": [
                            {
                                "traceId": TRACE_ID,
                                "spanId": PARENT_SPAN_ID,
                                "name": "synthetic-parent",
                                "kind": 1,
                                "startTimeUnixNano": now,
                                "endTimeUnixNano": str(int(now) + 1_000_000),
                                "attributes": [attr("prompt", SECRET_MARKERS[0])],
                            },
                            {
                                "traceId": TRACE_ID,
                                "spanId": CHILD_SPAN_ID,
                                "parentSpanId": PARENT_SPAN_ID,
                                "name": "synthetic-child",
                                "kind": 1,
                                "startTimeUnixNano": str(int(now) + 1_000_000),
                                "endTimeUnixNano": str(int(now) + 2_000_000),
                                "attributes": [
                                    attr("tool.arguments", SECRET_MARKERS[3]),
                                    attr("ck_nexus.operation", "policy_check"),
                                ],
                            },
                        ],
                    }
                ],
            }
        ]
    }
    metrics = {
        "resourceMetrics": [
            {
                "resource": resource,
                "scopeMetrics": [
                    {
                        "scope": {"name": "ck-nexus.synthetic-shadow", "version": "1"},
                        "metrics": [
                            {
                                "name": "ck_nexus_shadow_requests",
                                "description": "Synthetic shadow request count",
                                "unit": "1",
                                "sum": {
                                    "aggregationTemporality": 2,
                                    "isMonotonic": True,
                                    "dataPoints": [
                                        {
                                            "startTimeUnixNano": now,
                                            "timeUnixNano": str(int(now) + 2_000_000),
                                            "asInt": "1",
                                            "attributes": [
                                                attr("ck_nexus.component", "core")
                                            ],
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }
    post("/v1/traces", traces)
    post("/v1/metrics", metrics)
    print(
        json.dumps(
            {
                "status": "SYNTHETIC_OTLP_SENT",
                "trace_id": TRACE_ID,
                "parent_span_id": PARENT_SPAN_ID,
                "child_span_id": CHILD_SPAN_ID,
                "metric": "ck_nexus_shadow_requests",
                "secret_markers": list(SECRET_MARKERS),
                "no_external_exporter_configured": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
