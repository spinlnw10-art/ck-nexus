# Repository Organization — Safe Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make CK-NEXUS easier to navigate and maintain while preserving runtime behavior, release evidence, branch history and recoverability.

**Architecture:** Follow the current canonical application layout and organize documentation/navigation first. Perform duplicate migration consolidation and any archival only after every consumer is mapped and tests prove compatibility. Audit branches separately from file changes; branch cleanup is not part of the first implementation wave.

**Tech Stack:** Git/GitHub, Python, pytest, GitHub Actions, SQL migrations, Markdown.

**Spec:** `docs/audit/REPOSITORY_ORGANIZATION_AUDIT_2026-11-23.md`

## Global Constraints

- Never modify or delete original files or branches before exact path/SHA/reference review.
- Do not edit `main`; use a dedicated branch and draft PR.
- Keep Production NO-GO and do not change release gates or production configuration.
- Preserve `SHA256SUMS`, evidence, Q10–Q16 records, backups and provenance.
- Do not read secret values; inspect secret/config files as metadata only.
- Do not rename automation-consumed paths without updating every consumer and test.
- No branch deletion, force push, history rewrite, merge or deployment under this plan.
- Every consolidation requires rollback instructions and explicit human approval before deletion of originals.

## Review Focus

- Python import/package discovery behavior for empty `__init__.py` files.
- Runtime and packaged-install behavior for PostgreSQL and SQLite migrations.
- Workflow, release, evidence and checksum references to paths being moved.
- Existing open PRs and closed-unmerged branches whose unique commits may not be reachable from main.
- Historical evidence and backups that may be required for audit or recovery.

---

### Task 1: Complete all-branch retention inventory

**Files:**
- Create/update: `docs/audit/REPOSITORY_ORGANIZATION_AUDIT_2026-11-23.md`
- Create: machine-readable branch/file inventory under `docs/audit/evidence/` or attach as PR artifact.

**Interfaces:**
- Consumes: GitHub branch and PR inventory, main commit/tree SHA, prior PR #225 retention audit.
- Produces: branch-level KEEP / KEEP_RETAIN_HISTORY / REVIEW / ARCHIVE_CANDIDATE classification, exact commit/tree/blob identities, unique branch-only object list.

- [x] Freeze 401 pre-existing live branch names (track the audit branch separately), head SHAs, tree SHAs, commit dates, protection flags and PR relationships in machine-readable evidence.
- [x] For all 401 pre-existing live branches, calculate ahead/behind and inspect tree/file/blob identities; zero scan errors.
- [x] Identify same-head, same-tree and same-content groups without treating equality as deletion authorization.
- [ ] Complete reconciliation of GitHub Actions run history, environments, deployments, rulesets, release assets and external runbooks (candidate-specific current-main text/workflow checks are recorded; external evidence remains open).
- [ ] Complete a branch-by-branch delta reconciliation against PR #225's historical baseline (the older audit remains preserved as context).
- [x] Verify live branch counts and per-branch Git object/path counts against GitHub API and local Git results.

Expected: 401/401 pre-existing branch tips have machine-readable Git identity and object/path comparison evidence. Final retention classes remain pending external-use, deployment, release and recovery review; no branch deletion is authorized.

### Task 2: Build canonical documentation navigation

**Files:**
- Modify: `README.md` only if a specific navigation gap is demonstrated.
- Create/modify: `docs/README.md` (or existing canonical docs index after checking it).
- Create/modify: `docs/audit/...` as required.

**Interfaces:**
- Consumes: current docs tree and inbound-link inventory from Task 1.
- Produces: one maintained documentation index linking architecture, quick start, runtime/operations, integrations, security, testing, release, evidence and historical records.

- [ ] Inventory all Markdown files and classify by purpose, owner and freshness.
- [ ] Detect duplicate titles/near-duplicate documents and stale status claims.
- [ ] Identify inbound Markdown links and workflow/package references before proposing moves.
- [x] Draft index with links to existing paths; avoid moving files in this task.
- [x] Check all 107 relative links in the docs navigation index (0 broken); verify README release status remains NO-GO.
- [x] Check 23 relative links in README and 5 relative links in the audit report (0 broken); 135 checked relative links across changed Markdown files, 0 broken.
- [x] Run the available relative-link validation for changed Markdown files; full-repository Markdown lint and full docs classification remain open.

Expected: users can find the new navigation hub from README; the checked index has no broken relative links. Full docs classification remains pending.

### Task 3: Validate and consolidate PostgreSQL migration copies

**Files:**
- Candidate canonical source: `migrations/postgresql/001_email_gateway.sql`
- Review candidates: `migrations/001_email_journal.sql`, `services/email_gateway/migrations/postgresql.sql`
- Modify package metadata/checksum manifest/tests only if proven necessary.

**Interfaces:**
- Consumes: Task 1 path-reference inventory, current `services/email_gateway/repository.py`, packaging configuration.
- Produces: one canonical PostgreSQL migration source or a documented reason to retain multiple copies.

- [x] Inspect `pyproject.toml`, setuptools package-data configuration and the runtime migration loader; wheel/sdist contents remain unverified because Termux lacks `setuptools.build_meta`.
- [x] Search source, tests, scripts, workflows, Docker/deployment assets and docs for all three paths and generic migration globs; Docker Compose and installed-package runtime consumers are identified.
- [ ] Verify external installers, deployment scripts and operator runbooks before proposing any removal of the root-level copy.
- [ ] Add/adjust tests first for the canonical runtime/package contract; observe failure before implementation if behavior changes.
- [ ] If safe, change consumers/package data and regenerate `SHA256SUMS` in the same PR.
- [ ] Test source checkout and built package migration discovery; run relevant email gateway tests and full required suite.
- [ ] Keep original copies in the PR until reviewer and owner approve the exact deletion.

