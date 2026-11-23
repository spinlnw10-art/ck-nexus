# CK-NEXUS Work Ledger — Single Source of Work State

Updated: 2026-11-23 08:52 ICT (+07:00)
Do-not-repeat window: until 2026-11-24 07:50 ICT (+07:00)
Purpose: prevent duplicate scans, duplicate fixes, and conflicting status reports.

## Live work update — 2026-11-23 08:52 ICT — provider validation and PR CI repair

This section supersedes older PR/check snapshots below.

- Current isolated worktree: `fix/q10-attachment-hardening-20261123`, HEAD `bdf224b66e2798920f9fc3b3ae872086bb737ee5`; both remote task branches point to this SHA; `main` remains `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`.
- PR #392 remains OPEN / BLOCKED / REVIEW_REQUIRED. Live checks on HEAD `bdf224b6`: `preflight`, `Analyze (actions)`, `attack-regression`, `universal-system`, `Analyze (javascript-typescript)`, `Analyze (python)`, `CodeQL`, and SonarCloud PASS; CodeRabbit skipped; `test` FAIL. No merge or deploy.
- Failed `test` run `45095799547` failed during collection of `creator_app/ai_gateway/tests/test_gateway.py`: `ModuleNotFoundError: No module named 'creator_app'`. Root cause: CI invokes pytest without repository root in `PYTHONPATH`. Corrected `.github/workflows/ci.yml` Portable regression step to set `PYTHONPATH: ${{ github.workspace }}`; applied the same import-path fix to Q15 fresh-host install. Also fixed `candidate-automated-gates.yml` so `skip_q13=true` actually skips Q13 instead of rerunning reusable evidence. YAML parse PASS; `git diff --check` PASS; with `PYTHONPATH=.` the formerly failing file collected 10 tests.
- Provider key validation used fixed provider models-list GET endpoints only (no model generation). Results: Gemini AUTH_OK; Mistral AUTH_OK; OpenRouter AUTH_OK; OpenAI local key AUTH_OK for models-list; Groq AUTH_FAILED (invalid); Cerebras AUTH_FAILED (invalid). Values were not printed. Key files retain mode `0600`. AUTH_OK does not prove free quota or inference entitlement.
- Provider regression tests: `python -m pytest -q tests/test_free_providers.py tests/test_provider_adapters.py tests/test_provider_router.py creator_app/tests/test_cost_guarded_provider_router.py` => 32 passed. Full portable suite on Termux system Python is not a valid CI substitute: dependencies such as `defusedxml`, Pydantic v2, SQLAlchemy, and MCP are absent from the system interpreter.
- Q11 contract explicitly requires a live OpenAI Responses API call and `CK-NEXUS-P0-SMOKE-PASS`. Other vendors cannot be substituted as Q11 PASS without a reviewed contract/workflow change. The previously failing GitHub `OPENAI_API_KEY` secret remains unverified for Q11; local OpenAI models-list AUTH_OK is not the Q11 smoke test.
- Q10 no-repeat lock remains in force until 2026-11-24 07:50 ICT; do not rerun Q10/Bandit/secret scan before expiry unless new source change invalidates evidence.
- Next: publish the CI/Q15 import-path and Q13 reuse fixes with this status update; verify new remote SHA and PR checks. Then run current-subject gates only where evidence is missing/invalid, keeping Q11 blocked until an approved compatible credential/contract is available.

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
- Latest documentation HEAD before this policy commit: 787ef3729caa9bf2bb876c2dc097c51fa0821361 (documentation-only; application code candidate remains efbb2ee157fcfdedfde054508fafaf21cbaf88fa).
- Worktree status at ledger creation: clean
- Primary worktree: not touched
- Git remote: https://github.com/spinlnw10-art/ck-nexus.git

## Live GitHub state checked 2026-11-23
- Latest remote refs verified before this policy commit: both `fix/q10-attachment-hardening-20261123` and `ops/provider-free-go-clean` -> `787ef3729caa9bf2bb876c2dc097c51fa0821361`.
- PR #392 was last observed OPEN / BLOCKED / REVIEW_REQUIRED before the final documentation-only push; recheck the exact PR head and checks before making a current-state claim.
- No merge or deploy performed.

