from __future__ import annotations

import json
from urllib.parse import parse_qs, urlsplit

import pytest

from creator_app.global_knowledge.mcp_registry_discovery import (
    MCPRegistryDiscoveryError,
    MCPRegistryNotFoundError,
    _SameHostRedirectHandler,
    get_mcp_registry_server_details,
    search_mcp_registry,
)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload: bytes, url: str = "https://registry.modelcontextprotocol.io/v0.1/servers"):
        self.payload = payload
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def geturl(self):
        return self.url

    def read(self, size: int = -1):
        return self.payload if size < 0 else self.payload[:size]


def registry_payload():
    return {
        "servers": [
            {
                "server": {
                    "name": "io.github.example/search",
                    "description": "Search service",
                    "version": "1.2.0",
                    "repository": {"url": "https://github.com/example/search"},
                },
                "_meta": {
                    "io.modelcontextprotocol.registry/official": {
                        "status": "active",
                        "isLatest": True,
                    }
                },
            },
            {
                "server": {"name": "io.github.example/old", "version": "0.1.0"},
                "_meta": {
                    "io.modelcontextprotocol.registry/official": {
                        "status": "deprecated",
                        "isLatest": True,
                    }
                },
            },
            {
                "server": {"name": "io.github.example/stale", "version": "0.9.0"},
                "_meta": {
                    "io.modelcontextprotocol.registry/official": {
                        "status": "active",
                        "isLatest": False,
                    }
                },
            },
        ],
        "metadata": {"nextCursor": "opaque-cursor"},
    }


