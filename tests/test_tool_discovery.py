from __future__ import annotations

import pytest

from creator_app.global_knowledge.tool_discovery import (
    ReviewState,
    ToolCandidate,
    ToolKind,
    plan_tool_search,
    rank_discovered_functions,
    rank_tool_candidates,
)


def test_plan_tool_search_is_bounded_and_deduplicated() -> None:
    queries = plan_tool_search("MCP search connectors", max_queries=5)
    assert len(queries) == 5
    assert len(set(queries)) == len(queries)
    assert any("MCP server" in query for query in queries)


def test_plan_tool_search_rejects_empty_and_oversized_input() -> None:
    with pytest.raises(ValueError, match="query is required"):
        plan_tool_search("  ")
    with pytest.raises(ValueError, match="500 characters"):
        plan_tool_search("x" * 501)


def test_rank_tool_candidates_deduplicates_urls_and_never_auto_approves() -> None:
    candidates = [
        ToolCandidate(
            name="MCP Search Connector",
            url="https://example.test/tool/?ref=search",
            description="Search web sources through an MCP connector",
            kind=ToolKind.MCP,
        ),
        ToolCandidate(
            name="Search Connector mirror",
            url="https://EXAMPLE.test/tool#readme",
            description="Search tools",
            kind=ToolKind.MCP,
        ),
        ToolCandidate(
            name="Approved local search",
            url="https://local.example/search",
            description="Search local documents",
            review_state=ReviewState.APPROVED,
        ),
    ]
    ranked = rank_tool_candidates("MCP search connector", candidates)
    assert len(ranked) == 2
    assert ranked[0].candidate.name == "MCP Search Connector"
    assert ranked[0].disposition == "discovery_only_requires_review"
    assert any(item.disposition == "approved_subject_to_runtime_policy" for item in ranked)
    assert all(
        item.candidate.review_state is not ReviewState.APPROVED
        or item.disposition.startswith("approved")
        for item in ranked
    )


def test_candidate_rejects_non_http_url_and_embedded_credentials() -> None:
    with pytest.raises(ValueError, match=r"http\(s\)"):
        ToolCandidate(name="bad", url="file:///etc/passwd")
    with pytest.raises(ValueError, match="credentials"):
        ToolCandidate(name="bad", url="https://user:pass@example.test/tool")


def test_rank_limit_is_validated() -> None:
    candidate = ToolCandidate(name="search", url="https://example.test/search")
    with pytest.raises(ValueError, match="limit"):
        rank_tool_candidates("search", [candidate], limit=0)



def test_rank_discovered_functions_is_safe_and_ranks_by_relevance() -> None:
    functions = [
        {
            "connector_id": "docs",
            "name": "search_documents",
            "logical_name": "docs.search_documents",
            "description": "Search indexed project documents",
            "risk": "READ_ONLY",
            "schema_hash": "abc123",
            "connector_state": "SCHEMA_VERIFIED",
        },
        {
            "connector_id": "mail",
            "name": "send_email",
            "logical_name": "mail.send_email",
            "description": "Send an email message",
            "risk": "WRITE",
            "schema_hash": "def456",
            "connector_state": "SCHEMA_VERIFIED",
        },
    ]
    ranked = rank_discovered_functions("search documents", functions)
    assert ranked[0]["logical_name"] == "docs.search_documents"
    assert ranked[0]["execution_available"] is False
    assert ranked[0]["approval_required"] is False
    assert len(ranked) == 1
    assert all(
        item["disposition"] == "discovery_only_policy_authorization_required"
        for item in ranked
    )
    assert all("url" not in item and "input_schema" not in item for item in ranked)


def test_rank_discovered_functions_validates_bounds_and_deduplicates() -> None:
    function = {
        "connector_id": "docs",
        "name": "search",
        "logical_name": "docs.search",
        "risk": "READ_ONLY",
    }
    assert len(rank_discovered_functions("search", [function, function])) == 1
    with pytest.raises(ValueError, match="query is required"):
        rank_discovered_functions(" ", [function])
    with pytest.raises(ValueError, match="200 characters"):
        rank_discovered_functions("x" * 201, [function])
    with pytest.raises(ValueError, match="limit"):
        rank_discovered_functions("search", [function], limit=0)



def test_rank_discovered_functions_does_not_dedupe_before_matching() -> None:
    functions = [
        {
            "connector_id": "docs",
            "name": "list_documents",
            "logical_name": "docs.search",
            "description": "List items",
            "risk": "READ_ONLY",
        },
        {
            "connector_id": "docs",
            "name": "search_documents",
            "logical_name": "docs.search",
            "description": "Search indexed documents",
            "risk": "READ_ONLY",
        },
    ]
    ranked = rank_discovered_functions("search documents", functions)
    assert len(ranked) == 1
    assert ranked[0]["name"] == "search_documents"
