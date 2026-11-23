# Q10–Q16 Existing Control and Evidence Inventory
Date: 2026-11-23
Status: Read-only inventory on `main`; planning evidence only. No tool installed, no workflow run triggered, no gate status changed.

## 1. Scope and method

Inspected the canonical `main` tree (870 tracked files), Q10–Q16 closure contract, evidence execution/provenance contracts, selected GitHub Actions workflows, JSON evidence records and the PostgreSQL DR gate implementation.

This is a focused control inventory, not a complete audit of every workflow, historical branch, live VPS or external credential. Evidence records are treated as records of their stated subject/run only; they are not proof that the current PR head or a future release candidate passes.

## 2. Current gate inventory

| Gate | Existing CK-NEXUS control | Existing evidence snapshot | Gap before external adapter |
|---|---|---|---|
| Q10 | `.github/workflows/q10-evidence-gate.yml`: frozen target checkout, `uv lock --check`, frozen sync, pip-audit, Bandit, repository secret scan, black-box attack regression; aggregate report and artifact provenance. Also `dependency-audit.yml` scheduled/manual. | `evidence/Q10_DEPENDENCY_AUDIT.json`: component pip-audit PASS, zero reported vulnerabilities, whole gate `NOT_VERIFIED`; source SHA `4cf17cd...`, manifest `96dcd0...`. | No CycloneDX/SPDX SBOM generation found in this selected gate workflow; no central Dependency-Track ingestion. Preserve layered checks; add SBOM as a separately evidenced component only after format/version and scope are chosen. |
| Q11 | `verify-q11-final-subject.yml`: pins frozen source SHA/tree/subject, Python and uv, live Responses API smoke using Actions secret, sentinel check, redacted evidence artifact. | `evidence/Q11_OPENAI_LIVE.json`: `BLOCKED`, credential not configured, no sentinel; production promotion false. | The verifier design exists; operational blocker is authorized staging credential/model/account availability. Do not install a testing vendor to substitute for the live provider call. |
| Q12 | `verify-q12-final-subject.yml`: dedicated self-hosted Linux runner, non-root identity, delegated cgroup root, cpu/memory/pids checks, exact gate script and artifact upload. | `evidence/Q12_CGROUP_V2.json`: result PASS and actual kernel enforcement true for its recorded source/run; manifest `96dcd0...`. | Existing native enforcement proof is stronger than merely adding a container scanner. Need reconcile source SHA/tree, run provenance, runner lifecycle and current exact candidate before reuse. Evaluate gVisor/Kata only if threat model requires stronger isolation. |
| Q13 | `scripts/gate_postgres_dr.py` requires source and isolated restore target, staging environment, isolated target class and explicit destructive-restore acknowledgement; backup and restore run in a temporary directory. | `evidence/Q13_POSTGRES_DR.json`: backup/restore completed, sentinel PASS, status PASS, result PASS_CANDIDATE; manifest `96dcd0...`. | Evaluate pgBackRest vs Barman against actual topology, WAL/archive and RPO/RTO needs. Do not replace current isolated restore drill or point a destructive restore at a working DB. |
| Q14 | Existing Prometheus and Alertmanager evidence, failure injection and operator webhook receipt; alert rules at `observability/alert_rules.yaml`. | `evidence/Q14_OBSERVABILITY_ALERT.json`: alert delivery PASS, health metrics PASS, image digests and receipt digest present; manifest `96dcd0...`. | OpenTelemetry instrumentation/collector coverage is not proven by this evidence alone. Inventory current traces/logs/metrics and existing exporters before adding an OTel collector or duplicate monitoring stack. |
| Q15 | `evidence/Q15_CLEAN_MACHINE.json` records a fresh GitHub-hosted VM, frozen install, portable regression and health/control smoke. | Result PASS_CANDIDATE; manifest `96dcd0...`. | Need attest runner ephemerality, workspace isolation, credential cleanup, pinned runner image/toolchain and no cross-job state. Add proof to the existing workflow before introducing Packer/Ansible/Terraform without a concrete infra need. |
| Q16 | `candidate-runtime-licenses.yml` builds exact production image and inventories runtime Python distribution license metadata/files; `final-production-package.yml` enforces Q10–Q16 evidence, provenance and notices. | `evidence/Q16_PRODUCTION_IMAGE.json`: PASS_CANDIDATE; `Q16_RUNTIME_LICENSE_SUMMARY.json`: PASS for 55 runtime distributions, no unresolved metadata; both manifest `96dcd0...`. | Runtime metadata inventory is not a full legal review or source/package SBOM. Evaluate REUSE/ORT and SPDX/CycloneDX on the actual shipped source and image, with human review for ambiguous/missing licenses. |

