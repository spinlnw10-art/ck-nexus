# CK-NEXUS Audit & Evidence (MVP)

A read-only repository and ZIP evidence auditor. It is designed to work without a VPS, cloud credentials, third-party Python packages, or network access.

## What it does

- Walks a source directory without following symlinks.
- Excludes common generated/dependency directories.
- Computes SHA-256 and byte counts for every file within the configured size limit.
- Finds byte-identical duplicate files.
- Inspects ZIP archives without extracting them: CRC/integrity, entry count, uncompressed size, encrypted entries, unsafe paths, and suspicious compression ratios.
- Detects selected high-risk secret patterns and records only the file path and finding type. Secret values are never copied into the report.
- Writes a JSON report and a SHA-256 evidence manifest to a separate output directory.
- Returns exit code 0 for PASS and 2 for REVIEW_REQUIRED.

## Requirements

- Python 3.10+
- Standard library only

## Run locally

From the repository root:

```bash
python3 tools/cknexus_audit.py
python3 -m unittest discover -s tests/tools -v
```

Run the command from the repository directory you want to audit. The tool anchors its scan to the current working directory and writes reports to ./audit-output, which is excluded from the scan. It does not accept arbitrary root/output paths from CLI arguments. The auditor never extracts ZIPs and never modifies source files; it writes only its report and manifest.

## CI

The workflow `.github/workflows/audit-evidence.yml` runs the unit tests and creates an evidence artifact for pushes and pull requests. CI output is a candidate evidence report, not an approval to merge or deploy.

## Decision semantics

- `PASS`: scan completed without read errors, potential secret findings, corrupt/unsafe ZIP findings, or configured limit violations.
- `REVIEW_REQUIRED`: at least one finding, unreadable file, invalid archive, unsafe archive path, suspicious compression ratio, or configured limit violation exists.

A PASS is not a security certification, malware verdict, license-compliance determination, independent review, or production deployment approval. Pattern-based secret detection can produce false positives and false negatives. Review findings before making a release decision.

## Safety boundaries

- Read-only with respect to the audited source tree.
- No network calls, credential access, subprocess execution, archive extraction, deletion, git mutation, merge, or deployment.
- Symlinks are skipped and directory traversal is disabled.
- Reports contain file paths and hashes; treat them as potentially sensitive metadata.
- Do not upload reports publicly if repository paths or findings are confidential.

## Version

MVP `0.1.0`. See `docs/AUDIT_EVIDENCE_MVP.md` for scope and release limitations.
