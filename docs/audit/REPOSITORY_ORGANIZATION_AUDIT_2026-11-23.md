# CK-NEXUS Repository Organization Audit — 2026-11-23

Status: PHASE 1 INVENTORY / READ-ONLY / NO FILE OR BRANCH DELETION AUTHORIZED

## Scope and baseline

- Repository: `spinlnw10-art/ck-nexus`
- Default branch: `main`
- Audited main commit: `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`
- Main tree: `55bc545e5afd6379c46a464608601efeef213a6a`
- Recursive tree response: `truncated=false`
- Tracked files: 870
- Directories: 115
- Tracked content size reported by Git tree: 4,541,646 bytes
- Remote branches: 402 (including this audit branch)
- Pull requests returned across all states: 355
- Open PRs: 220
- Closed PRs: 135
- Merged PRs: 88
- Closed but unmerged PRs: 47
- Branch names with no PR head association in the enumerated PR set: 102

This phase inventories the complete current main tree and enumerates branch and PR references. It does not yet claim a complete per-branch tree/blob/unique-object review for all 401 branches. The older PR #225 retention audit inspected 274 branches at its 2026-09-04 baseline; its detailed decisions remain useful historical evidence but cannot substitute for re-auditing the 127 additional/currently changed branch references.

## Main tree composition

| Extension | Count |
|---|---:|
| Python (.py) | 497 |
| Markdown (.md) | 150 |
| Shell (.sh) | 57 |
| YAML (.yml) | 40 |
| JSON (.json) | 32 |
| systemd service | 19 |
| no extension | 10 |
| JavaScript (.js) | 9 |
| HTML (.html) | 9 |
| timer units | 9 |
| SQL (.sql) | 8 |
| CSS (.css) | 7 |
| other extensions | 23 |

Top-level layout includes application packages (`creator_app/`, `app/`, `services/`), automation and operations (`ops/`, `scripts/`, `deploy/`, `runbooks/`), docs and evidence (`docs/`, `evidence/`, `demo_evidence/`), interfaces and contracts (`gateway/`, `integrations/`, `contracts/`, `schemas/`), data migrations (`migrations/`), tests (`tests/`), and supporting orchestration/configuration.

The main README already defines canonical runtime entry point `python3 -m creator_app.unified`, describes the main architecture and links to core docs, and explicitly states Production is NO-GO. Preserve these statements and ensure future navigation reinforces rather than contradicts them.

## Exact duplicate-content findings in current main

Blob SHA comparison found exactly two duplicate-content groups in the current main tree.

### D1 — Empty Python package marker files (8 paths)

Blob SHA: `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`

- `app/__init__.py`
- `app/db/__init__.py`
- `creator_app/ai_team/tests/__init__.py`
- `creator_app/core/__init__.py`
- `creator_app/credentials/tests/__init__.py`
- `services/__init__.py`
- `services/billing/__init__.py`
- `tests/__init__.py`

Decision: KEEP all. Empty package markers can affect Python package discovery/import behavior and are not junk.

### D2 — PostgreSQL email gateway migration (3 paths)

Blob SHA: `a7c91587f2d3d461ae845a041cec21a59cb16789`; each file is 2,484 bytes.

- `migrations/001_email_journal.sql`
- `migrations/postgresql/001_email_gateway.sql`
- `services/email_gateway/migrations/postgresql.sql`

Evidence:
- Current `services/email_gateway/repository.py` explicitly documents production PostgreSQL schema at `migrations/postgresql/001_email_gateway.sql`.
- The same module loads the SQLite migration from `services/email_gateway/migrations/sqlite.sql`.
- GitHub code search for the exact `migrations/001_email_journal.sql` path text returned only `SHA256SUMS`.
- GitHub code search for the exact `services/email_gateway/migrations/postgresql.sql` path text returned only `SHA256SUMS`.
- GitHub code search for `migrations/postgresql/001_email_gateway.sql` returned `services/email_gateway/repository.py` and `SHA256SUMS`.

Decision: REVIEW / CONSOLIDATION CANDIDATE ONLY. Keep `migrations/postgresql/001_email_gateway.sql` as the provisional canonical source because it is explicitly named by runtime code. Do not remove the other two copies until package-data rules, installers, CI, external deployment scripts, migration discovery/globs and checksum generation are checked. If consolidated, update package metadata and SHA256SUMS in the same change and add tests proving runtime/package behavior.

## Branch and pull-request inventory

Branch prefix counts (401 total):

