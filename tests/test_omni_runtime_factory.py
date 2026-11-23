import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from creator_app.agnes.execution.omni_provider import OmniProviderAdapter
from creator_app.council_authority.runtime_binding import build_omni_context_factory


def _configure(monkeypatch, tmp_path):
    private = Ed25519PrivateKey.generate()
    omni_dir = tmp_path / "omni"
    omni_dir.mkdir()
    public_path = omni_dir / "issuer-public.pem"
    public_path.write_bytes(
        private.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    token_path = omni_dir / "service-token"
    token_path.write_text("short-lived-token-a")
    token_path.chmod(0o600)
    monkeypatch.setenv("CKNEXUS_OMNI_ENABLED", "true")
    monkeypatch.setenv("CKNEXUS_OMNI_URL", "http://127.0.0.1:8770")
    monkeypatch.setenv("CKNEXUS_OMNI_ISSUER_ID", "test-issuer")
    return token_path


def test_omni_factory_is_disabled_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv("CKNEXUS_OMNI_ENABLED", raising=False)
    assert build_omni_context_factory(runtime_data_dir=tmp_path) is None


def test_omni_factory_pins_public_key_and_reads_rotating_token(monkeypatch, tmp_path):
    token_path = _configure(monkeypatch, tmp_path)
    factory = build_omni_context_factory(runtime_data_dir=tmp_path)
    assert isinstance(factory, OmniProviderAdapter)
    assert factory.authority.service_token() == "short-lived-token-a"

    token_path.write_text("short-lived-token-b")
    token_path.chmod(0o600)
    assert factory.authority.service_token() == "short-lived-token-b"
    assert factory.replay_store.database_path == str(tmp_path / "omni-replay.sqlite3")


def test_omni_factory_rejects_broad_token_file_permissions(monkeypatch, tmp_path):
    token_path = _configure(monkeypatch, tmp_path)
    token_path.chmod(0o644)
    with pytest.raises(RuntimeError, match="permissions"):
        build_omni_context_factory(runtime_data_dir=tmp_path)


def test_omni_factory_requires_pinned_ed25519_key(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    omni_dir = tmp_path / "omni"
    public_path = omni_dir / "issuer-public.pem"
    public_path.write_text("not-a-public-key")
    with pytest.raises(ValueError):
        build_omni_context_factory(runtime_data_dir=tmp_path)

def test_omni_factory_rejects_symlink_credential_directory(monkeypatch, tmp_path):
    real_dir = tmp_path / "real-omni"
    real_dir.mkdir()
    (real_dir / "issuer-public.pem").write_text("unused")
    (real_dir / "service-token").write_text("unused")
    (real_dir / "service-token").chmod(0o600)
    (tmp_path / "omni").symlink_to(real_dir, target_is_directory=True)
    monkeypatch.setenv("CKNEXUS_OMNI_ENABLED", "true")
    monkeypatch.setenv("CKNEXUS_OMNI_URL", "http://127.0.0.1:8770")
    monkeypatch.setenv("CKNEXUS_OMNI_ISSUER_ID", "test-issuer")
    with pytest.raises(RuntimeError, match="directory"):
        build_omni_context_factory(runtime_data_dir=tmp_path)
