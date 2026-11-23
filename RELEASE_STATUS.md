# Live status update — 2026-11-23 (PR #392 current candidate)

**Decision: NO-GO FOR PRODUCTION.**

## Current exact candidate

- PR #392: OPEN; base `main`; head branch `ops/provider-free-go-clean`; no merge or deployment.
- Candidate source SHA: `c656ad5991464d7e9457adc2a33507b0d0daa623`.
- Candidate source tree: `ea290bb80de030a020c6b94582fe436c25dccbd6`.
- Canonical Q10–Q16 runtime manifest: `d3fb76bb9d576e88f9873eda1ff9eff23edeae41030439e3bea619ae1dbdc56c`.
- Candidate automated-gates run: `45117449244`; Q10 and Q11 were skipped.

## Latest candidate evidence (run 45117449244)

| Gate | Result | Meaning |
|---|---|---|
| Q10 | NOT_VERIFIED | Skipped; independent security review and current-subject scan remain open. |
| Q11 | BLOCKED / NOT_VERIFIED | Skipped; valid OpenAI credential and authorized live test are still required. |
| Q12 | PASS | Delegated cgroup v2 enforcement and non-root worker were observed. |
| Q13 | PASS_CANDIDATE | Isolated staging backup/restore and sentinel round-trip passed. |
| Q14 | PASS_CANDIDATE | Staging alert delivery and health/metrics checks passed. |
| Q15 | PASS_CANDIDATE | Fresh Ubuntu 24.04 host smoke and portable regression passed. |
| Q16 image | PASS_CANDIDATE | Candidate image checks passed, including non-root runtime. |
| Q16 licenses | PASS | 56 runtime distributions; unresolved license evidence: 0. |

The six downloaded artifact ZIPs were opened and their JSON contents inspected. Their source SHA and runtime manifest match the candidate above. However, their workflow branch is `ops/provider-free-go-clean`; the release provenance verifier currently allowlists different branches for Q12–Q16. Therefore these artifacts are **not yet accepted by the final release provenance gate**. The allowlist was not weakened.

## Corrections made on this PR branch

- Updated all three stale final-package manifest pins from `370f8a8...` to the canonical candidate manifest `d3fb76b...`.
- Updated the final package's runtime inventory assertion from 55 to 56, matching the latest candidate license artifact.
- The final package remains fail-closed: Q10/Q11 are unresolved and Q14 is still candidate-only. No package release, merge, or deployment is authorized.

## Remaining blockers

1. Q10: wait for the no-repeat lock to expire at **2026-11-24 07:50 ICT**, then perform the required current-candidate scan and independent human security review.
2. Q11: obtain an owner-authorized valid OpenAI API credential and an approved live test path. No paid generation request has been made.
3. Q12–Q16: regenerate/verify evidence through the provenance-approved branch paths; do not bypass branch restrictions or relabel candidate results as production PASS.
4. Obtain required independent review and complete the final production package only after every mandatory gate passes.

**Release decision remains NO-GO.** Q01–Q09 are not re-certified by this PR update; historical evidence must be checked separately.

---

# Current candidate update — 2026-11-23 (PR #392)

**Decision: NO-GO FOR PRODUCTION.**

- Current canonical Q10–Q16 manifest: 370f8a8f405e9b960e8b41722d0f61a4269237d137b94c014a1c2598e75e08de (computed from the staged remediation tree). This snapshot distinguishes the application code subject from the documentation-only PR head.

- PR: https://github.com/spinlnw10-art/ck-nexus/pull/392
- PR state: OPEN; merge state BLOCKED; review decision REVIEW_REQUIRED; base main.
- Latest PR head is a moving Git ref; read it live with GitHub CLI before acting. The previously observed head 0944ffd... was advanced by the AI handoff documentation update.
- Application code candidate SHA scanned by Q10: efbb2ee157fcfdedfde054508fafaf21cbaf88fa.
- Commits after the code candidate through the current PR head change documentation only; do not mislabel the Q10 report as if it were scanned against the documentation head.
- Both remote task branches were verified equal after the handoff update; query live refs for their current SHA.
- main remains at 944d7cb70a5d59d53c8fb379752bbee2085f7c8c; PR #392 has not been merged.
- Work was performed in the isolated Termux worktree ~/cknexus-pr392-audit; the primary worktree was not modified.
- The documentation push triggered a new CI cycle; its checks must be read live and not inferred from the previous head.\n- No merge or deployment has occurred.

