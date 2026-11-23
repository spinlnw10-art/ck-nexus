# Q15–Q16 Release Assurance Assessment — 2026-11-23

Status: READ-ONLY WORKFLOW / EVIDENCE REVIEW
Baseline: canonical `main` at `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`
No build, image pull, deployment, production access, credential use or infrastructure mutation was performed for this assessment.

## Executive findings

CK-NEXUS already has substantial Q15/Q16 automation. The immediate improvement is not to replace it, but to close the gap between generated evidence and the repository's own release-evidence provenance verifier.

### Q15 — clean-machine install

Observed in `.github/workflows/candidate-automated-gates.yml`:
- Job runs on `ubuntu-24.04`, a fresh GitHub-hosted runner.
- Checks out source, installs Python 3.12, validates frozen lock, installs all extras/dev dependencies, compiles, runs Ruff and pytest.
- Starts the unified app and checks health, control surface and control manifest.
- Emits `Q15_CLEAN_MACHINE.json` and uploads logs/health/manifest artifacts.
- The evidence is labeled `PASS_CANDIDATE`, not final PASS.

Observed in `scripts/gate_clean_machine.py`:
- Even when `CKNEXUS_CLEAN_MACHINE=YES` is set, the script always returns BLOCKED because deployment-specific evidence collection is not implemented.
- The candidate workflow does not invoke this gate script. Therefore the workflow test is useful clean-host CI evidence, but it is not the canonical Q15 gate implementation.

Evidence/provenance gap:
- The current workflow's Q15 evidence emitter includes source SHA/tree and run ID, but does not add `release_subject_manifest_sha256`, `artifact_id` or `artifact_digest`.
- The canonical `.github/release-tools/verify_release_evidence_provenance.py` requires the subject manifest, integer artifact ID/run ID and `sha256:` artifact digest for each evidence file.
- The checked-in historical `evidence/Q15_CLEAN_MACHINE.json` has artifact ID/digest and subject manifest, but is tied to old source `4cf17cd3...` and manifest `96dcd0f0...`; it is stale for current main.
- The current workflow's measured elapsed duration starts inside the install/test shell step after checkout and Python setup; describe it as workflow install-and-regression duration, not total clean-host provisioning time.

Recommended Q15 direction:
1. Preserve GitHub-hosted ephemeral VM as the clean-host test substrate.
2. Decide whether Q15 means clean source install or exact release-artifact installation; the closure contract says exact release artifact. Add a package/image artifact install test if that is the required contract.
3. Implement a real evidence collector or explicitly separate the candidate workflow evidence from the canonical gate script; avoid two conflicting Q15 authorities.
4. Bind the evidence to exact source SHA/tree and runtime/deployment subject manifest.
5. After artifact upload, obtain the actual GitHub artifact ID/digest and produce a final evidence envelope that the provenance verifier can validate. Do not invent or precompute GitHub artifact metadata.
6. Ensure server process cleanup runs with a shell trap even if a smoke assertion fails; hosted VM teardown is an additional safety boundary, not a substitute for clean process handling.
7. Add tests for missing health output, failed tests, artifact metadata mismatch, stale subject and failed cleanup.

### Q16 — production image and runtime license inventory

Observed in `.github/workflows/candidate-production-image.yml`:
- Builds a pinned Python base-image candidate from Dockerfile.
- Checks frozen production install contract, runtime imports, dependency consistency, absence of dev tools, health/control smoke and non-root runtime.
- Writes Q16 image evidence with source SHA/tree and runtime subject digest.
- Stops the container and uploads evidence/logs.
- Evidence result is `PASS_CANDIDATE`; this is a candidate image smoke, not production promotion authorization.

Observed in `.github/workflows/candidate-runtime-licenses.yml`:
- Builds the exact production Docker image.
- Enumerates installed Python distributions and license metadata/classifiers and hashes detected license files.
- Fails if a distribution has no detected license evidence.
- Excludes the proprietary `ck-nexus-creator` package from the third-party inventory.
- Binds summary to source SHA, runtime subject and workflow run, then uploads inventory and summary.

