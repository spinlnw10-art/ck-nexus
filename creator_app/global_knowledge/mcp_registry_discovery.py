"""Read-only discovery client for the official Model Context Protocol Registry."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

REGISTRY_BASE_URL = "https://registry.modelcontextprotocol.io"
MAX_RESPONSE_BYTES = 1_000_000


class MCPRegistryDiscoveryError(RuntimeError):
    """Raised when the official MCP Registry cannot provide a safe response."""


class MCPRegistryNotFoundError(MCPRegistryDiscoveryError):
    """Raised when an exact MCP Registry server/version does not exist."""


class _SameHostRedirectHandler(HTTPRedirectHandler):
    """Prevent the fixed registry client from following redirects to other hosts."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if (
            target.scheme != "https"
            or target.hostname != "registry.modelcontextprotocol.io"
            or target.port not in (None, 443)
            or target.username is not None
            or target.password is not None
        ):
            raise MCPRegistryDiscoveryError("Registry redirect target is not allowed.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def search_mcp_registry(
    query: str,
    limit: int = 20,
    *,
    cursor: str | None = None,
    opener=None,
) -> dict[str, object]:
    """Search the official registry without installing, fetching or executing servers."""
    normalized = " ".join(query.split())
    if len(normalized) < 3:
        raise ValueError("query must contain at least 3 characters")
    if len(normalized) > 120:
        raise ValueError("query must be <= 120 characters")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be within 1..50")
    if cursor is not None and len(cursor) > 512:
        raise ValueError("cursor must be <= 512 characters")

    query_params: dict[str, str | int] = {
        "search": normalized,
        "version": "latest",
        "limit": limit,
    }
    if cursor:
        query_params["cursor"] = cursor
    params = urlencode(query_params)
    url = f"{REGISTRY_BASE_URL}/v0.1/servers?{params}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "CK-NEXUS-MCP-Discovery/1.0",
        },
        method="GET",
    )
    open_request = opener or build_opener(_SameHostRedirectHandler()).open
    try:
        with open_request(request, timeout=8) as response:
            final_url = urlsplit(response.geturl())
            if (
                final_url.scheme != "https"
                or final_url.hostname != "registry.modelcontextprotocol.io"
                or final_url.port not in (None, 443)
                or final_url.username is not None
                or final_url.password is not None
            ):
                raise MCPRegistryDiscoveryError("Registry redirected outside the trusted host.")
            if getattr(response, "status", 200) != 200:
                raise MCPRegistryDiscoveryError(
                    "Official MCP Registry returned a non-success status."
                )
            content_type = response.headers.get("Content-Type", "application/json").split(";", 1)[0]
            if content_type.strip().lower() != "application/json":
                raise MCPRegistryDiscoveryError(
                    "Official MCP Registry returned an unexpected content type."
                )
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise MCPRegistryDiscoveryError(
            "Official MCP Registry is temporarily unavailable."
        ) from exc

    if len(raw) > MAX_RESPONSE_BYTES:
        raise MCPRegistryDiscoveryError("Official MCP Registry response exceeded the size limit.")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MCPRegistryDiscoveryError("Official MCP Registry returned invalid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("servers"), list):
        raise MCPRegistryDiscoveryError("Official MCP Registry response schema is invalid.")

    results: list[dict[str, object]] = []
    for item in payload["servers"]:
        if not isinstance(item, dict) or not isinstance(item.get("server"), dict):
            continue
        server = item["server"]
        metadata = item.get("_meta")
        official = (
            metadata.get("io.modelcontextprotocol.registry/official", {})
            if isinstance(metadata, dict)
            else {}
        )
        if not isinstance(official, dict):
            official = {}
        status = str(official.get("status", "unknown")).lower()
        is_latest = official.get("isLatest") is True
        if status != "active" or not is_latest:
            continue
        name = str(server.get("name", "")).strip()
        version = str(server.get("version", "")).strip()
        if not name or not version:
            continue
        results.append(
            {
                "name": name[:200],
                "description": str(server.get("description", ""))[:500],
                "version": version[:80],
                "registry_status": status,
                "is_latest": True,
                "source": "official_mcp_registry",
                "review_state": "OBSERVED",
                "installation_enabled": False,
                "execution_enabled": False,
            }
        )
        if len(results) >= limit:
            break

    metadata = payload.get("metadata")
    next_cursor = metadata.get("nextCursor") if isinstance(metadata, dict) else None
    if not isinstance(next_cursor, str) or len(next_cursor) > 512:
        next_cursor = None
    return {
        "available": True,
        "query": normalized,
        "count": len(results),
        "results": results,
        "has_more": bool(next_cursor),
        "next_cursor": next_cursor,
        "source": "official_mcp_registry",
        "discovery_only": True,
        "installation_enabled": False,
        "execution_enabled": False,
        "message": (
            "Candidates are OBSERVED only. Review package provenance, license and security "
            "before registration."
        ),
    }


def get_mcp_registry_server_details(
    server_name: str,
    version: str = "latest",
    *,
    opener=None,
) -> dict[str, object]:
    """Read sanitized metadata for one registry candidate; never install or execute it."""
    import re

    normalized_name = server_name.strip()
    if not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}/[A-Za-z0-9][A-Za-z0-9._-]{0,127}",
        normalized_name,
    ):
        raise ValueError("server_name must be a namespace/name identifier")
    normalized_version = version.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,79}", normalized_version):
        raise ValueError("version contains unsupported characters")

    url = (
        f"{REGISTRY_BASE_URL}/v0.1/servers/{quote(normalized_name, safe='')}"
        f"/versions/{quote(normalized_version, safe='')}"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "CK-NEXUS-MCP-Discovery/1.0",
        },
        method="GET",
    )
    open_request = opener or build_opener(_SameHostRedirectHandler()).open
    try:
        with open_request(request, timeout=8) as response:
            final_url = urlsplit(response.geturl())
            if (
                final_url.scheme != "https"
                or final_url.hostname != "registry.modelcontextprotocol.io"
                or final_url.port not in (None, 443)
                or final_url.username is not None
                or final_url.password is not None
            ):
                raise MCPRegistryDiscoveryError("Registry redirected outside the trusted host.")
            if getattr(response, "status", 200) != 200:
                raise MCPRegistryDiscoveryError(
                    "Official MCP Registry returned a non-success status."
                )
            content_type = response.headers.get("Content-Type", "application/json").split(";", 1)[0]
            if content_type.strip().lower() != "application/json":
                raise MCPRegistryDiscoveryError(
                    "Official MCP Registry returned an unexpected content type."
                )
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            raise MCPRegistryNotFoundError(
                "MCP server or version was not found in the official registry."
            ) from exc
        raise MCPRegistryDiscoveryError(
            "Official MCP Registry is temporarily unavailable."
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise MCPRegistryDiscoveryError(
            "Official MCP Registry is temporarily unavailable."
        ) from exc

    if len(raw) > MAX_RESPONSE_BYTES:
        raise MCPRegistryDiscoveryError("Official MCP Registry response exceeded the size limit.")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MCPRegistryDiscoveryError("Official MCP Registry returned invalid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("server"), dict):
        raise MCPRegistryDiscoveryError("Official MCP Registry detail schema is invalid.")

    server = payload["server"]
    official = payload.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
    if not isinstance(official, dict):
        official = {}
    repository = server.get("repository") if isinstance(server.get("repository"), dict) else {}
    repository_url = repository.get("url")
    repository_host = None
    if isinstance(repository_url, str):
        try:
            parsed_repository = urlsplit(repository_url)
            repository_host = parsed_repository.hostname
            safe_repository = (
                parsed_repository.scheme == "https"
                and repository_host in {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}
                and parsed_repository.username is None
                and parsed_repository.password is None
                and parsed_repository.port in (None, 443)
                and not parsed_repository.query
                and not parsed_repository.fragment
            )
        except ValueError:
            safe_repository = False
        if not safe_repository:
            repository_url = None
            repository_host = None
    else:
        repository_url = None
    website_url = server.get("websiteUrl")
    website_host = None
    if isinstance(website_url, str):
        try:
            website_host = urlsplit(website_url).hostname
        except ValueError:
            website_host = None
    website_url = None  # Display only a hostname; registry websites are untrusted input.

    packages: list[dict[str, object]] = []
    for package in server.get("packages", []) if isinstance(server.get("packages"), list) else []:
        if not isinstance(package, dict):
            continue
        transport = package.get("transport") if isinstance(package.get("transport"), dict) else {}
        environment = package.get("environmentVariables")
        hints = []
        for variable in environment if isinstance(environment, list) else []:
            if isinstance(variable, dict) and isinstance(variable.get("name"), str):
                hints.append({
                    "name": variable["name"][:100],
                    "required": variable.get("isRequired") is True,
                    "secret": variable.get("isSecret") is True,
                })
        packages.append({
            "registry_type": str(package.get("registryType", "unknown"))[:40],
            "identifier": str(package.get("identifier", ""))[:200],
            "version": str(package.get("version", ""))[:80],
            "transport": str(transport.get("type", "unknown"))[:40],
            "runtime_hint": str(package.get("runtimeHint", ""))[:40],
            "configuration_hints": hints[:40],
        })

    remotes: list[dict[str, str]] = []
    for remote in server.get("remotes", []) if isinstance(server.get("remotes"), list) else []:
        if not isinstance(remote, dict):
            continue
        remote_url = remote.get("url")
        try:
            parsed_remote = urlsplit(remote_url) if isinstance(remote_url, str) else None
            remote_host = (
                (parsed_remote.hostname or "unknown")[:200] if parsed_remote else "unknown"
            )
        except ValueError:
            remote_host = "unknown"
        remotes.append({
            "transport": str(remote.get("type", "unknown"))[:40],
            "host": remote_host,
        })

    return {
        "available": True,
        "name": str(server.get("name", normalized_name))[:200],
        "description": str(server.get("description", ""))[:1000],
        "version": str(server.get("version", normalized_version))[:80],
        "registry_status": str(official.get("status", "unknown"))[:40],
        "is_latest": official.get("isLatest") is True,
        "repository_url": repository_url,
        "repository_host": repository_host,
        "repository_source": str(repository.get("source", "unknown"))[:40],
        "repository_subfolder": str(repository.get("subfolder", ""))[:200],
        "website_host": website_host,
        "packages": packages[:20],
        "remotes": remotes[:20],
        "review_state": "OBSERVED",
        "installation_enabled": False,
        "execution_enabled": False,
        "message": (
            "Public registry metadata only; repository, license, provenance and security "
            "are not verified."
        ),
    }