**AI handoff:** Read [docs/ops/AI_HANDOFF_CURRENT_TRUTH.md](docs/ops/AI_HANDOFF_CURRENT_TRUTH.md) first, then [docs/ops/CKNEXUS_WORK_LEDGER.md](docs/ops/CKNEXUS_WORK_LEDGER.md). These identify canonical files, historical files, exact SHAs, completed work, and no-repeat rules.

## Exact-SHA checks already completed — do not rerun without a material change

- Latest observed GitHub checks on `efbb2ee157fcfdedfde054508fafaf21cbaf88fa`: `test` PASS, `preflight` PASS, `attack-regression` PASS, `universal-system` PASS, CodeQL PASS, Analyze Python PASS, Analyze JavaScript/TypeScript PASS, Analyze Actions PASS.
- Attack regression: 22/22 passed.
- SonarCloud Code Analysis: FAIL. Actionable issue-level details have not yet been triaged; this failure is not proof that every quality finding is a release blocker.
- Q10 workflow run: `45088376317`.
- Q10 report source SHA: `efbb2ee157fcfdedfde054508fafaf21cbaf88fa`; report SHA-256: `71dab5d573b4f2bf1bf0e31cf794c13b0be17c08e8f317b580b9f8bb4626b192`.
- Q10 scanner result: PASS; dependency vulnerabilities 0; Bandit High 0 / Medium 0 / Low 541; Secret Scan PASS (872 tracked files); attack regression exit 0.
- Q10 whole-gate status: **REVIEW REQUIRED**. The report explicitly records `security_review_status=REQUIRED` and `production_promotion_allowed=false`. Scanner PASS is not Q10 closure and is not Production GO.

## Bandit 541 — existing artifact triage, no rescan

Detailed source-context dispositions for the 107 non-test findings are recorded in docs/security/Q10_BANDIT_REVIEW_efbb2ee.md. This is AI-assisted triage, not independent human sign-off; Q10 remains REVIEW_REQUIRED.

All 541 findings are LOW. Grouped from the saved JSON artifact:

| Rule | Count | Initial handling |
|---|---:|---|
| B101 assert_used | 422 | Mostly test-path findings; classify, do not mass-suppress |
| B603 subprocess without shell=True | 42 | Review production call sites and argument handling |
| B105 hardcoded password string | 26 | Review whether values are real secrets, examples, or test fixtures |
| B404 subprocess import | 25 | Context review; import alone is not proof of exploitability |
| B607 partial executable path | 24 | Review executable resolution and trust boundary |
| B112 try/except continue | 1 | Review error handling |
| B110 try/except pass | 1 | Review swallowed exception |

434 findings are under test paths and 107 are outside test paths. This is a triage split, not a declaration that all test-path findings are harmless or all non-test findings are exploitable. Review the existing JSON; do not rerun Bandit on the unchanged SHA.

## Remaining release blockers / scope

1. Q10 independent security review and finding dispositions remain REQUIRED.
2. Issue #66 is CLOSED as of 2026-10-31 via ad2fac7aa0752117dde065c7ad9b0b8d41136aa2. Regression coverage exists in tests/test_attachment_magic_66.py, tests/test_attachment_signature_66.py, and tests/test_attachment_hardening_q10.py for signature mismatch, MIME, Office ZIP bombs, traversal, expected Office parts, and macro payloads. This development issue closure does not close Q10.
3. Existing Q11–Q16 evidence files are stale for this code candidate: Q11/Q13/Q14/Q15/Q16 bind to source 4cf17cd3... and manifest 96dcd0f0...; Q12 binds to source 512837c8... and the same old manifest. Current code manifest is be62b62b.... Current-subject workflow orchestration has been prepared but not yet executed.
4. PR #392 requires review; no merge or deploy has occurred.
5. SonarCloud failed on PR #392 (Security Rating D / Reliability Rating C). Authenticated Sonar issue export (run 45093845262) retrieved 43 issues: 1 CRITICAL + 3 MAJOR vulnerabilities, 4 MAJOR bugs, 35 code smells, 0 hotspots. The blocking TLS, workflow-install, and signup Promise findings have been remediated in the new candidate; fresh Sonar analysis is pending.

## Work deduplication record