Limitations:
1. License metadata presence is not legal compliance. SPDX identifiers/expressions should be normalized and checked; ambiguous, custom, dual or missing license declarations require human/legal disposition.
2. Current inventory scans installed Python distributions only. It does not, by itself, inventory OS packages, base-image packages, native libraries, application-bundled assets, frontend packages, external container images or redistributed operator tools.
3. The candidate image evidence checks non-root identity and smoke behavior, but a durable supply-chain claim should include the resulting image digest, SBOM, build provenance/attestation and signature verification.
4. The checked-in Q16 evidence records artifact ID/digest and exact runtime subject but is historical: source `4cf17cd3...`, tree `dfe3888...`, manifest `96dcd0f0...`.
5. The current workflow evidence emitters do not embed the GitHub artifact ID/digest in the JSON they upload. The provenance verifier requires both fields. Q16 image also needs the subject fields checked by the verifier. The verifier's artifact metadata checks are therefore not satisfied by a fresh run unless a later step enriches the evidence from actual uploaded artifact metadata.
6. `production_promotion_allowed` is emitted true when image component checks pass. This field must never be interpreted as overall production approval; release eligibility is still gated by Q10–Q16 and independent review. Consider renaming it to a component-specific eligibility flag or forcing it false in all shadow/candidate contexts.

Recommended Q16 direction:
1. Keep the current image build and smoke checks; do not rebuild a different image for license scanning.
2. Generate SPDX or CycloneDX SBOM for the exact image, including OS and language packages where supported; preserve raw scanner output and scanner/database versions.
3. Add license normalization (SPDX license expressions), policy review for exceptions and a human disposition record. Do not auto-approve ambiguous licenses.
4. Produce signed SLSA/in-toto provenance for the exact image digest; use Cosign verification before any promotion.
5. Generate the final evidence envelope only after GitHub has created the artifact, by retrieving its actual artifact ID/digest and checking they correspond to the uploaded file.
6. Ensure Q16 image, Q16 licenses, SBOM and provenance all bind to the same source SHA/tree, runtime subject and image digest.

## Cross-cutting provenance contract

The existing `.github/release-tools/verify_release_evidence_provenance.py` expects every evidence JSON to contain:
- `release_subject_manifest_sha256`;
- integer `artifact_id` and `github_run_id`;
- `artifact_digest` prefixed with `sha256:`;
- actual GitHub artifact/run records whose digest, workflow-run ID, repository, branch and successful conclusion match.

The evidence generator cannot safely guess artifact ID/digest before upload. Recommended sequence:
1. Generate raw report(s) and a provisional evidence payload with exact source/tree/runtime subject.
2. Upload the raw report bundle.
3. Retrieve artifact metadata through the GitHub Actions API.
4. Verify the artifact's digest and workflow-run binding.
5. Create a final evidence envelope referencing the actual artifact ID/digest, and upload/seal that envelope separately.
6. Run the independent provenance verifier against the exact release subject.
7. Keep all Q10–Q16 evidence on one exact candidate. Any source/runtime change invalidates affected evidence and requires reruns.

## Standards and candidate tooling

- SLSA provenance: https://slsa.dev/spec/v1.2/levels
- in-toto attestations: https://in-toto.io/
- Sigstore Cosign: https://docs.sigstore.dev/cosign/
- SPDX: https://spdx.dev/
- CycloneDX: https://cyclonedx.org/
- ORT: https://oss-review-toolkit.org/ort/docs/
- ScanCode: https://scancode-toolkit.readthedocs.io/

Tool versions and policies must be selected only after checking current maintenance, advisories, checksums/signatures, compatibility and licensing. No production pins are approved by this document.

## Proposed stages

| Stage | Work | Exit criteria |
|---|---|---|
| 0 | Evidence/workflow assessment | Current Q15/Q16 strengths and gaps documented (this PR) |
| 1 | Q15 evidence schema tests | Fresh candidate evidence passes schema and stale-subject negative tests |
| 2 | Q15 exact artifact install | Exact packaged release artifact installs on disposable fresh VM and runs health/regression |
| 3 | Q16 full image inventory | Image digest, OS + language SBOM, normalized license report and exception dispositions |
| 4 | Artifact provenance | SLSA/in-toto provenance and Cosign verification bind exact image digest |
| 5 | Evidence envelope | Actual artifact ID/digest retrieved after upload and verified against raw files |
| 6 | Cross-Gate rehearsal | Q10–Q16 all bound to one exact candidate; independent review; no auto-promotion |

## Safety and non-claims

- This PR is documentation-only.
- No Docker image was built or run, no external image pulled, no production host accessed, no credentials used, and no runtime/dependency/workflow/gate state changed.
- Historical Q15/Q16 evidence is not current-candidate evidence.
- No claim is made that current main passes Q15/Q16.
- Production remains NO-GO until all mandatory Q10–Q16 gates pass on one exact candidate, evidence provenance is independently verified, and owner approval is separately recorded.
