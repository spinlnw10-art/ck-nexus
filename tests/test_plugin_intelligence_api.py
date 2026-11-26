from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from creator_app.api import create_app
from creator_app.config import Settings


def make_settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "database_path": tmp_path / "app.db",
        "mock_ai": True,
        "access_token": "plugin-hub-test-token",
        "connector_fabric_enabled": True,
        "connector_registry_path": tmp_path / "connector-registry.json",
        "connector_evidence_path": tmp_path / "connector-evidence.jsonl",
    }
    values.update(overrides)
    return Settings(**values)


def test_plugin_inventory_endpoint_requires_access_token(tmp_path: Path):
    with TestClient(create_app(make_settings(tmp_path))) as client:
        denied = client.get("/api/plugins")
        allowed = client.get(
            "/api/plugins",
            headers={"Authorization": "Bearer plugin-hub-test-token"},
        )

    assert denied.status_code == 401
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["plugins"]
    assert all(item["installed"] is True for item in body["plugins"])
    assert "execution_policy" in body


def test_plugin_inventory_endpoint_redacts_registered_connector_secrets(tmp_path: Path):
    with TestClient(create_app(make_settings(tmp_path))) as client:
        headers = {"Authorization": "Bearer plugin-hub-test-token"}
        registered = client.post(
            "/api/connectors",
            headers=headers,
            json={
                "connector_id": "catalog-redaction-test",
                "url": "http://127.0.0.1:65532/mcp",
                "protocol": "mcp",
                "allow_private_network": True,
                "credential_ref": "GMAIL_ACCESS_TOKEN",
                "auto_discover": False,
            },
        )
        assert registered.status_code == 200
        response = client.get("/api/plugins", headers=headers)

    assert response.status_code == 200
    connector = next(
        item for item in response.json()["connectors"]
        if item["id"] == "catalog-redaction-test"
    )
    assert connector["execution_enabled"] is False
    assert "url" not in connector
    assert "credentialRef" not in connector
    assert "127.0.0.1" not in response.text
    assert "GMAIL_ACCESS_TOKEN" not in response.text


def test_gmail_oauth_start_and_callback_require_encrypted_vault(tmp_path: Path):
    with TestClient(create_app(make_settings(tmp_path))) as client:
        headers = {"Authorization": "Bearer plugin-hub-test-token"}
        start = client.get("/api/integrations/gmail/oauth/start", headers=headers)
        callback = client.get(
            "/api/integrations/gmail/oauth/callback?code=fake-code&state=fake-state",
            headers=headers,
            follow_redirects=False,
        )

    assert start.status_code == 503
    assert start.json()["detail"]["error"] == "ENCRYPTED_CREDENTIAL_VAULT_REQUIRED"
    assert callback.status_code == 503
    assert callback.json()["detail"]["error"] == "ENCRYPTED_CREDENTIAL_VAULT_REQUIRED"