The durable work ledger is [docs/ops/CKNEXUS_WORK_LEDGER.md](docs/ops/CKNEXUS_WORK_LEDGER.md). For the unchanged SHA `efbb2ee157fcfdedfde054508fafaf21cbaf88fa`, reuse the existing Q10, Bandit, Secret Scan, Attack Regression, Ruff, compile, targeted 43-test, and listed GitHub CI evidence. Do not repeat those checks within the 24-hour lock window unless a relevant source/workflow change invalidates the evidence. Record the exact reason before any rerun.

## Release decision

**NO-GO FOR PRODUCTION.** This candidate is not merged or deployed. The repository homepage and status page must not imply Production readiness. Historical sections below are retained as historical records and do not override this current exact-SHA snapshot.

---

# Release evidence snapshot — 2026-11-19 (PR #380 code baseline)

**Code-bearing baseline after PR #380:** `0d7b0d1c0efee01d6307b418c848cd0c84411ea0`

**Source tree at that baseline:** `8cc361ab7c0e9e35944277e4dd3fdb7e8a99b13a`

**Release-status maintenance after PR #381:** documentation-only merge commit `be8050e4e95bec0721473c8a16f64ac82defa353`, tree `95ae8ef312e6a717fabad79ae9cfcd36d3d13387`. PR #381 changed this status document only; it did not change runtime code.

**Before any Q10–Q16 run:** recalculate the exact candidate commit, source tree, and runtime/deployment subject from the latest `main`. The hashes above are a dated evidence snapshot, not an evergreen pointer to the latest branch head.

## Release decision

**NO-GO FOR PRODUCTION.** PR #380 added public feedback intake/triage, updated the CK-NEXUS product homepage, and hardened the `/api/dev-status` snapshot path. These changes do not close any Q10–Q16 release gate and do not authorize Production promotion.

- The prior Q10–Q16 evidence below is bound to older commits/runtime subjects. It is historical and is **not evidence for a new release candidate**.
- Recompute the exact release/runtime subject and rerun every mandatory gate Q10–Q16 against the latest candidate before any release claim.
- GitHub CI on PR #380 merge commit `0d7b0d1c0efee01d6307b418c848cd0c84411ea0`: **PASS** (run `44449966729`). CodeQL on the same commit: **PASS** (run `44449965823`). PR #381 documentation-only update CI and CodeQL also passed (runs `44450632654` and `44450631300`). These results are not Production approval.
- SonarCloud analysis on PR #380 and PR #381 failed/cancelled and remains unresolved. It was not one of the repository's three required branch-protection checks (`test`, `preflight`, `attack-regression`); do not describe it as passed.
- Termux local Python test execution was blocked because the Android/aarch64 environment could not build the required `cryptography` package (Rust target unsupported). GitHub CI passed; local Termux test execution is not claimed.
- The public feedback feature is merged into source only. It has **not** been deployed or exposed as a live beta service.
- Interactive public beta remains blocked until per-tester authentication, session ownership, and tenant isolation are implemented and independently tested. Do not share the global `CKNEXUS_ACCESS_TOKEN` with testers.
- The VPS hostname `vps3680569.trouble-free.net` did not resolve from Termux during this verification, so SSH/runtime reachability and service health are **NOT VERIFIED**. No deployment or server mutation was attempted.
- PRs #380 and #381 received approvals from the repository owner's secondary account. These satisfy GitHub's configured approval count but are **not independent third-party audits**.

The sections below are retained as historical evidence and must not be interpreted as closure for the latest candidate.

---

> **Historical evidence subject:** Q10 scanner PASS เฉพาะ commit `22edd1f` (run 41231931695).
> ณ วันที่บันทึกเดิม Q11–Q16 ยัง NOT_VERIFIED บน main ในขณะนั้น `f4c4447` และต้องรันใหม่บน main ปัจจุบัน.

# Release Status — CK-NEXUS Q10-Q16 Closure

Decision: **NO-GO FOR PRODUCTION CLAIMS**

