from __future__ import annotations

import codecs
import hashlib
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

BLOCKED_EXTENSIONS = {
    ".exe",
    ".dll",
    ".msi",
    ".bat",
    ".cmd",
    ".com",
    ".scr",
    ".ps1",
    ".vbs",
    ".js",
    ".jar",
    ".apk",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".png", ".jpg", ".jpeg", ".zip"}


_HEAD_BYTES = 512
_ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06")
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_EXEC_MAGIC = (
    b"MZ",
    b"\x7fELF",
    b"\xcf\xfa\xed\xfe",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xce",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"#!",
)
_TEXT_CONTROLS = frozenset({9, 10, 12, 13})
_ZIP_BASED = {".docx", ".xlsx", ".zip"}
_TEXT_EXTENSIONS = {".csv", ".txt"}


def _read_head(path: Path) -> bytes:
    with path.open("rb") as handle:
        return handle.read(_HEAD_BYTES)


def _looks_like_text(head: bytes) -> bool:
    if head.startswith(codecs.BOM_UTF8):
        head = head[len(codecs.BOM_UTF8) :]
    try:
        text = codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
    except UnicodeDecodeError:
        return False
    return all(ord(ch) in _TEXT_CONTROLS or unicodedata.category(ch) != "Cc" for ch in text)


def _sniff_mime(head: bytes) -> str:
    """MIME type from content signature only; never from the filename."""
    if head.startswith(_EXEC_MAGIC):
        return "application/x-executable"
    if head.lstrip(b"\xef\xbb\xbf\r\n\t ").startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(_ZIP_MAGIC):
        return "application/zip"
    if head.startswith(_OLE_MAGIC):
        return "application/x-ole-storage"
    if head.startswith(_PNG_MAGIC):
        return "image/png"
    if head.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if _looks_like_text(head):
        return "text/plain"
    return "application/octet-stream"


def _file_is_utf8_text(path: Path) -> bool:
    """Stream the whole file: valid UTF-8 (finalized at EOF), no control chars."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    first = True
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            if first and chunk.startswith(codecs.BOM_UTF8):
                chunk = chunk[len(codecs.BOM_UTF8) :]
            first = False
            try:
                text = decoder.decode(chunk, final=False)
            except UnicodeDecodeError:
                return False
            if any(
                ord(ch) not in _TEXT_CONTROLS and unicodedata.category(ch) == "Cc" for ch in text
            ):
                return False
    try:
        decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        return False
    return True


def _content_matches_extension(extension: str, head: bytes) -> bool:
    sniffed = _sniff_mime(head)
    if extension == ".pdf":
        return sniffed == "application/pdf"
    if extension in _ZIP_BASED:
        return sniffed == "application/zip"
    if extension == ".png":
        return sniffed == "image/png"
    if extension in {".jpg", ".jpeg"}:
        return sniffed == "image/jpeg"
    if extension in _TEXT_EXTENSIONS:
        return sniffed == "text/plain"
    return False


_DECLARED_MIME_BY_EXTENSION = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    ".zip": {"application/zip", "application/x-zip-compressed"},
    ".csv": {"text/csv", "application/csv", "text/plain"},
    ".txt": {"text/plain"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg", "image/pjpeg"},
    ".jpeg": {"image/jpeg", "image/pjpeg"},
}


def _declared_mime_matches(extension: str, declared_mime: str) -> bool:
    normalized = declared_mime.partition(";")[0].strip().casefold()
    return normalized in _DECLARED_MIME_BY_EXTENSION.get(extension, set())


@dataclass(frozen=True, slots=True)
class AttachmentScanResult:
    safe: bool
    status: str
    reason: str
    sha256: str
    size_bytes: int
    extension: str
    detected_mime: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zip_policy(
    path: Path,
    *,
    max_entries: int,
    max_uncompressed_bytes: int,
    max_ratio: float,
    required_entries: set[str] | None = None,
) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > max_entries:
                return False, "zip_too_many_entries"
            names = {info.filename for info in infos}
            total_compressed = 0
            total_uncompressed = 0
            for info in infos:
                normalized_name = info.filename.replace(chr(92), "/")
                parts = normalized_name.split("/")
                if normalized_name.startswith("/") or ".." in parts:
                    return False, "zip_path_traversal"
                if info.flag_bits & 0x1:
                    return False, "encrypted_zip_entry"
                total_compressed += max(1, info.compress_size)
                total_uncompressed += info.file_size
                if total_uncompressed > max_uncompressed_bytes:
                    return False, "zip_uncompressed_limit"
            if total_uncompressed / max(1, total_compressed) > max_ratio:
                return False, "zip_compression_ratio"
            if required_entries and not required_entries.issubset(names):
                return False, "invalid_office_package"
            if any(name.casefold().endswith("vbaproject.bin") for name in names):
                return False, "office_macro_payload"
    except zipfile.BadZipFile:
        return False, "invalid_zip"
    return True, "zip_safe"


def scan_attachment(
    path: Path,
    *,
    declared_mime: str | None = None,
    max_size_bytes: int = 25 * 1024 * 1024,
    max_zip_entries: int = 250,
    max_zip_uncompressed_bytes: int = 100 * 1024 * 1024,
    max_zip_ratio: float = 100.0,
) -> AttachmentScanResult:
    path = Path(path)
    size = path.stat().st_size
    extension = path.suffix.casefold()
    digest = _sha256(path)
    head = _read_head(path)
    detected = _sniff_mime(head)

    if extension in BLOCKED_EXTENSIONS:
        return AttachmentScanResult(
            False, "QUARANTINE", "blocked_extension", digest, size, extension, detected
        )
    if extension not in ALLOWED_EXTENSIONS:
        return AttachmentScanResult(
            False, "QUARANTINE", "extension_not_allowlisted", digest, size, extension, detected
        )
    if size > max_size_bytes:
        return AttachmentScanResult(
            False, "QUARANTINE", "file_too_large", digest, size, extension, detected
        )
    if head.startswith(_EXEC_MAGIC):
        return AttachmentScanResult(
            False, "QUARANTINE", "executable_signature", digest, size, extension, detected
        )
    if extension in _TEXT_EXTENSIONS and not _file_is_utf8_text(path):
        return AttachmentScanResult(
            False, "QUARANTINE", "content_signature_mismatch", digest, size, extension, detected
        )
    if not _content_matches_extension(extension, head):
        return AttachmentScanResult(
            False, "QUARANTINE", "content_signature_mismatch", digest, size, extension, detected
        )
    if declared_mime is not None and not _declared_mime_matches(extension, declared_mime):
        return AttachmentScanResult(
            False, "QUARANTINE", "declared_mime_mismatch", digest, size, extension, detected
        )
    if extension in _ZIP_BASED:
        required_entries = {
            ".docx": {"[Content_Types].xml", "word/document.xml"},
            ".xlsx": {"[Content_Types].xml", "xl/workbook.xml"},
        }.get(extension)
        safe, reason = _zip_policy(
            path,
            max_entries=max_zip_entries,
            max_uncompressed_bytes=max_zip_uncompressed_bytes,
            max_ratio=max_zip_ratio,
            required_entries=required_entries,
        )
        if not safe:
            return AttachmentScanResult(
                False, "QUARANTINE", reason, digest, size, extension, detected
            )
    if _sha256(path) != digest or path.stat().st_size != size:
        return AttachmentScanResult(
            False, "QUARANTINE", "file_changed_during_scan", digest, size, extension, detected
        )
    return AttachmentScanResult(True, "CLEAN", "allowlisted", digest, size, extension, detected)