> **Ledger precedence:** The newest dated section at the top is the current truth. Older dated entries below are historical snapshots and may contain statuses that were true at that time but have since changed. If any older entry conflicts with the latest section or AI_HANDOFF_CURRENT_TRUTH.md, do not repeat its task or status.

## Second gate batch findings — run 45094986250

- Q13: PASS_CANDIDATE, source a8f65e9, canonical manifest 370f8a8f...; artifact retained for reuse.
- Q16 production image: PASS_CANDIDATE, non-root image/import/health checks passed; runtime licenses: PASS_CANDIDATE; both use manifest 370f8a8f... and are retained for reuse.
- Q14: PASS in run 45094986250, but rerun once with hardened locked/no-build installer so the execution method matches the corrected workflow policy.
- Q10 and Q15 failed before scans/tests because uv 0.12.4 does not support --only-binary on uv sync. Correct syntax is --locked --no-build --no-install-project. This is a workflow-only fix; runtime manifest stays 370f8a8f....
- Q12 failed before starting because systemd-run rejected the unsupported DelegateControllers property. Retain Delegate=yes only; rerun.
- Q11 remains skipped until the repository OPENAI_API_KEY secret is replaced with a valid project key.
- Next rerun inputs: skip_q10=false, skip_q11=true, skip_q13=true, skip_q16=true, export_sonar_issues=true. Q12/Q14/Q15 run; Q13/Q16 are reused, not repeated.

## Sonar remediation and canonical Q10–Q16 manifest — 2026-11-23

- New candidate canonical manifest (includes scripts/): 370f8a8f405e9b960e8b41722d0f61a4269237d137b94c014a1c2598e75e08de. Source SHA is the live PR #392 head after the remediation push; read it from GitHub rather than copying an older SHA.

- SonarCloud baseline export from run 45093845262 is retained at evidence/sonarcloud/pr392-6a960b9c/. It reported 43 issues: 1 CRITICAL + 3 MAJOR vulnerabilities, 4 MAJOR bugs, 35 code smells, 0 hotspots; Security D / Reliability C.
- Remediated the blocking findings in the working candidate: explicit TLS CERT_REQUIRED + hostname validation; pinned uv 0.12.4 wheel-only install and frozen binary-only dependencies; signup autoScan/provider scan promises awaited; clipboard promise rejection handled; init promise rejection handled.
- Added scripts/release_subject_manifest.py as the only Q10–Q16 manifest source. It includes scripts/ in the runtime subject, so Q10 and Q11–Q16 cannot silently calculate different path sets. Updated Q10, Q11–Q16, CI, refresh-evidence, and final package workflows to use it.
- Q12 now runs inside a systemd Delegate=yes service as the non-root Actions runner on ubuntu-24.04. The first direct chown approach failed with PermissionError; the new systemd method is not yet verified.
- Previous batch run 45093845262 is not promoted: Q13/Q15/Q16 individual jobs passed but used a mismatched manifest; Q11 failed with 401 invalid_api_key; Q12 failed with PermissionError; Q14 was cancelled. The Sonar JSON is retained as historical triage only.
- OPENAI_API_KEY GitHub secret is configured but the Q11 Responses API call returned 401 invalid_api_key. The OpenAI Platform key setup flow was opened; owner must create a valid project key and replace the GitHub repository secret. Do not paste the key into chat.
- Next batch: dispatch candidate-automated-gates.yml with skip_q10=false, skip_q11=true, export_sonar_issues=true. This runs a new Q10 scan for the changed source and Q12–Q16 on the same canonical manifest; Q11 is rerun separately after the secret is corrected.
- The old 24-hour no-repeat lock applies only to the superseded efbb2ee source. This is a changed source candidate, so one new Q10 scan is justified. Do not repeat it again unless the application source changes or evidence is invalidated.

## Historical gate preparation — superseded candidate efbb2ee

