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
   `tests/fixtures/q16-license`; the synthetic fixture declares one exact-version public PyPI dependency in requirements.txt.
3. Generate a manifest bound to the exact CI candidate commit SHA and SHA-256 of all reports.
4. Emit evidence only. The manifest explicitly records that no gate decision, legal conclusion
   or license approval was made.

## Coverage boundary

ScanCode covers the checked-out repository source tree while explicitly excluding VCS metadata, dependency/build caches, and `.env*` files to avoid inspecting or retaining possible credentials. Those excluded files are outside the license-scan coverage and remain subject to the separate secret-scanning controls. ORT is configured to analyze and scan the full repository's NPM and PIP dependency graph in an isolated copy, as well as the deterministic synthetic fixture. The current repository inventory contains two NPM `package.json` files and Python `pyproject.toml` / `requirements-dev.txt`, but no NPM or Python lockfiles. Dynamic versions are therefore enabled for this shadow run; the resolved versions and download hashes are captured in ORT reports. This is an exploratory snapshot, not a reproducible lockfile-based release gate. No other package-manager manifests were found in the inspected repository tree. The result must not be described as legal approval or final system-wide license clearance.

## Safety

- No production data, production credentials, or persistent scan-result backend are used.
- The workflow contacts GitHub and package registries to retrieve pinned tool artifacts and
  resolve the synthetic fixture / repository dependency metadata. ORT may download package
  metadata or source archives into its ephemeral runner cache; it does not install these
  dependencies into CK-NEXUS or a production runtime.
- `.env*` files are excluded from ScanCode and ORT input copies. This is an explicit license-scan
  coverage exclusion; separate secret-scanning controls remain responsible for those files.
- CI runner is ephemeral; the candidate-bound report bundle is retained as a GitHub Actions
  artifact for 30 days, not written to production storage.
- ORT / ScanCode findings are advisory inputs for human/legal review. They cannot approve
  licenses, change policy, merge, deploy, or decide CK-NEXUS gates.

## References

- ORT: https://oss-review-toolkit.org/ort/docs/intro
- ORT usage: https://oss-review-toolkit.org/ort/docs/getting-started/usage
- ORT scanner: https://oss-review-toolkit.org/ort/docs/tools/scanner
- ScanCode: https://scancode-toolkit.readthedocs.io/en/stable/
- ScanCode installation: https://scancode-toolkit.readthedocs.io/en/stable/getting-started/installation/index.html
