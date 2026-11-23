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


def _protected_file(path: Path, *, private: bool) -> Path:
    """Accept only a regular file directly inside the trusted OMNI directory."""
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("OMNI credential must be a regular non-symlink file")
    resolved = path.resolve(strict=True)
    if resolved.parent != path.parent:
        raise RuntimeError("OMNI credential escaped its configured directory")
    mode = stat.S_IMODE(resolved.stat().st_mode)
    if private and mode & 0o077:
        raise RuntimeError("OMNI secret file permissions must be 0600 or stricter")
    return resolved


def build_omni_context_factory(*, runtime_data_dir: Path) -> Callable | None:
    """Build an authority client only when explicitly enabled and fully pinned.

    Credentials are provisioned at ``<runtime_data_dir>/omni/issuer-public.pem``
    and ``<runtime_data_dir>/omni/service-token``. The token file is read for
    every request to support local rotation. The issuer private key is never read.
    """
    enabled = os.environ.get("CKNEXUS_OMNI_ENABLED", "false").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return None

    base_url = os.environ.get("CKNEXUS_OMNI_URL", "").strip()
    issuer_id = os.environ.get("CKNEXUS_OMNI_ISSUER_ID", "").strip()
    if not base_url or not issuer_id:
        raise RuntimeError("required OMNI runtime settings missing: URL or issuer ID")

    runtime_root = Path(runtime_data_dir).expanduser().resolve(strict=True)
    omni_dir = runtime_root / "omni"
    if omni_dir.is_symlink() or not omni_dir.is_dir():
        raise RuntimeError("OMNI credential directory must exist and not be a symlink")
    omni_dir = omni_dir.resolve(strict=True)
    if omni_dir.parent != runtime_root:
        raise RuntimeError("OMNI credential directory escaped runtime data directory")

    public_key_path = _protected_file(omni_dir / "issuer-public.pem", private=False)
    _protected_file(omni_dir / "service-token", private=True)
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    if not isinstance(public_key, Ed25519PublicKey):
        raise RuntimeError("pinned OMNI issuer key must be Ed25519")

    def read_service_token() -> str:
        current_path = _protected_file(omni_dir / "service-token", private=True)
        token = current_path.read_text(encoding="utf-8").strip()
        if not token:
            raise RuntimeError("OMNI service token file is empty")
        return token

    replay_path = runtime_root / "omni-replay.sqlite3"
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
