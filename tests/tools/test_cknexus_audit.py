import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "tools" / "cknexus_audit.py"
spec = importlib.util.spec_from_file_location("cknexus_audit", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class AuditTests(unittest.TestCase):
    def test_hash_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sample.txt"
            p.write_text("hello", encoding="utf-8")
            digest, size = audit.sha256_file(p)
            self.assertEqual(size, 5)
            self.assertEqual(
                digest,
                "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            )

    def test_zip_integrity_and_unsafe_path_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sample.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("safe/file.txt", "ok")
                z.writestr("../escape.txt", "no")
            result = audit.scan_zip(p, 100, 1024 * 1024)
            self.assertEqual(result["status"], "review_required")
            self.assertIn("../escape.txt", result["unsafe_paths"])

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

if __name__ == "__main__":
    unittest.main()
