"""Installed-plugin inventory and safe presentation models for the NEXUS UI.

This module describes installed adapters only. It does not grant authority or
execute tools; all connector execution remains behind ConnectorFabric policy.
"""

from __future__ import annotations

from typing import Any


def plugin_entry(
    *,
    plugin_id: str,
    name: str,
    category: str,
    auth_method: str,
    capabilities: tuple[str, ...],
    configured: bool,
    connected: bool,
    message: str,
    connect_action: str | None = None,
    connect_ready: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a redacted UI record for an adapter known to be installed."""
    if connected:
        state = "CONNECTED"
    elif connect_action and connect_ready:
        state = "READY_TO_CONNECT"
    elif connect_action and configured:
        state = "PREREQUISITE_REQUIRED"
    elif configured:
        state = "CONFIGURED_NOT_VERIFIED"
    else:
        state = "SETUP_REQUIRED"
    return {
        "id": plugin_id,
        "name": name,
        "category": category,
        "installed": True,
        "configured": bool(configured),
        "connected": bool(connected),
        "state": state,
        "auth_method": auth_method,
        "capabilities": list(capabilities),
        "message": str(message)[:240],
        "connect_action": connect_action,
        "connect_ready": bool(connect_ready),
        "details": details or {},
    }


def connector_entry(record: Any) -> dict[str, Any]:
    """Expose safe connector metadata without endpoint URLs or credential refs."""
    return {
        "id": record.config.connector_id,
        "name": record.config.connector_id,
        "category": "connector",
        "protocol": record.config.protocol.value,
        "installed": True,
        "state": record.state.value,
        "tool_count": record.tool_count,
        "read_only_count": record.read_only_count,
        "write_count": record.write_count,
        "destructive_count": record.destructive_count,
        "schema_hash": record.schema_hash,
        "can_discover": record.state.value in {"REGISTERED", "BLOCKED"},
        "execution_enabled": False,
    }


def build_plugin_catalog(
    *,
    github: dict[str, Any],
    slack: dict[str, Any],
    google_drive: dict[str, Any],
    gmail: dict[str, Any],
    github_app: dict[str, Any],
    openai: dict[str, Any],
    connectors: tuple[Any, ...] = (),
    connector_fabric_available: bool = False,
) -> dict[str, Any]:
    """Build the installed-only catalog from adapters actually loaded by the API."""
    vault_ready = gmail.get("token_persistence") == "encrypted-vault"
    gmail_message = "Gmail authorization is active."
    if not gmail.get("authorized"):
        if gmail.get("configured") and not vault_ready:
            gmail_message = "Encrypted Credential Vault is required before OAuth can start."
        else:
            gmail_message = (
                "Gmail OAuth adapter is installed; configure Google OAuth credentials to connect."
            )

    github_app_message = "GitHub App installation token is ready."
    if not github_app.get("installation_token_ready"):
        github_app_message = (
            "GitHub App adapter is installed; configure its credentials to connect."
        )

    plugins = [
        plugin_entry(
            plugin_id="github",
            name="GitHub",
            category="development",
            auth_method="credential_broker",
            capabilities=("repository_read", "repository_status"),
            configured=bool(github.get("configured")),
            connected=bool(github.get("connected") and github.get("repository_access")),
            message=str(github.get("message") or "GitHub adapter is installed."),
            details={"login": github.get("login"), "repository": github.get("repository")},
        ),
        plugin_entry(
            plugin_id="github-app",
            name="GitHub App",
            category="development",
            auth_method="github_app_installation",
            capabilities=("installation_token", "repository_api"),
            configured=bool(github_app.get("configured")),
            connected=bool(github_app.get("installation_token_ready")),
            message=github_app_message,
            connect_action="github-app-token",
            connect_ready=bool(
                github_app.get("configured") and not github_app.get("installation_token_ready")
            ),
        ),
        plugin_entry(
            plugin_id="gmail",
            name="Gmail",
            category="productivity",
            auth_method="oauth2",
            capabilities=tuple(str(item) for item in gmail.get("scopes", [])),
            configured=bool(gmail.get("configured")),
            connected=bool(gmail.get("authorized")),
            message=gmail_message,
            connect_action="gmail-oauth",
            connect_ready=bool(
                gmail.get("configured") and vault_ready and not gmail.get("authorized")
            ),
            details={
                "token_persistence": gmail.get("token_persistence"),
                "vault_ready": vault_ready,
            },
        ),
        plugin_entry(
            plugin_id="slack",
            name="Slack",
            category="communication",
            auth_method="credential_broker",
            capabilities=("workspace_status",),
            configured=bool(slack.get("configured")),
            connected=bool(slack.get("connected")),
            message=str(slack.get("message") or "Slack adapter is installed."),
        ),
        plugin_entry(
            plugin_id="google-drive",
            name="Google Drive",
            category="productivity",
            auth_method="credential_broker",
            capabilities=("drive_metadata",),
            configured=bool(google_drive.get("configured")),
            connected=bool(google_drive.get("connected")),
            message=str(google_drive.get("message") or "Google Drive adapter is installed."),
        ),
        plugin_entry(
            plugin_id="openai",
            name="OpenAI Provider",
            category="ai_provider",
            auth_method="credential_broker",
            capabilities=("text_generation",),
            configured=bool(openai.get("configured")),
            connected=False,
            message=str(
                openai.get("message")
                or "Provider credentials are brokered; live inference is verified separately."
            ),
        ),
        plugin_entry(
            plugin_id="youtube-player",
            name="YouTube Player",
            category="media",
            auth_method="none",
            capabilities=("embedded_playback",),
            configured=True,
            connected=False,
            message=(
                "Built-in YouTube embedded player is available; Google account login is not "
                "required for public videos."
            ),
            connect_action="open-youtube-player",
            connect_ready=True,
        ),
    ]
    return {
        "plugins": [item for item in plugins if item["installed"]],
        "connectors": [connector_entry(item) for item in connectors],
        "connector_fabric_available": bool(connector_fabric_available),
        "execution_policy": (
            "CK-NEXUS Core authority required; unapproved tools remain unavailable."
        ),
    }