def test_mcp_registry_search_returns_only_active_latest_observations():
    calls = []

    def opener(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(json.dumps(registry_payload()).encode())

    result = search_mcp_registry(" search ", 10, cursor="opaque-in", opener=opener)
    assert result["query"] == "search"
    assert result["count"] == 1
    assert result["has_more"] is True
    assert result["next_cursor"] == "opaque-cursor"
    candidate = result["results"][0]
    assert candidate["name"] == "io.github.example/search"
    assert candidate["review_state"] == "OBSERVED"
    assert candidate["installation_enabled"] is False
    assert candidate["execution_enabled"] is False
    assert "repository" not in candidate
    request, timeout = calls[0]
    params = parse_qs(urlsplit(request.full_url).query)
    assert params == {
        "search": ["search"],
        "version": ["latest"],
        "limit": ["10"],
        "cursor": ["opaque-in"],
    }
    assert timeout == 8


def test_mcp_registry_search_rejects_bad_query_and_limit():
    with pytest.raises(ValueError, match="at least 3"):
        search_mcp_registry("ab", opener=lambda *_args, **_kwargs: None)
    with pytest.raises(ValueError, match="limit"):
        search_mcp_registry("search", 0, opener=lambda *_args, **_kwargs: None)
    with pytest.raises(ValueError, match="cursor"):
        search_mcp_registry("search", cursor="x" * 513, opener=lambda *_args, **_kwargs: None)


def test_mcp_registry_search_rejects_redirects_and_oversized_payloads():
    def redirect(*_args, **_kwargs):
        return FakeResponse(b"{}", "https://attacker.example/redirect")
    with pytest.raises(MCPRegistryDiscoveryError, match="redirected"):
        search_mcp_registry("search", opener=redirect)

    def oversized(*_args, **_kwargs):
        return FakeResponse(b"x" * 1_000_001)
    with pytest.raises(MCPRegistryDiscoveryError, match="size limit"):
        search_mcp_registry("search", opener=oversized)


def test_mcp_registry_redirect_handler_blocks_cross_host_redirects():
    from urllib.request import Request

    handler = _SameHostRedirectHandler()
    request = Request("https://registry.modelcontextprotocol.io/v0.1/servers")
    with pytest.raises(MCPRegistryDiscoveryError, match="redirect target"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://127.0.0.1/latest",
        )


def test_mcp_registry_detail_returns_sanitized_metadata_without_secret_values():
    payload = {
        "server": {
            "name": "io.github.example/terraform",
            "description": "Terraform metadata tools",
            "version": "1.2.3",
            "repository": {
                "url": "https://github.com/example/terraform",
                "source": "github",
                "subfolder": "server",
            },
            "packages": [{
                "registryType": "npm",
                "identifier": "example-terraform-mcp",
                "version": "1.2.3",
                "runtimeHint": "npx",
                "transport": {"type": "stdio"},
                "environmentVariables": [
                    {"name": "READ_ONLY", "isRequired": True, "isSecret": False},
                    {
                        "name": "API_TOKEN",
                        "isRequired": True,
                        "isSecret": True,
                        "default": "never expose",
                    },
                ],
            }],
            "remotes": [{"type": "streamable-http", "url": "https://example.org/mcp?token=never-expose"}],
        },
        "_meta": {
            "io.modelcontextprotocol.registry/official": {
                "status": "active",
                "isLatest": True,
            }
        },
    }
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return FakeResponse(json.dumps(payload).encode())

    result = get_mcp_registry_server_details("io.github.example/terraform", opener=opener)
    assert "%2F" in requests[0][0].full_url
    assert requests[0][1] == 8
    assert result["repository_host"] == "github.com"
    assert result["repository_url"] == "https://github.com/example/terraform"
    assert result["packages"][0]["transport"] == "stdio"
    assert result["packages"][0]["configuration_hints"] == [
        {"name": "READ_ONLY", "required": True, "secret": False},
        {"name": "API_TOKEN", "required": True, "secret": True},
    ]
    assert result["remotes"] == [{"transport": "streamable-http", "host": "example.org"}]
    assert "never-expose" not in json.dumps(result)
    assert result["installation_enabled"] is False
    assert result["execution_enabled"] is False


def test_mcp_registry_detail_rejects_untrusted_path_components():
    with pytest.raises(ValueError, match="namespace/name"):
        get_mcp_registry_server_details(
            "https://attacker.example/path", opener=lambda *_a, **_k: None
        )
    with pytest.raises(ValueError, match="version"):
        get_mcp_registry_server_details(
            "io.github.example/tool", "../../latest", opener=lambda *_a, **_k: None
        )


def test_mcp_registry_detail_does_not_expose_untrusted_repository_urls():
    payload = {
        "server": {
            "name": "io.github.example/tool",
            "version": "1.0.0",
            "repository": {"url": "https://attacker.example/repo?token=secret"},
            "websiteUrl": "https://attacker.example/?token=secret",
        },
        "_meta": {
            "io.modelcontextprotocol.registry/official": {
                "status": "active",
                "isLatest": True,
            }
        },
    }

    def opener(*_args, **_kwargs):
        return FakeResponse(json.dumps(payload).encode())

    result = get_mcp_registry_server_details("io.github.example/tool", opener=opener)
    assert result["repository_url"] is None
    assert result["website_host"] == "attacker.example"
    assert result.get("website_url") is None
    assert "token=secret" not in json.dumps(result)


def test_mcp_registry_detail_maps_http_404_to_not_found():
    from urllib.error import HTTPError

    def missing(*_args, **_kwargs):
        raise HTTPError(
            "https://registry.modelcontextprotocol.io/missing",
            404,
            "Not Found",
            {},
            None,
        )

    with pytest.raises(MCPRegistryNotFoundError, match="not found"):
        get_mcp_registry_server_details("io.github.example/missing", opener=missing)


def test_mcp_registry_detail_safely_handles_malformed_public_urls():
    payload = {
        "server": {
            "name": "io.github.example/malformed",
            "version": "1.0.0",
            "repository": {"url": "https://[invalid"},
            "websiteUrl": "https://[invalid",
            "remotes": [{"type": "streamable-http", "url": "https://[invalid"}],
        },
        "_meta": {
            "io.modelcontextprotocol.registry/official": {
                "status": "active",
                "isLatest": True,
            }
        },
    }

    def opener(*_args, **_kwargs):
        return FakeResponse(json.dumps(payload).encode())

    result = get_mcp_registry_server_details(
        "io.github.example/malformed", opener=opener
    )
    assert result["repository_url"] is None
    assert result["repository_host"] is None
    assert result["website_host"] is None
    assert result["remotes"] == [
        {"transport": "streamable-http", "host": "unknown"}
    ]
