import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest import mock

MODULE = Path(__file__).resolve().parents[2] / "tools" / "cknexus_audit.py"
spec = importlib.util.spec_from_file_location("cknexus_audit", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_hash_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("hello", encoding="utf-8")
            digest, size = audit.sha256_file(path)
            self.assertEqual(size, 5)
            self.assertEqual(
                digest,
                "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            )

    def test_zip_rejects_posix_windows_and_absolute_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.zip"
            with zipfile.ZipFile(path, "w") as archive:
                for name in ("safe/file.txt", "../escape.txt", r"..\\escape.txt",
                             r"C:\\temp\\evil.txt", "/absolute.txt", r"\\server\\share"):
                    archive.writestr(name, "payload")
            result = audit.scan_zip(path, 100, 1024 * 1024)
            self.assertEqual(result["status"], "review_required")
            self.assertGreaterEqual(len(result["unsafe_paths"]), 5)

    def test_zip_decompression_error_becomes_invalid_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("file.txt", "payload")
            with mock.patch.object(zipfile.ZipFile, "testzip", side_effect=zlib.error("bad stream")):
                result = audit.scan_zip(path, 100, 1024 * 1024)
            self.assertEqual(result["status"], "invalid")
            self.assertEqual(result["testzip_error"], "error")

    def test_encrypted_zip_entry_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "encrypted.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("secret.txt", "payload")
            with zipfile.ZipFile(path) as archive:
                info = archive.infolist()[0]
            info.flag_bits |= 0x1
            with mock.patch.object(zipfile.ZipFile, "infolist", return_value=[info]):
                result = audit.scan_zip(path, 10, 1024)
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(result["encrypted_entries"], 1)

    def test_truncated_text_secret_scan_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            (root / "large.pem").write_bytes(b"x" * (audit.SECRET_SCAN_LIMIT + 1))
            report = audit.scan_tree(root, None, audit.SECRET_SCAN_LIMIT + 10, 100, 1024)
            self.assertEqual(report["decision"], "REVIEW_REQUIRED")
            self.assertIn("secret_scan_size_limit_exceeded", {
                error["error"] for error in report["errors"]
            })

    def test_zip_entry_and_uncompressed_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("one.txt", "x" * 4096)
            too_many = audit.scan_zip(path, 0 + 1, 8192)
            too_large = audit.scan_zip(path, 10, 1024)
            self.assertEqual(too_many["status"], "ok")
            self.assertEqual(too_large["status"], "limit_exceeded")

    def test_size_limit_skip_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            (root / "oversized.txt").write_bytes(b"x" * 32)
            report = audit.scan_tree(root, Path(tmp) / "out", 16, 100, 1024 * 1024)
            self.assertEqual(report["decision"], "REVIEW_REQUIRED")
            self.assertEqual(report["summary"]["files_hashed"], 0)
            self.assertEqual(report["summary"]["files_skipped"], 1)
            self.assertEqual(report["files"][0]["status"], "skipped_size_limit")

    def test_pem_private_key_marker_is_detected_and_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            secret = b"-----BEGIN PRIVATE KEY-----\\nvery-secret-material\\n"
            (root / "private.pem").write_bytes(secret)
            report = audit.scan_tree(root, None, 1024 * 1024, 100, 1024 * 1024)
            self.assertEqual(report["decision"], "REVIEW_REQUIRED")
            self.assertEqual(report["secret_findings"][0]["kind"], "private_key")
            self.assertNotIn("very-secret-material", json.dumps(report))

    def test_symlink_and_special_files_are_not_silently_omitted(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            (root / "real.txt").write_text("safe", encoding="utf-8")
            (root / "link.txt").symlink_to(root / "real.txt")
            actual_dir = root / "actual-dir"
            actual_dir.mkdir()
            (actual_dir / "inside.txt").write_text("inside", encoding="utf-8")
            (root / "linked-dir").symlink_to(actual_dir, target_is_directory=True)
            report = audit.scan_tree(root, None, 1024 * 1024, 100, 1024 * 1024)
            statuses = {item["status"] for item in report["files"]}
            self.assertEqual(report["decision"], "REVIEW_REQUIRED")
            self.assertIn("skipped_symlink", statuses)
            self.assertIn("skipped_symlink_directory", statuses)

    def test_directory_walk_errors_force_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            def broken_walk(*args, **kwargs):
                kwargs["onerror"](PermissionError("cannot enumerate"))
                yield str(root), [], [], os.open(root, os.O_RDONLY)
            with mock.patch.object(audit.os, "fwalk", side_effect=broken_walk):
                report = audit.scan_tree(root, None, 1024 * 1024, 100, 1024 * 1024)
            self.assertEqual(report["decision"], "REVIEW_REQUIRED")
            self.assertEqual(report["summary"]["read_errors"], 1)

    def test_read_only_scan_and_secret_redaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            api_source = "API_" + "KEY = " + repr("abcdefghijklmnopqrstuvwx")
            (root / "app.py").write_text(api_source, encoding="utf-8")
            safe_source = "access_token = self._access_token(config)"
            (root / "safe.py").write_text(safe_source, encoding="utf-8")
            before = (root / "app.py").read_bytes()
            report = audit.scan_tree(root, Path(tmp) / "out", 1024 * 1024, 100, 1024 * 1024)
            self.assertEqual(report["decision"], "REVIEW_REQUIRED")
            self.assertEqual((root / "app.py").read_bytes(), before)
            self.assertEqual(len(report["secret_findings"]), 1)
            self.assertNotIn("abcdefghijklmnopqrstuvwx", str(report))

    def test_evidence_manifest_hashes_exact_written_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "audit-output"
            report = {"decision": "PASS", "generated_at": "2026-11-28T00:00:00+00:00"}
            report_hash, _ = audit.write_evidence(output, report)
            report_bytes = (output / "audit-report.json").read_bytes()
            manifest = json.loads((output / "evidence-manifest.json").read_text())
            self.assertEqual(hashlib.sha256(report_bytes).hexdigest(), report_hash)
            self.assertEqual(manifest["report_sha256"], report_hash)

    def test_output_symlink_is_rejected_without_touching_target(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "source.txt"
            target.write_text("preserve", encoding="utf-8")
            output = Path(tmp) / "audit-output"
            output.symlink_to(target)
            report = {"decision": "PASS", "generated_at": "now"}
            with self.assertRaises(ValueError):
                audit.write_evidence(output, report)
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve")

    def test_zip_symlink_entries_require_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "special.zip"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(info, "target")
            result = audit.scan_zip(path, 10, 1024)
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(result["special_entries"], ["link"])


if __name__ == "__main__":
    unittest.main()
