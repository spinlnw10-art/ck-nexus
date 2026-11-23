# CK-NEXUS Intra-Repository Cleanup and Legacy Audit Addendum — 2026-11-23

Baseline inspected: canonical `main` tree SHA `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`; 870 tracked blobs/files. Read-only tree and targeted file inspection. This addendum does not authorize removal or runtime changes.

## 1. Exact duplicate blob scan within canonical repository

Unlike the earlier cross-repository comparison, this scan groups identical Git blob SHAs across paths inside the same `ck-nexus` default-branch tree.

Two duplicate groups were found:

| Blob SHA | Paths | Interpretation | Disposition |
|---|---|---|---|
| `a7c91587f2d3d461ae845a041cec21a59cb16789` | `migrations/001_email_journal.sql`; `migrations/postgresql/001_email_gateway.sql`; `services/email_gateway/migrations/postgresql.sql` | Exact 2,484-byte SQL content repeated at 3 paths | Do not delete until migration runner, packaging, docs, tests and deployment references are mapped. Likely choose one canonical source and retain compatibility path only if tooling requires it. |
| `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | eight `__init__.py` paths in app, creator_app and services | All are empty Python package markers | Harmless structural reuse; not cleanup candidates absent package-layout changes. |

The SQL duplicate group is confirmed byte-for-byte, not merely similar by filename. The three files must be traced through all migration runners and deployment packaging before a consolidation proposal is made.

## 2. n8n: retired integration, residual source and operational artifacts

`docs/INTEGRATION_HUB.md` (blob `cce6db1eaab12e5e93c2b4d9e52d3f828b68f1ab`) explicitly says n8n was removed from the active CK-NEXUS runtime in R14 and that no current compose service, API integration, P0 gate or deployment script may start or require it.

However, default-branch tree still contains:
- `creator_app/n8n_intelligence/` (multiple Python modules, including a restricted read-only API client and AutoGitOps implementation);
- `creator_app/web/n8n-workflows.html`;
- `ops/vps/scripts/cknexus_n8n_*.py` and `connect-n8n.sh`;
- `ops/vps/systemd/cknexus-n8n-*.service` and timer units;
- `scripts/n8n_evidence_export.py`;
- n8n-specific tests and historical design plans/specs.

This is a **policy-to-tree inconsistency / legacy residue candidate**, not proof that all these files are unused. The code contains nontrivial bounded behavior: the read client validates HTTPS/loopback URL and caps reads; AutoGitOps has explicit path allowlists, denied paths and protected paths. Removing the package wholesale could therefore remove tests, evidence, or behavior that is still imported by other modules.

Required next checks:
1. Search every Python import, route registration, CLI entrypoint, service installer, workflow, docs and packaging reference to these paths and environment variables.
2. Identify which n8n systemd units are installed/enabled on each target host using read-only service inventory; GitHub source alone cannot establish live host state.
3. Classify each artifact as dead code, historical evidence, compatibility adapter, or accidentally active runtime.
4. If no active references remain, propose a separate archive/removal PR with test updates and an explicit rollback; do not remove files in this audit PR.

## 3. VPS cleanup scripts: destructive capability warning

The following tracked scripts contain actual destructive operations and must never be bulk-run or categorized as harmless duplicates by filename:
- `ops/vps/scripts/ck-cleanup.sh`: removes named files under home and temporary directories; removes empty directories.
- `ops/vps/scripts/cknexus-final-cleanup.sh`: deletes old temporary files, Python bytecode, a specific Codex temporary clone, vacuums system journal, and invokes `docker system prune -f`.
- `ops/vps/scripts/cknexus-safe-cleanup.sh`: deletes old temporary files and selected cache data; vacuums journal and clears npm cache.

The `final-cleanup` script has a broader effect surface than its name alone suggests. Although it states that Docker volumes and project source are protected, `docker system prune -f` can remove unused Docker resources. All three scripts should receive metadata headers declaring scope, dry-run support, required approval, protected paths, and expected side effects. A safe follow-up should add dry-run mode and explicit target allowlists before any execution is considered. This audit did not execute any script.

There are 30+ files under `ops/vps/scripts/`, with overlapping naming patterns (cleanup, final, signoff, Q10/Q11/Q16). Similar names do not establish duplicate behavior. Build a per-script capability table from complete contents, references and historical provenance.

## 4. Compose and environment examples

The repository has at least four root environment examples:
- `.env.example`
- `.env.p0.example`
- `.env.prod.example`
- `.env.universal.example`

It also has distinct deployment definitions including:
- `docker-compose.p0.yml`
- `docker-compose.prod.yml`
- `docker-compose.r9-r11.yml`
- `deploy/searxng/docker-compose.yml`

The inspected P0 compose file starts PostgreSQL, a migration job, the CK-NEXUS app, and an optional Redis queue profile. The production compose file has a distinct edge/Caddy, Redis and runtime-binding configuration. These are not interchangeable merely because they are Compose YAML files.

Next step: extract variable sets from each example and compose file, map each to its deployment stage and CI workflow, validate with Compose config using dummy values only, and document owner/status. Retain distinct environment files while they represent distinct supported environments; retire only after reference and deployment evidence proves they are obsolete.

## 5. Documents and evidence

`docs/plans/`, `docs/specs/`, `docs/superpowers/plans/` and `evidence/` contain both design history and release/audit artifacts. Historical evidence may be essential to explain prior decisions and cannot be treated as dead weight based on age.

Recommended classification:
- `ACTIVE`: current normative architecture, release contracts, runbooks and approved implementation plans.
- `HISTORICAL`: superseded designs, old release plans, prior architecture decisions.
- `EVIDENCE-IMMUTABLE`: test output, Q-gate records, attestations and release evidence bound to a commit/subject.
- `UNVERIFIED`: documents whose current applicability or subject SHA has not been checked.

Add front matter or a status index with owner, status, date, source commit/subject SHA and superseding document. Do not rewrite historical evidence in place; add a correction or superseding record.

## 6. Verified facts versus open work

Verified from GitHub default-branch source:
- 870 tracked blobs/files and 2 exact duplicate blob groups inside this repository.
- Three SQL migration paths are byte-identical (same SHA and 2,484 bytes).
- Eight empty `__init__.py` files share the empty-blob SHA.
- Integration Hub says n8n is retired from active runtime, while residual n8n source/tests/systemd artifacts remain in tree.
- The inspected cleanup scripts include destructive file, journal and Docker-prune operations.
- P0 and production Compose definitions have different service/configuration purposes.

Not yet established:
- exact number of lines (requires checkout or complete content retrieval and deterministic counting);
- all Python imports/routes and workflow references to n8n;
- whether n8n services are installed or running on any VPS;
- whether any VPS cleanup script is still operationally required;
- canonical migration path and all consumers of each identical SQL file;
- complete variable mapping for every env example and compose file;
- whether any historical docs/evidence can be archived or are release dependencies.

## 7. Safe disposition

| Area | Current decision |
|---|---|
| n8n source/tests/systemd | HOLD; dependency and live-host inventory before archive/removal |
| VPS cleanup scripts | HOLD; do not execute; annotate and add dry-run/allowlist proposal |
| Three identical SQL migrations | CONFIRMED DUPLICATE; map all references before choosing canonical path |
| Empty package markers | KEEP |
| docs/plans/specs/evidence | CLASSIFY, do not delete |
| env examples and Compose files | KEEP distinct until environment contract map proves redundancy |

No source, branch, backup, production configuration, database, credential or host state was modified. No cleanup command was executed.