| Prefix | Count |
|---|---:|
| post-p0 | 122 |
| fix | 58 |
| feat | 40 |
| ops | 20 |
| verify | 20 |
| docs | 14 |
| security | 13 |
| arch | 12 |
| upgrade | 10 |
| cknexus | 9 |
| feature | 8 |
| research | 8 |
| dev | 5 |
| prep | 5 |
| backup | 4 |
| sale | 4 |
| audit | 3 |
| closure | 3 |
| other prefixes/root names | 63 |

PR inventory:
- 219 open PRs; these are active review references and must not be treated as cleanup candidates.
- 88 merged PRs; branch retention still requires checking unique commits, tags, release/evidence links and recovery value.
- 47 closed, unmerged PRs; preserve their commits until their unique content and supersession are established.
- 102 branch names had no matching PR head association in the enumerated PR pages. This is not proof that they are orphaned: they may be used by workflows, tags, deployments, docs, recovery, or other branches.

Notable live references:
- PR #387 remains open and documents outstanding Q10 independent security review, Q11 invalid API key, Q12 runner/cgroup blocker, and Production NO-GO.
- PR #371 is open and documents operational status and stale release-state concerns.
- PR #352 is open and is another repository consolidation/status documentation candidate.
- PR #225 is open and contains the previous file retention audit. Do not supersede or close it automatically.

## Historical retention audit comparison

PR #225 (`post-p0/repo-file-retention-audit-v1-20260904`) documented:
- 531 tracked files / 2,828,981 bytes at its baseline;
- 274 remote branches and 1,444 branch-only unique blobs inspected;
- main retention: KEEP 423, KEEP_RETAIN_HISTORY 12, REVIEW 85, ARCHIVE_CANDIDATE 11, DELETE_CANDIDATE 0;
- branch-only retention: KEEP 1,151, KEEP_RETAIN_HISTORY 29, REVIEW 255, ARCHIVE_CANDIDATE 9, DELETE_CANDIDATE 0;
- no file or branch deletion authorized.

Its detailed report: `docs/audit/GITHUB_FILE_RETENTION_DECISIONS_2026-09-04.md` on branch `post-p0/repo-file-retention-audit-v1-20260904`.

The old audit also identified exact duplicate JSON/SQLite migration pairs that are not present as duplicate blobs in the current main tree. Do not carry forward stale duplicate findings as if they were still current.

## Proposed retention decisions

| Finding | Proposed action | Confidence | Gate before action |
|---|---|---|---|
| 8 empty `__init__.py` files | KEEP | High | None; preserve package markers |
| 3 identical PostgreSQL migration files | REVIEW then consolidate at most two copies | Medium | Trace package/install/deploy/migration consumers; update checksums; tests |
| Historical docs/evidence | KEEP or archive-only candidate | Low until links checked | Search inbound links, release evidence, checksums and audit references |
| Root-level launchers/configs | KEEP pending ownership mapping | Low | Identify canonical runtime, compatibility contracts and all references |
| Branches with open PRs | KEEP | High | PR owner/review disposition |
| Branches with closed-unmerged PRs | RETAIN pending unique-commit review | High | Verify supersession and preserve unique objects |
| Branches without PRs | REVIEW only | Low | Scan workflow refs, tags, deployments, commit reachability, unique blobs and backup purpose |
| Backup branches/snapshots | KEEP_RETAIN_HISTORY | High | Verify backup integrity and replacement recovery test before any retention change |

No DELETE_CANDIDATE is approved by this phase.

## Required next audit phase — all 401 branches

Before proposing branch archival or deletion:
1. Freeze the branch inventory with names, head SHAs, commit dates, protection flags and default-branch relation.
2. Enumerate all open/closed PR references and branch head/base relationships; preserve every open PR head.
3. For every branch, compute merge-base/ahead/behind versus main, commit reachability, tree SHA, file paths, blob SHA and branch-only unique blobs.
4. Identify same-head and same-tree groups; identical HEAD/tree is a review signal, not deletion authorization.
5. Search workflow YAML, scripts, docs, tags, releases, deployments, GitHub Actions run references and external runbooks for branch-name references.
6. Classify each branch KEEP, KEEP_RETAIN_HISTORY, REVIEW or ARCHIVE_CANDIDATE. Do not use DELETE_CANDIDATE until all required evidence is present.
7. Preserve full commit/object history and produce a machine-readable CSV/JSON evidence manifest.

## File organization plan