def test_tools_search_only_uses_schema_verified_snapshots(tmp_path: Path):
    from creator_app.connector_fabric.models import (
        ConnectorConfig,
        ConnectorProtocol,
        DiscoverySnapshot,
        NormalizedTool,
        RiskClass,
    )

    app = create_app(make_settings(tmp_path))
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer plugin-hub-test-token"}
        denied = client.get("/api/tools/search?q=search")
        assert denied.status_code == 401

        fabric = app.state.connector_fabric
        fabric.registry.register(
            ConnectorConfig(
                connector_id="verified-search",
                url="https://connector.example.test/mcp",
                protocol=ConnectorProtocol.MCP,
            )
        )
        fabric.registry.set_snapshot(
            DiscoverySnapshot(
                connector_id="verified-search",
                protocol=ConnectorProtocol.MCP,
                protocol_version="2025-06-18",
                schema_hash="verified-schema-hash",
                tools=(
                    NormalizedTool(
                        connector_id="verified-search",
                        name="search_documents",
                        description="Search indexed documents",
                        input_schema={
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                        },
                        risk=RiskClass.READ_ONLY,
                    ),
                    NormalizedTool(
                        connector_id="verified-search",
                        name="delete_document",
                        description="Delete a document",
                        input_schema={"type": "object"},
                        risk=RiskClass.DESTRUCTIVE,
                    ),
                ),
            )
        )
        response = client.get("/api/tools/search?q=search", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["available"] is True
        assert body["execution_enabled"] is False
        assert body["count"] == 1
        assert body["results"][0]["logical_name"] == "verified-search.search_documents"
        assert body["results"][0]["approval_required"] is False
        assert "inputSchema" not in response.text
        assert "connector.example.test" not in response.text

        destructive_response = client.get("/api/tools/search?q=delete", headers=headers)
        assert destructive_response.status_code == 200
        destructive = destructive_response.json()["results"][0]
        assert destructive["name"] == "delete_document"
        assert destructive["approval_required"] is True
        assert destructive["execution_available"] is False


def test_mcp_registry_discovery_endpoint_is_authenticated_and_observation_only(
    tmp_path: Path, monkeypatch
):
    def fake_search(query: str, limit: int, *, cursor: str | None = None):
        assert query == "filesystem"
        assert limit == 12
        assert cursor in (None, "opaque-cursor")
        return {
            "available": True,
            "query": query,
            "count": 1,
            "results": [
                {
                    "name": "io.github.example/filesystem",
                    "description": "Filesystem metadata tools",
                    "version": "1.0.0",
                    "registry_status": "active",
                    "is_latest": True,
                    "source": "official_mcp_registry",
                    "review_state": "OBSERVED",
                    "installation_enabled": False,
                    "execution_enabled": False,
                }
            ],
            "has_more": False,
            "discovery_only": True,
            "installation_enabled": False,
            "execution_enabled": False,
        }

    monkeypatch.setattr("creator_app.api.search_mcp_registry", fake_search)
    with TestClient(create_app(make_settings(tmp_path))) as client:
        denied = client.get("/api/tools/discovery/mcp-registry?q=filesystem")
        response = client.get(
            "/api/tools/discovery/mcp-registry?q=filesystem&limit=12&cursor=opaque-cursor",
            headers={"Authorization": "Bearer plugin-hub-test-token"},
        )
        invalid_query = client.get(
            "/api/tools/discovery/mcp-registry?q=ab",
            headers={"Authorization": "Bearer plugin-hub-test-token"},
        )
    assert denied.status_code == 401
    assert response.status_code == 200
    assert invalid_query.status_code == 422
    body = response.json()
    assert body["results"][0]["review_state"] == "OBSERVED"
    assert body["installation_enabled"] is False
    assert body["execution_enabled"] is False


def test_mcp_registry_detail_endpoint_is_authenticated_and_observation_only(
    tmp_path: Path, monkeypatch
):
    def fake_details(name: str, version: str):
        assert name == "io.github.example/tool"
        assert version == "latest"
        return {
            "available": True,
            "name": name,
            "version": version,
            "review_state": "OBSERVED",
            "packages": [
                {
                    "registry_type": "npm",
                    "identifier": "example-tool",
                    "transport": "stdio",
                }
            ],
            "remotes": [],
            "installation_enabled": False,
            "execution_enabled": False,
        }

    monkeypatch.setattr("creator_app.api.get_mcp_registry_server_details", fake_details)
    with TestClient(create_app(make_settings(tmp_path))) as client:
        denied = client.get(
            "/api/tools/discovery/mcp-registry/details?name=io.github.example%2Ftool"
        )
        response = client.get(
            "/api/tools/discovery/mcp-registry/details?name=io.github.example%2Ftool&version=latest",
            headers={"Authorization": "Bearer plugin-hub-test-token"},
        )
        invalid = client.get(
            "/api/tools/discovery/mcp-registry/details?name=https%3A%2F%2Fattacker.example%2Fpath",
            headers={"Authorization": "Bearer plugin-hub-test-token"},
        )
    assert denied.status_code == 401
    assert response.status_code == 200
    assert response.json()["review_state"] == "OBSERVED"
    assert response.json()["installation_enabled"] is False
    assert invalid.status_code == 422


def test_mcp_registry_detail_endpoint_returns_404_for_missing_candidate(
    tmp_path: Path, monkeypatch
):
    from creator_app.global_knowledge.mcp_registry_discovery import MCPRegistryNotFoundError

    def missing_details(_name: str, _version: str):
        raise MCPRegistryNotFoundError("MCP server was not found")

    monkeypatch.setattr("creator_app.api.get_mcp_registry_server_details", missing_details)
    with TestClient(create_app(make_settings(tmp_path))) as client:
        response = client.get(
            "/api/tools/discovery/mcp-registry/details?name=io.github.example%2Fmissing",
            headers={"Authorization": "Bearer plugin-hub-test-token"},
        )
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "MCP_SERVER_NOT_FOUND"
