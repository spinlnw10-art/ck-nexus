#!/usr/bin/env python3
"""Read-only CK-NEXUS repository and ZIP evidence auditor (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

VERSION = "0.1.0"
DEFAULT_EXCLUDES = {".git", ".hg", ".svn", ".venv", "venv", "__pycache__", "node_modules",
                    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build"}
SECRET_PATTERNS = [
    ("private_key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("generic_api_key_assignment", re.compile(rb"""(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*(['"])[A-Za-z0-9_./+=-]{20,}\1""")),
]
TEXT_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml",
                 ".ini", ".cfg", ".env", ".sh", ".bash", ".md", ".txt", ".sql", ".xml",
                 ".properties", ".conf", ".gradle", "Dockerfile"}

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size

def safe_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()

def scan_zip(path: Path, max_entries: int, max_uncompressed: int, display_path: str | None = None) -> dict:
    result = {"path": display_path or path.name, "status": "ok", "entries": 0, "total_uncompressed_bytes": 0,
              "encrypted_entries": 0, "unsafe_paths": [], "suspicious_compression": [],
              "testzip_error": None}
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            result["entries"] = len(infos)
            if len(infos) > max_entries:
                result["status"] = "limit_exceeded"
                result["error"] = "entry_count_limit"
                return result
            for info in infos:
                name = info.filename.replace("\\", "/")
                member = PurePosixPath(name)
                if name.startswith("/") or ".." in member.parts or (member.parts and ":" in member.parts[0]):
                    result["unsafe_paths"].append(name[:240])
                result["total_uncompressed_bytes"] += info.file_size
                if info.flag_bits & 0x1:
                    result["encrypted_entries"] += 1
                if info.compress_size == 0 and info.file_size > 1024 * 1024:
                    result["suspicious_compression"].append(name[:240])
                elif info.compress_size and info.file_size / info.compress_size > 1000:
                    result["suspicious_compression"].append(name[:240])
            if result["total_uncompressed_bytes"] > max_uncompressed:
                result["status"] = "limit_exceeded"
                result["error"] = "uncompressed_size_limit"
                return result
            bad = archive.testzip()
            if bad:
                result["status"] = "corrupt"
                result["testzip_error"] = bad[:240]
            if result["unsafe_paths"] or result["suspicious_compression"]:
                result["status"] = "review_required"
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        result["status"] = "invalid"
        result["error"] = type(exc).__name__
    return result

def scan_tree(root: Path, output: Path | None, max_file_bytes: int, max_zip_entries: int,
              max_zip_bytes: int) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("--root must be a directory")
    output_resolved = output.resolve() if output else None
    files, errors, archives, findings = [], [], [], []
    hashes = defaultdict(list)
    extension_counts = Counter()
    total_bytes = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in DEFAULT_EXCLUDES and
                         not (current_path / d).is_symlink())
        for name in sorted(names):
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                continue
            if output_resolved and (path.resolve() == output_resolved or output_resolved in path.resolve().parents):
                continue
            rel = safe_relative(path, root)
            try:
                info = path.stat()
                if info.st_size > max_file_bytes:
                    files.append({"path": rel, "status": "skipped_size_limit", "size_bytes": info.st_size})
                    continue
                digest, size = sha256_file(path)
                record = {"path": rel, "size_bytes": size, "sha256": digest, "status": "hashed"}
                files.append(record)
                hashes[digest].append(rel)
                total_bytes += size
                suffix = path.suffix.lower() or "[no_extension]"
                extension_counts[suffix] += 1
                if path.suffix.lower() == ".zip":
                    archives.append(scan_zip(path, max_zip_entries, max_zip_bytes, rel))
                if path.suffix.lower() in TEXT_SUFFIXES and size <= 2 * 1024 * 1024:
                    raw = path.read_bytes()
                    for kind, pattern in SECRET_PATTERNS:
                        if pattern.search(raw):
                            findings.append({"path": rel, "kind": kind, "severity": "high",
                                              "detail": "Potential secret pattern detected; value intentionally redacted"})
            except (OSError, PermissionError) as exc:
                errors.append({"path": rel, "error": type(exc).__name__})
    duplicates = [{"sha256": digest, "paths": sorted(paths)} for digest, paths in hashes.items() if len(paths) > 1]
    archives_bad = sum(a["status"] not in {"ok"} for a in archives)
    decision = "REVIEW_REQUIRED" if errors or findings or archives_bad else "PASS"
    return {
        "schema_version": "cknexus.audit.v1", "tool": "cknexus-audit-evidence", "tool_version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(), "root_label": root.name,
        "read_only": True, "decision": decision,
        "summary": {"files_hashed": len([f for f in files if f["status"] == "hashed"]),
                    "files_skipped": len([f for f in files if f["status"] != "hashed"]),
                    "total_bytes_hashed": total_bytes, "duplicate_groups": len(duplicates),
                    "zip_archives_checked": len(archives), "zip_archives_flagged": archives_bad,
                    "potential_secret_findings": len(findings), "read_errors": len(errors)},
        "extensions": dict(sorted(extension_counts.items())),
        "files": sorted(files, key=lambda x: x["path"]),
        "duplicates": duplicates, "archives": archives, "secret_findings": findings, "errors": errors,
    }

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only repository/ZIP inventory, integrity and evidence report"
    )
    parser.add_argument("--max-file-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--max-zip-entries", type=int, default=20000)
    parser.add_argument("--max-zip-uncompressed-bytes", type=int, default=2 * 1024 * 1024 * 1024)
    args = parser.parse_args()
    if min(args.max_file_bytes, args.max_zip_entries, args.max_zip_uncompressed_bytes) <= 0:
        parser.error("limits must be positive")

    # Anchor both paths to the current working directory; do not accept
    # user-controlled filesystem paths from CLI arguments in CI.
    root = Path.cwd().resolve(strict=True)
    output = root / "audit-output"
    report = scan_tree(
        root,
        output,
        args.max_file_bytes,
        args.max_zip_entries,
        args.max_zip_uncompressed_bytes,
    )
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    report_path = output / "audit-report.json"
    report_path.write_text(payload, encoding="utf-8")
    manifest = {
        "schema_version": "cknexus.manifest.v1",
        "report": report_path.name,
        "report_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "decision": report["decision"],
        "generated_at": report["generated_at"],
    }
    (output / "evidence-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "decision": report["decision"],
                "summary": report["summary"],
                "report": "audit-output/audit-report.json",
                "manifest": "audit-output/evidence-manifest.json",
            },
            indent=2,
        )
    )
    return 0 if report["decision"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