- Previous code candidate: efbb2ee157fcfdedfde054508fafaf21cbaf88fa; tree 2da60b807af2c389f1a798a1443fa475f91a94ed; historical manifest be62b62b04827ee7c90a090e59da8adf55212ed477671b99cb0dd885fa5a3d4b.
- Current PR head when checked: c869dd61f0491de584a4917657f55d66900008ea; checks PASS for CodeQL, attack-regression, preflight, test, universal-system, Analyze Actions/JS/TS/Python; SonarCloud FAIL. PR remains OPEN / BLOCKED / REVIEW_REQUIRED.
- Issue #66 is CLOSED at 2026-10-31T17:31:32Z, referenced closing commit ad2fac7aa0752117dde065c7ad9b0b8d41136aa2. Do not count as an open blocker; regression tests cover content signatures, MIME, Office ZIP bomb/path traversal, Office parts and macro payload.
- Q11 evidence is BLOCKED and Q12–Q16 evidence are PASS/PASS_CANDIDATE only for old manifest 96dcd0f0...; all are stale for current manifest be62b62b....
- Added source-context review report for 107 non-test Bandit LOW findings: docs/security/Q10_BANDIT_REVIEW_efbb2ee.md. It is AI-assisted triage, not owner/independent sign-off. Q10 remains REVIEW_REQUIRED; do not edit machine evidence to force PASS.
- Prepared current-subject gate orchestration: candidate-automated-gates.yml supports skip_q10 and optional authenticated Sonar export; Q11/Q12/Q14/Q16 workflows are reusable; Q13/Q15 now emit the exact runtime subject manifest. Q12 uses an ephemeral GitHub-hosted runner and provisions delegated cgroup v2, removing dependency on the offline self-hosted VPS runner.
- These workflows have not yet been dispatched. Next action after push: dispatch candidate-automated-gates.yml with skip_q10=true and export_sonar_issues=true; then download, inspect, and commit each exact-subject evidence artifact.
- Existing no-repeat lock remains active until 2026-11-24 07:50 ICT (+07:00). Do not rerun Q10/Bandit/secret/attack scans for unchanged application source.

## Current AI handoff and verified PR head — 2026-11-23

- First-read handoff: [AI_HANDOFF_CURRENT_TRUTH.md](AI_HANDOFF_CURRENT_TRUTH.md). It defines the canonical document order, exact SHA meanings, completed work, open blockers, and historical/confusing files.
- PR #392 head is a moving ref; read it live with gh pr view 392 before acting. The previously observed head 0944ffd... was advanced by the AI handoff documentation update.
- Both task branch refs were read back equal after the handoff update; query live refs for the current SHA.
- main remains 944d7cb70a5d59d53c8fb379752bbee2085f7c8c; no merge or deployment.
- Q10 report remains bound to application code SHA efbb2ee157fcfdedfde054508fafaf21cbaf88fa; commits through PR head 0944ffd... are documentation-only. Never relabel the Q10 source SHA.
- Previous complete checks on 0944ffd...: CodeQL, Analyze Actions, Analyze JS/TS, Analyze Python, attack-regression, preflight, test, universal-system PASS; SonarCloud Code Analysis FAIL; CodeRabbit skipped. The handoff documentation push triggered new CI; read current checks live.
- This handoff update corrects stale README/RELEASE_STATUS references that previously described efbb2ee... as the PR head. Do not redo this documentation reconciliation absent new facts.
- Documentation validation: git diff --check PASS; python -m pytest -q tests/test_readme_homepage.py PASS (3 passed). The bare pytest command was unavailable, but the Python module invocation succeeded.

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

## Historical status-record conflict — reconciled in documentation update
The older RELEASE_STATUS.md snapshot contained stale PR/Q10 identifiers. It was updated in documentation commit `b5e542e41cb55bad9604cd487818a1faaa80e738`, then the ledger timestamp was corrected in `787ef3729caa9bf2bb876c2dc097c51fa0821361`. Do not reopen this documentation task unless new source facts make the current record inaccurate.

## Current release decision
NO-GO FOR PRODUCTION.
Reasons currently evidenced:
1. Q10 whole security review remains REQUIRED.
2. PR #392 is OPEN / BLOCKED / REVIEW_REQUIRED.
3. SonarCloud Code Analysis currently FAIL; issue-level actionable details not yet reviewed in this ledger.
4. Q11–Q16 current-subject closure is not established by the evidence collected in this session.
5. Historical statement superseded: Issue #66 is CLOSED as of 2026-10-31; do not treat it as an open task.

