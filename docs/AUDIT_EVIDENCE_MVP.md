# CK-NEXUS Audit & Evidence

A read-only repository inventory and ZIP evidence auditor using the Python standard library.

## Capabilities

- Traverses directories without following symlinks; records symlink and special-file skips instead of silently omitting them.
- Uses directory file descriptors, `O_NOFOLLOW` where supported, and `fstat` identity/size checks to reduce path-swap and TOCTOU exposure while opening and hashing files.
- Records directory traversal, open, and read errors; incomplete inventory always requires review.
- Computes SHA-256 and byte counts for files within configured limits and identifies byte-identical duplicates.
- Inspects ZIP archives without extracting them, including POSIX/Windows traversal paths, symlink/special entries, encryption, CRC/decompression errors, entry count, total uncompressed size, and suspicious compression ratios.
- Scans selected text formats including PEM and KEY files for high-risk secret markers. Secret values are never included in evidence.
- Writes report and manifest atomically. The manifest hash is computed from the exact report bytes written. Existing output symlinks are rejected.
- Uses no network access, credentials, subprocesses, third-party Python packages, archive extraction, deletion, Git mutation, merge, or deployment.

## Requirements and local use

- Python 3.10+
- Standard library only

From the repository root:

```bash
python3 tools/cknexus_audit.py
python3 -m unittest discover -s tests/tools -v
```

The CLI anchors the scan to the current working directory and writes to `./audit-output`. It does not accept arbitrary root or output paths. The programmatic `scan_tree` function is intended for controlled test harnesses and requires an explicit root.

## Decision semantics

- `PASS`: inventory completed without read/traversal errors, skipped entries, potential secret findings, invalid/unsafe ZIP findings, or configured limit violations.
- `REVIEW_REQUIRED`: any incomplete inventory, symlink/special entry, unreadable/changed file, potential secret, invalid/encrypted/corrupt archive, unsafe archive entry, suspicious compression, or configured limit violation.

A PASS is not a security certification, malware verdict, license-compliance determination, independent review, merge authorization, or production deployment approval. Pattern-based secret detection can produce false positives and false negatives. Review findings before making a release decision.

## Security limitations

- File-descriptor-relative opens and `O_NOFOLLOW` reduce symlink/path replacement races on supported POSIX systems. Platform guarantees differ; this utility is not a substitute for sandboxing or a filesystem snapshot.
- File content modified in place during a read is detected using descriptor metadata checks where available, but a hostile concurrently writable filesystem can require stronger isolation.
- ZIP archives are inspected without extraction; encrypted entries cannot have their CRC verified without a password and are therefore marked for review.
- Secret detection is pattern-based and is not exhaustive.
- Evidence includes paths and hashes; treat it as potentially sensitive metadata.

## CI

The workflow `.github/workflows/audit-evidence.yml` runs the unit tests and produces an evidence artifact for pull requests and pushes to `main`. CI evidence is a candidate verification artifact, not approval to merge or deploy.

## Version

MVP `0.2.0`. Production remains NO-GO until all mandatory security, independent-review, operational, and CK-NEXUS Core approval gates are satisfied.
