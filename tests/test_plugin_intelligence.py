from __future__ import annotations

from types import SimpleNamespace

from creator_app.plugin_intelligence import build_plugin_catalog


def test_catalog_keeps_installed_and_authorized_states_separate():
    catalog = build_plugin_catalog(
        github={"configured": False, "connected": False, "message": "not configured"},
        slack={"configured": False, "connected": False, "message": "not configured"},
        google_drive={"configured": False, "connected": False, "message": "not configured"},
        gmail={
            "enabled": False,
            "configured": False,
            "authorized": False,
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "token_persistence": "ephemeral-memory",
        },
        github_app={"configured": False, "installation_token_ready": False},
        openai={"configured": False, "message": "provider unavailable"},
    )
    plugins = {item["id"]: item for item in catalog["plugins"]}

    assert plugins["gmail"]["installed"] is True
    assert plugins["gmail"]["configured"] is False
    assert plugins["gmail"]["connected"] is False
    assert plugins["gmail"]["state"] == "SETUP_REQUIRED"
    assert plugins["gmail"]["connect_ready"] is False
    assert plugins["youtube-player"]["installed"] is True
    assert plugins["youtube-player"]["connect_ready"] is True


def test_catalog_redacts_connector_endpoint_and_credential_reference():
    record = SimpleNamespace(
        config=SimpleNamespace(
            connector_id="demo",
            protocol=SimpleNamespace(value="mcp"),
            url="http://127.0.0.1:9999/mcp",
            credential_ref="GMAIL_ACCESS_TOKEN",
        ),
        state=SimpleNamespace(value="REGISTERED"),
        tool_count=0,
        read_only_count=0,
        write_count=0,
        destructive_count=0,
        schema_hash="",
    )
    catalog = build_plugin_catalog(
        github={}, slack={}, google_drive={}, gmail={}, github_app={}, openai={},
        connectors=(record,), connector_fabric_available=True,
    )
    connector = catalog["connectors"][0]

    assert connector["id"] == "demo"
    assert connector["can_discover"] is True
    assert connector["execution_enabled"] is False
    assert "url" not in connector
    assert "credential_ref" not in connector
    assert "credentialRef" not in connector
    assert "127.0.0.1" not in repr(catalog)
    assert "GMAIL_ACCESS_TOKEN" not in repr(catalog)


def test_unregistered_connectors_are_not_included():
    catalog = build_plugin_catalog(
        github={}, slack={}, google_drive={}, gmail={}, github_app={}, openai={},
        connectors=(), connector_fabric_available=False,
    )
    assert catalog["connectors"] == []
    assert catalog["connector_fabric_available"] is False
    assert all(item["installed"] is True for item in catalog["plugins"])


def test_catalog_marks_configured_gmail_without_encrypted_vault_as_blocked():
    catalog = build_plugin_catalog(
        github={"configured": True, "connected": False, "repository_access": False},
        slack={},
        google_drive={},
        gmail={
            "configured": True,
            "authorized": False,
            "scopes": [],
            "token_persistence": "ephemeral-memory",
        },
        github_app={},
        openai={},
    )
    plugins = {item["id"]: item for item in catalog["plugins"]}
    assert plugins["gmail"]["state"] == "PREREQUISITE_REQUIRED"
    assert plugins["gmail"]["connect_ready"] is False
    assert plugins["github"]["state"] == "CONFIGURED_NOT_VERIFIED"