## Next actions — do these in order, without repeating completed checks
1. Recheck PR #392 head SHA and checks after the latest documentation-only push; do not rerun application scans.
2. Review the 107 non-test Bandit LOW findings from the saved JSON; record dispositions and only remediate real risks.
3. Review SonarCloud actionable issues; separate real release blockers from maintainability/quality findings.
4. Do not reopen Issue #66; it is CLOSED and has attachment signature/MIME/Office archive regression coverage.
5. Work on only the remaining current-subject Q11–Q16 evidence gaps.
6. Obtain required review; PR merge and deployment remain separate approval steps.

## 24-hour duplicate-work lock
Until 2026-11-24 07:40 ICT, do not repeat the following against SHA efbb2ee157fcfdedfde054508fafaf21cbaf88fa:
- Q10 layered security scan
- Bandit scan
- Secret scan
- Attack regression
- Ruff / compile / targeted 43-test suite
- GitHub CI checks already listed above
Re-use this ledger and artifacts. If a check must be repeated because the code or workflow changed, state exactly what changed and why the old evidence is invalid before rerunning only the affected check.

## Mandatory completion and no-repeat rule (approved 2026-11-23)

- Before every action, search this ledger and existing Git/evidence artifacts for the same task or fingerprint.
- If a matching task is already complete and its evidence remains valid, reuse it and take no duplicate action.
- When an authorized task is completed, update this ledger, commit, push to its designated task branch immediately, then verify the remote branch SHA equals the local commit SHA.
- Status vocabulary: `DONE` = task outcome verified; `PUBLISHED` = commit pushed and remote SHA read back; `BLOCKED` = publication/verification failed. Never conflate these states.
- Record task fingerprint, source SHA, changed files, test/check result, evidence path/hash, commit SHA, remote branch/SHA, and timestamp.
- Reopen only for a material source/workflow/requirement change, expired or defective evidence, or a newly observed failure. Record why old evidence no longer applies and rerun only the affected check.
- Do not merge, deploy, force-push, or make destructive/permission changes under this rule; those require separate authorization.

## 24-hour history review — 2026-11-22 to 2026-11-23 (ICT)

This is a bounded review of retrievable conversation summaries and current repository artifacts, not a claim that every raw message was exhaustively exported.

### Confirmed completed outcomes
- Provider work: history records commit `8eb52e86` and later commit `177b35e2160e9e8fd3559ea323db4b725471bd7f` on `ops/provider-free-go-clean`; the provider-focused test set was reported as 37/37 PASS. Treat the test result as reusable for the exact tested source SHA only. The available history does not expose enough raw detail to count every repeated edit/run between these commits.
- Repository status documentation: `README.md`, `RELEASE_STATUS.md`, and this work ledger were updated and pushed; latest known remote branch SHA is `787ef3729caa9bf2bb876c2dc097c51fa0821361` on `fix/q10-attachment-hardening-20261123` and `ops/provider-free-go-clean`. Do not redo these documentation updates without a new factual change.
- ChatGPT-to-Fireflies connector: account/meeting reads were verified. This is NOT proof that Fireflies is integrated with CK-NEXUS.

### Not completed / must not be counted as done
- Fireflies-to-CK-NEXUS and n8n-to-CK-NEXUS integration remained NOT VERIFIED/BLOCKED; n8n was not available on Termux at port 5678 and VPS was offline in the retrieved session summary.
- SonarCloud remained FAIL or cancelled; no completed issue-level disposition was evidenced.
- PR #392 remained OPEN / BLOCKED / REVIEW_REQUIRED in the latest prior check; do not claim merge.

### Duplicate-work finding and correction
- At least two provider-related commit points are recorded (`8eb52e86`, `177b35e...`) with the same reported 37/37 provider test outcome. This establishes repeated work around the same workstream, but the available summary is insufficient to assert an exact number of duplicate test executions or duplicate code edits.
- The assistant also revisited PR/status and release planning after prior results existed, instead of consistently treating the ledger and exact-SHA evidence as authoritative.
- Earlier wording that counted Fireflies as a completed CK-NEXUS integration was incorrect: only the ChatGPT connector read path was verified; CK-NEXUS integration was not.
- Going forward, count one task once by stable task fingerprint; later commits are revisions of that task, not separate completed outcomes. Reuse valid 37/37 evidence for its tested SHA and do not rerun it without a documented invalidation reason.
