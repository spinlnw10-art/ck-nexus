"""Fail-closed construction of the AGNES-side OMNI authority client."""

from __future__ import annotations

import os
import stat
from collections.abc import Callable
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from creator_app.agnes.execution.omni_provider import (
    DurableExecutionReplayStore,
    OmniProviderAdapter,
)
from creator_app.council_authority.omni_transport import HttpIndependentOmniAuthority


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required OMNI runtime setting missing: {name}")
    return value


def _protected_file(name: str, *, private: bool) -> Path:
    path = Path(_required(name)).expanduser()
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"OMNI file must be a regular non-symlink file: {name}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if private and mode & 0o077:
        raise RuntimeError(f"OMNI secret file permissions must be 0600 or stricter: {name}")
    return path


def build_omni_context_factory(*, runtime_data_dir: Path) -> Callable | None:
    """Build an authority client only when explicitly enabled and fully pinned.

    AGNES receives only the issuer public key and a rotatable short-lived service
    token file. It never loads the issuer private key or identity signing secret.
    """
    enabled = os.environ.get("CKNEXUS_OMNI_ENABLED", "false").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return None

    base_url = _required("CKNEXUS_OMNI_URL")
    issuer_id = _required("CKNEXUS_OMNI_ISSUER_ID")
    public_key_path = _protected_file("CKNEXUS_OMNI_PUBLIC_KEY_FILE", private=False)
    token_path = _protected_file("CKNEXUS_OMNI_SERVICE_TOKEN_FILE", private=True)
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    if not isinstance(public_key, Ed25519PublicKey):
        raise RuntimeError("pinned OMNI issuer key must be Ed25519")

    def read_service_token() -> str:
        # Read on every request so a local token broker can rotate credentials
        # without restarting the web application or exposing them to the UI.
        if token_path.is_symlink() or not token_path.is_file():
            raise RuntimeError("OMNI service token file unavailable")
        if stat.S_IMODE(token_path.stat().st_mode) & 0o077:
            raise RuntimeError("OMNI service token file permissions are too broad")
        token = token_path.read_text(encoding="utf-8").strip()
        if not token:
            raise RuntimeError("OMNI service token file is empty")
        return token

    replay_path = Path(
        os.environ.get(
            "CKNEXUS_OMNI_REPLAY_DB", str(runtime_data_dir / "omni-replay.sqlite3")
        )
    ).expanduser()
    if replay_path.is_symlink():
        raise RuntimeError("OMNI replay database must not be a symlink")
    replay_store = DurableExecutionReplayStore(replay_path)
    authority = HttpIndependentOmniAuthority(
        base_url,
        service_token=read_service_token,
        public_key=public_key,
        issuer_id=issuer_id,
    )
    return OmniProviderAdapter(authority=authority, replay_store=replay_store)