Historical canonical main at the original rebaseline: 22edd1f07147f7223cf02abba056c6ce4a3beee0 (tree 3a742e8b91001efb3558fc2cdb9a617fbc4e6c9a)
Closure branch: release/q10-q16-closure (historical evidence line; not rebased to current main)
Previous closure head: a55a8d36b0a1b61b426c5d59ab44ebd841eb8d53 (historical)
Previous frozen runtime/security source SHA: ad2fac7aa0752117dde065c7ad9b0b8d41136aa2 (superseded for current main)
Previous frozen source tree: eb2074176319072ca3f31d5c8c990752ba849b0a (superseded for current main)
Previous frozen runtime/deployment subject: 772662ac4ed60e785f30370c0c66bfdf8f798ea5f67fe13063404b20f2f74200 (superseded for current main)
Unified application subject: `dff89dc7fa9cd6e40480c3344f688a75383ec798929efe23f3a29c79d1186cec`
Closure contract: `docs/Q10_Q16_CLOSURE_CONTRACT.md`

## Historical main rebaseline status — 2026-10-31

Live repository verification found current canonical main 22edd1f07147f7223cf02abba056c6ce4a3beee0, tree 3a742e8b91001efb3558fc2cdb9a617fbc4e6c9a. Recomputing the runbook runtime/deployment path set on current main yields c8e6dca69fd241e6f555ae9ccd880cdd3b34c8d7b2417c94b3ca89dce9b95ef9, not the previous frozen subject 772662ac... . PR #330 added services/email_gateway/attachments.py to the runtime path set and changed the subject. The old Q11–Q16 evidence remains historical only and is not evidence for current main.

- Current-subject Q10 layered scanner: PASS on source 22edd1f07147f7223cf02abba056c6ce4a3beee0, tree 3a742e8b91001efb3558fc2cdb9a617fbc4e6c9a, runtime subject c8e6dca69fd241e6f555ae9ccd880cdd3b34c8d7b2417c94b3ca89dce9b95ef9; workflow run 41231931695; report SHA-256 db33d3e7b80f34b13f42a235aea5e59f6efc470b92550cd7297804b492692389; 0 dependency vulnerabilities, 0 Bandit high, 0 Bandit medium, secret scan exit 0, attack regression exit 0. 513 Bandit low findings remain visible for disposition.
- Q10 whole gate: NOT_VERIFIED until an independent human reviews the exact report/findings and attests.
- Q11 current-subject: NOT_VERIFIED / BLOCKED. Existing workflow remains pinned to the previous subject; secret-name presence does not prove a successful exact-subject provider run.
- Q12 current-subject: NOT_VERIFIED / BLOCKED. Registered cknexus-q12 GitHub runner is offline; no current-subject delegated cgroup evidence exists.
- Q13, Q14, Q15 and Q16 evidence currently recorded below is bound to the previous subject and is STALE FOR CURRENT MAIN until each gate is rerun against the new exact subject.
- Production remains NO-GO. No Q10–Q16 promotion or owner approval is implied by the Q10 scanner PASS.

Issue #329 was updated with this exact mismatch and the evidence blockers. Workflow constants and previous subject-bound evidence were deliberately not rewritten because Q11–Q16 evidence has not yet been regenerated.

This status follows the rotated closure authority recorded by commit `a55a8d36...`, the schema-v3 Q10 scan request, operator preflight, and final-production-package workflow. Older references to `96dcd0f0...` / `4cf17cd3...` are superseded for the current production-closure decision.

## Update 2026-09-15 — Post-P0 consolidation & rotated authority (automated housekeeping)

- Merged to main: #246, #240, #241, #242, #244, #245 (Post-P0 chain), #237 (Buyer Delivery V2 + Sonar fix), #230 (rotated closure authority reconciliation).
- Closed as duplicates/superseded: #226 (kept #227), #235 (kept #234), #236 (kept #237).
- Evidence Q05/Q08/Q09 regenerated for the current exact tree via `refresh-candidate-evidence` (runs 34926334985, 34926729111).
- CI on main: **CK-NEXUS CI PASS**. Q05: 598 passed / 0 failed. Q08 live: PostgreSQL PASS, Redis PASS.
- Buyer Delivery V2 (spec, packaging script, transfer schedule template, acceptance checklist) is on main; candidate ZIP built and validated in CI (run 34927478355, checksums OK, secret_scan PASS).
- Authority note: Q10-Q12 frozen authorities below follow the rotated closure authority (`a55a8d36...`); production-claims verdict stays NO-GO until gates move beyond PASS_CANDIDATE.
- Outstanding: remaining Post-P0 backlog PRs require rebase onto current main; #243/#250 CI unstable.

## Historical release candidate record (as of 2026-10-31)

Unified Control and production hardening are converged on the closure branch but are **not merged to `main`**. The production image remains fail-closed and production eligibility is false while Q10, Q11, and Q12 are unresolved.

