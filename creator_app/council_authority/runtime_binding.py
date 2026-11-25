"""Fail-closed construction of the AGNES-side OMNI authority client."""

from __future__ import annotations

import ipaddress
import os
import stat
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from creator_app.agnes.execution.omni_provider import (
    DurableExecutionReplayStore,
    OmniProviderAdapter,
)
from creator_app.council_authority.omni_transport import HttpIndependentOmniAuthority

_CREDENTIAL_DIRECTORY = "omni-credentials"
_PUBLIC_KEY_FILENAME = "issuer-public-key.pem"
_SERVICE_TOKEN_FILENAME = "service-token.txt"
_REPLAY_DATABASE_FILENAME = "omni-replay.sqlite3"
_MAX_PUBLIC_KEY_BYTES = 64 * 1024
_MAX_SERVICE_TOKEN_BYTES = 8 * 1024


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required OMNI runtime setting missing: {name}")
    return value


def _validated_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("OMNI authority URL must be an absolute HTTP(S) URL without userinfo")
    if parsed.scheme == "http":
        try:
            loopback = ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            loopback = parsed.hostname.lower() == "localhost"
        if not loopback:
            raise RuntimeError("non-loopback OMNI authority URLs must use HTTPS")
    return value.rstrip("/")


def _open_credentials_directory(runtime_data_dir: Path) -> int:
    data_dir = Path(runtime_data_dir)
    if data_dir.is_symlink():
        raise RuntimeError("OMNI runtime data directory must not be a symlink")
    data_dir.mkdir(parents=True, exist_ok=True)
    data_dir = data_dir.resolve(strict=True)

    credentials_dir = data_dir / _CREDENTIAL_DIRECTORY
    credentials_dir.mkdir(mode=0o700, exist_ok=True)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        directory_fd = os.open(credentials_dir, flags)
    except OSError as exc:
        raise RuntimeError("OMNI credentials directory must be a real directory") from exc

    directory_stat = os.fstat(directory_fd)
    if not stat.S_ISDIR(directory_stat.st_mode):
        os.close(directory_fd)
        raise RuntimeError("OMNI credentials path is not a directory")
    if stat.S_IMODE(directory_stat.st_mode) & 0o077:
        os.close(directory_fd)
        raise RuntimeError("OMNI credentials directory permissions must be 0700 or stricter")
    return directory_fd


def _read_credential(directory_fd: int, filename: str, *, private: bool, limit: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        file_fd = os.open(filename, flags, dir_fd=directory_fd)
    except OSError as exc:
        raise RuntimeError("OMNI credential file unavailable or unsafe") from exc

    with os.fdopen(file_fd, "rb") as stream:
        file_stat = os.fstat(stream.fileno())
        if not stat.S_ISREG(file_stat.st_mode):
            raise RuntimeError("OMNI credential must be a regular file")
        if private and stat.S_IMODE(file_stat.st_mode) & 0o077:
            raise RuntimeError("OMNI service token file permissions must be 0600 or stricter")
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise RuntimeError("OMNI credential file exceeds the permitted size")
    if not content.strip():
        raise RuntimeError("OMNI credential file is empty")
    return content


def build_omni_context_factory(*, runtime_data_dir: Path) -> Callable | None:
    """Build an authority client only when explicitly enabled and fully pinned.

    AGNES reads only the issuer public key and a rotatable short-lived service
    token from fixed filenames under its private runtime data directory. It
    never loads the issuer private key or identity signing secret.
    """
    enabled = os.environ.get("CKNEXUS_OMNI_ENABLED", "false").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return None

    base_url = _validated_base_url(_required("CKNEXUS_OMNI_URL"))
    issuer_id = _required("CKNEXUS_OMNI_ISSUER_ID")
    credentials_fd = _open_credentials_directory(runtime_data_dir)
    try:
        public_key_bytes = _read_credential(
            credentials_fd,
            _PUBLIC_KEY_FILENAME,
            private=False,
            limit=_MAX_PUBLIC_KEY_BYTES,
        )
        public_key = serialization.load_pem_public_key(public_key_bytes)
        if not isinstance(public_key, Ed25519PublicKey):
            raise RuntimeError("pinned OMNI issuer key must be Ed25519")
        _read_credential(
            credentials_fd,
            _SERVICE_TOKEN_FILENAME,
            private=True,
            limit=_MAX_SERVICE_TOKEN_BYTES,
        )
    except Exception:
        os.close(credentials_fd)
        raise

    def read_service_token() -> str:
        # Re-open by a fixed basename on every request so local rotation works
        # without following a swapped symlink or accepting a caller-controlled path.
        token_bytes = _read_credential(
            credentials_fd,
            _SERVICE_TOKEN_FILENAME,
            private=True,
            limit=_MAX_SERVICE_TOKEN_BYTES,
        )
        return token_bytes.decode("utf-8").strip()

    replay_path = Path(runtime_data_dir).resolve() / _REPLAY_DATABASE_FILENAME
    if replay_path.is_symlink():
        os.close(credentials_fd)
        raise RuntimeError("OMNI replay database must not be a symlink")
    try:
        replay_store = DurableExecutionReplayStore(replay_path)
        authority = HttpIndependentOmniAuthority(
            base_url,
            service_token=read_service_token,
            public_key=public_key,
            issuer_id=issuer_id,
        )
        return OmniProviderAdapter(authority=authority, replay_store=replay_store)
    except Exception:
        os.close(credentials_fd)
        raise
