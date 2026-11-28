#!/usr/bin/env python3
"""Create GitLab CI provenance and a CK-NEXUS EvidenceGraph lineage artifact.

The manifest fails closed: every required report must exist and parse, the evidence
graph must validate, JUnit must be clean, Secret Detection must be clean, and an
explicit versioned SAST policy must evaluate to PASS. The default policy blocks any
SAST finding; scanner execution success is never treated as a security verdict.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from creator_app.global_knowledge.evidence_graph import (  # noqa: E402
    EvidenceEdgeKind,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    EvidenceNodeKind,
)

REQUIRED_REPORTS: dict[str, str] = {
    "junit": "report.xml",
    "sast": "gl-sast-report.json",
    "secret_detection": "gl-secret-detection-report.json",
    "historical_index": "evidence/gitlab/historical-evidence.json",
    "sast_policy": "evidence/gitlab/sast-policy.json",
    "q12_gate": "q12-cgroup-gate.json",
}
HISTORICAL_INDEX_PATH = REQUIRED_REPORTS["historical_index"]
JUNIT_COUNTERS = ("tests", "failures", "errors", "skipped")
SAST_POLICY_ID = "CKNEXUS-SAST-STRICT-0"


class EvidenceManifestError(RuntimeError):
    """Required evidence is missing or invalid; no manifest may be published."""


@dataclass(frozen=True, slots=True)
class EvidenceManifestResult:
    manifest: dict[str, Any]
    graph: dict[str, Any]


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=cwd or ROOT, text=True, stderr=subprocess.PIPE
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceManifestError(f"git {' '.join(args)} failed: {exc}") from exc


def _read_required_bytes(root: Path, name: str) -> bytes:
    path = root / name
    if not path.is_file():
        raise EvidenceManifestError(f"required evidence report missing: {name}")
    data = path.read_bytes()
    if not data.strip():
        raise EvidenceManifestError(f"required evidence report is empty: {name}")
    return data


def report_record(root: Path, name: str) -> dict[str, Any]:
    data = _read_required_bytes(root, name)
    return {
        "path": name,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _load_json_report(root: Path, name: str) -> dict[str, Any]:
    data = _read_required_bytes(root, name)
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceManifestError(
            f"required evidence report is not valid JSON: {name}"
        ) from exc
    if not isinstance(value, dict):
        raise EvidenceManifestError(
            f"required evidence report must be a JSON object: {name}"
        )
    return value


def _parse_junit_report(root: Path, name: str) -> dict[str, int]:
    data = _read_required_bytes(root, name)
    try:
        xml_root = ET.fromstring(data)
    except (ET.ParseError, DefusedXmlException) as exc:
        raise EvidenceManifestError(f"{name} is not valid JUnit XML") from exc

    totals = dict.fromkeys(JUNIT_COUNTERS, 0)
    # Count only top-level suites: parent JUnit suites aggregate their
    # nested per-module suites, so summing every descendant double-counts tests.
    suites = (
        [xml_root]
        if xml_root.tag == "testsuite"
        else [child for child in xml_root if child.tag == "testsuite"]
    )
    if suites:
        for suite in suites:
            for counter in JUNIT_COUNTERS:
                raw = suite.get(counter)
                if raw is None:
                    continue
                try:
                    value = int(raw)
                except ValueError as exc:
                    raise EvidenceManifestError(
                        f"{name} has a non-integer {counter} attribute"
                    ) from exc
                if value < 0:
                    raise EvidenceManifestError(
                        f"{name} has a negative {counter} attribute"
                    )
                totals[counter] += value
        return totals

    # Node's built-in JUnit reporter emits <testsuites><testcase> rather than
    # pytest's <testsuites><testsuite tests=...> form.
    cases = list(xml_root.iter("testcase"))
    if not cases:
        raise EvidenceManifestError(f"{name} contains no testsuite or testcase elements")
    totals["tests"] = len(cases)
    for case in cases:
        for child in case:
            if child.tag in {"failure", "error", "skipped"}:
                totals[child.tag] += 1
    return totals


def parse_junit(root: Path) -> dict[str, int]:
    totals = dict.fromkeys(JUNIT_COUNTERS, 0)
    for name in ("report.xml", "node-report.xml", "cgroup-report.xml"):
        report_totals = _parse_junit_report(root, name)
        for counter in JUNIT_COUNTERS:
            totals[counter] += report_totals[counter]
    return totals


def validate_q12_gate(payload: dict[str, Any]) -> dict[str, Any]:
    """Require observed delegated cgroup v2 enforcement, not a mocked health check."""
    if payload.get("status") != "PASS":
        raise EvidenceManifestError("Q12 cgroup staging gate did not report PASS")
    if payload.get("environment") != "staging":
        raise EvidenceManifestError("Q12 gate evidence is not bound to staging")

    health = payload.get("health")
    if not isinstance(health, dict):
        raise EvidenceManifestError("Q12 gate health evidence is missing")
    if health.get("unified_v2") is not True or health.get("delegated_writable") is not True:
        raise EvidenceManifestError("Q12 requires writable delegated unified cgroup v2")
    controllers = health.get("controllers")
    if not isinstance(controllers, list) or not {"cpu", "memory", "pids"}.issubset(controllers):
        raise EvidenceManifestError("Q12 required cgroup controllers are unavailable")
    root = health.get("root")
    if not isinstance(root, str) or not root:
        raise EvidenceManifestError("Q12 delegated cgroup root is missing")

    observed = payload.get("observed")
    expected = {
        "cpu.max": "20000 100000",
        "memory.max": str(64 * 1024 * 1024),
        "pids.max": "16",
        "pid_attached": True,
    }
    if not isinstance(observed, dict) or observed != expected:
        raise EvidenceManifestError("Q12 observed resource limits or child attachment do not match")
    return {
        "status": "PASS",
        "environment": "staging",
        "delegated_root": root,
        "controllers": sorted(controllers),
        "observed": expected,
    }


def _load_q12_gate(root: Path) -> dict[str, Any]:
    return validate_q12_gate(_load_json_report(root, REQUIRED_REPORTS["q12_gate"]))


def _line_number(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def evaluate_sast_policy(
    policy: dict[str, Any], findings: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    expected_keys = {"schema_version", "policy_id", "fail_on_any_finding"}
    if set(policy) != expected_keys:
        raise EvidenceManifestError("SAST policy schema must contain only the required keys")
    if policy.get("schema_version") != 1 or policy.get("policy_id") != SAST_POLICY_ID:
        raise EvidenceManifestError("SAST policy schema version or policy id is unsupported")
    if policy.get("fail_on_any_finding") is not True:
        raise EvidenceManifestError("SAST policy must fail closed on every finding")
    return {
        "policy_id": SAST_POLICY_ID,
        "rule": "zero_findings",
        "evaluated": True,
        "passed": len(findings) == 0,
        "finding_count": len(findings),
    }


def report_findings(report: dict[str, Any], name: str) -> list[dict[str, Any]]:
    items = report.get("vulnerabilities")
    if not isinstance(items, list):
        raise EvidenceManifestError(f"{name} must contain a vulnerabilities list")

    findings: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise EvidenceManifestError(f"{name} contains a non-object vulnerability entry")
        location = item.get("location")
        if not isinstance(location, dict):
            location = {}
        identifiers = item.get("identifiers")
        if not isinstance(identifiers, list):
            identifiers = []
        rule_id = next(
            (
                entry.get("value")
                for entry in identifiers
                if isinstance(entry, dict) and entry.get("type") in {
                    "semgrep_id",
                    "cwe",
                    "gitleaks_rule_id",
                }
            ),
            None,
        )
        findings.append(
            {
                "id": item.get("id"),
                "rule_id": rule_id,
                "name": item.get("name"),
                "severity": item.get("severity"),
                "confidence": item.get("confidence"),
                "file": location.get("file"),
                "start_line": location.get("start_line"),
                "commit": location.get("commit"),
            }
        )
    return sorted(
        findings,
        key=lambda finding: (
            str(finding.get("file")),
            _line_number(finding.get("start_line")),
            str(finding.get("rule_id")),
        ),
    )


def _load_historical_index(root: Path) -> dict[str, Any]:
    report = _load_json_report(root, HISTORICAL_INDEX_PATH)
    if not isinstance(report.get("records"), list):
        raise EvidenceManifestError(
            "historical evidence index must contain a records list"
        )
    return report


def derived_from_cycles(edges: Sequence[EvidenceGraphEdge]) -> tuple[tuple[str, ...], ...]:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        if edge.kind is EvidenceEdgeKind.DERIVED_FROM:
            adjacency.setdefault(edge.from_node_id, []).append(edge.to_node_id)

    cycles: set[tuple[str, ...]] = set()
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            index = visiting.index(node_id)
            cycles.add(tuple(visiting[index:] + [node_id]))
            return
        if node_id in visited:
            return
        visiting.append(node_id)
        for target in adjacency.get(node_id, ()):
            visit(target)
        visiting.pop()
        visited.add(node_id)

    for node_id in adjacency:
        visit(node_id)
    return tuple(sorted(cycles))


def validate_evidence_graph(
    nodes: Sequence[EvidenceGraphNode], edges: Sequence[EvidenceGraphEdge]
) -> dict[str, Any]:
    """Validate node/edge IDs, references, and DERIVED_FROM cycles."""
    node_ids = [node.node_id for node in nodes]
    edge_ids = [edge.edge_id for edge in edges]
    errors: list[str] = []

    if not node_ids:
        errors.append("graph has no nodes")
    if len(set(node_ids)) != len(node_ids):
        errors.append("duplicate node_id values")
    if len(set(edge_ids)) != len(edge_ids):
        errors.append("duplicate edge_id values")

    known_nodes = set(node_ids)
    missing = sorted(
        {
            endpoint
            for edge in edges
            for endpoint in (edge.from_node_id, edge.to_node_id)
            if endpoint not in known_nodes
        }
    )
    if missing:
        errors.append("edges reference missing nodes: " + ",".join(missing))

    cycles = derived_from_cycles(edges)
    if cycles:
        errors.append("derived_from cycles detected")

    if not errors:
        try:
            EvidenceGraph(tuple(nodes), tuple(edges))
        except ValueError as exc:
            errors.append(f"evidence graph invalid: {exc}")

    return {
        "validated": not errors,
        "errors": errors,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "derived_from_cycles": [list(cycle) for cycle in cycles],
    }


def _serialize(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _lineage(graph: EvidenceGraph, start_node_id: str) -> list[dict[str, Any]]:
    return [
        {
            "root_node_id": path.root_node_id,
            "node_ids": list(path.node_ids),
            "depth": path.depth,
            "independent_validation_edges": path.independent_validation_edges,
            "cycle_detected": path.cycle_detected,
        }
        for path in graph.trace_lineage(start_node_id)
    ]


def build_manifest(
    root: Path = ROOT,
    *,
    environ: Mapping[str, str] | None = None,
    observed_at: str | None = None,
    git_runner: Callable[..., str] | None = None,
) -> EvidenceManifestResult:
    """Collect and validate evidence; raises EvidenceManifestError when incomplete."""
    env = os.environ if environ is None else environ
    observed_at = observed_at or datetime.now(UTC).isoformat()
    runner = git_runner or (lambda *args: git(*args, cwd=root))

    reports = {
        key: report_record(root, name) for key, name in REQUIRED_REPORTS.items()
    }
    junit = parse_junit(root)
    sast_report = _load_json_report(root, REQUIRED_REPORTS["sast"])
    secret_report = _load_json_report(root, REQUIRED_REPORTS["secret_detection"])
    sast_policy = _load_json_report(root, REQUIRED_REPORTS["sast_policy"])
    q12_gate = _load_q12_gate(root)
    _load_historical_index(root)

    sast_findings = report_findings(sast_report, REQUIRED_REPORTS["sast"])
    sast_policy_result = evaluate_sast_policy(sast_policy, sast_findings)
    secret_findings = report_findings(
        secret_report, REQUIRED_REPORTS["secret_detection"]
    )

    commit_sha = env.get("CI_COMMIT_SHA") or runner("rev-parse", "HEAD")
    source_sha = env.get("CI_MERGE_REQUEST_SOURCE_BRANCH_SHA") or commit_sha
    diff_base_sha = env.get("CI_MERGE_REQUEST_DIFF_BASE_SHA") or None
    merge_result_tree_sha = runner("rev-parse", f"{commit_sha}^{{tree}}")
    source_tree_sha = runner("rev-parse", f"{source_sha}^{{tree}}")
    for label, value in (
        ("commit_sha", commit_sha),
        ("source_branch_sha", source_sha),
        ("merge_result_tree_sha", merge_result_tree_sha),
        ("source_tree_sha", source_tree_sha),
    ):
        if not value:
            raise EvidenceManifestError(f"unable to resolve {label}")

    pipeline_id = env.get("CI_PIPELINE_ID", "unknown")
    job_id = env.get("CI_JOB_ID", "unknown")
    project_path = env.get("CI_PROJECT_PATH") or "unknown-project"
    historical_sha = reports["historical_index"]["sha256"]

    source_id = f"gitlab-ci:{pipeline_id}:{commit_sha}"
    claim_id = f"gitlab-verification:{pipeline_id}:{commit_sha}"
    historical_source_id = f"historical-evidence-index:{historical_sha}"
    historical_claim_id = f"historical-verification-reference:{historical_sha}"

    nodes = (
        EvidenceGraphNode(
            node_id=source_id,
            kind=EvidenceNodeKind.SOURCE,
            observed_at=observed_at,
            source_id=f"{project_path}@{commit_sha}",
        ),
        EvidenceGraphNode(
            node_id=claim_id,
            kind=EvidenceNodeKind.CLAIM,
            observed_at=observed_at,
            claim_id=f"pipeline:{pipeline_id}:reports-collected",
        ),
        EvidenceGraphNode(
            node_id=historical_source_id,
            kind=EvidenceNodeKind.SOURCE,
            observed_at=observed_at,
            source_id=f"{HISTORICAL_INDEX_PATH}@sha256:{historical_sha}",
        ),
        EvidenceGraphNode(
            node_id=historical_claim_id,
            kind=EvidenceNodeKind.CLAIM,
            observed_at=observed_at,
            claim_id="historical-verification:reference-only-not-current-candidate-pass",
        ),
    )
    edges = (
        EvidenceGraphEdge(
            edge_id=f"derived:{pipeline_id}:{commit_sha}",
            from_node_id=claim_id,
            to_node_id=source_id,
            kind=EvidenceEdgeKind.DERIVED_FROM,
            independent_validation=False,
        ),
        EvidenceGraphEdge(
            edge_id=f"historical-reference:{historical_sha}",
            from_node_id=historical_claim_id,
            to_node_id=historical_source_id,
            kind=EvidenceEdgeKind.DERIVED_FROM,
            independent_validation=False,
        ),
    )

    graph_validation = validate_evidence_graph(nodes, edges)
    graph = EvidenceGraph(nodes, edges) if graph_validation["validated"] else None

    graph_payload: dict[str, Any] = {
        "schema_version": 1,
        "graph_type": "ck-nexus-evidence-lineage",
        "observed_at": observed_at,
        "nodes": [
            {
                "node_id": node.node_id,
                "kind": node.kind.value,
                "observed_at": node.observed_at,
                "source_id": node.source_id,
                "claim_id": node.claim_id,
            }
            for node in nodes
        ],
        "edges": [
            {
                "edge_id": edge.edge_id,
                "from_node_id": edge.from_node_id,
                "to_node_id": edge.to_node_id,
                "kind": edge.kind.value,
                "independent_validation": edge.independent_validation,
            }
            for edge in edges
        ],
        "validation": {
            "node_count": graph_validation["node_count"],
            "edge_count": graph_validation["edge_count"],
            "validated": graph_validation["validated"],
            "errors": graph_validation["errors"],
            "derived_from_cycles": graph_validation["derived_from_cycles"],
            "citation_cycles": (
                [list(cycle) for cycle in graph.report().citation_cycles] if graph else []
            ),
            "lineage": _lineage(graph, claim_id) if graph else [],
            "historical_reference_lineage": (
                _lineage(graph, historical_claim_id) if graph else []
            ),
        },
    }
    graph_sha = hashlib.sha256(_serialize(graph_payload)).hexdigest()

    reports_present = all(report is not None for report in reports.values())
    junit_clean = junit["failures"] == 0 and junit["errors"] == 0
    secret_clean = not secret_findings
    sast_policy_pass = bool(sast_policy_result["passed"])
    valid = bool(
        reports_present
        and graph_validation["validated"]
        and junit_clean
        and secret_clean
        and sast_policy_pass
        and q12_gate.get("status") == "PASS"
    )
    sast_verdict = "NO_FINDINGS_DETECTED" if not sast_findings else "FINDINGS_PRESENT"
    policy_evaluation = "PASS" if sast_policy_pass else "FAIL"
    secret_verdict = "FINDINGS_PRESENT" if secret_findings else "NO_FINDINGS_DETECTED"

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "gitlab-ci-evidence",
        "generated_at": observed_at,
        "project": env.get("CI_PROJECT_PATH"),
        "project_id": env.get("CI_PROJECT_ID"),
        "pipeline_id": pipeline_id,
        "pipeline_url": env.get("CI_PIPELINE_URL"),
        "job_id": job_id,
        "ref": env.get("CI_COMMIT_REF_NAME"),
        "ref_type": env.get("CI_COMMIT_REF_TYPE"),
        "pipeline_source": env.get("CI_PIPELINE_SOURCE"),
        # Merge-result provenance: the commit/tree this pipeline actually ran on.
        "commit_sha": commit_sha,
        "tree_sha": merge_result_tree_sha,
        "merge_result_commit_sha": commit_sha,
        "merge_result_tree_sha": merge_result_tree_sha,
        # Candidate source provenance: the branch head that produced the merge result.
        "source_branch_sha": source_sha,
        "source_tree_sha": source_tree_sha,
        "merge_request_diff_base_sha": diff_base_sha,
        "reports": reports,
        "junit": junit,
        "junit_failures_and_errors": junit["failures"] + junit["errors"],
        "sast_findings": sast_findings,
        "sast_findings_count": len(sast_findings),
        "sast_verdict": sast_verdict,
        "policy_evaluation": policy_evaluation,
        "sast_policy": {
            "path": REQUIRED_REPORTS["sast_policy"],
            "sha256": reports["sast_policy"]["sha256"],
            **sast_policy_result,
        },
        "q12_cgroup_staging": {
            "path": REQUIRED_REPORTS["q12_gate"],
            "sha256": reports["q12_gate"]["sha256"],
            **q12_gate,
        },
        "secret_findings": secret_findings,
        "secret_findings_count": len(secret_findings),
        "secret_verdict": secret_verdict,
        "historical_evidence": {
            "path": HISTORICAL_INDEX_PATH,
            "sha256": historical_sha,
            "classification": "HISTORICAL_REFERENCE_ONLY",
            "current_candidate_pass_claim": False,
        },
        "evidence_graph": {
            "path": "evidence/gitlab/evidence-graph.json",
            "sha256": graph_sha,
            "node_count": graph_validation["node_count"],
            "edge_count": graph_validation["edge_count"],
            "validated": graph_validation["validated"],
            "validation_errors": graph_validation["errors"],
            "derived_from_cycles": graph_validation["derived_from_cycles"],
        },
        "validation": {
            "valid": valid,
            "status": "PASSED" if valid else "FAILED",
            "required_reports_present": reports_present,
            "required_reports": list(REQUIRED_REPORTS.values()),
            "evidence_graph_validated": graph_validation["validated"],
            "junit_failures": junit["failures"],
            "junit_errors": junit["errors"],
            "junit_clean": junit_clean,
            "secret_clean": secret_clean,
            "secret_findings_count": len(secret_findings),
            "sast_policy_evaluated": sast_policy_result["evaluated"],
            "sast_policy_pass": sast_policy_pass,
            "sast_findings_count": len(sast_findings),
            "q12_cgroup_staging_pass": q12_gate.get("status") == "PASS",
        },
        "authority": {
            "release_decision": "NOT_GRANTED",
            "core_approval": "REQUIRED",
            "independent_review": "REQUIRED",
            "note": (
                "Validated CI lineage artifact only; not a canonical runtime ledger write "
                "and grants no release approval."
            ),
        },
    }
    return EvidenceManifestResult(manifest=manifest, graph=graph_payload)


def write_evidence_artifacts(
    root: Path, result: EvidenceManifestResult
) -> tuple[Path, Path]:
    out_dir = root / "evidence" / "gitlab"
    out_dir.mkdir(parents=True, exist_ok=True)

    graph_path = out_dir / "evidence-graph.json"
    graph_bytes = _serialize(result.graph)
    if hashlib.sha256(graph_bytes).hexdigest() != result.manifest["evidence_graph"]["sha256"]:
        raise EvidenceManifestError("evidence graph sha256 does not match manifest")
    graph_path.write_bytes(graph_bytes)

    manifest_path = out_dir / "ci-evidence.json"
    manifest_path.write_bytes(_serialize(result.manifest))
    return graph_path, manifest_path


def main() -> int:
    result = build_manifest(ROOT)
    graph_path, manifest_path = write_evidence_artifacts(ROOT, result)
    manifest = result.manifest

    print(f"evidence_graph={graph_path.relative_to(ROOT)}")
    print(f"evidence_graph_sha256={manifest['evidence_graph']['sha256']}")
    print(f"evidence_manifest={manifest_path.relative_to(ROOT)}")
    print(f"evidence_manifest_sha256={hashlib.sha256(manifest_path.read_bytes()).hexdigest()}")
    print(f"validation_status={manifest['validation']['status']}")
    print(
        "junit="
        f"tests={manifest['junit']['tests']} "
        f"failures={manifest['junit']['failures']} "
        f"errors={manifest['junit']['errors']} "
        f"skipped={manifest['junit']['skipped']}"
    )
    print(f"sast_verdict={manifest['sast_verdict']}")
    print(f"sast_policy_evaluation={manifest['policy_evaluation']}")
    print(f"sast_findings_count={manifest['sast_findings_count']}")
    print(f"secret_findings_count={manifest['secret_findings_count']}")
    for finding in manifest["sast_findings"]:
        print(
            "[SAST] "
            f"severity={finding.get('severity')} confidence={finding.get('confidence')} "
            f"rule={finding.get('rule_id') or finding.get('name')} "
            f"location={finding.get('file')}:{finding.get('start_line')} "
            f"name={finding.get('name')}"
        )
    for finding in manifest["secret_findings"]:
        print(
            "[SECRET] "
            f"rule={finding.get('rule_id') or finding.get('name')} "
            f"location={finding.get('file')}:{finding.get('start_line')} "
            f"commit={finding.get('commit') or 'UNAVAILABLE'} "
            f"name={finding.get('name')}"
        )
    return 0 if manifest["validation"]["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())