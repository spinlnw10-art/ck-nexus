"""Compatibility checks for the canonical credential broker facade."""

from creator_app.credential_broker import (
    CredentialBroker as LegacyCredentialBroker,
)
from creator_app.credential_broker import (
    CredentialId as LegacyCredentialId,
)
from creator_app.credentials.credential_broker import (
    CredentialBroker,
    CredentialId,
)


def test_legacy_broker_path_reexports_canonical_class() -> None:
    assert LegacyCredentialBroker is CredentialBroker
    assert LegacyCredentialId is CredentialId


def test_legacy_broker_path_preserves_enum_identity() -> None:
    assert LegacyCredentialId.OPENAI_API_KEY is CredentialId.OPENAI_API_KEY
