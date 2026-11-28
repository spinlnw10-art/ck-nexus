#!/usr/bin/env python3
"""Read-only CK-NEXUS repository and ZIP evidence auditor (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

VERSION = "0.2.0"
DEFAULT_EXCLUDES = {
    ".git", ".hg", ".svn", ".venv", "venv", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
}
SECRET_PATTERNS = [
    ("private_key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("generic_api_key_assignment", re.compile(
        rb"""(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*(['"])[A-Za-z0-9_./+=-]{20,}\1"""
    )),
]
TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".env", ".sh", ".bash", ".md", ".txt", ".sql", ".xml",
    ".properties", ".conf", ".gradle", ".pem", ".key", ".crt",
}
READ_CHUNK = 1024 * 1024
SECRET_SCAN_LIMIT = 2 * 1024 * 1024
ZIP_RATIO_LIMIT = 1000


def sha256_file(path: Path, chunk_size: int = READ_CHUNK) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def safe_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _zip_name_is_unsafe(name: str) -> bool:
    normalized = name.replace("\\", "/")
    posix = PurePosixPath(normalized)
    windows = PureWindowsPath(name)
    return (
        not name or "\x00" in name or normalized.startswith("/")
        or normalized.startswith("//") or bool(windows.drive) or windows.is_absolute()
        or ".." in posix.parts
    )


def scan_zip_bytes(data: bytes, display_path: str, max_entries: int,
                   max_uncompressed: int) -> dict:
    result = {
        "path": display_path, "status": "ok", "entries": 0,
        "total_uncompressed_bytes": 0, "encrypted_entries": 0,
        "unsafe_paths": [], "suspicious_compression": [],
        "testzip_error": None, "special_entries": [],
    }
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            result["entries"] = len(infos)
            if len(infos) > max_entries:
                result.update(status="limit_exceeded", error="entry_count_limit")
                return result
            for info in infos:
                name = info.filename
                if _zip_name_is_unsafe(name):
                    result["unsafe_paths"].append(name[:240])
                result["total_uncompressed_bytes"] += info.file_size
                if info.flag_bits & 0x1:
                    result["encrypted_entries"] += 1
                mode = (info.external_attr >> 16) & 0xFFFF
                file_type = stat.S_IFMT(mode)
                if file_type and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    result["special_entries"].append(name[:240])
                if info.file_size and info.compress_size == 0:
                    result["suspicious_compression"].append(name[:240])
                elif info.compress_size and info.file_size / info.compress_size > ZIP_RATIO_LIMIT:
                    result["suspicious_compression"].append(name[:240])
            if result["total_uncompressed_bytes"] > max_uncompressed:
                result.update(status="limit_exceeded", error="uncompressed_size_limit")
                return result
            if result["encrypted_entries"]:
                result["status"] = "review_required"
                result["testzip_error"] = "encrypted_entries_not_verified"
            else:
                try:
                    bad = archive.testzip()
                    if bad:
                        result["status"] = "corrupt"
                        result["testzip_error"] = bad[:240]
                except (OSError, RuntimeError, EOFError, NotImplementedError,
                        zipfile.BadZipFile, zlib.error) as exc:
                    result["status"] = "invalid"
                    result["testzip_error"] = type(exc).__name__
            if (result["unsafe_paths"] or result["suspicious_compression"]
                    or result["special_entries"]):
                result["status"] = "review_required"
    except (OSError, RuntimeError, EOFError, NotImplementedError,
            zipfile.BadZipFile, zlib.error) as exc:
        result["status"] = "invalid"
        result["error"] = type(exc).__name__
    return result


def scan_zip(path: Path, max_entries: int, max_uncompressed: int,
             display_path: str | None = None) -> dict:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"path": display_path or path.name, "status": "invalid",
                "error": type(exc).__name__}
    return scan_zip_bytes(data, display_path or path.name, max_entries, max_uncompressed)