Expected: runtime and installed package resolve the intended schema; no migration path disappears without consumer replacement.

### Task 4: Classify historical documents and root-level files

**Files:**
- Candidate paths only after inventory; no predetermined delete list.

**Interfaces:**
- Consumes: Task 1 inbound references, evidence manifest and file ownership classification.
- Produces: path-by-path KEEP / KEEP_RETAIN_HISTORY / REVIEW / ARCHIVE_CANDIDATE report.

- [ ] Map every candidate file to runtime, build, test, docs, evidence, workflow or recovery consumers.
- [ ] Identify stale/contradictory status documents and preserve their history.
- [ ] Prefer an archive proposal over deletion; do not move files until link/checksum/package consumers are mapped.
- [ ] Produce exact old path, new path, blob SHA, references, tests and rollback for each proposed move.
- [ ] Request explicit owner approval before removing any original path.

Expected: no file is moved or removed solely because of age, size, naming, duplicate content or apparent lack of use.

### Task 5: Branch retention plan (separate from file organization)

**Files:**
- Update: `docs/audit/REPOSITORY_ORGANIZATION_AUDIT_2026-11-23.md`

**Interfaces:**
- Consumes: complete branch/PR/tree/object inventory from Task 1.
- Produces: branch retention table with exact SHA, PR state, unique commits/blobs, references, recovery value and proposed next action.

- [ ] Keep every branch with an open PR.
- [ ] Preserve closed-unmerged PR heads until their unique commits are reviewed and supersession is proven.
- [ ] Preserve backup/recovery branches until integrity and restore tests verify a replacement.
- [ ] Treat no-PR and identical-head branches as REVIEW, never auto-delete.
- [ ] Make no branch deletion in this implementation plan.

Expected: a reviewer can trace the reason for retaining every branch proposed for archival; no branch is deleted by this plan.

## Verification

- `git diff --check`
- Validate all changed Markdown links and paths.
- Run relevant Python tests and the full repository test command after any code or migration behavior changes.
- Verify built wheel/sdist contains all required migration assets.
- Compare `SHA256SUMS` against actual tracked files if changed.
- Re-fetch GitHub branch/PR state and verify original refs remain unchanged.
- Review the complete PR diff before marking ready.

## Rollback

All work is isolated in the audit branch. Revert the specific consolidation commit to restore previous paths; preserve original blobs and branches until explicit approval. Do not use force push or history rewriting.


## Execution record — 2026-11-23

- Work was isolated on `audit/repository-organization-20261123`; the user's existing Termux checkout was not switched or modified. Its active Q10 worktree remains clean and one commit ahead of its remote; 25 worktrees were detected and left untouched.
- Task 1 evidence files now include (401 pre-existing branch baseline; audit branch excluded):
  - `branch-head-tree-inventory-2026-11-23.json`
  - `branch-unique-object-inventory-2026-11-23.json`
  - `branch-path-diff-summary-2026-11-23.json`
  - `branch-protection-pr-associations-2026-11-23.json`
  - `duplicate-blob-groups-all-branches-2026-11-23.json`
  - `branch-unique-objects-vs-main-2026-11-23.tsv`
- The baseline scan covered all 401 pre-existing live branch refs, with zero scan errors. It found 371 branches with commits not in main, 367 branches with unique blobs, and 28 distinct exact duplicate blob/path-set signatures across branch snapshots. The audit branch itself is excluded from its own baseline to avoid self-reference.
- Task 2 navigation hub was created, README linked to it, and 135 relative links across changed Markdown files were checked with zero broken links.
- Tasks 3–5 remain gated: no migration package behavior was changed; no source files or evidence were moved/deleted; no branch was archived/deleted. Consumer, deployment, release, local-worktree and recovery reviews remain required.
- Verification: `git diff --check origin/main...origin/audit/repository-organization-20261123` exited 0; GitHub compare shows the audit branch ahead of main and not behind. No application test suite was run because the PR contains documentation and generated Git inventory evidence only.


### Task 3 consumer-mapping update

The current-main migration consumers were verified:
- `docker-compose.p0.yml` mounts `./migrations/postgresql` and executes `/migrations/001_email_gateway.sql`.
- `services/email_gateway/postgres_repository.py` loads the package-local `migrations/postgresql.sql`.
- `pyproject.toml` includes `services.email_gateway` package data matching `migrations/*.sql`.
- `SHA256SUMS` contains all three identical copies.
- A source-archive wheel build was attempted in Termux but the environment lacks `setuptools.build_meta`; wheel contents remain unverified.

Ruling: keep the two active deployment/package copies; classify `migrations/001_email_journal.sql` as REVIEW / possible archive candidate only. External consumers, wheel/CI verification, checksum regeneration and migration behavior tests remain required before any removal.


### Supplemental branch accounting

The 401 pre-existing branches remain the baseline. A later live check found 403 current remote refs: the 401 baseline branches, this audit branch, and `integration/autonomous-engineering-foundation` under separate Draft PR #394. That post-snapshot branch was checked separately at HEAD `723e9828579678d3ca041241999f110da72d95ae`: four commits ahead of main, four Markdown files added, no existing paths changed or removed. It was not modified by this plan.
