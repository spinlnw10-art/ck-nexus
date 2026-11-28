from __future__ import annotations

from copy import deepcopy

import pytest

from creator_app.agnes.execution.phase3.hardening import CgroupV2Manager
from scripts.gitlab_evidence_manifest import (
    EvidenceManifestError,
    junit_is_clean,
    pipeline_provenance,
    validate_q12_gate,
)


@pytest.fixture
def passing_q12_gate() -> dict[str, object]:
    return {
        "status": "PASS",
        "environment": "staging",
        "health": {
            "unified_v2": True,
            "delegated_writable": True,
            "ready": True,
            "controllers": ["cpu", "memory", "pids"],
            "enabled_controllers": ["cpu", "memory", "pids"],
            "missing_enabled_controllers": [],
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
        (("health", "ready"), False),
        (("health", "controllers"), ["cpu", "memory"]),
        (("health", "enabled_controllers"), ["cpu", "memory"]),
        (("health", "missing_enabled_controllers"), ["pids"]),
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


@pytest.mark.parametrize(
    ("junit", "expected"),
    [
        ({"tests": 3, "failures": 0, "errors": 0, "skipped": 0}, True),
        ({"tests": 3, "failures": 0, "errors": 0, "skipped": 1}, True),
        ({"tests": 0, "failures": 0, "errors": 0, "skipped": 0}, False),
        ({"tests": 3, "failures": 0, "errors": 0, "skipped": 3}, False),
        ({"tests": 3, "failures": 1, "errors": 0, "skipped": 0}, False),
        ({"tests": 3, "failures": 0, "errors": 1, "skipped": 0}, False),
    ],
)
def test_junit_gate_requires_executed_tests_and_no_failures(junit, expected):
    assert junit_is_clean(junit) is expected


def test_cgroup_manager_uses_configured_delegated_root(tmp_path, monkeypatch):
    root = tmp_path / "delegated"
    root.mkdir()
    (root / "cgroup.controllers").write_text("cpu memory pids")
    (root / "cgroup.subtree_control").write_text("cpu memory pids")
    monkeypatch.setenv("CKNEXUS_AGNES_CGROUP_ROOT", str(root))
    health = CgroupV2Manager().health()
    assert health["root"] == str(root)
    assert health["ready"] is True
    assert health["enabled_controllers"] == ["cpu", "memory", "pids"]


def test_detached_merge_request_does_not_claim_merge_result():
    env = {"CI_PIPELINE_SOURCE": "merge_request_event", "CI_MERGE_REQUEST_EVENT_TYPE": "detached"}
    provenance = pipeline_provenance(
        env, commit_sha="source-sha", git_runner=lambda *args: "source-tree"
    )
    assert provenance["pipeline_subject_kind"] == "detached_merge_request_source"
    assert provenance["source_branch_sha"] == "source-sha"
    assert provenance["source_tree_sha"] == "source-tree"
    assert provenance["merge_result_commit_sha"] is None
    assert provenance["merge_result_tree_sha"] is None


def test_merged_result_pipeline_records_distinct_source_and_merge_result():
    env = {
        "CI_PIPELINE_SOURCE": "merge_request_event",
        "CI_MERGE_REQUEST_EVENT_TYPE": "merged_result",
        "CI_MERGE_REQUEST_SOURCE_BRANCH_SHA": "source-sha",
    }
    provenance = pipeline_provenance(
        env, commit_sha="merge-sha",
        git_runner=lambda *args: (
            "merge-tree"
            if args == ("rev-parse", "merge-sha^{tree}")
            else "source-tree"
        ),
    )
    assert provenance["pipeline_subject_kind"] == "merged_result"
    assert provenance["source_branch_sha"] == "source-sha"
    assert provenance["source_tree_sha"] == "source-tree"
    assert provenance["merge_result_commit_sha"] == "merge-sha"
    assert provenance["merge_result_tree_sha"] == "merge-tree"


def test_merged_result_requires_explicit_source_branch_sha():
    env = {
        "CI_PIPELINE_SOURCE": "merge_request_event",
        "CI_MERGE_REQUEST_EVENT_TYPE": "merged_result",
    }
    with pytest.raises(EvidenceManifestError, match="missing CI_MERGE_REQUEST_SOURCE_BRANCH_SHA"):
        pipeline_provenance(
            env, commit_sha="merge-sha", git_runner=lambda *args: "tree-sha"
        )