def _read_fd(fd: int, expected: os.stat_result, max_file_bytes: int,
             rel: str, files: list, errors: list, hashes: dict,
             extension_counts: Counter, archives: list, findings: list,
             max_zip_entries: int, max_zip_bytes: int) -> int:
    current = os.fstat(fd)
    if not stat.S_ISREG(current.st_mode):
        files.append({"path": rel, "status": "skipped_special_file"})
        return 0
    if (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino):
        errors.append({"path": rel, "error": "file_changed_during_open"})
        return 0
    if current.st_size > max_file_bytes:
        files.append({"path": rel, "status": "skipped_size_limit",
                      "size_bytes": current.st_size})
        return 0
    digest = hashlib.sha256()
    total = 0
    secret_sample = bytearray()
    zip_data = bytearray() if rel.lower().endswith(".zip") else None
    while True:
        chunk = os.read(fd, READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_file_bytes:
            files.append({"path": rel, "status": "skipped_changed_size",
                          "size_bytes": total})
            return 0
        digest.update(chunk)
        if len(secret_sample) < SECRET_SCAN_LIMIT:
            secret_sample.extend(chunk[:SECRET_SCAN_LIMIT - len(secret_sample)])
        if zip_data is not None:
            zip_data.extend(chunk)
    after = os.fstat(fd)
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
            current.st_dev, current.st_ino, total, current.st_mtime_ns):
        errors.append({"path": rel, "error": "file_changed_during_read"})
        return 0
    hexdigest = digest.hexdigest()
    files.append({"path": rel, "size_bytes": total, "sha256": hexdigest,
                  "status": "hashed"})
    hashes[hexdigest].append(rel)
    suffix = Path(rel).suffix.lower() or "[no_extension]"
    extension_counts[suffix] += 1
    if zip_data is not None:
        archives.append(scan_zip_bytes(bytes(zip_data), rel, max_zip_entries, max_zip_bytes))
    if suffix in TEXT_SUFFIXES or Path(rel).name == "Dockerfile":
        if total > SECRET_SCAN_LIMIT:
            errors.append({"path": rel, "error": "secret_scan_size_limit_exceeded"})
        raw = bytes(secret_sample)
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(raw):
                findings.append({
                    "path": rel, "kind": kind, "severity": "high",
                    "detail": "Potential secret pattern detected; value intentionally redacted",
                })
    return total


