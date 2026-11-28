from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.gitlab_evidence_manifest import EvidenceManifestError, validate_q12_gate


@pytest.fixture
def passing_q12_gate() -> dict[str, object]:
    return {
        "status": "PASS",
        "environment": "staging",
        "health": {
            "unified_v2": True,
            "delegated_writable": True,
            "controllers": ["cpu", "memory", "pids"],
            "root": "/sys/fs/cgroup/cknexus-delegated",
        },
        "observed": {
            "cpu.max": "20000 100000",
            "memory.max": "67108864",
            "pids.max": "16",
            "pid_attached": True,
        },
    }


def test_q12_evidence_requires_observed_delegated_limits(passing_q12_gate):
    result = validate_q12_gate(passing_q12_gate)
    assert result["status"] == "PASS"
    assert result["environment"] == "staging"
    assert result["observed"]["pid_attached"] is True


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("status",), "BLOCKED"),
        (("environment",), "development"),
        (("health", "unified_v2"), False),
        (("health", "delegated_writable"), False),
        (("health", "controllers"), ["cpu", "memory"]),
        (("observed", "cpu.max"), "max 100000"),
        (("observed", "memory.max"), "max"),
        (("observed", "pids.max"), "max"),
        (("observed", "pid_attached"), False),
    ],
)
def test_q12_evidence_fails_closed_on_missing_or_mismatched_observation(
    passing_q12_gate, path, value
):
    payload = deepcopy(passing_q12_gate)
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(EvidenceManifestError):
        validate_q12_gate(payload)


def test_q12_evidence_requires_a_delegated_root(passing_q12_gate):
    payload = deepcopy(passing_q12_gate)
    payload["health"]["root"] = ""

    with pytest.raises(EvidenceManifestError):
        validate_q12_gate(payload)