Use the existing architecture rather than a disruptive monorepo migration:
- Keep application/runtime packages in their established locations.
- Keep tests adjacent to current test conventions; do not move tests across import/package boundaries without test updates.
- Keep operational scripts and runbooks in `scripts/`, `ops/`, `deploy/`, and `runbooks/` according to execution ownership.
- Consolidate documentation navigation through a maintained `docs/README.md` or equivalent index, with clear links to architecture, getting started, operations, security, testing, release, evidence and historical records.
- Group historical documents only in a later isolated PR after inbound links, checksum manifests, workflow references and release packaging are updated.
- Avoid renaming public/automation-consumed paths in the first pass.
- Keep `README.md` as the concise entry point and source of navigation, not a second full documentation archive.

## Safety rules

- No deletion or rewriting on `main`.
- No branch deletion, force push, history rewrite, merge or deployment during the audit.
- All changes must be made on a dedicated branch and submitted as a draft PR first.
- Preserve `SHA256SUMS`, release evidence, Q10/Q11/Q12/Q13/Q14/Q15/Q16 records, backup snapshots, audit logs and provenance until proven superseded.
- Never inspect secret values. Secret/config files are metadata-only.
- Every proposed move/delete must list exact path, blob SHA, references searched, replacement/archive destination, tests and rollback method.
- Human approval is required before any deletion, branch cleanup, merge or production action.

## Limitations and open work

This document is a verified phase-1 snapshot of the full current main tree and the complete branch/PR name inventory. The all-branch Git object and path-level comparison is now complete for the 402 live remote refs. External deployment/workflow history, release/tag use, local worktree ownership and recovery intent remain incomplete. This is not a final deletion manifest and authorizes no destructive operation.


## Addendum — local Git head/tree inventory (2026-11-23)

A read-only inventory was run against the Termux clone's fetched remote-tracking refs and cross-checked against `git ls-remote --heads origin`.

- Live remote branch refs: **402**
- Local remote-tracking refs present: 407
- Local-only stale tracking refs (not present in current live remote listing): 5
  - `docs/clarify-release-evidence-baseline-20261119`
  - `docs/rebaseline-release-status-20261119`
  - `feature/public-beta-feedback-20261119`
  - `pr-387`
  - `pr-392-audit`
- Distinct branch head commits: **381**
- Distinct root tree SHAs: **373**
- Branch refs whose tips are merged into main according to `git branch -r --merged origin/main`: **30** (includes `main`)
- Branch refs not merged into main: **372**
- Only `main` has the same root tree SHA as current `main`.
- Same-HEAD groups: **18** groups (including backup pairs and parallel feature/fix/post-p0/verify/Q10 branches).
- Same-tree groups: **22** groups (some branches have different commits but identical root trees).

The exact per-branch name, head SHA, tree SHA, merged-into-main boolean, and local SHA comparison are preserved in [branch-head-tree-inventory-2026-11-23.json](evidence/branch-head-tree-inventory-2026-11-23.json).

Important interpretation:
- Same HEAD/tree is evidence of identical snapshots only; it does not prove the branch has no PR, tags, deployment, backup or recovery purpose.
- A branch tip being merged into main does not alone authorize deletion; branch protection, PR references, tags/releases, GitHub Actions, deployments, and recovery policies must still be checked.
- The five stale local tracking refs are not current remote branches. They were left untouched; their local presence may still be useful for forensic comparison.
- The head/tree snapshot is now supplemented by full per-branch ahead/behind, unique commit/blob, and path-level tree comparisons (see the evidence files below). External deployment/workflow history and owner/recovery intent still require review before any archival recommendation.

PR inventory was refreshed after opening this audit PR: **355 total**, **220 open**, **135 closed** (**88 merged**, **47 closed-unmerged**). These counts are a point-in-time snapshot and will change as PR activity continues.


## Addendum — full all-branch object and path-level comparison (2026-11-23)

The local Git scan used the 402 live remote branch names from the branch inventory (not the five stale local-only tracking refs) and compared each branch tip against `origin/main` at `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`.

### Per-branch Git object reachability

