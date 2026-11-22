# Current candidate update — 2026-11-23 (PR #392)

**Decision: NO-GO FOR PRODUCTION.** This is a provider-routing candidate only; it is not merged or deployed.

- PR: https://github.com/spinlnw10-art/ck-nexus/pull/392
- Branch: `ops/provider-free-go-clean`
- Latest code commit pushed: `8eb52e86f1570e16a8c6952d8255b85a04e9f062`; the README/status documentation refresh is being committed separately.
- Scope: private Termux key-file loading with strict ownership/mode checks; Gemini-first then Groq routing; paid providers excluded unless both explicit opt-ins are enabled; Gemini API key sent in the `x-goog-api-key` header; Groq default refreshed to `openai/gpt-oss-20b`; tests cover provider order, paid-provider exclusion, fail-closed behavior, fallback, and key-header handling.
- Termux provider/credential test selection on the pushed code commit: **37 passed**. Ruff, `compileall`, JavaScript syntax check, and `git diff --check`: PASS.
- GitHub Actions and CodeQL on the pushed code commit `8eb52e86...` passed: CK-NEXUS CI, AI Factory preflight, Security Attack Regression V1, universal-system, and CodeQL Actions/JavaScript/Python.
- The documentation refresh commit `bb62d6a0...` also completed the same GitHub Actions/CodeQL checks successfully. SonarCloud Code Analysis on that latest checked PR head was **cancelled/failed** (check run `137372723238`, zero annotations, generic “last analysis has failed” summary). This is not a passing result. The SonarCloud host responded to a Termux connectivity probe, but unauthenticated project APIs returned “Project doesn't exist”; project-side diagnostics require an authorized SonarCloud session.
- PR checks are not all green: SonarCloud remains failed/cancelled, and independent review is required.
- PR remains OPEN and requires independent review. No merge or deployment is recorded.
- No live model-generation request was sent. API model-list HTTP 200 is not evidence of generation quota or zero cost. Provider billing/quota must be checked before any live call.
- Full repository pytest is not claimed; the validated local selection is the 37 targeted provider/credential tests.
- This candidate does not close Q10–Q16 and does not change the production NO-GO decision.

This is a dated candidate snapshot. Re-check the latest PR head and checks before treating any evidence as current.

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