## 3. Existing evidence and exact-subject warning

The inspected evidence snapshots are mostly bound to release subject manifest:
`96dcd0f0f93b1aaa69e88da30fedcce1b786b51b83f36b72baf7ac910d02b04f`
and source SHA `4cf17cd3befaafeaf64cd4c149739133aa220f73`, not the current integration branch head.

The Q11 and Q12 final-subject verifier workflows also pin a separate frozen source SHA/tree and manifest. Their configured subjects must not be silently substituted with `main` or the PR branch. Before any adapter is treated as gate evidence, the existing provenance verifier must reconcile source SHA, tree, release manifest, workflow run and artifact digest for the exact candidate.

Current snapshot interpretation:
- Q10 whole gate: NOT_VERIFIED.
- Q11: BLOCKED (missing authorized provider credential).
- Q12: recorded PASS for its stated run/subject; not automatically portable to another candidate.
- Q13: PASS_CANDIDATE.
- Q14: PASS for its recorded alert test/subject.
- Q15: PASS_CANDIDATE.
- Q16 image: PASS_CANDIDATE; runtime license metadata summary: PASS.
- Overall production release: NO-GO until the final production workflow accepts a complete, current, exact-subject evidence set.

## 4. Adapter design decisions

1. Reuse the existing Q10 workflow and evidence provenance machinery; do not create a competing security gate.
2. Add SBOM generation as an additive Q10/Q16 evidence producer. Pick one canonical format and pin its schema/tool version. Keep scanner outputs separate from SBOM output.
3. Q11 remains a live CK-NEXUS provider test. Adapter may normalize metadata and redact diagnostics; it must not copy or expose credentials or provider payloads.
4. Q12 adapter reads observed kernel/cgroup results; it must not weaken host delegation, run privileged by default, or turn config inspection into enforcement proof.
5. Q13 adapter records backup/restore tool version, backup/WAL identifiers, restore target class, measured RPO/RTO and integrity/sentinel result. Restore remains isolated and explicitly approved.
6. Q14 adapter may export OpenTelemetry-compatible signals, but Alertmanager/operator receipt remains the delivery assertion unless an approved replacement is tested end-to-end.
7. Q15 adapter records runner image, runner identity, job/workspace isolation, image/tool digests and credential cleanup proof.
8. Q16 adapter records shipped source/image SBOM, license evidence/notices and unresolved legal review items. Machine output cannot self-approve ambiguous licensing.
9. All adapters emit a common envelope referencing `gate_id`, policy version, exact source SHA/tree, runtime subject manifest, build/artifact digest, tool and adapter versions, config digest, workflow run/artifact identity, report digest, scope/completeness and normalized status.
10. Adapter status is evidence input only. The existing CK-NEXUS gate evaluator remains the sole authority for PASS/FAIL/INCOMPLETE.

## 5. Recommended staging order

- Phase A: no new dependency — map current controls and schemas (this document).
- Phase B: prototype a read-only evidence normalizer/schema validator in a dedicated branch using checked-in synthetic reports only.
- Phase C: add SBOM generation to a disposable CI branch and compare results without changing gate decisions.
- Phase D: run one staging adapter at a time, shadow-only; test stale-subject rejection, artifact tampering, missing reports, timeout, secret redaction and incomplete scope.
- Phase E: owner review, pinned versions, compatibility/license review, rollback procedure and explicit policy change before enabling an adapter as required evidence.

## 6. Safety boundary

This inventory made no changes to `main`, production runtime, databases, secrets, GitHub Actions secrets/variables, VPS, runners, Docker, PostgreSQL or external providers. No workflow was triggered. No tool was installed. No release gate was marked passed. No branch was merged or deleted. Production remains NO-GO.