## Gate matrix

| Gate | State | Evidence |
|---|---|---|
| Q05 quality/regression | PASS | rotated-subject quality evidence on closure line |
| Q08 PostgreSQL/Redis live idempotency | PASS | rotated-subject live evidence on closure line |
| Q09 governance binding | PASS_CANDIDATE | governance binding on rotated subject |
| Q10 dependency component | **PASS (current main scanner)** | run 41231931695; 0 dependency vulnerabilities; report SHA-256 db33d3e7... |
| Q10 whole security gate | **NOT_VERIFIED / BLOCKER** | Current main scanner PASS on 22edd1f (run 41231931695, report sha256 db33d3e7...); independent human review/disposition still required |
| Q11 live provider P0-AI-001 | **NOT_VERIFIED / BLOCKED** | Existing evidence is previous-subject only; workflow remains pinned to ad2fac7a; no current-subject run |
| Q12 delegated cgroup v2 | **NOT_VERIFIED / BLOCKED** | Current cknexus-q12 runner is registered but OFFLINE; no current-subject delegated cgroup v2 evidence |
| Q13 PostgreSQL DR | **NOT_VERIFIED / STALE SUBJECT** | Previous run 31950497105 is historical; rerun required on current subject |
| Q14 observability/operator delivery | **NOT_VERIFIED / STALE SUBJECT** | Previous run 31950773095 is historical; rerun required on current subject |
| Q15 clean-machine deployment | **NOT_VERIFIED / STALE SUBJECT** | Previous run 31950497105 is historical; rerun required on current subject |
| Q16 production image | **NOT_VERIFIED / STALE SUBJECT** | Previous run 31950497111 is historical; rerun required on current subject |
| Q16 runtime license inventory | **NOT_VERIFIED / STALE SUBJECT** | Previous run 31950497135 is historical; rerun required on current subject |
| Q16 final merge/tag/package | **NOT ELIGIBLE** | blocked by Q10 whole gate + Q11 + Q12 |

## Previous Q10 authority (historical; current request is not rebaselined)

Previous canonical request: `evidence/q10/Q10_SCAN_REQUEST_FINAL_SUBJECT.json`

Required scan identity:

- target SHA: `ad2fac7aa0752117dde065c7ad9b0b8d41136aa2`
- target tree: `eb2074176319072ca3f31d5c8c990752ba849b0a`
- release subject: `772662ac4ed60e785f30370c0c66bfdf8f798ea5f67fe13063404b20f2f74200`
- scope: `.`
- mode: `layered`
- executor: **CK-NEXUS Open-Source Layered Security Gate**
- request state: **PREPARED_NOT_EXECUTED**
- production status: **NO-GO**

Q10 must not be promoted from any single scanner or ordinary CI alone. The replacement gate combines frozen dependency audit, Bandit, secret scanning, and black-box security regression. PASS requires a successful run ID, aggregate report SHA-256, completion timestamp, review/disposition of recorded findings, and exact release-subject provenance.

## External blockers required before Production Ready

1. Run the **open-source layered Q10 security gate** against the exact candidate commit; preserve full reports, review all medium/high findings, bind the aggregate report digest to the release subject, and regenerate all subject-bound evidence after any remediation.
2. Securely configure a seller/owner-authorized staging `OPENAI_API_KEY` through GitHub Actions secret or an equivalent secure runner secret and rerun the exact-subject Q11 verifier. Never place the raw credential in source, issue text, logs, or chat evidence.
3. Run `scripts/agnes_cgroup_v2_staging_gate.py` through the required self-hosted Linux runner labeled `cknexus-q12` with a writable non-root delegated cgroup v2 boundary for `cpu`, `memory`, and `pids`.

## Independent verification and release authority

- Native scanner evidence does **not** substitute for independent HUMAN review.
- Repository owner/AI must not self-approve the independent-review gate.
- Evidence should be hash-sealed and bound to exact subject/provenance before independent review.
- Owner HUMAN sign-off occurs only after independent review.
- PR #14 must remain governed and unmerged until all mandatory gates pass and the final production package succeeds.

## Commercial status

The repository remains sellable as a **source-code / Release Candidate package without Production Ready or Certified claims**. Do not mark the artifact Production Ready, create a production tag, or merge PR #14 to `main` until Q10, Q11, and Q12 are closed and the final production package workflow succeeds.
