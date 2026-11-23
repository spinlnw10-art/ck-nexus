from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from services.email_gateway.attachments import scan_attachment


@pytest.mark.parametrize("suffix", [".docx", ".xlsx"])
def test_office_zip_bomb_is_quarantined(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"payload{suffix}"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        member = "word/document.xml" if suffix == ".docx" else "xl/workbook.xml"
        archive.writestr(member, "A" * 2_000_000)

    result = scan_attachment(path)
    assert not result.safe
    assert result.status == "QUARANTINE"
    assert result.reason in {"zip_uncompressed_limit", "zip_compression_ratio"}


@pytest.mark.parametrize("suffix", [".docx", ".xlsx"])
def test_office_zip_path_traversal_is_quarantined(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"payload{suffix}"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("..\\..\\outside.txt", "not safe")

    result = scan_attachment(path)
    assert not result.safe
    assert result.reason == "zip_path_traversal"


def test_declared_mime_must_match_extension_and_content(tmp_path: Path) -> None:
    path = tmp_path / "invoice.pdf"
    path.write_bytes(b"%PDF-1.7\nvalid test fixture")

    mismatch = scan_attachment(path, declared_mime="text/plain")
    assert not mismatch.safe
    assert mismatch.reason == "declared_mime_mismatch"

    matching = scan_attachment(path, declared_mime="application/pdf; charset=binary")
    assert matching.safe
    assert matching.detected_mime == "application/pdf"

    missing = scan_attachment(path, declared_mime="")
    assert not missing.safe
    assert missing.reason == "declared_mime_mismatch"


def test_office_declared_mime_is_checked(tmp_path: Path) -> None:
    path = tmp_path / "report.docx"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")

    mismatch = scan_attachment(path, declared_mime="application/pdf")
    assert not mismatch.safe
    assert mismatch.reason == "declared_mime_mismatch"

    matching = scan_attachment(
        path,
        declared_mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert matching.safe


@pytest.mark.parametrize(
    "suffix,entries",
    [
        (".docx", {"[Content_Types].xml": "<Types/>", "word/document.xml": "<document/>"}),
        (".xlsx", {"[Content_Types].xml": "<Types/>", "xl/workbook.xml": "<workbook/>"}),
    ],
)
def test_office_package_requires_expected_parts(
    tmp_path: Path, suffix: str, entries: dict[str, str]
) -> None:
    path = tmp_path / f"valid{suffix}"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    result = scan_attachment(path)
    assert result.safe

    invalid = tmp_path / f"invalid{suffix}"
    with zipfile.ZipFile(invalid, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("readme.txt", "not an Office package")
    result = scan_attachment(invalid)
    assert not result.safe
    assert result.reason == "invalid_office_package"


def test_office_macro_payload_is_quarantined(tmp_path: Path) -> None:
    path = tmp_path / "macro.docx"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
        archive.writestr("word/vbaProject.bin", b"MZ" + b"x" * 32)
    result = scan_attachment(path)
    assert not result.safe
    assert result.reason == "office_macro_payload"
