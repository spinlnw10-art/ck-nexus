# CK-NEXUS Work Ledger — Single Source of Work State

Updated: 2026-11-23 07:40 ICT (+07:00)
Do-not-repeat window: until 2026-11-24 07:40 ICT (+07:00)
Purpose: prevent duplicate scans, duplicate fixes, and conflicting status reports.

## Operating rules
1. Read this ledger before starting any CK-NEXUS task.
2. A completed check is reusable only when its subject SHA matches the current target and its evidence is still valid.
3. Never rerun a whole scan just because a new chat/session started.
4. If a target SHA is unchanged, reuse its existing artifacts. Recheck only when a source change, workflow change, expiry, or explicit evidence defect affects the result.
5. Keep findings, remediation tasks, and release gates separate. Do not treat every warning as a release blocker.
6. Every new action must record: date/time, exact target SHA, command/workflow, result, evidence path/hash, and next action.
7. Never mark a gate GO without exact-subject evidence and required human/owner review.
8. Do not merge or deploy without separate explicit authorization.

## Canonical working location
- Device: Termux localhost (Desktop Commander device ID 9e94297b-f265-496a-9cb6-10f78f8d0022)
- Worktree: $HOME/cknexus-pr392-audit
- Branch: fix/q10-attachment-hardening-20261123
- HEAD: efbb2ee157fcfdedfde054508fafaf21cbaf88fa
- Worktree status at ledger creation: clean
- Primary worktree: not touched
- Git remote: https://github.com/spinlnw10-art/ck-nexus.git

## Live GitHub state checked 2026-11-23
- Remote branch fix/q10-attachment-hardening-20261123 -> efbb2ee157fcfdedfde054508fafaf21cbaf88fa
- Remote branch ops/provider-free-go-clean -> efbb2ee157fcfdedfde054508fafaf21cbaf88fa
- PR #392: OPEN; head SHA efbb2ee157fcfdedfde054508fafaf21cbaf88fa; base main; merge state BLOCKED; review decision REVIEW_REQUIRED.
- No merge or deploy performed.

## Exact-subject Q10 artifact already exists — DO NOT RERUN
Local artifact directory:
$HOME/cknexus-q10-efbb2ee/q10-open-source-security-efbb2ee157fcfdedfde054508fafaf21cbaf88fa/

- Workflow run: 45088376317
- Report: q10-open-source-security-report.json
- Report source SHA: efbb2ee157fcfdedfde054508fafaf21cbaf88fa
- Source tree: 2da60b807af2c389f1a798a1443fa475f91a94ed
- Report SHA-256: 71dab5d573b4f2bf1bf0e31cf794c13b0be17c08e8f317b580b9f8bb4626b192
- Bandit JSON SHA-256: 5d180508658f4bae93f170b69b2975d8e397e19a171a48292793f04b077d2547
- Q10 scanner result: PASS
- Dependency vulnerabilities: 0
- Bandit: High 0, Medium 0, Low 541
- Secret scan: PASS, 872 tracked files
- Attack regression: 22/22 passed
- Security review status: REQUIRED
- production_promotion_allowed: false

This is a scanner PASS, NOT Q10 whole-gate closure and NOT Production GO. Use the report above for review; do not repeat the scan unless the target SHA changes or an evidence defect is found.

## Existing Bandit findings — triage from saved JSON only; no rescan
All 541 are LOW. Existing grouping:
- B101 assert_used: 422
- B603 subprocess_without_shell_equals_true: 42
- B105 hardcoded_password_string: 26
- B404 subprocess blacklist import: 25
- B607 partial executable path: 24
- B112 try_except_continue: 1
- B110 try_except_pass: 1
- 434 findings are in paths containing /tests/; 107 are outside test paths.
Do not suppress or mass-fix. Next triage should start with the 107 non-test findings, grouped by rule and reviewed for actual exploitability. The 434 test-path findings can be classified separately; no blanket suppression.

## Live PR checks checked 2026-11-23
- SonarCloud Code Analysis: FAIL
- CodeQL: PASS
- Analyze Actions: PASS
- Analyze JavaScript/TypeScript: PASS
- Analyze Python: PASS
- attack-regression: PASS
- preflight: PASS
- test: PASS
- universal-system: PASS
The PR is still blocked by REVIEW_REQUIRED. SonarCloud failure needs issue-level review only if it contains a release-relevant defect; it is not by itself proof that every finding must be fixed.

## Known stale/conflicting status record — do not rely on without reconciliation
RELEASE_STATUS.md at this worktree still states:
- PR head dc42ab23adcad8c25724f202fa7c72d0c8b5baa3
- Q10 latest artifact source SHA eea74e4df3406c231f22dc6fe5dced4039b20129
These conflict with live GitHub PR head and downloaded exact-subject Q10 report above. Treat those lines as STALE until RELEASE_STATUS.md is reconciled. Do not rerun Q10 to compensate for stale prose; update the status record to cite the already-existing run 45088376317 and exact report hash.

## Current release decision
NO-GO FOR PRODUCTION.
Reasons currently evidenced:
1. Q10 whole security review remains REQUIRED.
2. PR #392 is OPEN / BLOCKED / REVIEW_REQUIRED.
3. SonarCloud Code Analysis currently FAIL; issue-level actionable details not yet reviewed in this ledger.
4. Q11–Q16 current-subject closure is not established by the evidence collected in this session.
5. Issue #66 acceptance criteria are not verified as fully closed.

## Next actions — do these in order, without repeating completed checks
1. Reconcile RELEASE_STATUS.md against the exact live PR SHA and existing Q10 artifact (no scanner rerun).
2. Review the 107 non-test Bandit LOW findings from the saved JSON; record dispositions and only remediate real risks.
3. Review SonarCloud's actionable issues; separate real release blockers from maintainability/quality findings.
4. Verify Issue #66 acceptance criteria against current code/tests; do not reopen already-passed tests without a reason.
5. Work on only the remaining current-subject Q11–Q16 evidence gaps.
6. Request/obtain the required independent review; PR merge and deployment remain separate approval steps.

## 24-hour duplicate-work lock
Until 2026-11-24 07:40 ICT, do not repeat the following against SHA efbb2ee157fcfdedfde054508fafaf21cbaf88fa:
- Q10 layered security scan
- Bandit scan
- Secret scan
- Attack regression
- Ruff / compile / targeted 43-test suite
- GitHub CI checks already listed above
Re-use this ledger and artifacts. If a check must be repeated because the code or workflow changed, state exactly what changed and why the old evidence is invalid before rerunning only the affected check.
