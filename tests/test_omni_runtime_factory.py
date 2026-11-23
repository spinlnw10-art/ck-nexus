import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from creator_app.agnes.execution.omni_provider import OmniProviderAdapter
from creator_app.council_authority.runtime_binding import build_omni_context_factory


def _configure(monkeypatch, tmp_path):
    private = Ed25519PrivateKey.generate()
    credentials_dir = tmp_path / "omni-credentials"
    credentials_dir.mkdir(mode=0o700)
    public_path = credentials_dir / "issuer-public-key.pem"
    public_path.write_bytes(
        private.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    token_path = credentials_dir / "service-token.txt"
    token_path.write_text("short-lived-token-a")
    token_path.chmod(0o600)
    monkeypatch.setenv("CKNEXUS_OMNI_ENABLED", "true")
    monkeypatch.setenv("CKNEXUS_OMNI_URL", "http://127.0.0.1:8770")
    monkeypatch.setenv("CKNEXUS_OMNI_ISSUER_ID", "test-issuer")
    # Legacy arbitrary path overrides must not influence filesystem access.
    monkeypatch.setenv("CKNEXUS_OMNI_PUBLIC_KEY_FILE", str(tmp_path / "outside-key"))
    monkeypatch.setenv("CKNEXUS_OMNI_SERVICE_TOKEN_FILE", str(tmp_path / "outside-token"))
    monkeypatch.setenv("CKNEXUS_OMNI_REPLAY_DB", str(tmp_path / "outside-replay.sqlite"))
    return token_path, credentials_dir


def test_omni_factory_is_disabled_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv("CKNEXUS_OMNI_ENABLED", raising=False)
    assert build_omni_context_factory(runtime_data_dir=tmp_path) is None
    assert not (tmp_path / "omni-credentials").exists()


def test_omni_factory_pins_public_key_and_reads_rotating_token(monkeypatch, tmp_path):
    token_path, _ = _configure(monkeypatch, tmp_path)
    factory = build_omni_context_factory(runtime_data_dir=tmp_path)
    assert isinstance(factory, OmniProviderAdapter)
    assert factory.authority.service_token() == "short-lived-token-a"

    token_path.write_text("short-lived-token-b")
    token_path.chmod(0o600)
    assert factory.authority.service_token() == "short-lived-token-b"
    assert factory.replay_store.database_path == str(tmp_path / "omni-replay.sqlite3")
    assert not (tmp_path / "outside-replay.sqlite").exists()


def test_omni_factory_rejects_broad_token_file_permissions(monkeypatch, tmp_path):
    token_path, _ = _configure(monkeypatch, tmp_path)
    token_path.chmod(0o644)
    with pytest.raises(RuntimeError, match="permissions"):
        build_omni_context_factory(runtime_data_dir=tmp_path)


def test_omni_factory_rejects_symlinked_token_file(monkeypatch, tmp_path):
    token_path, credentials_dir = _configure(monkeypatch, tmp_path)
    token_path.unlink()
    target = tmp_path / "external-token"
    target.write_text("must-not-be-followed")
    target.chmod(0o600)
    token_path.symlink_to(target)
    with pytest.raises(RuntimeError, match="unavailable or unsafe"):
        build_omni_context_factory(runtime_data_dir=tmp_path)


def test_omni_factory_rejects_broad_credentials_directory_permissions(monkeypatch, tmp_path):
    _, credentials_dir = _configure(monkeypatch, tmp_path)
    credentials_dir.chmod(0o755)
    with pytest.raises(RuntimeError, match="directory permissions"):
        build_omni_context_factory(runtime_data_dir=tmp_path)


def test_omni_factory_requires_pinned_ed25519_key(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    public_path = tmp_path / "omni-credentials" / "issuer-public-key.pem"
    public_path.write_text("not-a-public-key")
    with pytest.raises(ValueError):
        build_omni_context_factory(runtime_data_dir=tmp_path)


def test_omni_factory_rejects_non_loopback_plain_http(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setenv("CKNEXUS_OMNI_URL", "http://issuer.example.test")
    with pytest.raises(RuntimeError, match="HTTPS"):
        build_omni_context_factory(runtime_data_dir=tmp_path)


def test_omni_factory_allows_https_authority(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setenv("CKNEXUS_OMNI_URL", "https://issuer.example.test")
    factory = build_omni_context_factory(runtime_data_dir=tmp_path)
    assert isinstance(factory, OmniProviderAdapter)