- Branches scanned: **402 / 402**
- Scan errors: **0**
- Branches ahead of main (one or more unique commits): **372**
- Branches behind main: **387**
- Branches with unique commits: **372**
- Branches with unique blob objects: **368**
- Branches with zero unique commits and zero unique blobs: **30**
- Branches with unique commit(s) but no unique blob: **4**
  - `backup/pre-consolidation-20261031` — 1 unique commit, 0 unique blobs
  - `backup/termux-20261029` — 1 unique commit, 0 unique blobs
  - `code-coverage-agent/fix-341440761-1333067619-504675e3-5573-4c55-8a40-02cfbfbc651f` — 1 unique commit, 0 unique blobs; closed-unmerged PR #296
  - `r33-closure-hardening-v02` — 1 unique commit, 0 unique blobs
- Per-branch unique-object counts are not additive repository-wide; the same blob/commit can be counted for multiple branches.

Full per-branch ahead/behind, unique commit/blob/tree/object counts and head dates: [branch-unique-object-inventory-2026-11-23.json](evidence/branch-unique-object-inventory-2026-11-23.json).

### Per-branch file-path and duplicate-content comparison

- Branch trees scanned: **402 / 402**
- Scan errors: **0**
- Main tracked files: **870**
- Total branch-tree file entries across all snapshots: **222,770**
- Branches with a path/blob difference from main: **401**
- Branches with exactly the same path/blob tree as main: **1** (`main`)
- Aggregate branch-tree comparison instances: **41,685 changed-path instances**, **11,977 branch-only path instances**, and **138,947 main-path-missing instances**. These are summed across branch snapshots, not unique repository files.
- Across all branch snapshots, the scanner recorded **1,606 duplicate-blob groups** and **4,083 duplicate extra-path instances**. These are per-tree group occurrences, not 1,606 distinct repository-wide duplicate files.
- Current main still has exactly the two duplicate-content groups documented above: 8 empty package markers (KEEP) and 3 identical PostgreSQL migration copies (REVIEW).

Full per-branch file counts, changed paths, branch-only paths, main paths missing and duplicate-group counts: [branch-path-diff-summary-2026-11-23.json](evidence/branch-path-diff-summary-2026-11-23.json).

### Branch protection, PRs, tags and low-delta review candidates

GitHub branch API and PR inventory:
- 402 remote branches.
- Only `main` is marked protected by the branch API.
- 355 PRs: 220 open, 135 closed (88 merged, 47 closed-unmerged).
- 219 branch names map to at least one open PR head; 102 branch names have no PR head association.
- One Git tag exists: `v0.2.0-buyer`.

Full branch protection flags and branch-to-PR head associations: [branch-protection-pr-associations-2026-11-23.json](evidence/branch-protection-pr-associations-2026-11-23.json).

The following **13 branches** have zero unique commits and zero unique blobs versus main, no associated PR head in the captured PR inventory, and no exact textual reference in the current main tracked files. They are **ARCHIVE_CANDIDATE_PENDING**, not deletion candidates:

- `feat/facebook-meta-connector`
- `fix/q05-bandit`
- `fix/q15-launcher-mode`
- `noop`
- `ops/canonical-export-20260904-run`
- `ops/canonical-export-20260904-trigger`
- `post-p0/standards-integration-v1`
- `q10/aikido-frozen-39f5c1ad`
- `q10/aikido-frozen-39f5c1ad-20260829`
- `q10/frozen-39f5c1ad-aikido`
- `revert/pr-348`
- `tmp-do-not-use`
- `verify/q04-q05-converged-v3`

One nearby low-delta branch is explicitly **KEEP** pending workflow migration: `release/q04-q08-clean` has zero unique commits/blobs but is referenced in `.github/workflows/ci.yml` (branch filter and job condition).

Do not confuse the 30 branches with zero unique commits/blobs with deletable branches. Some still have PR relationships (including open PRs), and others may have local worktrees, external deployment references, release/evidence associations or recovery value. The four branches with unique commits but no unique blob must retain their commit objects until the commit purpose is reviewed. Backup branches remain KEEP_RETAIN_HISTORY.

### Final gates before any branch archival/deletion

1. Match the single tag `v0.2.0-buyer` to its exact target and check release assets and deployment provenance.
2. Inspect repository rulesets, branch protection policy, GitHub Actions run history, environments, deployments and workflow filters; the branch API `protected` flag alone is not sufficient.
3. Search all open/closed PR head/base refs and verify supersession, especially closed-unmerged PR heads.
4. Check the 25 local Git worktrees and owners; do not remove local branches/worktrees as part of this PR.
5. Confirm external consumers, operator runbooks and recovery intent with the owner.
6. For any approved archive, create and verify a recoverable immutable ref/backup first, then request a separate explicit approval before deletion.

No branch archival, deletion, or merge is performed in this audit PR.