def scan_tree(root: Path, output: Path | None, max_file_bytes: int,
              max_zip_entries: int, max_zip_bytes: int) -> dict:
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    if min(max_file_bytes, max_zip_entries, max_zip_bytes) <= 0:
        raise ValueError("limits must be positive")
    output_resolved = output.resolve() if output else None
    files, errors, archives, findings = [], [], [], []
    hashes = defaultdict(list)
    extension_counts = Counter()
    total_bytes = 0

    def traversal_error(exc: OSError) -> None:
        errors.append({"path": getattr(exc, "filename", None) or ".",
                       "error": type(exc).__name__})

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    for current, dirs, names, dir_fd in os.fwalk(
            root, topdown=True, follow_symlinks=False, onerror=traversal_error):
        current_path = Path(current)
        kept_dirs = []
        for dirname in sorted(dirs):
            if dirname in DEFAULT_EXCLUDES:
                continue
            try:
                st = os.stat(dirname, dir_fd=dir_fd, follow_symlinks=False)
                if stat.S_ISLNK(st.st_mode):
                    files.append({"path": safe_relative(current_path / dirname, root),
                                  "status": "skipped_symlink_directory"})
                elif stat.S_ISDIR(st.st_mode):
                    kept_dirs.append(dirname)
                else:
                    files.append({"path": safe_relative(current_path / dirname, root),
                                  "status": "skipped_special_directory_entry"})
            except OSError as exc:
                errors.append({"path": safe_relative(current_path / dirname, root),
                               "error": type(exc).__name__})
        dirs[:] = kept_dirs

        for name in sorted(names):
            path = current_path / name
            rel = safe_relative(path, root)
            try:
                before = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
                if stat.S_ISLNK(before.st_mode):
                    files.append({"path": rel, "status": "skipped_symlink"})
                    continue
                if not stat.S_ISREG(before.st_mode):
                    files.append({"path": rel, "status": "skipped_special_file"})
                    continue
                if output_resolved and (path.resolve() == output_resolved
                                        or output_resolved in path.resolve().parents):
                    continue
                fd = os.open(name, flags | nofollow, dir_fd=dir_fd)
                try:
                    total_bytes += _read_fd(
                        fd, before, max_file_bytes, rel, files, errors, hashes,
                        extension_counts, archives, findings, max_zip_entries, max_zip_bytes,
                    )
                finally:
                    os.close(fd)
            except OSError as exc:
                errors.append({"path": rel, "error": type(exc).__name__})

    duplicates = [
        {"sha256": digest, "paths": sorted(paths)}
        for digest, paths in hashes.items() if len(paths) > 1
    ]
    archives_bad = sum(a["status"] != "ok" for a in archives)
    files_skipped = sum(f["status"] != "hashed" for f in files)
    decision = "REVIEW_REQUIRED" if errors or findings or archives_bad or files_skipped else "PASS"
    return {
        "schema_version": "cknexus.audit.v1", "tool": "cknexus-audit-evidence",
        "tool_version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(),
        "root_label": root.name, "read_only": True, "decision": decision,
        "summary": {
            "files_hashed": sum(f["status"] == "hashed" for f in files),
            "files_skipped": files_skipped, "total_bytes_hashed": total_bytes,
            "duplicate_groups": len(duplicates), "zip_archives_checked": len(archives),
            "zip_archives_flagged": archives_bad,
            "potential_secret_findings": len(findings), "read_errors": len(errors),
        },
        "extensions": dict(sorted(extension_counts.items())),
        "files": sorted(files, key=lambda x: x["path"]),
        "duplicates": duplicates, "archives": archives,
        "secret_findings": findings, "errors": errors,
    }


def _atomic_write(directory: Path, filename: str, payload: bytes) -> None:
    target = directory / filename
    fd, temporary = tempfile.mkstemp(prefix=".cknexus-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def write_evidence(output: Path, report: dict) -> tuple[str, str]:
    try:
        output_stat = output.lstat()
    except FileNotFoundError:
        output.mkdir(parents=True, exist_ok=True)
        output_stat = output.lstat()
    if stat.S_ISLNK(output_stat.st_mode) or not stat.S_ISDIR(output_stat.st_mode):
        raise ValueError("audit-output must be a real directory, not a symlink")
    report_bytes = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(output, "audit-report.json", report_bytes)
    manifest = {
        "schema_version": "cknexus.manifest.v1", "report": "audit-report.json",
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "decision": report["decision"], "generated_at": report["generated_at"],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(output, "evidence-manifest.json", manifest_bytes)
    return hashlib.sha256(report_bytes).hexdigest(), hashlib.sha256(manifest_bytes).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only repository/ZIP inventory, integrity and evidence report"
    )
    parser.add_argument("--max-file-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--max-zip-entries", type=int, default=20000)
    parser.add_argument("--max-zip-uncompressed-bytes", type=int, default=2 * 1024 * 1024 * 1024)
    args = parser.parse_args()
    if min(args.max_file_bytes, args.max_zip_entries,
           args.max_zip_uncompressed_bytes) <= 0:
        parser.error("limits must be positive")
    root = Path.cwd().resolve(strict=True)
    output = root / "audit-output"
    report = scan_tree(root, output, args.max_file_bytes,
                       args.max_zip_entries, args.max_zip_uncompressed_bytes)
    report_hash, manifest_hash = write_evidence(output, report)
    print(json.dumps({
        "decision": report["decision"], "summary": report["summary"],
        "report": "audit-output/audit-report.json",
        "manifest": "audit-output/evidence-manifest.json",
        "report_sha256": report_hash, "manifest_sha256": manifest_hash,
    }, indent=2))
    return 0 if report["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
