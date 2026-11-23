# Q16 ORT + ScanCode license assurance shadow

**Status:** Draft CI prototype. No legal approval, release gate, or production dependency decision.

## Toolchain

- ORT 99.1.0: analyzer, scanner, evaluator/reporter ecosystem.
- ScanCode Toolkit 32.5.0: repository-wide license, copyright, package and file metadata scan.
- ORT's scanner integration uses ScanCode on the isolated synthetic fixture.

ORT's documented stages include Analyzer, Scanner, Evaluator and Reporter, and it supports
CycloneDX/SPDX reporting. ScanCode is one of the scanners ORT explicitly recommends as a
thoroughly tested integration.

## Artifact integrity and provenance limits

- ORT archive SHA-256 is pinned to the GitHub Release API digest:
  `1c0bf055287f860902ecf98e60f271c62952ea7c2df4697126ca27e8be9e5842`.
- The detached ORT signature asset is also hash-pinned, but the ORT release signing-key
  fingerprint has not yet been independently established in this repository. Therefore
  this prototype records archive integrity, not cryptographic signer authenticity.
- ScanCode v32.5.0 release tag is reported by GitHub as signature-verified; its Python 3.12
  Linux archive SHA-256 is pinned to
  `638adcd0af576d1f4d5b64dde228724b3ca4fdee2c4de20d88e4356be353f027`.
- Before production promotion, pin and independently verify each tool's signing identity,
  provenance and exact artifact digest. Do not infer trust from a version tag alone.

## Test scope

1. Scan the checked-out CK-NEXUS source tree with ScanCode, excluding only VCS metadata,
   dependency caches, bytecode caches and generated build outputs.
2. Run ORT Analyzer and its ScanCode-backed Scanner on the synthetic fixture in
   `tests/fixtures/q16-license`; no external dependencies are declared.
3. Generate a manifest bound to the exact CI candidate commit SHA and SHA-256 of all reports.
4. Emit evidence only. The manifest explicitly records that no gate decision, legal conclusion
   or license approval was made.

## Coverage boundary

ScanCode covers the checked-out repository source tree. ORT Analyzer/Scanner currently exercises the isolated synthetic fixture only; it does **not** yet resolve and scan all CK-NEXUS dependency trees or every OS/native/frontend package manager. Full dependency inventory requires a separately reviewed, isolated analyzer policy and dependency-source download boundary. This PR must not be described as complete system-wide dependency license clearance.

## Safety

- No production data, secrets, credentials, external package downloads requested by the fixture,
  or persistent scan-result backend.
- CI runner is ephemeral; report artifacts remain in the job workspace unless explicitly
  published later through a separately reviewed retention policy.
- ORT / ScanCode findings are advisory inputs for human/legal review. They cannot approve
  licenses, change policy, merge, deploy, or decide CK-NEXUS gates.

## References

- ORT: https://oss-review-toolkit.org/ort/docs/intro
- ORT usage: https://oss-review-toolkit.org/ort/docs/getting-started/usage
- ORT scanner: https://oss-review-toolkit.org/ort/docs/tools/scanner
- ScanCode: https://scancode-toolkit.readthedocs.io/en/stable/
- ScanCode installation: https://scancode-toolkit.readthedocs.io/en/stable/getting-started/installation/index.html
