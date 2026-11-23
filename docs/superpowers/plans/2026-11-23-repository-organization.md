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

- [ ] Freeze branch names, head SHAs, commit dates, protection flags and PR relationships.
- [ ] For all 401 branches, calculate merge-base/ahead/behind against main and inspect tree/file/blob identities.
- [ ] Identify same-head, same-tree and same-content groups without treating equality as deletion authorization.
- [ ] Search workflow files, scripts, docs, tags, releases and deployments for branch/path references.
- [ ] Compare with PR #225 historical baseline and record changed/new branches.
- [ ] Verify report counts against GitHub API and local Git results.

Expected: every branch has an evidence-backed retention class; open PR heads and branches with unique unreconciled objects are retained.

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
- [ ] Draft index with links to existing paths; avoid moving files in this task.
- [ ] Check all relative links and verify README release status remains NO-GO.
- [ ] Run Markdown/link validation available in the repository.

Expected: users can find canonical documentation from README and docs index without breaking existing paths.

### Task 3: Validate and consolidate PostgreSQL migration copies

**Files:**
- Candidate canonical source: `migrations/postgresql/001_email_gateway.sql`
- Review candidates: `migrations/001_email_journal.sql`, `services/email_gateway/migrations/postgresql.sql`
- Modify package metadata/checksum manifest/tests only if proven necessary.

**Interfaces:**
- Consumes: Task 1 path-reference inventory, current `services/email_gateway/repository.py`, packaging configuration.
- Produces: one canonical PostgreSQL migration source or a documented reason to retain multiple copies.

- [ ] Inspect `pyproject.toml`, build backend package-data configuration and wheel/sdist contents.
- [ ] Search source, tests, scripts, workflows, Docker/deployment assets and docs for all three paths and generic migration globs.
- [ ] Verify any installer or external deployment consumer before proposing a move.
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
